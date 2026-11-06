"""F22: the kanban notifier's wake-profile selection is board-aware.

Incident 2026-10-24 (follow-on to the F21 misfiling root): the notifier
claimed notification subscriptions by stamped profile alone, ignoring board
ownership. Pre-fence residue rows — a butler's auto-subscribe stamped on a card
that had misfiled onto the DEFAULT board — were claimed and woken through that
butler, whose own tool-layer board pin (602ea0a874) then refused the card ops:
"started on the wrong board again". The fence here mirrors the tool layer: a
profile pinned to board B' can never be selected for events on board B != B';
such rows are self-healed by re-stamping to the board's owning profile, so an
event on board B renders via the profile subscribed for B (``default`` for the
default board), never another board's butler.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
from hermes_yaml import safe_dump

from gateway import kanban_watchers_notifier as notifier
from gateway.config import GatewayConfig, Platform
from gateway.kanban_watchers_notifier import _notifier_collect
from gateway.run import GatewayRunner
from hermes_cli import (
    kanban_db as kb,
    kanban_db_boards as kbb,
    kanban_db_connect as kbc,
    kanban_db_notify as kbn,
)


class RecordingAdapter:
    supports_async_delivery = True

    def __init__(self):
        self.sent = []

    async def send(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text, kwargs))


@pytest.fixture
def fence_env(tmp_path, monkeypatch):
    """Root home with two extra boards + a butler profile pinned to software-co.

    No ``HERMES_KANBAN_DB`` pin (the gateway daemon strips env pins at boot), so
    every board slug maps to its own DB — the production topology the fence runs
    against. The default board's DB is the root ``kanban.db``.
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    for var in (
        "HERMES_KANBAN_DB",
        "HERMES_KANBAN_WORKSPACES_ROOT",
        "HERMES_KANBAN_HOME",
        "HERMES_KANBAN_BOARD",
        "HERMES_KANBAN_TASK",
        "HERMES_KANBAN_RUN_ID",
    ):
        monkeypatch.delenv(var, raising=False)
    import hermes_constants
    hermes_constants._default_hermes_root_memo = None  # type: ignore[attr-defined]
    kb._INITIALIZED_PATHS.clear()
    kb._PROFILE_BOARD_PIN_CACHE.clear()
    monkeypatch.setattr(notifier, "_CROSS_BOARD_WARNED", set())
    kbb.create_board("software-co")
    kbb.create_board("gaudi")
    butler = home / "profiles" / "swco-butler"
    butler.mkdir(parents=True)
    (butler / "config.yaml").write_text(
        safe_dump({"kanban": {"board": "software-co"}}), encoding="utf-8")
    # An UNPINNED hosted profile: dispatcher/orchestrator-style, no kanban.board.
    architect = home / "profiles" / "arch"
    architect.mkdir(parents=True)
    (architect / "config.yaml").write_text("agent:\n  description: unpinned\n", encoding="utf-8")
    yield home
    kb._PROFILE_BOARD_PIN_CACHE.clear()


@pytest.fixture
def runner(fence_env, monkeypatch):
    return make_runner(monkeypatch)


def make_runner(monkeypatch, butler_telegram=True):
    """Multiplexer-shaped runner stub hosting the pinned butler as a served profile."""
    from typing import Any as _Any, cast as _cast
    runner: _Any = GatewayRunner.__new__(GatewayRunner)
    runner.adapters = {Platform.TELEGRAM: RecordingAdapter()}
    butler_adapters = {Platform.TELEGRAM: RecordingAdapter()} if butler_telegram else {}
    runner._profile_adapters = _cast("dict", {"swco-butler": butler_adapters, "arch": {}})
    runner._primary_profile_name = "default"
    runner._kanban_notifier_profile = "default"
    runner._kanban_dispatcher_lock_handle = object()
    runner.config = GatewayConfig(multiplex_profiles=False)
    # The route-authorization gate is orthogonally covered by
    # test_kanban_routed_transport.py; the fence must run ahead of it.
    monkeypatch.setattr(notifier, "_adapter_for_subscription",
                        lambda runner, platform, sub, owner: object())
    return runner


