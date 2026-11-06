"""F23: kanban stream WIDEN — auto-subscribe every open card, terminal events only.

Operator ruling 2026-10-24 (t_7bbbfe1c): stream coverage changes from per-card
opt-in to auto-subscribe. The notifier tick inserts a
``telegram``-destination subscription row for every card on every board that
lacks one — new cards AND a backfill of pre-existing open cards — stamped with
the board's owning profile (the F22 topology, so delivery-time derivation stays
inert). Done/archived cards are skipped so the stale-done GC is never fought
with, rows start caught up (no history replay), and terminal-only needs no
knob: the notifier never claims non-terminal kinds.
"""
from __future__ import annotations

import logging

from hermes_yaml import safe_dump

from gateway import kanban_watchers_notifier as notifier
from gateway.config import Platform
from gateway.kanban_watchers_notifier import (
    _KanbanNotification,
    _notifier_collect,
    _resolve_stream_subscription,
)
from gateway.run import GatewayRunner
from hermes_cli import (
    kanban_db as kb,
    kanban_db_boards as kbb,
    kanban_db_connect as kbc,
    kanban_db_notify as kbn,
)

STREAM = {"platform": "telegram", "chat_id": "8158007517", "delivery_mode": "notify"}


class RecordingAdapter:
    supports_async_delivery = True

    def __init__(self):
        self.sent = []

    async def send(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text, kwargs))


def make_fixture(tmp_path, monkeypatch):
    """Root home with a butler-owned board (software-co) and an ownerless one (gaudi)."""
    from pathlib import Path
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
    kb._PROFILE_BOARD_PIN_CACHE.clear()


def make_runner(monkeypatch):
    from typing import Any as _Any, cast as _cast
    runner: _Any = GatewayRunner.__new__(GatewayRunner)
    runner.adapters = {Platform.TELEGRAM: RecordingAdapter()}
    runner._profile_adapters = _cast("dict", {"swco-butler": {Platform.TELEGRAM: RecordingAdapter()}})
    runner._primary_profile_name = "default"
    runner._kanban_notifier_profile = "default"
    runner._kanban_dispatcher_lock_handle = object()
    runner.config = type("Cfg", (), {"multiplex_profiles": False})()
    monkeypatch.setattr(notifier, "_adapter_for_subscription",
                        lambda runner, platform, sub, owner: object())
    return runner


def collect(runner, stream_sub=None):
    return _notifier_collect(runner, kb, notifier_profile="default",
                             gc_due=False, gc_retention_days=30, stream_sub=stream_sub)


def make_task(board, title, *, assignee="worker"):
    with kbc.connect(board=board) as conn:
        return kb.create_task(conn, title=title, assignee=assignee)


def stream_rows(board, task):
    with kbc.connect(board=board) as conn:
        return kbn.list_notify_subs(conn, task_id=task)


def max_event_id(board, task):
    with kbc.connect(board=board) as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(id), 0) AS m FROM task_events WHERE task_id = ?", (task,)
        ).fetchone()
        return int(row["m"])


class TestResolveStreamSubscription:
    def test_disabled_when_config_absent_or_off(self):
        assert _resolve_stream_subscription(None) is None
        assert _resolve_stream_subscription({}) is None
        assert _resolve_stream_subscription({"stream_notify_enabled": False}) is None

    def test_partial_destination_disables_with_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger=notifier.logger.name):
            assert _resolve_stream_subscription({"stream_notify_enabled": True}) is None
            assert _resolve_stream_subscription(
                {"stream_notify_enabled": True, "stream_notify_platform": "telegram"}) is None
            assert _resolve_stream_subscription(
                {"stream_notify_enabled": True, "stream_notify_chat_id": "8158007517"}) is None
        assert any("platform/chat_id" in r.getMessage() for r in caplog.records)

    def test_full_config_resolves(self):
        sub = _resolve_stream_subscription({
            "stream_notify_enabled": True,
            "stream_notify_platform": "Telegram",
            "stream_notify_chat_id": "8158007517",
            "stream_notify_delivery_mode": "notify",
        })
        assert sub is not None
        assert sub == {"platform": "telegram", "chat_id": "8158007517",
                       "delivery_mode": "notify", "kinds": None}

    def test_unknown_mode_falls_back_to_notify(self, caplog):
        with caplog.at_level(logging.WARNING, logger=notifier.logger.name):
            sub = _resolve_stream_subscription({
                "stream_notify_enabled": True,
                "stream_notify_platform": "telegram",
                "stream_notify_chat_id": "8158007517",
                "stream_notify_delivery_mode": "smoke-signal",
            })
        assert sub["delivery_mode"] == "notify"
        assert any("stream_notify_delivery_mode" in r.getMessage() for r in caplog.records)


