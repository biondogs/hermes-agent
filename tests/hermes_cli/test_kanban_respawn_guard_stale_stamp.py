"""A stale rate-limit stamp must never park a card as ``blocker_auth`` (LOCAL HOTFIX t_b274ffbe).

Specimen (default board, card t_ed6f85c9, 2026-10-30 → 11-02): two runs ended
``rate_limited`` (provider quota wall, exit 75); the non-counting requeue stamped
``tasks.last_failure_error = "pid … exited rate-limited (quota wall) — requeued without
counting a failure"``. The NEXT run worked normally and ended ``blocked`` (needs_input).
Nothing on that path clears the stamp (only ``complete_task`` / ``unblock_task`` do), and
the card was later re-queued by the triage specifier (triage → todo → ready) and by an
operator promote. ``check_respawn_guard`` step 1 only recognises the stamp while the
LATEST run is ``rate_limited``; with a later ``blocked`` run on top, step 2 regex-matched
the stale quota text and returned ``blocker_auth`` every tick — 16,765 ``respawn_guarded``
events and no worker for ~3.5 days, and downstream lanes read it as "broken credentials".

Contract pinned here:
* a non-counting requeue stamp (rate-limited / drain-refused) whose producing run has been
  superseded by a later run is stale: the guard must NOT return ``blocker_auth`` for it;
* while the rate-limited run is still the latest, the cooldown behaviour is unchanged;
* a genuine auth/quota failure (e.g. a spawn failure) still guards as ``blocker_auth``;
* ``respawn_guarded`` events for ``blocker_auth`` name the cause plainly
  (``provider_quota`` vs ``auth``) so no lane mislabels a quota wall as a credential fault.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

import hermes_cli.kanban_db as _kb
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_dispatch as kbd
from hermes_cli.quiet_single_query import KANBAN_WORKER_EXIT_TRAILER

DAY = 86400


@pytest.fixture
def kanban_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_KANBAN_CRASH_GRACE_SECONDS", "0")
    monkeypatch.setenv("HERMES_KANBAN_RATE_LIMIT_COOLDOWN_SECONDS", "300")
    monkeypatch.setattr(kb, "_pid_alive", lambda _pid: False)
    kbd._recent_worker_exits.clear()
    kb.init_db()
    return home


def _rate_limited_run(conn, tid: str, pid: int) -> None:
    """Claim ``tid`` for a worker that already exited on the quota sentinel, then reap it
    through the real dead-worker sweep (which books ``rate_limited`` + stamps the error)."""
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
            "custom:litellm rejected the request and retrying won't help.\n"
            "Provider said: quota exceeded (429)\n\n"
            f"{KANBAN_WORKER_EXIT_TRAILER}{kb.KANBAN_RATE_LIMIT_EXIT_CODE}\n"
        )
    assert kbd.detect_crashed_workers(conn) == []
    assert kbd.detect_crashed_workers._last_rate_limited == [tid]


def _latest_outcome(conn, tid: str) -> str:
    return conn.execute(
        "SELECT outcome FROM task_runs WHERE task_id=? AND ended_at IS NOT NULL "
        "ORDER BY ended_at DESC, id DESC LIMIT 1", (tid,),
    ).fetchone()["outcome"]


def _stamp(conn, tid: str) -> str:
    return conn.execute("SELECT last_failure_error FROM tasks WHERE id=?", (tid,)).fetchone()[0] or ""


class _Clock:
    """Controllable wall clock: the specimen's runs ended minutes/days apart, and the
    guard orders runs by ``ended_at`` — same-second fixtures would hide the bug."""

    def __init__(self, monkeypatch):
        self.now = float(int(time.time()))
        monkeypatch.setattr(_kb.time, "time", lambda: self.now)

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock(monkeypatch) -> _Clock:
    return _Clock(monkeypatch)


def _far_future(clock: _Clock, days: float = 3.5) -> None:
    clock.advance(days * DAY)


def _requeue_via_promote(conn, tid: str) -> None:
    ok, why = kb.promote_task(conn, tid, actor="operator", reason="operator GO: retry")
    assert ok, why


def _requeue_via_specify(conn, tid: str) -> None:
    # The specimen's path: the block-loop breaker routed the card to triage, the
    # auto-specifier moved it triage -> todo, and recompute_ready promoted it.
    conn.execute("UPDATE tasks SET status='triage' WHERE id=?", (tid,))
    conn.commit()
    assert kb.specify_triage_task(conn, tid, title="submit gate (specified)", author="auto-decomposer")
    kb.recompute_ready(conn)


@pytest.mark.parametrize("requeue", [_requeue_via_promote, _requeue_via_specify],
                         ids=["operator-promote", "triage-specify"])
def test_stale_rate_limit_stamp_after_blocked_run_is_not_blocker_auth(kanban_home, clock, requeue):
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="upstream PR submit gate", assignee="a")

        # Runs 353/357: two quota walls ~15 min apart, each a non-counting requeue + stamp.
        _rate_limited_run(conn, tid, 71001)
        clock.advance(900)
        _rate_limited_run(conn, tid, 71002)
        assert "exited rate-limited (quota wall)" in _stamp(conn, tid)
        assert kb.get_task(conn, tid).consecutive_failures == 0

        # Run 360: the quota cleared, the worker ran normally and blocked on a decision.
        clock.advance(300)
        claimed = kb.claim_task(conn, tid)
        assert claimed is not None
        clock.advance(760)
        assert kb.block_task(conn, tid, reason="needs operator decision", kind="needs_input",
                             expected_run_id=claimed.current_run_id)
        assert _latest_outcome(conn, tid) == "blocked"

        # Re-queued later (specifier minutes later / operator GO days later); nothing on
        # either path clears the stamp — that is the specimen's precondition.
        clock.advance(60)
        requeue(conn, tid)
        assert kb.get_task(conn, tid).status == "ready"
        assert "exited rate-limited (quota wall)" in _stamp(conn, tid)
        _far_future(clock)

        assert kbd.check_respawn_guard(conn, tid) is None, (
            "a rate-limit stamp superseded by a later normal run must not guard as blocker_auth"
        )


def test_review_lane_not_parked_by_stale_rate_limit_stamp(kanban_home, clock):
    """Unit form of upstream e2e gate #119070: a rate-limited implementer run, then a retry
    that hands off to review — the review lane must not see ``blocker_auth``."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="impl", assignee="a")
        _rate_limited_run(conn, tid, 71101)
        clock.advance(10)
        claimed = kb.claim_task(conn, tid)
        assert claimed is not None
        clock.advance(60)
        assert kb.request_review(conn, tid, summary="ready", expected_run_id=claimed.current_run_id)
        assert kb.get_task(conn, tid).status == "review"
        clock.advance(10)
        assert kbd.check_respawn_guard(conn, tid, lane="review") is None


