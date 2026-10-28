"""Regression tests for the CLI --board fence-divergence refusal (t_bedadfbe).

A fenced context (dispatched worker HERMES_KANBAN_TASK, or a delegate lineage
carrying HERMES_DELEGATED_CHILD_CONTEXT) resolves kanban paths through the
HERMES_KANBAN_DB pin BY DESIGN (5ec6baa: "workers physically cannot see other
boards" — see test_kanban_board_path_priority.py's pinned-path tests). But that
made ``hermes kanban --board <other> diagnostics`` (and every sibling read
command) silently answer from the SESSION's board: the nightly audit of
2026-10-28 got byte-identical default-board output for all 7 board slugs.

The fix refuses loudly at the CLI intent layer — the same contract the tool
layer already has for explicit board= (t_5651fc5b). These tests pin the CLI
behavior end to end through the real parser and kanban_command().
"""
import argparse
import os
from pathlib import Path

import pytest

from hermes_cli import kanban as kc
from hermes_cli import kanban_db as kb


@pytest.fixture()
def two_board_home(monkeypatch, tmp_path):
    """A hermes home with board 'own' (the worker's, pinned) and 'other'."""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    kb.create_board("own")
    kb.create_board("other")
    # A recognizable task on each board so misdirected reads are detectable.
    from hermes_cli import kanban_db_connect as kbc
    for name in ("own", "other"):
        with kbc.connect(board=name) as conn:
            kb.create_task(conn, title=f"task-on-{name}", assignee="somebody")
    pinned = kb.kanban_db_path(board="own")
    monkeypatch.setenv("HERMES_KANBAN_DB", str(pinned))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "own")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACES_ROOT",
                       str(home / "kanban" / "boards" / "own" / "workspaces"))
    yield home


def _run_cli(monkeypatch, *argv: str) -> tuple[int, str, str]:
    """Parse + execute a `hermes kanban ...` argv through the real CLI path."""
    parser = argparse.ArgumentParser(prog="hermes", add_help=False)
    sub = parser.add_subparsers(dest="command")
    kc.build_parser(sub)
    args = parser.parse_args(["kanban", *argv])
    import io
    import contextlib
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        rc = kc.kanban_command(args)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _fenced_env(monkeypatch):
    """The exact env a dispatcher-spawned worker runs with (plus its task pin)."""
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_bedadfbe")


def test_fenced_diagnostics_refuses_divergent_board(two_board_home, monkeypatch, capsys):
    """Fenced worker + --board other: loud refusal, exit 1, and stdout must
    NOT carry the session board's rows (the silent-fallback defect)."""
    _fenced_env(monkeypatch)
    rc, out, err = _run_cli(monkeypatch, "--board", "other", "diagnostics")
    assert rc == 1
    assert "REFUSED" in err and "dispatcher fence" in err
    assert "env -u HERMES_KANBAN_DB" in err, "remedy must name the env-stripped caller"
    assert "task-on-own" not in out, "silent current-board fallback regressed"


def test_fenced_refusal_covers_sibling_read_commands(two_board_home, monkeypatch):
    """Every read command routed through kanban_command shares the guard."""
    _fenced_env(monkeypatch)
    for cmd in (["list"], ["stats"], ["runs", "t_bedadfbe"], ["context", "t_bedadfbe"]):
        rc, out, err = _run_cli(monkeypatch, "--board", "other", *cmd)
        assert rc == 1 and "REFUSED" in err, f"{cmd} must refuse a divergent --board"
        assert "task-on-own" not in out


def test_fenced_own_board_still_works(two_board_home, monkeypatch):
    """--board <own pinned slug> is not divergent: must keep working."""
    _fenced_env(monkeypatch)
    rc, out, err = _run_cli(monkeypatch, "--board", "own", "list")
    assert rc == 0, err
    assert "task-on-own" in out


def test_unfenced_explicit_board_still_honored(two_board_home, monkeypatch):
    """No HERMES_KANBAN_TASK / child marker: the explicit slug wins over the
    worker-injected pin (os-reviewer P1 on PR#107195 / t_11c4afd8) — the guard
    must not turn the sanctioned operator-shell shape into a refusal."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("HERMES_DELEGATED_CHILD_CONTEXT", raising=False)
    rc, out, err = _run_cli(monkeypatch, "--board", "other", "list")
    assert rc == 0, err
    assert "task-on-other" in out and "task-on-own" not in out


def test_delegated_child_lineage_also_refused(two_board_home, monkeypatch):
    """A delegate descendant (HERMES_DELEGATED_CHILD_CONTEXT marker) gets the
    same loud refusal, not the silent pin fallback."""
    monkeypatch.setenv("HERMES_DELEGATED_CHILD_CONTEXT", str(two_board_home))
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    rc, out, err = _run_cli(monkeypatch, "--board", "other", "diagnostics")
    assert rc == 1 and "REFUSED" in err
    assert "task-on-own" not in out


def test_boards_list_unaffected_from_fenced_context(two_board_home, monkeypatch, capsys):
    """`boards ...` returns before the --board guard: hotfix #14's pin-free
    per-board COUNTS listing must keep working from a fenced worker."""
    _fenced_env(monkeypatch)
    rc, out, err = _run_cli(monkeypatch, "boards", "list")
    assert rc == 0, err
    assert "other" in out and "own" in out
