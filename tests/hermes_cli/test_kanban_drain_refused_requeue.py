"""An owner-drain refusal is a host condition, never a card failure.

During a graceful-restart deferred drain (SIGUSR1 / `hermes update` window) the profile
owner refuses new guard spawns with ``runtime_draining``. The worker exits on the
``KANBAN_DRAIN_REFUSED_EXIT_CODE`` sentinel (76), and the dead-worker sweep must book it
as a ``drain_refused`` requeue — back to ``ready`` WITHOUT counting against the retry
budget, with NO ``gave_up`` and NO breaker trip — mirroring the rate-limit contract.
The respawn guard then spaces retries by the shared rate-limit cooldown.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_dispatch as kbd
from hermes_cli.quiet_single_query import KANBAN_WORKER_EXIT_TRAILER


@pytest.fixture
def kanban_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_KANBAN_CRASH_GRACE_SECONDS", "0")
    monkeypatch.delenv("HERMES_KANBAN_RATE_LIMIT_COOLDOWN_SECONDS", raising=False)
    monkeypatch.setattr(kb, "_pid_alive", lambda _pid: False)
    kbd._recent_worker_exits.clear()
    kb.init_db()
    return home


def _dead_worker_with_log(conn, tid: str, pid: int, rc: int) -> None:
    """Claim ``tid`` for a worker that already exited ``rc`` and wrote its log — never reaped here."""
    host = kb._claimer_id().split(":", 1)[0]
    kb.claim_task(conn, tid, claimer=f"{host}:w{pid}")
    conn.execute(
        "UPDATE tasks SET worker_pid=?, worker_started_at=NULL, started_at=? WHERE id=?",
        (pid, int(time.time()) - 120, tid),
    )
    conn.commit()
    log = kb.worker_log_path(tid)
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(
            f"Kanban owner refused: runtime_draining\n\n{KANBAN_WORKER_EXIT_TRAILER}{rc}\n"
        )


def test_drain_refused_exit_is_a_non_counting_requeue(kanban_home):
    """The 76 sentinel is booked ``drain_refused``: back to ``ready``, zero failures, no
    ``gave_up`` — the crash that used to burn retry budgets during a drain window."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="drain window", assignee="a")
        _dead_worker_with_log(conn, tid, 72001, kb.KANBAN_DRAIN_REFUSED_EXIT_CODE)

        crashed = kbd.detect_crashed_workers(conn)

        assert crashed == [], "a drain-refused worker must not be reported as a crash"
        assert kbd.detect_crashed_workers._last_drain_refused == [tid]
        ev = conn.execute(
            "SELECT kind FROM task_events WHERE task_id=? ORDER BY id DESC LIMIT 1", (tid,)
        ).fetchone()
        run = conn.execute(
            "SELECT outcome, error, metadata FROM task_runs WHERE task_id=? ORDER BY id DESC LIMIT 1",
            (tid,),
        ).fetchone()
        task = kb.get_task(conn, tid)
        assert ev["kind"] == "drain_refused"
        assert run["outcome"] == "drain_refused"
        assert task.status == "ready"
        assert task.consecutive_failures == 0
        # The decoded sentinel lands in the run row so the booking stays tellable after
        # the fact (same contract as the quota sentinel, #113611).
        assert kb._json_dict(run["metadata"]).get("exit_code") == kb.KANBAN_DRAIN_REFUSED_EXIT_CODE
        for kind in ("crashed", "gave_up", "blocked", "rate_limited", "protocol_violation"):
            assert not conn.execute(
                "SELECT 1 FROM task_events WHERE task_id=? AND kind=?", (tid, kind)
            ).fetchone(), f"unexpected {kind} event on a drain-refused card"


def test_repeated_drain_refusals_never_trip_the_breaker(kanban_home):
    """A drain window can outlive 180s of worker owner-wait; the dispatcher may re-spawn
    into it repeatedly. Even a run of refusals far past ``failure_limit`` must leave the
    card retryable: budget untouched, no ``gave_up``, never ``blocked``."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="long drain", assignee="a")
        for i in range(5):
            _dead_worker_with_log(conn, tid, 72100 + i, kb.KANBAN_DRAIN_REFUSED_EXIT_CODE)
            kbd.detect_crashed_workers(conn)
            kb.recompute_ready(conn, failure_limit=2)
            task = kb.get_task(conn, tid)
            assert task.status == "ready", f"round {i}: drain refusal must never block the card"
            assert task.consecutive_failures == 0, f"round {i}: drain refusal must not count"
        assert not conn.execute(
            "SELECT 1 FROM task_events WHERE task_id=? AND kind='gave_up'", (tid,)
        ).fetchone(), "a drain window must never produce a gave_up"


def test_respawn_guard_spaces_drain_requeues_by_the_shared_cooldown(kanban_home):
    """After a drain-refused requeue the respawn guard holds the card for the rate-limit
    cooldown (so a still-draining host is not hammered every tick) and releases it once
    the cooldown elapses or is disabled."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="cooldown", assignee="a")
        _dead_worker_with_log(conn, tid, 72200, kb.KANBAN_DRAIN_REFUSED_EXIT_CODE)
        kbd.detect_crashed_workers(conn)
        assert kbd.check_respawn_guard(conn, tid, lane="ready") == "rate_limit_cooldown"

    # Cooldown disabled → respawn immediately (and skip blocker_auth on the stamped text).
    monkey = pytest.MonkeyPatch()
    monkey.setenv("HERMES_KANBAN_RATE_LIMIT_COOLDOWN_SECONDS", "0")
    try:
        with kbc.connect() as conn:
            assert kbd.check_respawn_guard(conn, tid, lane="ready") is None
    finally:
        monkey.undo()


def test_exit_code_classification(kanban_home):
    """The sentinel maps to its own kind before any DB work, like the quota/config sentinels."""
    assert kbd._exit_code_kind(kb.KANBAN_DRAIN_REFUSED_EXIT_CODE) == (
        "drain_refused", kb.KANBAN_DRAIN_REFUSED_EXIT_CODE,
    )
    assert kbd._exit_code_kind(1) == ("nonzero_exit", 1)
    dead = kbd._classify_dead_worker_exit(
        1234, "host:w", kb.KANBAN_DRAIN_REFUSED_EXIT_CODE,
    )
    assert dead.drain_refused and not dead.rate_limited
    assert dead.run_outcome == "drain_refused"
    assert dead.event_kind == "drain_refused"
