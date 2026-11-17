"""Adopt loop proof: simulated bounce re-attaches via reconnect."""
import socket, threading, json, os
from pathlib import Path
from unittest.mock import MagicMock, patch

def test_adopt_sends_reconnect(tmp_path, monkeypatch):
    """Real outbox with control.sock + scope.json: adopt dials and sends reconnect, worker detached->attached."""
    # Create a live listener mimicking the worker\'s control.sock
    exec_id = "admission-worker:abc123deadbeef1234567890abcdef12"
    import tempfile, shutil
    # AF_UNIX path limit ~108 chars; make the entire outbox tree short
    short_home = Path(tempfile.mkdtemp(prefix="ah-"))
    outbox = short_home / "worker-outboxes" / exec_id.replace(":", "-")
    outbox.mkdir(parents=True)
    sock_path = outbox / "control.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(sock_path))
    listener.listen(1)
    received = {}
    def accept_once():
        conn, _ = listener.accept()
        data = conn.recv(8192)
        received["raw"] = data
        conn.close()
    t = threading.Thread(target=accept_once, daemon=True)
    t.start()
    # scope.json with pid/birth for liveness
    from hermes_cli.process_identity import worker_birth as _wb
    import psutil
    scope = {"execution_id": exec_id, "generation": 1, "epoch": 0, "session_id": "sess1", "pid": os.getpid(), "birth": _wb(psutil.Process()), "kanban": {"task_id": "t_fake", "board": "b", "db": str(tmp_path / "nope.db"), "claim_lock": "x", "run_id": 1}}
    (outbox / "scope.json").write_text(json.dumps(scope))
    authority = MagicMock()
    authority._managed_workers = {}
    import gateway.kanban_detached_supervisor as mod
    def fake_find(s, name):
        return {"pid": s.get("pid"), "birth": s.get("birth"), "generation": s.get("generation", 0), "owner_epoch": s.get("epoch", 0), "execution_id": s.get("execution_id"), "session_id": s.get("session_id")}
    with patch.object(mod, "_resolve_homes", return_value=[short_home]), patch.object(mod, "_find_task_for_scope", side_effect=fake_find):
        n = mod.adopt_detached_kanban_workers(authority)
        t.join(timeout=3)
        assert n >= 1, f"adopt returned {n}, expected >=1"
        assert received.get("raw"), "adopt did not dial control.sock"
        assert b"reconnect" in received["raw"], f"expected reconnect frame, got {received['raw']!r}"
    listener.close()
    shutil.rmtree(str(short_home), ignore_errors=True)

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
    ctrl.route = "r"
    ctrl.scope = {"execution_id": "e1", "generation": 1}
    ctrl.listener = MagicMock()
    ctrl.stream = io.BytesIO()
    ctrl.detached = True
    ctrl.attached = threading.Event()
    ctrl.stopped = threading.Event()
    ctrl.finish = threading.Event()
    ctrl.clarifications = {}
    ctrl.lock = threading.Lock()
    ctrl.agent = None
    assert getattr(ctrl, "detached", False) is True
    ctrl._reconnect({"execution_id": "e1", "generation": 1})
    assert ctrl.detached is False
    assert ctrl.attached.is_set()