class TestStreamAutoSubscribe:
    def test_open_cards_on_every_board_get_owner_stamped_rows(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t_default = make_task("default", "open on default")
        t_owned = make_task("software-co", "open on butler board")
        t_ownerless = make_task("gaudi", "open on ownerless board")
        assert collect(runner, stream_sub=STREAM) == []
        assert [s["notifier_profile"] for s in stream_rows("default", t_default)] == ["default"]
        # Butler-owned board: the row is stamped with the board owner from
        # birth (F22 topology), so delivery-time derivation stays inert.
        assert [s["notifier_profile"] for s in stream_rows("software-co", t_owned)] == ["swco-butler"]
        # Ownerless board: the unpinned render profile, per the F22 decision.
        assert [s["notifier_profile"] for s in stream_rows("gaudi", t_ownerless)] == ["default"]
        for board, task in (("default", t_default), ("software-co", t_owned), ("gaudi", t_ownerless)):
            rows = stream_rows(board, task)
            assert len(rows) == 1
            assert rows[0]["delivery_mode"] == "notify"
            assert rows[0]["platform"] == "telegram" and rows[0]["chat_id"] == "8158007517"
            assert rows[0]["thread_id"] == ""
            # Caught up to the card's full history: no replay at first tick.
            assert rows[0]["last_event_id"] == max_event_id(board, task)

    def test_done_and_archived_cards_are_skipped(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t_done = make_task("default", "already done")
        with kbc.connect(board="default") as conn:
            kb.complete_task(conn, t_done, result="finished")
        t_archived = make_task("default", "archived")
        with kbc.connect(board="default") as conn:
            kb.archive_task(conn, t_archived)
        assert collect(runner, stream_sub=STREAM) == []
        assert stream_rows("default", t_done) == []
        assert stream_rows("default", t_archived) == []

    def test_existing_opt_in_row_is_never_downgraded(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("default", "creator-opted-in")
        with kbc.connect(board="default") as conn:
            kbn.add_notify_sub(conn, task_id=t, platform="telegram", chat_id="8158007517",
                               chat_type="dm", notifier_profile="default", delivery_mode="notify+wake")
        assert collect(runner, stream_sub=STREAM) == []
        rows = stream_rows("default", t)
        assert len(rows) == 1
        assert rows[0]["delivery_mode"] == "notify+wake"

    def test_idempotent_second_tick_and_new_card_coverage(self, tmp_path, monkeypatch, caplog):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t1 = make_task("default", "first")
        with caplog.at_level(logging.INFO, logger=notifier.logger.name):
            assert collect(runner, stream_sub=STREAM) == []
            assert collect(runner, stream_sub=STREAM) == []
        first = [r for r in caplog.records if "stream auto-subscribed" in r.getMessage()]
        assert len(first) == 1 and "1 open card" in first[0].getMessage()
        # A card created AFTER the backfill is covered by the very next tick.
        t2 = make_task("default", "created between ticks")
        assert collect(runner, stream_sub=STREAM) == []
        assert len(stream_rows("default", t1)) == 1
        assert len(stream_rows("default", t2)) == 1

    def test_stream_disabled_leaves_no_rows(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("default", "no stream")
        assert collect(runner) == []  # stream_sub=None: pre-F23 behavior
        assert stream_rows("default", t) == []

    def test_purged_done_row_is_not_re_inserted(self, tmp_path, monkeypatch):
        """The stale-done GC must not fight the auto-subscribe: a card that
        goes done keeps its row (``done`` is reversible), but once the GC
        purges it the row must NOT be resurrected — done is excluded from
        inserts, so the two mechanisms converge instead of churning."""
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("default", "done then purged")
        assert collect(runner, stream_sub=STREAM) == []
        with kbc.connect(board="default") as conn:
            kb.complete_task(conn, t, result="done")
            # done is reversible: the stream row survives the transition.
            assert len(kbn.list_notify_subs(conn, task_id=t)) == 1
            # Simulate the stale-done GC purge.
            assert kbn.remove_notify_sub(conn, task_id=t, platform="telegram", chat_id="8158007517")
        # A done card is NOT re-covered by later ticks.
        with kbc.connect(board="default") as conn:
            assert kbn.auto_subscribe_stream(conn, platform="telegram", chat_id="8158007517") == 0
            assert kbn.auto_subscribe_stream(conn, platform="telegram", chat_id="8158007517",
                                             notifier_profile="default") == 0
        assert stream_rows("default", t) == []

    def test_terminal_transition_streams_exactly_one_claim_no_wake(self, tmp_path, monkeypatch):
        """End-to-end through the collector: a completed card whose only row is
        the auto-subscribed stream row is claimed once, renders via the board
        owner, and the notify-only mode produces no wake kinds."""
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("software-co", "will complete")
        assert collect(runner, stream_sub=STREAM) == []
        with kbc.connect(board="software-co") as conn:
            kb.complete_task(conn, t, result="finished")
        rows = collect(runner, stream_sub=STREAM)
        assert [row["task"].id for row in rows] == [t]
        sub = rows[0]["sub"]
        assert sub["notifier_profile"] == "swco-butler"
        assert sub["delivery_mode"] == "notify"
        assert [ev.kind for ev in rows[0]["events"]] == ["completed"]
        n = _KanbanNotification(runner, rows[0], platform_cls=Platform, sub_fail_counts={})
        n.is_push_adapter = True
        assert n.wake_agent is False
        for ev in rows[0]["events"]:
            assert n.format_event(ev) is not None
        n.build_wake_text()
        assert n.wake_kinds == set()
        # The created-event (non-terminal) was never claimed/mentioned.
        assert all(ev.kind != "created" for ev in rows[0]["events"])


class TestStreamKinds:
    """t_1962d623: kanban.stream_notify_kinds — the stream stamps its rows
    with an event-kind allowlist so the GC purge/re-add cycle cannot silently
    drop the filter, and a filtered stream row skips excluded events."""

    def test_resolve_carries_kinds_from_config(self, caplog):
        sub = _resolve_stream_subscription({
            "stream_notify_enabled": True, "stream_notify_platform": "telegram",
            "stream_notify_chat_id": "1", "stream_notify_kinds": "blocked,gave_up",
        })
        assert sub["kinds"] == "blocked,gave_up"
        plain = _resolve_stream_subscription({
            "stream_notify_enabled": True, "stream_notify_platform": "telegram",
            "stream_notify_chat_id": "1",
        })
        assert plain["kinds"] is None
        with caplog.at_level(logging.WARNING, logger=notifier.logger.name):
            reset = _resolve_stream_subscription({
                "stream_notify_enabled": True, "stream_notify_platform": "telegram",
                "stream_notify_chat_id": "1", "stream_notify_kinds": "all",
            })
        assert reset["kinds"] is None
        assert any("stream_notify_kinds" in r.getMessage() for r in caplog.records)

    def test_stream_kinds_stamped_on_backfilled_rows(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("software-co", "filtered stream card")
        stream = dict(STREAM, kinds="blocked,gave_up,crashed,timed_out")
        assert collect(runner, stream_sub=stream) == []
        rows = stream_rows("software-co", t)
        assert len(rows) == 1
        assert rows[0]["kinds"] == ["blocked", "gave_up", "crashed", "timed_out"]

    def test_stream_filtered_row_skips_completed_and_pins_cursor(self, tmp_path, monkeypatch):
        make_fixture(tmp_path, monkeypatch)
        runner = make_runner(monkeypatch)
        t = make_task("software-co", "quiet completion")
        stream = dict(STREAM, kinds=("blocked", "gave_up"))
        assert collect(runner, stream_sub=stream) == []
        pinned = stream_rows("software-co", t)[0]["last_event_id"]
        with kbc.connect(board="software-co") as conn:
            kb.complete_task(conn, t, result="done quietly")
        # The completed event is excluded by the row's allowlist: nothing is
        # claimed/delivered and the cursor never advances past it.
        assert collect(runner, stream_sub=stream) == []
        assert stream_rows("software-co", t)[0]["last_event_id"] == pinned
