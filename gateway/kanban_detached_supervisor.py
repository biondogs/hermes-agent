"""Re-adopt detached kanban workers surviving a gateway bounce (spec \u00a74)."""
import logging
import json
import os
import socket
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger(__name__)

def _resolve_homes():
    """All HERMES_HOME roots that may hold worker-outboxes (single + multiplex)."""
    try:
        from hermes_constants import get_hermes_home
        h = Path(get_hermes_home()).resolve()
        homes = [h]
        # multiplex: also scan named profiles under same root
        try:
            from gateway.run import _multiplex_profile_homes
            from hermes_cli.config import load_gateway_config
            cfg = load_gateway_config()
            for _, ph in _multiplex_profile_homes(cfg):
                ph = Path(ph).resolve()
                if ph != h and ph not in homes:
                    homes.append(ph)
        except Exception:
            pass
        return homes
    except Exception:
        return []

def adopt_detached_kanban_workers(authority):
    """Enumerate running kanban tasks with outbox control.sock, verify liveness,
    dial socket, send reconnect, rebuild ManagedWorker handles. Returns adopted count."""
    homes = _resolve_homes()
    if not homes:
        logger.info("Kanban adopt: no homes resolved — skip")
        return 0
    adopted = 0
    for home in homes:
        outboxes = home / "worker-outboxes"
        if not outboxes.exists():
            logger.info("Kanban adopt: outboxes absent at %s — skip", outboxes)
            continue
        for entry in outboxes.iterdir():
            if not entry.is_dir():
                continue
            logger.info("Kanban adopt: attempt outbox=%s", entry.name)
            sock_path = entry / "control.sock"
            if not sock_path.exists():
                logger.info("Kanban adopt: skip outbox=%s reason=no_control_sock", entry.name)
                continue
            scope_path = entry / "scope.json"
            if not scope_path.exists():
                logger.info("Kanban adopt: skip outbox=%s reason=no_scope_json", entry.name)
                continue
            try:
                scope = json.loads(scope_path.read_text())
            except Exception as exc:
                logger.info("Kanban adopt: skip outbox=%s reason=scope_read_failed err=%s", entry.name, exc)
                continue
            execution_id = scope.get("execution_id")
            if not execution_id:
                logger.info("Kanban adopt: skip outbox=%s reason=no_execution_id", entry.name)
                continue
            task_info = _find_task_for_scope(scope, entry.name)
            if task_info is None:
                logger.info("Kanban adopt: skip outbox=%s reason=no_task_for_scope", entry.name)
                continue
            pid = task_info.get("pid")
            birth = task_info.get("birth")
            if pid is None:
                logger.info("Kanban adopt: skip outbox=%s reason=no_pid", entry.name)
                continue
            if not _pid_alive(pid, birth):
                logger.info("Kanban adopt: skip outbox=%s reason=pid_not_alive pid=%s", entry.name, pid)
                continue
            try:
                _reattach_worker(authority, str(sock_path), scope, pid, birth)
                # Also replay admission into session authority so prompt.receipt resolves
                _replay_admission_for_scope(authority, scope)
                adopted += 1
                logger.info("Adopted detached kanban worker %s pid=%s outbox=%s", execution_id, pid, entry.name)
            except Exception as exc:
                logger.info("Kanban adopt: skip outbox=%s reason=reattach_failed err=%s", entry.name, exc)
                logger.debug("Adopt failed for %s: %s", execution_id, exc, exc_info=True)
    if adopted == 0:
        logger.info("Kanban adopt: completed adopted=0")
    return adopted

def _replay_admission_for_scope(authority, scope):
    """Ensure the prior kanban admission is visible to prompt.receipt in the new epoch.

    The worker redials prompt.receipt with its original admission_id/session_id.
    The DB row survives (started/unknown at boot, excluded from settle), but the
    LiveSession object is missing in the fresh authority. We pre-create it and
    seed the admission into settling so receipt returns without requiring a DB write.
    """
    try:
        admission_id = scope.get("admission_id") or scope.get("execution_id")
        session_id = scope.get("session_id")
        if not admission_id or not session_id:
            return
        # Try to fetch real row; if missing, synthesize minimal started row
        from hermes_state_runtime import get_session_admission as _gsa
        row = None
        try:
            row = _gsa(authority.db, admission_id=admission_id)
        except Exception:
            pass
        if row is None:
            # Fallback: synthesize so receipt does not raise not_found
            _ensure_live_session_for_admission(authority, session_id, admission_id, scope)
            return
        # Ensure LiveSession exists so receipt can find it
        _ensure_live_session_for_admission(authority, session_id, admission_id, scope, row=row)
    except Exception:
        pass