def collect(runner):
    return _notifier_collect(runner, kb, notifier_profile="default",
                             gc_due=False, gc_retention_days=30)


def complete_on(board, *, stamp):
    """Task + stamped telegram subscription + completion event on one board."""
    with kbc.connect(board=board) as conn:
        task = kb.create_task(conn, title=f"{board} card", assignee="worker")
        kbn.add_notify_sub(conn, task_id=task, platform="telegram", chat_id="8158007517",
                           chat_type="dm", notifier_profile=stamp, delivery_mode="notify+wake")
        kb.complete_task(conn, task, result="finished")
    return task


def subs_on(board, task):
    with kbc.connect(board=board) as conn:
        return kbn.list_notify_subs(conn, task_id=task)


def unseen_on(board, task):
    with kbc.connect(board=board) as conn:
        return kbn.unseen_events_for_sub(conn, task_id=task, platform="telegram",
                                         chat_id="8158007517", kinds=["completed"])[1]


# ---------------------------------------------------------------------------
# The probe: a default-board event can never select a board-pinned butler.
# ---------------------------------------------------------------------------

class TestBoardAwareSelection:
    def test_default_board_event_cannot_select_board_pinned_butler(self, runner):
        task = complete_on("default", stamp="swco-butler")
        # First tick: the residue row is fenced AND healed to the default
        # board's owning profile; nothing is delivered under the butler stamp.
        assert collect(runner) == []
        assert [s["notifier_profile"] for s in subs_on("default", task)] == ["default"]
        # The fence skipped the claim, so the event was never consumed.
        assert unseen_on("default", task)
        # Second tick: the healed row renders via the DEFAULT profile only.
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "default"
        assert not unseen_on("default", task)

    def test_fence_never_consumes_events_when_heal_fails(self, runner):
        """A fenced row that cannot be healed keeps its events retryable (skip,
        never claim-and-advance through a profile that cannot own the board)."""
        task = complete_on("gaudi", stamp="swco-butler")  # no profile owns gaudi
        assert collect(runner) == []
        assert collect(runner) == []
        assert [s["notifier_profile"] for s in subs_on("gaudi", task)] == ["swco-butler"]
        assert unseen_on("gaudi", task)

    def test_ownerless_board_row_warns_once(self, runner, caplog, monkeypatch):
        task = complete_on("gaudi", stamp="swco-butler")
        with caplog.at_level(logging.WARNING, logger=notifier.logger.name):
            assert not collect(runner)
            assert not collect(runner)
        warnings = [r for r in caplog.records
                    if "board-pinned" in r.getMessage() and task in r.getMessage()]
        assert len(warnings) == 1 and warnings[0].levelno == logging.WARNING

    def test_healed_row_logs_once_and_is_idempotent(self, runner, caplog):
        task = complete_on("default", stamp="swco-butler")
        with caplog.at_level(logging.INFO, logger=notifier.logger.name):
            collect(runner)  # heals
            collect(runner)  # claims under default; no second heal possible
        heals = [r for r in caplog.records
                 if r.getMessage().startswith("kanban notifier: fence: pinned off-board residue")
                 and task in r.getMessage()]
        assert len(heals) == 1 and heals[0].levelno == logging.INFO

    def test_butler_keeps_selection_for_events_on_its_own_board(self, runner):
        task = complete_on("software-co", stamp="swco-butler")
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "swco-butler"
        assert not unseen_on("software-co", task)

    def test_unpinned_stamp_derives_to_board_owner_at_delivery(self, runner):
        """Delivery-time derivation (operator scope-add 2026-10-24): the stamp is
        a subscribe-time accident (whichever chat session created the card); an
        UNPINNED stamp on a board with an owning butler renders via that butler
        — this very tick, not just after a re-subscribe."""
        task = complete_on("software-co", stamp="arch")
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "swco-butler"
        assert [s["notifier_profile"] for s in subs_on("software-co", task)] == ["swco-butler"]
        assert not unseen_on("software-co", task)

    def test_no_derivation_when_owner_serves_no_adapter(self, fence_env, monkeypatch):
        """Derivation is the board→butler topology, not a blanket re-route: when
        the owning profile hosts no adapter for the row's platform here, the
        original stamped profile keeps the row (and it still delivers)."""
        runner = make_runner(monkeypatch, butler_telegram=False)
        task = complete_on("software-co", stamp="arch")
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "arch"
        assert [s["notifier_profile"] for s in subs_on("software-co", task)] == ["arch"]

    def test_no_derivation_on_ownerless_board(self, runner):
        """A board with no pinned butler (skipjack-class) never derives."""
        task = complete_on("gaudi", stamp="arch")
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "arch"

    def test_no_derivation_for_default_board_unpinned_stamps(self, runner):
        """Upstream safety: `default` owns no secondary adapters, so unpinned
        stamps on the default board (profile_routes authority included) never
        derive — only board butlers are ever synthesis targets."""
        task = complete_on("default", stamp="arch")
        rows = collect(runner)
        assert [row["task"].id for row in rows] == [task]
        assert rows[0]["sub"]["notifier_profile"] == "arch"
        assert [s["notifier_profile"] for s in subs_on("default", task)] == ["arch"]

    def test_unstamped_legacy_row_passes_the_fence(self, runner):
        with kbc.connect(board="default") as conn:
            task = kb.create_task(conn, title="legacy unowned", assignee="worker")
            kbn.add_notify_sub(conn, task_id=task, platform="telegram", chat_id="8158007517",
                               chat_type="dm", delivery_mode="notify")
            kb.complete_task(conn, task, result="legacy")
        rows = collect(runner)  # dispatcher-lock holder claims unowned rows
        assert task in [row["task"].id for row in rows]


