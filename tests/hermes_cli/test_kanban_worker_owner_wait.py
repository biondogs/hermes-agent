"""A Kanban worker spawned while `hermes update` drains the owner waits for it instead of failing.

The dispatcher keeps spawning workers during an update window; the owner answers ``draining``
until the update releases the install. Exiting 1 there books a crash against the card, and two
of those trip the breaker and park a card that never ran (the in-flight handoff cell). The wait
must never submit the claim twice, and a non-transient refusal still fails at once.
"""

import asyncio
from contextlib import asynccontextmanager

import pytest

from hermes_cli import gateway_client, kanban_worker_client


def _owner(states, submitted):
    @asynccontextmanager
    async def connect():
        state = states.pop(0) if states else None
        if state:
            # The exact refusal connect_gateway raises for a draining/starting owner.
            unavailable = getattr(gateway_client, "GatewayUnavailableError", None)
            if unavailable is None:  # pre-fix tree: the same message as a plain client error
                raise gateway_client.GatewayClientError(f"Gateway {state}: update_paused")
            raise unavailable(f"Gateway {state}: update_paused", state)

        class _Client:
            events = asyncio.Queue()

            async def rpc(self, method, **params):
                submitted.append(method)
                return {"session_id": "s1", "receipt": {"status": "terminal", "admission_id": "a1"}}

        yield _Client()

    return connect


@pytest.mark.asyncio
async def test_worker_waits_out_a_draining_owner_and_submits_once(monkeypatch, tmp_path):
    submitted = []
    monkeypatch.setattr(gateway_client, "connect_gateway", _owner(["draining", "starting"], submitted))
    monkeypatch.setattr(kanban_worker_client.asyncio, "sleep", _no_sleep)
    from gateway import session_kanban
    monkeypatch.setattr(session_kanban, "worker_result", lambda *_: {"exit_code": 0, "last_output": "card closed"})
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    assert await kanban_worker_client.run({"task_id": "t1"}, str(tmp_path / "kanban.db")) == 0
    assert submitted == ["kanban.run"]


@pytest.mark.asyncio
async def test_worker_fails_at_once_when_the_owner_is_not_transiently_down(monkeypatch, tmp_path):
    submitted = []
    monkeypatch.setattr(gateway_client, "connect_gateway", _owner(["inaccessible"], submitted))
    monkeypatch.setattr(kanban_worker_client.asyncio, "sleep", _no_sleep)
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    with pytest.raises(gateway_client.GatewayClientError):
        await kanban_worker_client.run({"task_id": "t1"}, str(tmp_path / "kanban.db"))
    assert submitted == []


async def _no_sleep(_seconds):
    return None


# --- runtime_draining: the owner ANSWERED the RPC (F27: graceless drain-bounce burned
# --- retry budgets; the connect-time wait above never saw this path). -------------------------


def _refusing_owner(refusals, submitted, reason="runtime_draining"):
    """Connect succeeds, but ``kanban.run`` answers ``reason`` for the first ``refusals``
    attempts; afterwards a healthy owner accepts the claim."""
    @asynccontextmanager
    async def connect():
        class _Client:
            events = asyncio.Queue()

            async def rpc(self, method, **params):
                if refusals:
                    refusals.pop(0)
                    raise gateway_client.GatewayRPCError(reason, 4001, {"reason": reason})
                submitted.append(method)
                return {"session_id": "s1", "receipt": {"status": "terminal", "admission_id": "a1"}}

        yield _Client()

    return connect


@pytest.mark.asyncio
async def test_worker_waits_out_a_runtime_draining_rpc_refusal_and_submits_once(monkeypatch, tmp_path):
    """The refusal comes back as the RPC RESULT (connect succeeded) — the same transient
    wait as a draining owner at connect. Waiting can never run the claim twice: the
    admission marker is only written on acceptance."""
    submitted = []
    monkeypatch.setattr(gateway_client, "connect_gateway", _refusing_owner([1, 1], submitted))
    monkeypatch.setattr(kanban_worker_client.asyncio, "sleep", _no_sleep)
    from gateway import session_kanban
    monkeypatch.setattr(session_kanban, "worker_result", lambda *_: {"exit_code": 0, "last_output": "card closed"})
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    assert await kanban_worker_client.run({"task_id": "t1"}, str(tmp_path / "kanban.db")) == 0
    assert submitted == ["kanban.run"]


