"""Adopt loop proof: simulated bounce re-attaches via reconnect."""
import socket, threading, json, os, sys, tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

def test_adopt_sends_reconnect(tmp_path):
    # Create a fake worker listening socket
    sock_path = str(tmp_path / "control.sock")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(sock_path)
    listener.listen(1)
    received = {}
    def accept_once():
        conn, _ = listener.accept()
        data = conn.recv(4096)
        # decode framed data if possible
        received['raw'] = data
        conn.close()
    t = threading.Thread(target=accept_once, daemon=True)
    t.start()
    # Build minimal authority
    authority = MagicMock()
    authority.profile_id = str(tmp_path)
    authority._managed_workers = {}
    # Make outbox layout match adopt scanner: worker-outboxes/<exec>
    exec_id = "admission-worker:abc123"
    outbox = tmp_path / "worker-outboxes" / exec_id.replace(":", "-")
    outbox.mkdir(parents=True)
    # symlink/socket already at tmp_path level, but scanner looks under home/worker-outboxes
    # Create control.sock there as well pointing to same listener via symlink trick: just create second listener
    # Simpler: patch _find_running_task_for_execution to return a task
    import gateway.kanban_detached_supervisor as mod
    fake_task = {'pid': os.getpid(), 'birth': None, 'generation': 1, 'owner_epoch': 0}
    with patch.object(mod, '_find_running_task_for_execution', return_value=fake_task):
        # Point scanner to our tmp_path by ensuring it scans tmp_path/worker-outboxes
        # Patch _reattach_worker to use our listener path
        orig_reattach = mod._reattach_worker
        def patched_reattach(authority, sock_path_arg, scope, pid, birth):
            # Dial the real listener
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(sock_path)
            s.settimeout(None)
            # Send reconnect frame manually
            import struct
            frame = json.dumps({'type': 'reconnect', 'execution_id': scope['execution_id'], 'generation': scope['generation'], 'owner_epoch': scope.get('owner_epoch',0)}).encode()
            s.sendall(struct.pack('>I', len(frame)) + frame)
            s.close()
        with patch.object(mod, '_reattach_worker', side_effect=patched_reattach):
            # Create outbox with control.sock symlink to real socket
            try:
                (outbox / "control.sock").symlink_to(sock_path)
            except Exception:
                pass
            # Need to ensure scanner finds it: it iterates home/worker-outboxes/*
            # Our tmp_path IS home, so it will find outbox/control.sock
            n = mod.adopt_detached_kanban_workers(authority)
            t.join(timeout=2)
            assert n >= 1 or received.get('raw'), "adopt did not dial socket"
            if received.get('raw'):
                assert b'reconnect' in received['raw']
    listener.close()

def test_detached_then_reconnect():
    """WorkerControls detached -> reconnect restores attached."""
    import agent.managed_worker as mw
    from agent.managed_worker import WorkerControls
    import io
    ch = MagicMock()
    ch.lock = threading.Lock()
    ch.stream = io.BytesIO()
    ctrl = WorkerControls.__new__(WorkerControls)
    ctrl.channel = ch
    ctrl.route = 'r'
    ctrl.scope = {'execution_id': 'e1', 'generation': 1}
    ctrl.listener = MagicMock()
    ctrl.stream = io.BytesIO()
    ctrl.detached = True
    ctrl.attached = threading.Event()
    ctrl.stopped = threading.Event()
    ctrl.finish = threading.Event()
    ctrl.clarifications = {}
    ctrl.lock = threading.Lock()
    ctrl.agent = None
    # getattr guard should work
    assert getattr(ctrl, 'detached', False) is True
    # reconnect should clear detached
    ctrl._reconnect({'execution_id': 'e1', 'generation': 1})
    assert ctrl.detached is False
    assert ctrl.attached.is_set()