# ---------------------------------------------------------------------------
# named_profile_board_pin: name-based pin resolution, independent of active home.
# ---------------------------------------------------------------------------

class TestNamedProfileBoardPin:
    def test_resolves_by_name_independent_of_active_home(self, fence_env):
        from hermes_constants import reset_hermes_home_override, set_hermes_home_override
        # Active home = the root (unpinned): the ACTIVE pin is None, yet the
        # butler's pin must resolve by NAME.
        assert kb.profile_board_pin() is None
        assert kb.named_profile_board_pin("swco-butler") == "software-co"
        token = set_hermes_home_override(str(fence_env))
        try:
            # Even while scoped inside some other profile's home.
            assert kb.named_profile_board_pin("swco-butler") == "software-co"
        finally:
            reset_hermes_home_override(token)

    def test_unknown_and_unpinned_names_resolve_none(self, fence_env):
        assert kb.named_profile_board_pin("") is None
        assert kb.named_profile_board_pin(None) is None
        assert kb.named_profile_board_pin("no-such-profile") is None
        # 'default' resolves through the root home, which pins no board here.
        assert kb.named_profile_board_pin("default") is None

    def test_stale_pin_board_resolves_none(self, fence_env):
        butler_cfg = fence_env / "profiles" / "swco-butler" / "config.yaml"
        butler_cfg.write_text(safe_dump({"kanban": {"board": "deleted-board"}}),
                              encoding="utf-8")
        st = butler_cfg.stat()
        import os
        os.utime(butler_cfg, ns=(st.st_atime_ns + 1_000_000_000, st.st_mtime_ns + 1_000_000_000))
        assert kb.named_profile_board_pin("swco-butler") is None


# ---------------------------------------------------------------------------
# _board_owner_profile: the profile subscribed FOR a board.
# ---------------------------------------------------------------------------

class TestBoardOwnerProfile:
    def test_pinned_butler_owns_its_board(self, fence_env):
        assert notifier._board_owner_profile(kb, "software-co") == "swco-butler"

    def test_default_board_falls_back_to_default_profile(self, fence_env):
        assert notifier._board_owner_profile(kb, "default") == "default"

    def test_board_without_owner_resolves_none(self, fence_env):
        assert notifier._board_owner_profile(kb, "gaudi") is None
