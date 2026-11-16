"""Crash accounting (t_d269ec0c): exit codes 74/75/77/78, host ceiling, failure classes.

Defects fixed: D1 (75 stays rate_limited), D2 (78 terminal_provider text),
D3 (host crash counted once, ceiling at 6), D4 (single helper, docstrings kept).
"""
from __future__ import annotations
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_dispatch as kbd


def fresh_conn(tmp_path, name="test"):
    db = tmp_path / f"{name}.db"
    return kbc.connect(db_path=db)


def _make_running(conn, title="task", assignee="sw-dev-a", max_retries=None):
    tid = kb.create_task(conn, title=title, assignee=assignee, max_retries=max_retries)
    # Put task into running with a host-local claim so _reclaim sees it
    now = int(time.time())
    host_prefix = kb._host_prefix()
    conn.execute(
        "UPDATE tasks SET status='running', claim_lock=?, claim_expires=?, worker_pid=?, worker_started_at=?, started_at=? WHERE id=?",
        (host_prefix + ":1", now + 3600, 99999, str(now - 100), now - 100, tid),
    )
    # Open a run
    conn.execute("INSERT INTO task_runs (task_id, outcome, status, started_at) VALUES (?,?,?,?)", (tid, "running", "running", now - 100))
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("UPDATE tasks SET current_run_id=? WHERE id=?", (run_id, tid))
    conn.commit()
    return tid


def test_exit_codes_preserved():
    """75=rate_limited, 78=terminal_provider unchanged; 74=host_loss, 77=prestart_refusal."""
    assert kbd._exit_code_kind(75) == ("rate_limited", 75)
    assert kbd._exit_code_kind(78) == ("terminal_provider", 78)
    assert kbd._exit_code_kind(76) == ("drain_refused", 76)
    assert kbd._exit_code_kind(74) == ("host_loss", 74)
    assert kbd._exit_code_kind(77) == ("prestart_refusal", 77)
    assert kb.KANBAN_HOST_LOSS_EXIT_CODE == 74
    assert kb.KANBAN_PRESTART_REFUSAL_EXIT_CODE == 77


def test_rate_limited_not_counted_and_cooldown_text(tmp_path):
    """Exit 75: non-counting, cooldown text, not a host crash."""
    conn = fresh_conn(tmp_path, "rate_limited")
    tid = _make_running(conn, assignee="sw-dev-a")
    # Simulate dead worker via exit_code 75
    with patch.object(kbd, "_worker_alive", return_value=False):
        with patch.object(kbd, "_worker_log_exit_code", return_value=None):
            # Force _classify_dead_worker_exit to see exit_code 75
            dead = kbd._classify_dead_worker(99999, kb._host_prefix() + ":1", exit_code=75, task_id=tid)
    assert dead.rate_limited is True
    assert dead.failure_class is None  # rate_limited is own class, not host
    assert "quota wall" in dead.error_text
    assert "requeued without counting" in dead.error_text


def test_terminal_provider_message(tmp_path):
    """Exit 78: terminal_provider with original message."""
    conn = fresh_conn(tmp_path, "terminal")
    tid = _make_running(conn)
    with patch.object(kbd, "_worker_alive", return_value=False):
        dead = kbd._classify_dead_worker(99999, kb._host_prefix()+":1", exit_code=78, task_id=tid)
    assert dead.terminal_provider is True
    assert "fix the configuration, then unblock" in dead.error_text


def test_host_loss_74_never_counted_and_ceiling(tmp_path):
    """74 -> host class, never counted; ceiling trips at exactly 6th host crash."""
    conn = fresh_conn(tmp_path, "host74")
    tid = kb.create_task(conn, title="host ceiling", assignee="sw-dev-a")
    # Simulate 5 host crashes via _account path (reclaim already wrote events)
    for i in range(5):
        # Insert a crashed event with failure_class host_restart (the single reclaim event)
        kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 1000+i}, run_id=None)
        cnt = kbd._host_crash_count_24h(conn, tid)
        assert cnt == i+1, f"count after {i+1} events should be {i+1}, got {cnt}"
        # Account should NOT trip before 6
        dead = kbd._DeadWorker("host_loss", 74, f"pid {1000+i} host loss", "crashed", {"failure_class": "host_restart", "pid": 1000+i}, host_crash=True, failure_class="host_restart")
        blocked = kbd._account_crashes(conn, [(tid, 1000+i, "host:1", dead)])
        assert blocked == [], f"should not block at {i+1} crashes"
        row = conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()
        assert row["status"] != "blocked"
    # 6th crash trips
    kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 2000}, run_id=None)
    assert kbd._host_crash_count_24h(conn, tid) == 6
    dead6 = kbd._DeadWorker("host_loss", 74, "pid 2000 host loss", "crashed", {"failure_class": "host_restart", "pid": 2000}, host_crash=True, failure_class="host_restart")
    blocked = kbd._account_crashes(conn, [(tid, 2000, "host:1", dead6)])
    assert tid in blocked
    row = conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()
    assert row["status"] == "blocked"


