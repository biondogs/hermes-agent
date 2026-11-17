"""Durable workers v2: owner loss is detachment, not death; 74/77 exits; bounded persist retry."""
import io
import threading
from unittest import mock

import pytest

from agent import managed_worker as mw
from agent import runtime_session_store as rss


class _Chan:
    lock = threading.Lock()
    stream = mock.Mock()

    def send(self, *a, **k):
        pass


def _controls(stream):
    c = mw.WorkerControls.__new__(mw.WorkerControls)
    c.channel, c.route, c.scope, c.listener, c.stream = _Chan(), "r", {"execution_id": "e", "generation": 1}, None, stream
    c.detached, c.attached = False, threading.Event()
    c.attached.set()
    c.agent, c.stopped, c.finish = None, threading.Event(), threading.Event()
    c.clarifications, c.lock = {}, threading.Lock()
    return c


def test_owner_eof_detaches_without_dying_or_stopping():
    c = _controls(io.BytesIO(b""))
    state = {"event": threading.Event(), "answer": None}
    c.clarifications["p"] = state
    with mock.patch.object(mw, "_die_with_owner") as die:
        c.read()
    die.assert_not_called()
    assert c.detached and not c.stopped.is_set() and not c.finish.is_set()
    assert state["answer"] is mw._DETACHED
    assert c.clarify([{"question": "q", "choices": [], "multi_select": False, "qid": "a"}]) == {
        "answers": {},
        "outcome": "timed_out",
    }


def test_reconnect_by_new_owner_readmits_and_stop_still_works():
    from agent.managed_worker import encode_frame

    c = _controls(
        io.BytesIO(
            encode_frame({"type": "reconnect", "execution_id": "e", "generation": 1, "owner_epoch": 2})
            + encode_frame({"type": "stop"})
            + encode_frame({"type": "finish"})
        )
    )
    c.detached = True
    c.attached.clear()
    c.read()
    assert not c.detached and c.attached.is_set() and c.stopped.is_set()


def test_reconnect_wrong_generation_rejected():
    from agent.managed_worker import encode_frame

    c = _controls(io.BytesIO(encode_frame({"type": "reconnect", "execution_id": "e", "generation": 9})))
    c.read()
    assert c.finish.is_set() and c.stopped.is_set()


class _Rpc:
    def __init__(self, failures, error):
        self.failures, self.error, self.calls = failures, error, 0

    def __call__(self, method, **params):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return {}


def _store(tmp_path, rpc):
    s = rss.RuntimeSessionStore.__new__(rss.RuntimeSessionStore)
    s.rpc, s.failure, s.lock = rpc, None, threading.RLock()
    s.scope = {"session_id": "s"}
    s.path = tmp_path / "pending.json"
    s._outbox_owner = mock.Mock(closed=False)
    s.max_bytes = 1 << 20
    s.journal = {"scope": s.scope, "next_sequence": 2, "pending": [{"sequence": 1, "operation": "x", "payload": {}}]}
    s._compression_receipt_journal = lambda cand, result: cand
    return s


def test_retry_rides_out_gap_and_resends_same_entry(tmp_path):
    rpc = _Rpc(3, rss.WorkerPersistenceError("owner_unavailable"))
    with mock.patch.object(rss.time, "sleep"):
        _store(tmp_path, rpc).retry_pending()
    assert rpc.calls == 4


def test_retry_budget_expiry_latches_host_lost(tmp_path):
    rpc = _Rpc(10**6, TimeoutError("worker_receipt_timeout"))
    s = _store(tmp_path, rpc)
    clock = iter(range(0, 10**6, 100))

    with mock.patch.object(rss.time, "sleep"), mock.patch.object(rss.time, "monotonic", lambda: next(clock)):
        with pytest.raises(rss.WorkerPersistenceError, match="host_lost"):
            s.retry_pending()
    assert s.failure == "host_lost"


def test_non_retryable_latches_immediately(tmp_path):
    rpc = _Rpc(10, rss.WorkerPersistenceError("permission_denied"))
    s = _store(tmp_path, rpc)
    with pytest.raises(rss.WorkerPersistenceError, match="permission_denied"):
        s.retry_pending()
    assert rpc.calls == 1


def test_exit_74_and_77_write_trailer(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    frame = {"policy": {"kanban_json": '{"task_id":"t_x","board":"b"}'}}
    from hermes_cli.kanban_db import worker_log_path

    assert mw._exit_code_for(rss.WorkerPersistenceError("host_lost"), frame) == 74
    assert mw._exit_code_for(mw.PrestartRefusal("kanban_skills_unavailable"), frame) == 77
    log_text = worker_log_path("t_x", board="b").read_text()
    assert "[kanban-worker-exit] rc=74" in log_text and "[kanban-worker-exit] rc=77" in log_text
    assert mw._exit_code_for(RuntimeError("x"), frame) == 1


def test_detached_kanban_counts_and_drain_exclusion():
    import pathlib

    wt = pathlib.Path(__file__).resolve().parents[1]
    smw_src = (wt / "gateway" / "session_managed_worker.py").read_text()
    assert "def get_kanban_detached_counts" in smw_src
    assert "control_socket" in smw_src
    shutdown_src = (wt / "gateway" / "run_shutdown.py").read_text()
    assert "_kanban_detached_count" in shutdown_src
    assert "non_cron - self._wedged_chat_agent_count() - self._kanban_detached_count()" in shutdown_src
    # max_runtime / operator stop still kill detached: verify those paths are pid-based
    import inspect

    from hermes_cli.kanban_db_dispatch import enforce_max_runtime

    src = inspect.getsource(enforce_max_runtime)
    assert "control_socket" not in src and "detached" not in src
    # close still signals group even when socket-tracked
    assert "control_socket" in smw_src and "_signal_group" in smw_src
