"""Per-profile board pin (``kanban.board`` in the active profile's config.yaml).

Regression coverage for the swco-butler → gargantua02 misfiling incident
(2026-10-23): gateway chat sessions carry no ``HERMES_KANBAN_*`` pins (the
daemon strips them at boot so one session cannot retarget another), so they
fell through to the shared ``<root>/kanban/current`` pointer — which a
``boards switch`` had left aimed at gargantua02 fleet-wide, and every butler's
unpinned kanban call misfiled onto that board. The pin makes board resolution
profile-scoped for pin-less sessions, and the tool layer fences pinned
profiles (board butlers) off every other board.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the worktree (not the stale global clone) is first on sys.path.
_WORKTREE = Path(__file__).resolve().parents[2]
if str(_WORKTREE) not in sys.path:
    sys.path.insert(0, str(_WORKTREE))

from hermes_yaml import safe_dump
from hermes_constants import (
    reset_hermes_home_override,
    set_hermes_home_override,
)


# ---------------------------------------------------------------------------
# Fixture: shared kanban root + one "butler" profile home whose config pins a
# board, mirroring the multiplex gateway (ContextVar home override, no env).
# ---------------------------------------------------------------------------

@pytest.fixture
def boards_env(tmp_path, monkeypatch):
    """Shared HERMES_HOME root with two boards; profile home override cleared."""
    root = tmp_path / "hermes_home"
    root.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(root))
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
    from hermes_cli import kanban_db as kb
    from hermes_cli import kanban_db_boards as kbb
    kb._INITIALIZED_PATHS.clear()
    kb._PROFILE_BOARD_PIN_CACHE.clear()
    kbb.create_board("software-co")
    kbb.create_board("gargantua02")
    # Snapshot + clear the home override at SETUP (the tests set it themselves
    # mid-body, mirroring a routed gateway turn), restore the pre-test state at
    # teardown. Resetting a token captured at TEARDOWN would re-install the
    # test's leftover override and poison every later test in the process.
    override_token = set_hermes_home_override(None)
    yield root
    reset_hermes_home_override(override_token)
    kb._PROFILE_BOARD_PIN_CACHE.clear()


@pytest.fixture
def butler_home(boards_env):
    """A profile home (like ``<root>/profiles/swco-butler``) with a pinned config."""
    profile = boards_env / "profiles" / "swco-butler"
    profile.mkdir(parents=True)


    def set_pin(slug):
        (profile / "config.yaml").write_text(
            safe_dump({"kanban": {"board": slug}} if slug else {"kanban": {}}),
            encoding="utf-8",
        )
        # Force an mtime bump: same-second rewrites must invalidate the cache.
        st = (profile / "config.yaml").stat()
        os.utime(profile / "config.yaml", ns=(st.st_atime_ns + 1_000_000_000, st.st_mtime_ns + 1_000_000_000))
        return profile

    set_pin("software-co")
    yield set_pin


# ---------------------------------------------------------------------------
# Resolution precedence — hermes_cli.kanban_db.get_current_board
# ---------------------------------------------------------------------------

class TestPinResolution:
    def test_pin_resolves_for_pinless_session(self, butler_home):
        """Gateway-chat session: ContextVar home, no env pins -> pinned board."""
        from hermes_cli import kanban_db as kb
        set_hermes_home_override(str(butler_home("software-co")))
        assert kb.profile_board_pin() == "software-co"
        assert kb.get_current_board() == "software-co"
        assert kb.kanban_db_path().parent.name == "software-co"

    def test_env_board_pin_outranks_profile_pin(self, butler_home, monkeypatch):
        from hermes_cli import kanban_db as kb
        set_hermes_home_override(str(butler_home("software-co")))
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "gargantua02")
        assert kb.get_current_board() == "gargantua02"

    def test_context_override_outranks_profile_pin(self, butler_home):
        from hermes_cli import kanban_db as kb
        set_hermes_home_override(str(butler_home("software-co")))
        with kb.scoped_current_board("gargantua02"):
            assert kb.get_current_board() == "gargantua02"
        assert kb.get_current_board() == "software-co"

    def test_missing_pin_board_falls_through(self, butler_home, boards_env):
        from hermes_cli import kanban_db as kb
        set_hermes_home_override(str(butler_home("no-such-board")))
        assert kb.profile_board_pin() is None
        assert kb.get_current_board() == "default"

    def test_malformed_pin_falls_through(self, butler_home):
        from hermes_cli import kanban_db as kb
        set_hermes_home_override(str(butler_home("Bad Slug!")))
        assert kb.get_current_board() == "default"

    def test_archived_pin_board_falls_through(self, butler_home):
        from hermes_cli import kanban_db as kb
        from hermes_cli import kanban_db_boards as kbb
        kbb.remove_board("gargantua02", archive=True)
        set_hermes_home_override(str(butler_home("gargantua02")))
        assert kb.profile_board_pin() is None
        assert kb.get_current_board() == "default"

    def test_pin_not_honored_over_stale_current_file(self, butler_home):
        from hermes_cli import kanban_db as kb
        # A `boards switch` left the shared pointer aimed elsewhere — the pin
        # is exactly the guard against that stale pointer for pinned profiles.
        kb.set_current_board("gargantua02")
        set_hermes_home_override(str(butler_home("software-co")))
        assert kb.get_current_board() == "software-co"

    def test_stale_current_file_still_wins_for_unpinned_profile(self, boards_env):
        """Original fall-through behaviour is untouched when no pin is set."""
        from hermes_cli import kanban_db as kb
        unpinned = boards_env / "profiles" / "plain"
        unpinned.mkdir(parents=True)
        (unpinned / "config.yaml").write_text("agent: {}\n", encoding="utf-8")
        kb.set_current_board("gargantua02")
        set_hermes_home_override(str(unpinned))
        assert kb.get_current_board() == "gargantua02"

    def test_cache_invalidates_on_config_change(self, butler_home):
        from hermes_cli import kanban_db as kb
        home = butler_home("software-co")
        set_hermes_home_override(str(home))
        assert kb.profile_board_pin() == "software-co"        # cached
        assert kb.profile_board_pin() == "software-co"        # cache hit
        butler_home("gargantua02")                            # rewrite + mtime bump
        assert kb.profile_board_pin() == "gargantua02"
        butler_home(None)                                     # pin removed
        assert kb.profile_board_pin() is None
        assert kb.get_current_board() == "default"


# ---------------------------------------------------------------------------
# Tool-layer fence — tools.kanban_tools._board
# ---------------------------------------------------------------------------

class TestToolFence:
    def _handler(self):
        from tools import kanban_tools as kt
        return kt

    def test_other_board_refused_for_pinned_session(self, butler_home):
        import json
        set_hermes_home_override(str(butler_home("software-co")))
        kt = self._handler()
        out = kt._handle_list({"board": "gargantua02"})
        assert '"ok": false' in out or '"error"' in out
        assert "pinned to kanban board 'software-co'" in out

    def test_mutation_other_board_refused(self, butler_home):
        set_hermes_home_override(str(butler_home("software-co")))
        kt = self._handler()
        out = kt._handle_comment({"task_id": "t_nope", "board": "gargantua02", "body": "x"})
        assert "pinned to kanban board 'software-co'" in out
        # No gargantua02 task was touched (board untouched is implicit: refusal
        # happens before connect()).

    def test_own_board_ok(self, butler_home):
        import json
        set_hermes_home_override(str(butler_home("software-co")))
        kt = self._handler()
        out = json.loads(kt._handle_list({"board": "software-co"}))
        assert "error" not in out and "tasks" in out

    def test_unpinned_call_resolves_to_pin(self, butler_home):
        import json
        from hermes_cli import kanban_db as kb
        from hermes_cli import kanban_db_connect as kbc
        set_hermes_home_override(str(butler_home("software-co")))
        conn = kbc.connect(board="software-co")
        tid = kb.create_task(conn, title="only on software-co", assignee="sw-pm")
        conn.close()
        kt = self._handler()
        out = json.loads(kt._handle_list({}))
        assert "error" not in out and "tasks" in out
        assert any(t.get("id") == tid for t in out["tasks"]), out

    def test_unpinned_profile_keeps_explicit_cross_board(self, boards_env):
        import json
        from hermes_cli import kanban_db as kb
        from hermes_cli import kanban_db_connect as kbc
        unpinned = boards_env / "profiles" / "plain"
        unpinned.mkdir(parents=True)
        (unpinned / "config.yaml").write_text("agent: {}\n", encoding="utf-8")
        set_hermes_home_override(str(unpinned))
        conn = kbc.connect(board="gargantua02")
        tid = kb.create_task(conn, title="cross-board op", assignee="x")
        conn.close()
        kt = self._handler()
        out = json.loads(kt._handle_list({"board": "gargantua02"}))
        assert "error" not in out and "tasks" in out
        assert any(t.get("id") == tid for t in out["tasks"]), out

    def test_invalid_slug_for_pinned_session_is_clean_error(self, butler_home):
        set_hermes_home_override(str(butler_home("software-co")))
        kt = self._handler()
        out = kt._handle_list({"board": "--bad--"})
        assert '"ok": false' in out or '"error"' in out
