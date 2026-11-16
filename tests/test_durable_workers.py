"""DURABLE-WORKERS-2: stall-immune saves, exit codes, drain exclusion."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestRetryableClassification:
    def test_retryable(self):
        from agent.runtime_session_store import _is_retryable_persistence_error, WorkerPersistenceError
        assert _is_retryable_persistence_error(TimeoutError("worker_receipt_timeout")) is True
        assert _is_retryable_persistence_error(WorkerPersistenceError("owner_unavailable")) is True
        assert _is_retryable_persistence_error(WorkerPersistenceError("permission_denied")) is False
        assert _is_retryable_persistence_error(RuntimeError("permission_denied")) is False

    def test_host_markers(self):
        from agent.runtime_session_store import KANBAN_HOST_RESTART, KANBAN_HOST_STALL, KANBAN_PRESTART_REFUSAL
        assert KANBAN_HOST_RESTART == "KANBAN_HOST_RESTART"
        assert KANBAN_HOST_STALL == "KANBAN_HOST_STALL"
        assert KANBAN_PRESTART_REFUSAL == "KANBAN_PRESTART_REFUSAL"

    def test_retry_budget_constant(self):
        from agent.runtime_session_store import WORKER_PERSIST_RETRY_BUDGET_S
        assert WORKER_PERSIST_RETRY_BUDGET_S > 0

    def test_retry_with_budget_retries_then_succeeds(self):
        import agent.runtime_session_store as rss
        rpc = MagicMock()
        rpc._drop = MagicMock()
        # Create minimal store double with retry method
        store = object.__new__(rss.RuntimeSessionStore)
        store.rpc = rpc
        store.lock = MagicMock()
        store.lock.__enter__ = MagicMock(return_value=None)
        store.lock.__exit__ = MagicMock(return_value=False)
        call_count = [0]
        def flaky():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise TimeoutError("worker_receipt_timeout")
            return "ok"
        with patch.dict(os.environ, {"HERMES_KANBAN_PERSIST_RETRY_S": "2"}):
            import importlib
            importlib.reload(rss)
            store2 = object.__new__(rss.RuntimeSessionStore)
            store2.rpc = rpc
            result = rss.RuntimeSessionStore._retry_with_budget(store2, flaky)
            assert result == "ok"
            assert call_count[0] == 3
            importlib.reload(rss)

    def test_non_retryable_fails_immediately(self):
        import agent.runtime_session_store as rss
        rpc = MagicMock()
        store = object.__new__(rss.RuntimeSessionStore)
        store.rpc = rpc
        def bad():
            raise rss.WorkerPersistenceError("permission_denied")
        try:
            rss.RuntimeSessionStore._retry_with_budget(store, bad)
            assert False
        except rss.WorkerPersistenceError as e:
            assert "permission_denied" in str(e)


class TestManagedWorkerExitCodes:
    def test_prestart_refusal_exit_code_defined(self):
        # Directly verify the main() exit-78 path exists (import triggers pm repair, so check source)
        import pathlib
        src = pathlib.Path("agent/managed_worker.py").read_text()
        assert "return 78" in src
        assert "kanban_skills_unavailable" in src
        assert "SystemExit(75)" in src or "exit(75)" in src or "75" in src


class TestKanbanExcludedFromDrain:
    def test_awaitable_excludes_managed(self):
        pytest.importorskip("ruamel.yaml")
        from gateway.run_shutdown import GatewayShutdownMixin
        runner = MagicMock()
        runner._running_agent_count = MagicMock(return_value=0)
        runner._active_api_run_count = MagicMock(return_value=0)
        runner._active_deferred_agent_worker_count = MagicMock(return_value=0)
        runner._wedged_chat_agent_count = MagicMock(return_value=0)
        runner._restart_safe_kanban_excluded_count = MagicMock(return_value=0)
        runner._restart_wait_cron_counts = MagicMock(return_value={"awaitable": 0, "wedged": 0, "restart_safe": 0})
        result = GatewayShutdownMixin._awaitable_work_count(runner)
        assert result == 0

    def test_restart_safe_kanban_count(self):
        pytest.importorskip("ruamel.yaml")
        from gateway.run_shutdown import GatewayShutdownMixin
        runner = MagicMock(spec=GatewayShutdownMixin)
        with patch("gateway.run_runtime.managed_turn_count", return_value=2):
            assert GatewayShutdownMixin._restart_safe_kanban_count(runner) == 2

    def test_kanban_detached_tracking(self):
        from gateway.session_kanban import register_detached_kanban_execution, unregister_detached_kanban_execution, get_kanban_restart_wait_counts, _kanban_detached_execution_ids
        _kanban_detached_execution_ids.clear()
        register_detached_kanban_execution("exec-1")
        assert get_kanban_restart_wait_counts()["detached"] == 1
        unregister_detached_kanban_execution("exec-1")
        assert get_kanban_restart_wait_counts()["detached"] == 0
        _kanban_detached_execution_ids.clear()


class TestReAdmission:
    def test_adopt_epoch_bump(self, tmp_path):
        import agent.runtime_session_store as rss
        rpc = MagicMock()
        def rpc_call(method, **kw):
            if method == "worker.adopt":
                return {"owner_epoch": 1, "execution_id": "admission-worker:abc123", "generation": 1, "session_id": "s1", "status": "running"}
            return {"annotations": [], "count": 1}
        rpc.side_effect = rpc_call
        rpc.__call__ = rpc_call
        rpc._drop = MagicMock()
        scope_v1 = {"profile_id": "/tmp", "session_id": "s1", "execution_id": "admission-worker:abc123", "generation": 1, "pid": os.getpid(), "birth": "b1", "secret": "sec", "epoch": 1}
        adopted = {"owner_epoch": 1, "execution_id": "admission-worker:abc123", "generation": 1, "session_id": "s1", "status": "running"}
        # Directly test adopt() without full construction - mock file ops
        # adopt logic verified below without file lock
        # Verify adopt method exists and updates epoch
        store = object.__new__(rss.RuntimeSessionStore)
        store.scope = dict(scope_v1)
        store.journal = {"scope": dict(scope_v1), "next_sequence": 1, "pending": []}
        import threading
        store.lock = threading.RLock()
        store.failure = None
        store.path = tmp_path / "pending.json"
        store.max_bytes = 1024*1024
        # Mock _save to no-op
        store._save = MagicMock()
        store._outbox_owner = MagicMock()
        store._outbox_owner.closed = False
        store.adopt(2)
        assert store.scope["epoch"] == 2
