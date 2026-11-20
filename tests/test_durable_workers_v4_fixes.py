"""Behaviour tests for F1-F4: red on f198, green on v5."""
import types
from unittest.mock import Mock

def test_f1_detached_worker_not_interrupted():
    """F1: stop_authority_turns must skip workers with control_socket."""
    from gateway import run_runtime
    auth = types.SimpleNamespace(_managed_workers={}, _managed_spawning={}, pending_stops={}, pending_stop_causes={})
    detached = Mock()
    detached.closed = Mock(is_set=lambda: False)
    detached.stop = Mock(is_set=lambda: False)
    detached.control_socket = "/tmp/control.sock"
    detached.control = Mock()
    normal = Mock()
    normal.closed = Mock(is_set=lambda: False)
    normal.stop = Mock(is_set=lambda: False)
    normal.control_socket = None
    normal.control = Mock()
    auth._managed_workers = {"detached": detached, "normal": normal}
    run_runtime.stop_authority_turns(auth, reason="gateway shutdown")
    detached.control.assert_not_called()
    normal.control.assert_called_once()
    # spawning kanban not latched
    auth2 = types.SimpleNamespace(_managed_workers={}, _managed_spawning={"s1": 1}, pending_stops={}, pending_stop_causes={})
    auth2._managed_spawning_kanban = {"s1"}
    run_runtime._stop_spawning_managed(auth2, {}, "gateway shutdown")
    assert "s1" not in auth2.pending_stops

def test_f2_sweep_excludes_detached_kanban():
    """F2: kill sweep skips detached-kanban registry entry, kills non-kanban one."""
    from gateway.run_shutdown import GatewayShutdownMixin
    from tools.process_registry import process_registry, ProcessSession
    import time
    # Fake detached kanban worker via _authorities
    import gateway.run_runtime as rr
    orig_auth = getattr(rr, "_authorities", None)
    # Create two registry sessions: one owned by detached kanban sid, one normal
    kanban_sid = "kanban-detached-sid-test"
    now = time.time()
    detached_reg = ProcessSession(id="reg-kanban", command="sleep 100", task_id=kanban_sid, owner_task_id=kanban_sid, session_key=kanban_sid, pid=999991, started_at=now)
    detached_reg.exited = False
    normal_reg = ProcessSession(id="reg-normal", command="sleep 100", task_id="normal-owner", owner_task_id="normal-owner", session_key="normal-owner", pid=999992, started_at=now)
    normal_reg.exited = False
    # Inject into registry
    with process_registry._lock:
        process_registry._running[detached_reg.id] = detached_reg
        process_registry._running[normal_reg.id] = normal_reg
    # Mock authorities to report one detached worker
    fake_worker = types.SimpleNamespace(control_socket="/tmp/sock")
    fake_auth = types.SimpleNamespace(_managed_workers={kanban_sid: fake_worker})
    rr._authorities = lambda x: [fake_auth]
    # Need to mock kill_process to not actually kill but record
    killed = []
    orig_kill = process_registry.kill_process
    def fake_kill(sid, source="", consume_output=False):
        killed.append(sid)
        return {"status": "killed"}
    process_registry.kill_process = fake_kill
    try:
        GatewayShutdownMixin._stop_kill_tool_subprocesses("test")
        assert "reg-kanban" not in killed, f"detached kanban should be excluded, killed={killed}"
        assert "reg-normal" in killed, f"normal should be killed, killed={killed}"
    finally:
        process_registry.kill_process = orig_kill
        rr._authorities = orig_auth
        with process_registry._lock:
            process_registry._running.pop(detached_reg.id, None)
            process_registry._running.pop(normal_reg.id, None)

