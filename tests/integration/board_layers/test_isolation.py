"""Negative / isolation legs: fence, unreachable state, boards:all, zero-change."""
import os
import pytest
import hermes_yaml as yaml
from pathlib import Path

class TestFence:
    def test_alpha_pin_refuses_beta(self, assistant_alpha_beta, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
        monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
        from hermes_cli.kanban_db import _explicit_board_slug
        with pytest.raises(PermissionError, match="board-pinned"):
            _explicit_board_slug("beta")
        # alpha itself still allowed
        assert _explicit_board_slug("alpha") == "alpha"

    def test_beta_memory_unreachable_from_alpha_pin(self, assistant_alpha_beta, monkeypatch):
        # Directly verify board_state still resolves correct paths even when pinned,
        # but kanban fence prevents cross-board ops. Memory file check via explicit board.
        from hermes_cli.board_state import memory_dir
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
        monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
        # memory_dir for beta is still computable, but a dispatcher worker would never call it
        beta_mem = memory_dir("assistant", "beta")
        alpha_mem = memory_dir("assistant", "alpha")
        assert beta_mem != alpha_mem
        # Simulate fence: _explicit_board_slug("beta") must raise
        from hermes_cli.kanban_db import _explicit_board_slug
        with pytest.raises(PermissionError):
            _explicit_board_slug("beta")

    def test_beta_skill_not_in_alpha_index(self, assistant_alpha_beta):
        from hermes_cli.board_state import effective_skills_dirs
        dirs = [str(p) for p in effective_skills_dirs("assistant", "alpha")]
        assert not any("boards/beta" in d for d in dirs)
        assert any("boards/alpha" in d for d in dirs)

    def test_beta_env_absent_from_alpha(self, assistant_alpha_beta):
        from hermes_cli.board_state import board_env_names
        assert "FAKE_BOT_TOKEN_BETA" not in board_env_names("alpha", "assistant")
        assert "FAKE_BOT_TOKEN_BETA" in board_env_names("beta", "assistant")

class TestBoardsAll:
    def test_boards_all_can_address_both(self, e2e_home, monkeypatch):
        # Write to root config (what _is_boards_all_exempt reads) AND profile config (what compose reads)
        (e2e_home / "config.yaml").write_text(yaml.safe_dump({
            "boards": {"capability": "all", "granted_by": "operator", "granted_at": "2026-11-01"},
        }), encoding="utf-8")
        prof = e2e_home / "profiles" / "assistant"
        prof.mkdir(parents=True, exist_ok=True)
        (prof / "config.yaml").write_text(yaml.safe_dump({
            "model": {"provider": "openai", "model": "gpt-4o-mini"},
            "boards": {"capability": "all", "granted_by": "operator", "granted_at": "2026-11-01"},
        }), encoding="utf-8")
        (prof / "SOUL.md").write_text("You are Assistant.", encoding="utf-8")
        # boards alpha/beta exist, make them layered minimally
        for slug in ("alpha", "beta"):
            from hermes_cli.kanban_db import board_dir
            (board_dir(slug) / "board.yaml").write_text("version: 1\n", encoding="utf-8")
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
        monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
        from hermes_cli.kanban_db import _explicit_board_slug
        assert _explicit_board_slug("beta") == "beta"
        assert _explicit_board_slug("alpha") == "alpha"
        # also check compose says boards:all
        from hermes_cli.board_layer import compose
        ep = compose("assistant", "alpha")
        assert ep.boards_capability == "all"

    def test_effective_shows_boards_all_posture(self, e2e_home):
        prof = e2e_home / "profiles" / "assistant"
        prof.mkdir(parents=True, exist_ok=True)
        (prof / "config.yaml").write_text(yaml.safe_dump({
            "boards": {"capability": "all", "granted_by": "operator", "granted_at": "2026-11-01"},
        }), encoding="utf-8")
        (prof / "SOUL.md").write_text("You are Assistant.", encoding="utf-8")
        from hermes_cli.kanban_db import board_dir
        for slug in ("alpha", "beta"):
            (board_dir(slug) / "board.yaml").write_text("version: 1\n", encoding="utf-8")
        from hermes_cli.board_layer import compose
        from hermes_cli.profile_effective import render_text, _isolation_posture
        ep = compose("assistant", "alpha")
        posture, _ = _isolation_posture(ep)
        assert "all" in posture.lower()

class TestZeroChange:
    def test_no_board_byte_identical_to_role(self, e2e_home):
        soul = "You are Assistant, plain.\nLine two."
        prof = e2e_home / "profiles" / "assistant"
        prof.mkdir(parents=True, exist_ok=True)
        (prof / "config.yaml").write_text(yaml.safe_dump({"model": {"provider": "openai", "model": "gpt-4o-mini"}}), encoding="utf-8")
        (prof / "SOUL.md").write_text(soul, encoding="utf-8")
        from hermes_cli.board_layer import compose
        ep_none = compose("assistant", None)
        _ep_nowrap = compose("assistant", "none") if False else ep_none  # 'none' is handled by CLI, not compose
        assert ep_none.is_layered is False
        assert ep_none.soul_text == soul.strip()
        assert ep_none.provenance == {}
        assert ep_none.env_manifest is None

    def test_effective_no_board_posture(self, e2e_home):
        prof = e2e_home / "profiles" / "assistant"
        prof.mkdir(parents=True, exist_ok=True)
        (prof / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
        (prof / "SOUL.md").write_text("You are Assistant.", encoding="utf-8")
        from hermes_cli.board_layer import compose
        from hermes_cli.profile_effective import render_text
        ep = compose("assistant", None)
        txt = render_text(ep, role="assistant", board_arg=None)
        assert "no board" in txt.lower() or "role alone" in txt.lower()
        assert "FAKE_BOT_TOKEN" not in txt

    def test_invalid_board_slug_rejected(self, monkeypatch):
        from hermes_cli.kanban_db import _normalize_board_slug
        with pytest.raises(ValueError):
            _normalize_board_slug("bad slug!")
        assert _normalize_board_slug("") is None
        assert _normalize_board_slug(None) is None

    def test_unlayered_board_is_zero_change(self, e2e_home):
        # alpha exists but no board.yaml
        from hermes_cli.board_layer import compose
        prof = e2e_home / "profiles" / "assistant"
        prof.mkdir(parents=True, exist_ok=True)
        (prof / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
        (prof / "SOUL.md").write_text("You are Assistant.", encoding="utf-8")
        ep = compose("assistant", "alpha")
        assert ep.is_layered is False
        assert "You are Assistant." in ep.soul_text
