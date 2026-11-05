"""Positive legs: effective composes right SOUL/env/skills/posture; dispatcher isolation; cron board."""
from __future__ import annotations
import os
from pathlib import Path
import pytest
import hermes_yaml as yaml

class TestEffectivePositive:
    def _env_lines(self, txt: str) -> list[str]:
        lines = txt.splitlines()
        try:
            i = lines.index("Env:")
        except ValueError:
            return []
        out: list[str] = []
        for ln in lines[i + 1:]:
            if not ln.startswith("  "):
                break
            if ln.strip().startswith("Board:"):
                break
            if ln.strip() in ("(no env manifest)",) or ln.strip().startswith("(pinned)"):
                continue
            out.append(ln)
        return out

    def test_alpha_effective_soul_slots_env_posture(self, assistant_alpha_beta):
        from hermes_cli.board_layer import compose
        from hermes_cli.profile_effective import render_text, render_json
        ep = compose("assistant", "alpha")
        assert ep.is_layered is True
        assert "alpha-hosts: 2xNode" in ep.soul_text
        assert "Alpha board context" in ep.soul_text
        assert "alpha-rule-1" in ep.soul_text
        txt = render_text(ep, role="assistant", board_arg="alpha")
        env_ls = self._env_lines(txt)
        assert any(ln.strip().startswith("FAKE_BOT_TOKEN_ALPHA ") for ln in env_ls), f"FAKE_BOT_TOKEN_ALPHA not in Env section: {env_ls}"
        assert not any("version:" in ln for ln in env_ls), f"garbage leaked: {env_ls}"
        assert "fake-alpha-token" not in txt
        assert "pinned" in txt.lower() or "board: alpha" in txt.lower()
        # JSON env exact
        j = render_json(ep, role="assistant", board_arg="alpha")
        assert [e["name"] for e in j["env"]] == ["FAKE_BOT_TOKEN_ALPHA"]

    def test_beta_effective_soul_slots_env_posture(self, assistant_alpha_beta):
        from hermes_cli.board_layer import compose
        from hermes_cli.profile_effective import render_text, render_json
        ep = compose("assistant", "beta")
        assert ep.is_layered is True
        assert "beta-hosts: 4xNode" in ep.soul_text
        assert "Beta board context" in ep.soul_text
        assert "alpha-hosts" not in ep.soul_text
        txt = render_text(ep, role="assistant", board_arg="beta")
        env_ls = self._env_lines(txt)
        assert any(ln.strip().startswith("FAKE_BOT_TOKEN_BETA ") for ln in env_ls), f"FAKE_BOT_TOKEN_BETA not in Env section: {env_ls}"
        assert not any(ln.strip().startswith("FAKE_BOT_TOKEN_ALPHA ") for ln in env_ls)
        j = render_json(ep, role="assistant", board_arg="beta")
        assert [e["name"] for e in j["env"]] == ["FAKE_BOT_TOKEN_BETA"]

    def test_effective_json_has_right_keys(self, assistant_alpha_beta):
        from hermes_cli.board_layer import compose
        from hermes_cli.profile_effective import render_text
        import json
        ep = compose("assistant", "alpha")
        # json rendering path: ensure no crash via direct field check
        assert ep.board == "alpha"
        assert ep.soul_text is not None
        assert ep.env_manifest == "./env/manifest.yaml"

    def test_skills_index_alpha_vs_beta(self, assistant_alpha_beta):
        from hermes_cli.board_state import effective_skills_dirs
        dirs_alpha = [str(p) for p in effective_skills_dirs("assistant", "alpha")]
        dirs_beta = [str(p) for p in effective_skills_dirs("assistant", "beta")]
        # board skills dir contains the board slug in its path: .../boards/<slug>/skills
        assert any("boards/alpha" in d for d in dirs_alpha)
        assert any("boards/beta" in d for d in dirs_beta)
        assert not any("boards/beta" in d for d in dirs_alpha)
        assert not any("boards/alpha" in d for d in dirs_beta)

class TestDispatcherIsolation:
    def test_memory_writes_do_not_collide(self, assistant_alpha_beta):
        from hermes_cli.board_state import memory_dir, session_db_path, hindsight_bank
        # Simulate dispatcher spawn: write a file under alpha only
        alpha_mem = memory_dir("assistant", "alpha")
        beta_mem = memory_dir("assistant", "beta")
        assert alpha_mem != beta_mem
        alpha_mem.mkdir(parents=True, exist_ok=True)
        beta_mem.mkdir(parents=True, exist_ok=True)
        (alpha_mem / "MEMORY.md").write_text("# alpha memory", encoding="utf-8")
        (beta_mem / "MEMORY.md").write_text("# beta memory", encoding="utf-8")
        assert (alpha_mem / "MEMORY.md").read_text() == "# alpha memory"
        assert (beta_mem / "MEMORY.md").read_text() == "# beta memory"
        # session DBs distinct
        assert session_db_path("assistant", "alpha") != session_db_path("assistant", "beta")
        # banks distinct
        assert hindsight_bank("assistant", "alpha") != hindsight_bank("assistant", "beta")

    def test_compose_env_alpha_vs_beta(self, assistant_alpha_beta):
        from hermes_cli.board_state import compose_env, board_env_names
        assert "FAKE_BOT_TOKEN_ALPHA" in board_env_names("alpha", "assistant")
        assert "FAKE_BOT_TOKEN_BETA" in board_env_names("beta", "assistant")
        env_a = compose_env("assistant", "alpha", {})
        env_b = compose_env("assistant", "beta", {})
        assert env_a.get("FAKE_BOT_TOKEN_ALPHA") == "fake-alpha-token-123"
        assert env_b.get("FAKE_BOT_TOKEN_BETA") == "fake-beta-token-123"
        assert "FAKE_BOT_TOKEN_BETA" not in env_a
        assert "FAKE_BOT_TOKEN_ALPHA" not in env_b

class TestCronBoard:
    def test_cron_declaring_board_beta_composes_beta(self, assistant_alpha_beta):
        from cron.jobs import _normalize_board
        assert _normalize_board("beta") == "beta"
        # Simulate scheduler env injection: HERMES_KANBAN_BOARD=beta → compose beta
        from hermes_cli.board_layer import compose
        ep = compose("assistant", "beta")
        assert ep.board == "beta"
        assert ep.is_layered is True
        assert "beta-hosts" in ep.soul_text

    def test_cron_board_invalid_rejected(self):
        from cron.jobs import _normalize_board
        with pytest.raises(ValueError):
            _normalize_board("bad slug!")