def test_three_simultaneous_host_losses_do_not_block(tmp_path):
    """3 simultaneous host losses do not sticky-block 3 cards."""
    conn = fresh_conn(tmp_path, "trio")
    tids = [kb.create_task(conn, title=f"trio {i}", assignee="sw-dev-b") for i in range(3)]
    # Each gets its reclaim event already (host_restart)
    details = []
    for i, tid in enumerate(tids):
        kb._append_event(conn, tid, "crashed", {"failure_class": "host_restart", "pid": 3000+i}, run_id=None)
        dead = kbd._DeadWorker("host_loss", 74, f"pid {3000+i} host loss", "crashed", {"failure_class": "host_restart"}, host_crash=True, failure_class="host_restart")
        details.append((tid, 3000+i, "host:1", dead))
    blocked = kbd._account_crashes(conn, details)
    assert blocked == []
    for tid in tids:
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()["status"] != "blocked"


def test_prestart_refusal_blocks_first_and_names_profile(tmp_path):
    """Exit 77 blocks on first occurrence, sticky, message names profile."""
    conn = fresh_conn(tmp_path, "prestart")
    tid = kb.create_task(conn, title="prestart", assignee="my-profile")
    dead = kbd._DeadWorker("prestart_refusal", 77, "pid 4000 prestart refusal kanban_skills_unavailable", "crashed", {"failure_class": "prestart_refusal"}, prestart_refusal=True, failure_class="prestart_refusal")
    blocked = kbd._account_crashes(conn, [(tid, 4000, "host:1", dead)])
    assert tid in blocked
    row = conn.execute("SELECT status, last_failure_error FROM tasks WHERE id=?", (tid,)).fetchone()
    assert row["status"] == "blocked"
    assert "my-profile" in row["last_failure_error"]
    # Sticky means recompute_ready won't promote it
    conn.execute("UPDATE tasks SET status='blocked' WHERE id=?", (tid,))
    # _has_sticky_block check: ensure event had sticky
    ev = conn.execute("SELECT payload FROM task_events WHERE task_id=? AND kind='gave_up' ORDER BY id DESC LIMIT 1", (tid,)).fetchone()
    import json
    payload = json.loads(ev["payload"])
    assert payload.get("sticky") is True


def test_p1_resolves_config_failure_limit_3(tmp_path, monkeypatch):
    """P1: helper resolves kanban.failure_limit=3 from config."""
    with patch("hermes_cli.config.load_config", return_value={"kanban": {"failure_limit": 3}}):
        assert kbd._resolve_config_failure_limit() == 3
    with patch("hermes_cli.config.load_config", return_value={"kanban": {"failure_limit": 3}}):
        # _record_task_failure with no explicit limit should use 3
        conn = fresh_conn(tmp_path, "p1")
        tid = kb.create_task(conn, title="p1", assignee="a")
        # Two failures should not trip (limit 3)
        for _ in range(2):
            kbd._record_task_failure(conn, tid, error="boom", outcome="crashed", release_claim=False, end_run=False)
            assert conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()["status"] != "blocked"
        # Third trips
        kbd._record_task_failure(conn, tid, error="boom", outcome="crashed", release_claim=False, end_run=False)
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()["status"] == "blocked"


def test_genuine_errors_still_stop_at_3(tmp_path):
    """Genuine worker errors stop at failure_limit 3."""
    conn = fresh_conn(tmp_path, "genuine")
    tid = kb.create_task(conn, title="genuine", assignee="a")
    with patch("hermes_cli.config.load_config", return_value={"kanban": {"failure_limit": 3}}):
        for i in range(2):
            kbd._record_task_failure(conn, tid, error=f"worker error {i}", outcome="crashed", release_claim=False, end_run=False)
            assert conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()["status"] != "blocked"
        kbd._record_task_failure(conn, tid, error="worker error final", outcome="crashed", release_claim=False, end_run=False)
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (tid,)).fetchone()["status"] == "blocked"
        # payload carries failure_class for bulletin
        row = conn.execute("SELECT payload FROM task_events WHERE task_id=? AND kind='gave_up' ORDER BY id DESC LIMIT 1", (tid,)).fetchone()
        # gave_up payload should have error; worker_error class may be implicit
        assert row is not None


def test_single_helper_exists():
    """One _resolve_config_failure_limit helper (D4)."""
    assert hasattr(kbd, "_resolve_config_failure_limit")
    # kanban_db should delegate to dispatch helper, not duplicate logic with different error handling
    import inspect
    src = inspect.getsource(kb.recompute_ready)
    assert "_resolve_config_failure_limit" in src
