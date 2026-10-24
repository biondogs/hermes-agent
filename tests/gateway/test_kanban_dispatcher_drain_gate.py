"""The embedded dispatcher holds its claim/spawn ticks while the gateway drains.

A SIGUSR1 deferred drain (graceful restart / `hermes update`) used to leave the
dispatcher ticking: every re-spawn was refused by its owner with ``runtime_draining``
within seconds and booked as a crash, burning retry budgets until cards parked
``gave_up`` that never ran (observed live: 8 cards across 3 boards in one bounce).
The watcher's ``_draining`` flag (set by ``request_restart`` the instant the drain
begins) must gate the tick loop next to the `hermes pause` emergency stop.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import gateway.kanban_watchers as watchers
from gateway.kanban_watchers import GatewayKanbanWatchersMixin


class _Recorder:
    def __init__(self) -> None:
        self.ticks = 0
        self.ready_checks = 0
        self.decompose_calls = 0

    def reset(self) -> None:
        self.ticks = self.ready_checks = self.decompose_calls = 0


_RECORDER = _Recorder()


class _StubDispatcher:
    def __init__(self, _kb, _settings) -> None:
        pass

    def tick_once(self):
        _RECORDER.ticks += 1
        return []

    def ready_nonempty(self):
        _RECORDER.ready_checks += 1
        return False

    def auto_decompose_tick(self, n):
        _RECORDER.decompose_calls += 1
        return 0


class _StubRunner(GatewayKanbanWatchersMixin):
    """Just enough runner for the watcher loop: drain flag, running flag, stop after N passes."""

    def __init__(self, passes: int = 3) -> None:
        self._running = True
        self._draining = False
        self._kanban_dispatcher_lock_handle = None
        self._passes = passes
        self._done = 0

    def _kanban_dispatcher_boot(self):
        return (lambda: {}, object(), {})

    async def _sleep_between_ticks(self, interval: float) -> None:
        self._done += 1
        if self._done >= self._passes:
            self._running = False


def _install_stubs(monkeypatch):
    async def _inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(watchers, "_to_thread_process_service", _inline)
    monkeypatch.setattr(watchers, "_KanbanDispatcher", _StubDispatcher)
    monkeypatch.setattr(watchers, "_resolve_dispatcher_settings", lambda cfg, kb: SimpleNamespace(interval=0.01))
    monkeypatch.setattr(watchers, "_resolve_auto_decompose_settings", lambda _cfg: (False, 0))
    monkeypatch.setattr(watchers, "_log_spawn_results", lambda results: False)
    monkeypatch.setattr(watchers, "_kanban_dispatch_allowed", lambda: True)
    monkeypatch.setattr(watchers, "reap_worker_zombies", lambda: [], raising=False)


def _drive(runner: _StubRunner) -> None:
    asyncio.run(runner._kanban_dispatcher_watcher())


def test_dispatcher_ticks_normally_without_drain(monkeypatch):
    _install_stubs(monkeypatch)
    _RECORDER.reset()
    _drive(_StubRunner(passes=3))
    assert _RECORDER.ticks == 3, "one dispatch tick per pass while healthy"
    assert _RECORDER.ready_checks == 3


def test_dispatcher_holds_all_ticks_while_draining(monkeypatch):
    _install_stubs(monkeypatch)
    _RECORDER.reset()
    runner = _StubRunner(passes=3)
    runner._draining = True
    _drive(runner)
    assert _RECORDER.ticks == 0, "no claims or spawns while the gateway drains"
    assert _RECORDER.ready_checks == 0
    assert _RECORDER.decompose_calls == 0


def test_drain_gate_releases_when_the_drain_ends(monkeypatch):
    """Drain for the first two passes, then release: the third pass dispatches again —
    the gate observes the flag live each tick, so a recover-to-dispatch cycle needs no
    restart (and the retry regime of the restarted gateway is the steady-state path)."""

    class _Recovering(_StubRunner):
        async def _sleep_between_ticks(self, interval: float) -> None:
            await super()._sleep_between_ticks(interval)
            if self._done == 2:
                self._draining = False

    _install_stubs(monkeypatch)
    _RECORDER.reset()
    runner = _Recovering(passes=3)
    runner._draining = True
    _drive(runner)
    assert _RECORDER.ticks == 0 or _RECORDER.ticks == 1, "held during drain, at most one tick after release"
    assert _RECORDER.ticks == runner._passes - 2, "exactly the post-release passes dispatched"