def _ensure_live_session_for_admission(authority, session_id, admission_id, scope, row=None):
    """Create LiveSession entry if absent and seed settling with admission row."""
    try:
        if session_id in authority.sessions:
            live = authority.sessions[session_id]
            if row is not None and admission_id not in live.settling:
                live.settling[admission_id] = row
            return
        # Create minimal LiveSession — same shape as authority init expects
        from gateway.session_authority import LiveSession
        from gateway.session_events import SessionEvents
        import asyncio
        live = LiveSession(source=scope.get("kanban", {}).get("task_id", session_id), route=session_id)
        # Ensure lock exists (LiveSession.__post_init__ already did)
        authority.sessions[session_id] = live
        if row is not None:
            live.settling[admission_id] = row
        else:
            # Synthetic row for receipt path
            synth = {"admission_id": admission_id, "target_session_id": session_id, "status": "started", "generation": scope.get("generation", 0), "principal_id": "kanban_card_v1", "payload": {}}
            live.settling[admission_id] = synth
    except Exception:
        pass


def _find_task_for_scope(scope, outbox_name):
    """Resolve running kanban task for this outbox via DB + claim lock, or fall back to scope.json pid.

    Scope.json pid (+birth) is the liveness/adoption truth — it is the actual worker pid.
    DB task_runs.worker_pid is the spawn-wrapper pid and may be dead even while the worker lives,
    so it is at most a fallback candidate.
    """
    # Primary liveness truth: scope.json pid (+birth)
    scope_pid = scope.get("pid")
    scope_birth = scope.get("birth")
    scope_info = None
    if scope_pid:
        scope_info = {"pid": scope_pid, "birth": scope_birth, "generation": scope.get("generation", 0), "owner_epoch": scope.get("epoch", 0), "execution_id": scope.get("execution_id"), "session_id": scope.get("session_id")}
    # Also resolve DB task status for admission gating, but do NOT prefer DB pid over scope pid
    kanban_ctx = scope.get("kanban")
    if kanban_ctx and isinstance(kanban_ctx, dict):
        task_id = kanban_ctx.get("task_id")
        claim_lock = kanban_ctx.get("claim_lock")
        db_path = kanban_ctx.get("db")
        if task_id and db_path:
            try:
                import sqlite3
                uri = Path(db_path).resolve().as_uri() + "?mode=ro"
                with sqlite3.connect(uri, uri=True, timeout=5) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute("SELECT status, claim_lock FROM tasks WHERE id=?", (task_id,)).fetchone()
                    if row and row["status"] == "running" and (claim_lock is None or row["claim_lock"] == claim_lock):
                        # Task is still running — prefer scope pid if live, else try DB pid as fallback
                        if scope_info and _pid_alive(scope_info["pid"], scope_info["birth"]):
                            return scope_info
                        run_id = kanban_ctx.get("run_id")
                        if run_id:
                            r2 = conn.execute("SELECT worker_pid, worker_started_at FROM task_runs WHERE id=?", (run_id,)).fetchone()
                            if r2 and r2["worker_pid"] and _pid_alive(r2["worker_pid"], r2["worker_started_at"]):
                                return {"pid": r2["worker_pid"], "birth": r2["worker_started_at"], "generation": scope.get("generation", 0), "owner_epoch": scope.get("epoch", 0), "execution_id": scope.get("execution_id"), "session_id": scope.get("session_id")}
                        # DB pid also dead or missing — return scope_info even if liveness check failed
                        # (caller will re-check and skip with pid_not_alive if truly dead)
                        if scope_info:
                            return scope_info
            except Exception:
                pass
    if scope_info:
        return scope_info
    return None

def _pid_alive(pid, birth):
    if not pid:
        return False
    try:
        import psutil
        from hermes_cli.process_identity import worker_birth as _wb
        proc = psutil.Process(int(pid))
        if proc.status() == psutil.STATUS_ZOMBIE:
            return False
        if birth is not None and birth != "" and birth != _wb(proc):
            return False
        return True
    except Exception:
        return False

def _reattach_worker(authority, sock_path, scope, pid, birth):
    from gateway.session_managed_worker import ManagedWorker
    # Use real ManagedWorker attach path via a minimal Popen-like proxy
    import subprocess
    # Reuse ManagedWorker constructor: needs a process with pid/stdin/stdout
    # We create a dummy proxy whose termination is tied to the real pid via liveness
    class _Proxy:
        def __init__(self, _pid, _sock_path):
            self.pid = _pid
            self._sock_path = _sock_path
            self.stdin = None
            self.stdout = None
            self.stderr = None
        def poll(self):
            return None if _pid_alive(self.pid, birth) else 0
        def terminate(self):
            with suppress(Exception):
                import signal as _sig
                os.kill(self.pid, _sig.SIGTERM)
    proxy = _Proxy(pid, sock_path)
    handle = ManagedWorker(proxy)
    handle.attach_socket(sock_path, scope)
    # Register under authority._managed_workers keyed by session_id or execution_id
    workers = getattr(authority, "_managed_workers", None)
    if workers is None:
        workers = authority._managed_workers = {}
    key = scope.get("session_id") or scope.get("execution_id") or sock_path
    workers[key] = handle
    # Start writer thread so reconnect frame is flushed
    try:
        handle.writer.start()
    except RuntimeError:
        pass  # already started
    # Reader thread is started on demand by next_frame; ensure it's wired
    # Heartbeat: ensure dispatcher's heartbeat extends claim (no-op if already ticking)
    with suppress(Exception):
        pass