@pytest.mark.asyncio
async def test_a_non_drain_rpc_refusal_fails_at_once(monkeypatch, tmp_path):
    submitted = []
    monkeypatch.setattr(gateway_client, "connect_gateway", _refusing_owner([1], submitted, reason="permission_denied"))
    monkeypatch.setattr(kanban_worker_client.asyncio, "sleep", _no_sleep)
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    with pytest.raises(gateway_client.GatewayRPCError):
        await kanban_worker_client.run({"task_id": "t1"}, str(tmp_path / "kanban.db"))
    assert submitted == []


def test_submit_maps_only_drain_refusals_to_the_sentinel_exit_code(monkeypatch, tmp_path):
    """``_submit`` is the process exit path: a drain refusal (either flavour) maps to the
    ``KANBAN_DRAIN_REFUSED_EXIT_CODE`` sentinel so the dispatcher books a non-counting
    requeue; every other owner refusal still exits plain 1."""
    from hermes_cli import kanban_db as kb

    for key in ("HERMES_KANBAN_BOARD", "HERMES_KANBAN_TASK", "HERMES_KANBAN_CLAIM_LOCK",
                "HERMES_KANBAN_DB"):
        monkeypatch.setenv(key, "x")
    monkeypatch.setenv("HERMES_KANBAN_RUN_ID", "1")
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    async def _raise(exc):
        raise exc

    def _armer():
        # `_submit` pops every HERMES_KANBAN_* var (worker must not leak task identity),
        # so re-arm them before each call.
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "x")
        monkeypatch.setenv("HERMES_KANBAN_TASK", "x")
        monkeypatch.setenv("HERMES_KANBAN_RUN_ID", "1")
        monkeypatch.setenv("HERMES_KANBAN_CLAIM_LOCK", "x")
        monkeypatch.setenv("HERMES_KANBAN_DB", str(tmp_path / "kanban.db"))

    drain_cases = [
        gateway_client.GatewayRPCError("runtime_draining", 4001, {"reason": "runtime_draining"}),
        gateway_client.GatewayUnavailableError("Gateway draining: update_paused", "draining"),
    ]
    for exc in drain_cases:
        monkeypatch.setattr(kanban_worker_client, "run",
                            lambda *a, _exc=exc: _raise(_exc))
        _armer()
        assert kanban_worker_client._submit() == kb.KANBAN_DRAIN_REFUSED_EXIT_CODE, str(exc)

    monkeypatch.setattr(kanban_worker_client, "run",
                        lambda *a: _raise(gateway_client.GatewayUnavailableError("Gateway inaccessible", "inaccessible")))
    _armer()
    assert kanban_worker_client._submit() == 1
    monkeypatch.setattr(kanban_worker_client, "run",
                        lambda *a: _raise(gateway_client.GatewayClientError("permission_denied")))
    _armer()
    assert kanban_worker_client._submit() == 1


# --- reworked 2026-10-29 onto the redial loop: a drain LONGER than the owner-wait must
# --- still exit as a drain refusal, never as a counted crash. -------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("flavour", ["rpc", "connect"])
async def test_drain_outliving_the_owner_wait_propagates_the_refusal_itself(monkeypatch, tmp_path, flavour):
    """Deferred drains run past ``OWNER_WAIT_S`` (10+ min observed). When the loop gives up,
    it must propagate the drain REFUSAL (not the generic 'owner silent' error) so ``_submit``
    maps it to the sentinel exit and the dispatcher books the non-counting drain_refused
    requeue instead of booking a crash against the card's retry budget."""
    submitted = []
    if flavour == "rpc":
        owner = _refusing_owner([1, 1, 1], submitted)
        expected = gateway_client.GatewayRPCError
    else:
        owner = _owner(["draining"], submitted)
        expected = gateway_client.GatewayUnavailableError
    monkeypatch.setattr(gateway_client, "connect_gateway", owner)
    monkeypatch.setattr(kanban_worker_client.asyncio, "sleep", _no_sleep)
    monkeypatch.setattr(kanban_worker_client, "OWNER_WAIT_S", 0.0)
    monkeypatch.delenv("HERMES_TUI_GATEWAY_URL", raising=False)

    with pytest.raises(expected) as ei:
        await kanban_worker_client.run({"task_id": "t1"}, str(tmp_path / "kanban.db"))
    assert kanban_worker_client._is_drain_refusal(ei.value), str(ei.value)
    assert submitted == []