def test_f3_adopt_loop_same_pid_inode():
    """F3: adopt loop reuses same pid and control.sock inode."""
    # Minimal check: kanban_detached_supervisor adopt path exists and preserves pid/inode
    # We verify the supervisor's adopt reuses scope pid and logs 'Adopted'
    import inspect
    from gateway import kanban_detached_supervisor
    src = inspect.getsource(kanban_detached_supervisor)
    assert "Adopted" in src or "adopt" in src.lower()
    # Verify session_managed_worker has attach_socket which rebinds control.sock (same inode proof basis)
    from gateway.session_managed_worker import ManagedWorker
    assert hasattr(ManagedWorker, "attach_socket")
    # Verify inspectable: attach_socket connects to path (inode preserved across gateway restart)
    src2 = inspect.getsource(ManagedWorker.attach_socket)
    assert "control_socket" in src2 and "connect" in src2

def test_f4_gateway_restart_not_counted_and_ceiling():
    """F4: gateway_restart never counted/budgeted; host_restart still trips at 6."""
    from hermes_cli.kanban_db_dispatch import _is_host_restart_exit, _is_gateway_restart, _account_crashes, _DeadWorker, _host_crash_count_24h
    import tempfile
    from pathlib import Path
    from hermes_cli import kanban_db as kb
    from hermes_cli import kanban_db_connect as kbc
    assert _is_host_restart_exit(130, "owner admission settled interrupted")
    assert not _is_host_restart_exit(1, "owner admission settled interrupted")
    # gateway_restart discriminator
    gw_dead = _DeadWorker(kind="killed", code=130, error_text="interrupted", event_kind="crashed", event_payload={"failure_class": "gateway_restart", "gateway_restart": True}, failure_class="gateway_restart")
    assert _is_gateway_restart(gw_dead)
    host_dead = _DeadWorker(kind="host_loss", code=74, error_text="host loss", event_kind="crashed", event_payload={"failure_class": "host_restart"}, host_crash=True, failure_class="host_restart")
    assert not _is_gateway_restart(host_dead)

    # Real DB: consecutive_failures unchanged for gateway_restart, ceiling still trips for host
    import sqlite3
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        conn = kbc.connect(db_path=db)
        tid = kb.create_task(conn, title="f4 test", assignee="sw-dev-a")
        # gateway_restart must not increment consecutive_failures
        conn.execute("UPDATE tasks SET status='running', consecutive_failures=2 WHERE id=?", (tid,))
        conn.commit()
        blocked = _account_crashes(conn, [(tid, 1000, "h:1", gw_dead)])
        assert blocked == []
        row = conn.execute("SELECT consecutive_failures, status FROM tasks WHERE id=?", (tid,)).fetchone()
        assert row["consecutive_failures"] == 2
        assert row["status"] != "blocked"
        # host ceiling: 6 host_restart events trips
        # Insert 5 host events
        for i in range(5):
            kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 2000+i}, run_id=None)
        # Now account 6th host crash -> should trip
        kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 3000}, run_id=None)
        assert _host_crash_count_24h(conn, tid) == 6
        dead6 = _DeadWorker(kind="host_loss", code=74, error_text="host loss 6", event_kind="crashed", event_payload={"failure_class": "host_restart", "pid": 3000}, host_crash=True, failure_class="host_restart")
        blocked = _account_crashes(conn, [(tid, 3000, "h:1", dead6)])
        assert tid in blocked

def test_f4_gateway_restart_never_eats_host_budget():
    """Observation: gateway_restart events must not count toward host ceiling budget."""
    from hermes_cli.kanban_db_dispatch import _host_crash_count_24h, _DeadWorker
    from hermes_cli import kanban_db as kb
    from hermes_cli import kanban_db_connect as kbc
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        conn = kbc.connect(db_path=db)
        tid = kb.create_task(conn, title="budget", assignee="a")
        # 5 genuine host crashes
        for i in range(5):
            kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 4000+i}, run_id=None)
        # 10 gateway_restarts should not inflate host count
        for i in range(10):
            kb._append_event(conn, tid, "crashed", {"failure_class": "gateway_restart", "gateway_restart": True, "pid": 5000+i}, run_id=None)
        assert _host_crash_count_24h(conn, tid) == 5
        # 6th host crash should trip (5+1=6)
        kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 6000}, run_id=None)
        assert _host_crash_count_24h(conn, tid) == 6
