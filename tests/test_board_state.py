"""BOARD-LAYERS-3-STATE: hermetic per-board state tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import hermes_yaml as yaml

from hermes_cli.board_layer import compose


@pytest.fixture
def iso_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))
    try:
        import hermes_constants as hc
        hc._default_hermes_root_memo = None
    except Exception:
        pass
    return home


@pytest.fixture
def boards(iso_home):
    from hermes_cli.kanban_db import board_dir
    for slug in ("alpha", "beta"):
        d = board_dir(slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "board.json").write_text(f'{{"name":"{slug}"}}', encoding="utf-8")
    return ("alpha", "beta")


def _write_board_yaml(slug: str, doc: dict):
    from hermes_cli.kanban_db import board_dir
    p = board_dir(slug) / "board.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _write_profile(home: Path, role: str, config: dict | None = None):
    prof = home / "profiles" / role
    prof.mkdir(parents=True, exist_ok=True)
    cfg = config or {"model": {"provider": "openai", "model": "gpt-4o-mini"}}
    (prof / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (prof / "SOUL.md").write_text(f"You are {role}.", encoding="utf-8")
    return prof


class TestPathMatrix:
    """alpha/beta × role-a/assistant path resolution."""

    @pytest.mark.parametrize("board", ["alpha", "beta"])
    @pytest.mark.parametrize("role", ["role-a", "assistant"])
    def test_paths_scoped(self, iso_home, boards, board, role):
        _write_profile(iso_home, role)
        _write_board_yaml(board, {"version": 1, "roles": [role]})
        from hermes_cli.board_state import memory_dir, session_db_path, hindsight_bank, state_root
        from hermes_cli.kanban_db import board_dir
        bd = board_dir(board)
        assert memory_dir(role, board) == bd / "state" / role / "memories"
        assert session_db_path(role, board) == bd / "state" / role / "state.db"
        assert state_root(role, board) == bd / "state" / role
        assert hindsight_bank(role, board) == f"board-{board}-{role}"

    def test_no_board_is_profile_home(self, iso_home):
        _write_profile(iso_home, "role-a")
        from hermes_cli.board_state import memory_dir, session_db_path, state_root
        from hermes_constants import get_hermes_home
        assert state_root("role-a", None) is None
        assert memory_dir("role-a", None) == get_hermes_home() / "memories"
        assert session_db_path("role-a", None) == get_hermes_home() / "state.db"


class TestNegative:
    """beta unreachable from alpha composition."""

    def test_alpha_does_not_see_beta(self, iso_home, boards):
        for role in ("role-a", "assistant"):
            _write_profile(iso_home, role)
        _write_board_yaml("alpha", {"version": 1, "roles": ["role-a"]})
        _write_board_yaml("beta", {"version": 1, "roles": ["role-a"]})
        from hermes_cli.board_state import memory_dir, session_db_path, board_skills_dir
        from hermes_cli.kanban_db import board_dir
        # alpha's memory path is distinct from beta's
        md = memory_dir("role-a", "alpha")
        assert str(board_dir("alpha")) in str(md)
        assert str(board_dir("beta")) not in str(md)
        assert session_db_path("role-a", "alpha") != session_db_path("role-a", "beta")
        # board skills dirs distinct
        assert board_skills_dir("alpha") != board_skills_dir("beta")
        # beta bank not reachable via alpha
        from hermes_cli.board_state import hindsight_bank
        assert hindsight_bank("role-a", "alpha") != hindsight_bank("role-a", "beta")


class TestEnvIsolation:
    def test_env_names_scoped(self, iso_home, boards):
        _write_profile(iso_home, "role-a")
        _write_board_yaml("alpha", {"version": 1})
        _write_board_yaml("beta", {"version": 1})
        from hermes_cli.kanban_db import board_dir
        import hermes_yaml as yaml
        for slug, token in (("alpha", "alpha-token"), ("beta", "beta-token")):
            bd = board_dir(slug)
            (bd / "env").mkdir(exist_ok=True)
            (bd / "env" / "manifest.yaml").write_text(yaml.safe_dump({
                "version": 1, "vars": {"BOT_TOKEN": {"value": token}}, "export": ["BOT_TOKEN"]
            }), encoding="utf-8")
            (bd / "board.yaml").write_text(yaml.safe_dump({
                "version": 1, "env": {"manifest": "./env/manifest.yaml"}
            }), encoding="utf-8")
        from hermes_cli.board_state import board_env_names, compose_env
        assert board_env_names("alpha", "role-a") == ["BOT_TOKEN"]
        assert board_env_names("beta", "role-a") == ["BOT_TOKEN"]
        # composed env carries correct board's value
        assert compose_env("role-a", "alpha")["BOT_TOKEN"] == "alpha-token"
        assert compose_env("role-a", "beta")["BOT_TOKEN"] == "beta-token"
        # alpha composition never leaks beta value
        assert compose_env("role-a", "alpha")["BOT_TOKEN"] != "beta-token"

    def test_no_board_no_env(self, iso_home):
        _write_profile(iso_home, "role-a")
        from hermes_cli.board_state import board_env_names
        assert board_env_names(None, "role-a") == []


class TestSkillsPointer:
    def test_board_skills_added(self, iso_home, boards):
        _write_profile(iso_home, "role-a")
        _write_board_yaml("alpha", {"version": 1, "skills": {"add": ["my-skill"]}})
        from hermes_cli.board_state import effective_skills_dirs, board_skills_dir
        dirs = effective_skills_dirs("role-a", "alpha")
        assert board_skills_dir("alpha") in dirs
        assert board_skills_dir("beta") not in dirs

    def test_pinned_skills_excludes_board(self, iso_home, boards):
        _write_profile(iso_home, "role-a", config={"boards": {"pin": ["skills"]}})
        _write_board_yaml("alpha", {"version": 1, "skills": {"add": ["my-skill"]}})
        from hermes_cli.board_state import effective_skills_dirs, board_skills_dir
        dirs = effective_skills_dirs("role-a", "alpha")
        assert board_skills_dir("alpha") not in dirs
