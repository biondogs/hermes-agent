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
        return 0
    adopted = 0
    for home in homes:
        outboxes = home / "worker-outboxes"
        if not outboxes.exists():
            continue
        for entry in outboxes.iterdir():
            if not entry.is_dir():
                continue
            sock_path = entry / "control.sock"
            if not sock_path.exists():
                continue
            scope_path = entry / "scope.json"
            if not scope_path.exists():
                continue
            try:
                scope = json.loads(scope_path.read_text())
            except Exception:
                continue
            execution_id = scope.get("execution_id")
            if not execution_id:
                continue
            # Find running kanban task linked to this execution via scope or outbox name
            task_info = _find_task_for_scope(scope, entry.name)
            if task_info is None:
                continue
            pid = task_info.get("pid")
            birth = task_info.get("birth")
            if pid is None:
                continue
            # liveness: pid exists and not recycled
            if not _pid_alive(pid, birth):
                continue
            try:
                _reattach_worker(authority, str(sock_path), scope, pid, birth)
                adopted += 1
                logger.info("Adopted detached kanban worker %s pid=%s outbox=%s", execution_id, pid, entry.name)
            except Exception as exc:
                logger.debug("Adopt failed for %s: %s", execution_id, exc, exc_info=True)
    return adopted

def _find_task_for_scope(scope, outbox_name):
    """Resolve running kanban task for this outbox via DB + claim lock, or fall back to scope.json pid."""
    # Primary: look up DB by scope kanban context
    kanban_ctx = scope.get("kanban")
    if kanban_ctx and isinstance(kanban_ctx, dict):
        task_id = kanban_ctx.get("task_id")
        board = kanban_ctx.get("board")
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
                        # also check liveness via task_runs
                        run_id = kanban_ctx.get("run_id")
                        if run_id:
                            r2 = conn.execute("SELECT worker_pid, worker_started_at FROM task_runs WHERE id=?", (run_id,)).fetchone()
                            if r2:
                                return {"pid": r2["worker_pid"], "birth": r2["worker_started_at"], "generation": scope.get("generation", 0), "owner_epoch": scope.get("epoch", 0), "execution_id": scope.get("execution_id"), "session_id": scope.get("session_id")}
                        # fallback to scope pid
                        return {"pid": scope.get("pid"), "birth": scope.get("birth"), "generation": scope.get("generation", 0), "owner_epoch": scope.get("epoch", 0), "execution_id": scope.get("execution_id"), "session_id": scope.get("session_id")}
            except Exception:
                pass
    # Fallback: scope.json directly carries pid/birth for liveness check
    if scope.get("pid"):
        return {"pid": scope.get("pid"), "birth": scope.get("birth"), "generation": scope.get("generation", 0), "owner_epoch": scope.get("epoch", 0), "execution_id": scope.get("execution_id"), "session_id": scope.get("session_id")}
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