def test_live_rate_limit_run_keeps_cooldown_semantics(kanban_home, clock):
    """Unchanged: while the rate-limited run is the latest, the cooldown spaces retries and
    an elapsed cooldown releases the card (never blocker_auth)."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="quota", assignee="a")
        _rate_limited_run(conn, tid, 71201)
        clock.advance(10)
        assert kbd.check_respawn_guard(conn, tid) == "rate_limit_cooldown"
        clock.advance(600)
        assert kbd.check_respawn_guard(conn, tid) is None


def test_genuine_auth_failure_still_guards(kanban_home):
    """Control: a real auth failure stamped by a spawn failure is still ``blocker_auth``,
    and a stale requeue stamp is recognised only by its exact producer wording."""
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="bad key", assignee="a")
        claimed = kb.claim_task(conn, tid)
        assert claimed is not None
        kbd._record_task_failure(
            conn, tid, "401 Unauthorized: invalid api key", outcome="spawn_failed",
            failure_limit=99, release_claim=True, end_run=True,
        )
        assert _latest_outcome(conn, tid) == "spawn_failed"
        assert kbd.check_respawn_guard(conn, tid) == "blocker_auth"
        assert not kbd._is_stale_requeue_stamp("401 Unauthorized: invalid api key", "blocked")
        assert not kbd._is_stale_requeue_stamp("429 rate limit from provider", "blocked")


@pytest.mark.parametrize("err, cause", [
    ("pid 1 exited rate-limited (quota wall) — requeued without counting a failure", "provider_quota"),
    ("429 Too Many Requests", "provider_quota"),
    ("insufficient_quota: billing hard limit reached", "provider_quota"),
    ("401 Unauthorized: invalid api key", "auth"),
    ("403 Forbidden: Resource not accessible by integration", "auth"),
])
def test_blocker_cause_names_quota_plainly(err, cause):
    got = kbd.respawn_blocker_cause(err)
    assert got["cause"] == cause
    if cause == "provider_quota":
        assert "credential" not in got["detail"].lower() or "not a credential" in got["detail"].lower()
        assert "quota" in got["detail"].lower()


def test_respawn_guarded_event_carries_plain_cause(kanban_home, monkeypatch, all_assignees_spawnable):
    with kbc.connect() as conn:
        tid = kb.create_task(conn, title="quota spawn", assignee="a")
        claimed = kb.claim_task(conn, tid)
        kbd._record_task_failure(
            conn, tid, "429 Too Many Requests: quota exceeded", outcome="spawn_failed",
            failure_limit=99, release_claim=True, end_run=True,
        )
        assert claimed is not None
        res = kbd.dispatch_once(conn, spawn_fn=lambda *a, **k: None)
        assert dict(res.respawn_guarded).get(tid) == "blocker_auth"
        payload = json.loads(conn.execute(
            "SELECT payload FROM task_events WHERE task_id=? AND kind='respawn_guarded' "
            "ORDER BY id DESC LIMIT 1", (tid,),
        ).fetchone()[0])
        assert payload["reason"] == "blocker_auth"
        assert payload["cause"] == "provider_quota"
        assert "quota" in payload["detail"].lower()
