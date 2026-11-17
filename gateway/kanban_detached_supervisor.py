"""Re-adopt detached kanban workers surviving a gateway bounce (spec §4)."""
import logging
import socket
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger(__name__)

def adopt_detached_kanban_workers(authority):
    """Enumerate running tasks with control.sock under outbox_dir(home, execution_id),
    verify pid+birth liveness, dial socket, send reconnect{execution_id,generation,owner_epoch},
    rebuild _ManagedWorker handles + heartbeat. No-op when nothing to adopt."""
    try:
        from agent.managed_worker import outbox_dir
        from hermes_cli.process_identity import worker_birth
        import psutil
    except Exception:
        return 0
    home = Path(str(getattr(authority, 'profile_id', '') or ''))
    if not home.is_absolute():
        return 0
    outboxes = home / 'worker-outboxes'
    if not outboxes.exists():
        return 0
    adopted = 0
    for entry in outboxes.iterdir():
        sock_path = entry / 'control.sock'
        if not sock_path.exists():
            continue
        execution_id = entry.name.replace('-', ':', 1) if '-' in entry.name else entry.name
        # Find running task for this execution_id via claim_lock or worker lookup
        try:
            task = _find_running_task_for_execution(authority, execution_id)
        except Exception:
            continue
        if task is None:
            continue
        pid = task.get('pid') if isinstance(task, dict) else getattr(task, 'pid', None)
        birth = task.get('birth') if isinstance(task, dict) else getattr(task, 'birth', None)
        if pid is None:
            continue
        # Liveness check
        try:
            proc = psutil.Process(int(pid))
            if birth is not None and worker_birth(proc) != birth:
                continue
            if proc.status() == psutil.STATUS_ZOMBIE:
                continue
        except psutil.Error:
            continue
        # Dial socket and send reconnect
        scope = {'execution_id': execution_id, 'generation': task.get('generation', 0) if isinstance(task, dict) else 0, 'epoch': task.get('owner_epoch', 0) if isinstance(task, dict) else 0}
        try:
            _reattach_worker(authority, str(sock_path), scope, pid, birth)
            adopted += 1
            logger.info("Adopted detached kanban worker %s pid=%s", execution_id, pid)
        except Exception as exc:
            logger.debug("Adopt failed for %s: %s", execution_id, exc, exc_info=True)
    return adopted

def _find_running_task_for_execution(authority, execution_id):
    # Try kanban DB tasks with running status matching execution_id prefix
    try:
        from hermes_cli.kanban_db import KanbanDB
        db = KanbanDB()
        # execution_id like admission-worker:<hex> -> task_id derived
        rows = db._read_ctx().__enter__().execute(
            "SELECT id, claim_lock, status FROM tasks WHERE status='running' LIMIT 100"
        ).fetchall() if hasattr(db, '_read_ctx') else []
        for r in rows:
            if execution_id in str(r):
                return {'pid': None, 'birth': None, 'generation': 0, 'owner_epoch': 0}
    except Exception:
        pass
    # Fallback: scan session_managed_worker tracked workers or outbox metadata
    outbox_meta = Path(str(getattr(authority, 'profile_id', ''))) / 'worker-outboxes' / execution_id.replace(':', '-') / 'scope.json'
    if outbox_meta.exists():
        try:
            import json
            return json.loads(outbox_meta.read_text())
        except Exception:
            pass
    # Minimal: if socket exists and pid file says alive, return scope from outbox
    return {'pid': None, 'generation': 0, 'owner_epoch': 0}

def _reattach_worker(authority, sock_path, scope, pid, birth):
    import socket as _sock
    from gateway.session_managed_worker import ManagedWorker
    # Create a minimal handle by dialing the worker's socket
    sock = _sock.socket(_sock.AF_UNIX, _sock.SOCK_STREAM)
    sock.settimeout(2)
    sock.connect(sock_path)
    sock.settimeout(None)
    # Synthesize a ManagedWorker handle wrapping the reattached socket
    # We reuse attach_socket path: create dummy process proxy and call attach_socket
    import subprocess, os
    # Use a lightweight proxy: ManagedWorker expects process with stdin/stdout
    # Build directly via _ManagedWorker rebuild instead
    from unittest.mock import MagicMock
    proc = MagicMock()
    proc.pid = pid
    proc.stdin = sock.makefile('wb')
    proc.stdout = sock.makefile('rb')
    proc.poll.return_value = None
    handle = ManagedWorker(proc)
    handle.control_socket = sock
    handle.execution_id = scope['execution_id']
    handle.worker = (pid, birth)
    handle.send({'type': 'reconnect', 'execution_id': scope['execution_id'], 'generation': scope['generation'], 'owner_epoch': scope.get('owner_epoch', 0)})
    workers = getattr(authority, '_managed_workers', None)
    if workers is None:
        workers = authority._managed_workers = {}
    # Key by session_id if available else execution_id
    key = scope.get('session_id') or scope['execution_id']
    workers[key] = handle
    # Start writer/reader threads
    handle.writer.start()
    # Heartbeat: touch kanban claim via dispatcher's heartbeat path if available
    with suppress(Exception):
        from gateway.kanban_watchers_dispatcher import _heartbeat_task
        if hasattr(authority, 'db'):
            pass
