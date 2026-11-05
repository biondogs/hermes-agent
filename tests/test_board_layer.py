"""Tests for hermes_cli.board_layer — precedence, slots, validation, zero-change."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import hermes_yaml as yaml

from hermes_cli.board_layer import (
    ALLOWED_PINS,
    BoardLayerError,
    EffectiveProfile,
    compose,
    is_layered_board,
    load_board_yaml,
    render_slots,
    validate_board_yaml,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _write_board_yaml(board_slug: str, doc: dict, monkeypatch=None) -> Path:
    """Write board.yaml for board_slug under the current kanban home."""
    from hermes_cli.kanban_db import board_dir

    p = board_dir(board_slug) / "board.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _write_soul_fragment(board_slug: str, content: str) -> Path:
    from hermes_cli.kanban_db import board_dir

    p = board_dir(board_slug) / "SOUL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _write_role_profile(tmp_home: Path, role: str, config: dict | None = None, soul: str | None = None):
    prof = tmp_home / "profiles" / role
    prof.mkdir(parents=True, exist_ok=True)
    if config is not None:
        (prof / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    else:
        (prof / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    if soul is not None:
        (prof / "SOUL.md").write_text(soul, encoding="utf-8")
    else:
        (prof / "SOUL.md").write_text("You are role-a.", encoding="utf-8")
    # identity marker
    return prof


# ── isolated-HOME fixtures ───────────────────────────────────────────────

@pytest.fixture
def iso_home(tmp_path, monkeypatch):
    """Point HERMES_HOME and kanban home at a temp dir."""
    home = tmp_path / "hermes-home"
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))
    # clear memo
    try:
        from hermes_constants import get_default_hermes_root

        import hermes_constants as hc

        hc._default_hermes_root_memo = None  # type: ignore[attr-defined]
    except Exception:
        pass
    return home


@pytest.fixture
def board_alpha(iso_home):
    """Create a board dir for alpha (board.json marker + kanban home scaffolding)."""
    from hermes_cli.kanban_db import board_dir

    d = board_dir("alpha")
    d.mkdir(parents=True, exist_ok=True)
    (d / "board.json").write_text('{"name":"Alpha"}', encoding="utf-8")
    return "alpha"


@pytest.fixture
def board_beta(iso_home):
    from hermes_cli.kanban_db import board_dir

    d = board_dir("beta")
    d.mkdir(parents=True, exist_ok=True)
    (d / "board.json").write_text('{"name":"Beta"}', encoding="utf-8")
    return "beta"


# ── validation ────────────────────────────────────────────────────────────

class TestValidation:
    def test_missing_version(self):
        with pytest.raises(BoardLayerError, match="version"):
            validate_board_yaml({})

    def test_unknown_version(self):
        with pytest.raises(BoardLayerError, match="unknown version"):
            validate_board_yaml({"version": 2})

    def test_unknown_top_level_key(self):
        with pytest.raises(BoardLayerError, match="unknown top-level key"):
            validate_board_yaml({"version": 1, "skils": []})

    def test_x_prefix_allowed(self):
        validate_board_yaml({"version": 1, "x-custom": 123})

    def test_roles_must_be_list(self):
        with pytest.raises(BoardLayerError, match="'roles' must be a list"):
            validate_board_yaml({"version": 1, "roles": "assistant"})

    def test_overrides_unknown_key(self):
        with pytest.raises(BoardLayerError, match="unknown key"):
            validate_board_yaml({"version": 1, "overrides": {"role-a": {"unknown_key": 1}}})

    def test_overrides_x_prefix_allowed(self):
        validate_board_yaml({"version": 1, "overrides": {"role-a": {"x-note": "hi"}}})

    def test_model_without_reason(self):
        with pytest.raises(BoardLayerError, match="requires a sibling 'reason:'"):
            validate_board_yaml({"version": 1, "overrides": {"role-a": {"model": "openrouter/auto"}}})

    def test_model_with_reason_ok(self):
        validate_board_yaml({"version": 1, "overrides": {"role-a": {"model": "openrouter/auto", "reason": "benchmark"}}})

    def test_provider_without_reason(self):
        with pytest.raises(BoardLayerError, match="requires a sibling 'reason:'"):
            validate_board_yaml({"version": 1, "overrides": {"role-a": {"provider": "anthropic"}}})

    def test_replace_without_reason(self):
        with pytest.raises(BoardLayerError, match="requires a sibling 'reason:'"):
            validate_board_yaml({"version": 1, "overrides": {"assistant": {"toolsets": {"replace": ["default", "kanban"]}}}})

    def test_replace_with_reason_ok(self):
        validate_board_yaml({"version": 1, "overrides": {"assistant": {"toolsets": {"replace": ["default", "kanban"]}, "reason": "lock down"}}})

    def test_invalid_profile_name_in_roles(self):
        with pytest.raises(BoardLayerError, match="invalid profile name"):
            validate_board_yaml({"version": 1, "roles": ["-bad"]})

    def test_invalid_profile_name_in_overrides(self):
        with pytest.raises(BoardLayerError, match="invalid profile name"):
            validate_board_yaml({"version": 1, "overrides": {"-bad": {}}})

    def test_path_escape_rejected(self, iso_home, board_alpha):
        from hermes_cli.kanban_db import board_dir

        doc = {"version": 1, "soul": {"fragment": "../../../etc/passwd"}}
        with pytest.raises(BoardLayerError, match="escapes the board home"):
            validate_board_yaml(doc, board_slug=board_alpha, board_dir_path=board_dir(board_alpha))

    def test_skills_replace_only_in_overrides(self):
        with pytest.raises(BoardLayerError, match="'replace' is only allowed in overrides"):
            validate_board_yaml({"version": 1, "skills": {"replace": ["a"]}})

    def test_skills_replace_not_for_skills(self):
        with pytest.raises(BoardLayerError, match="not allowed for skills"):
            validate_board_yaml({"version": 1, "overrides": {"role-a": {"skills": {"replace": ["a"]}, "reason": "x"}}}, board_slug="alpha")

    def test_pins_closed_list(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["notakey"]}}, soul="hi")
        _write_board_yaml(board_alpha, {"version": 1, "memory": {"provider": "hindsight"}})
        with pytest.raises(BoardLayerError, match="unknown pin key"):
            compose("role-a", "alpha")

    def test_star_pin(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["*"]}}, soul="hi")
        _write_board_yaml(board_alpha, {"version": 1, "memory": {"provider": "hindsight"}})
        ep = compose("role-a", "alpha")
        assert "*" in ep.pinned_keys


# ── slots ─────────────────────────────────────────────────────────────

class TestSlots:
    def test_strict_unknown_raises(self):
        with pytest.raises(BoardLayerError, match="unfilled slot"):
            render_slots("hello {{board.hosts}} world", {}, strict=True, board_slug="alpha")

    def test_tolerant_renders_marker(self):
        out = render_slots("hello {{board.hosts}} world", {}, strict=False, board_slug="alpha")
        assert "[UNFILLED SLOT {{board.hosts}}" in out

    def test_other_braces_passthrough(self):
        out = render_slots("hi {{Myshortcode}} there", {}, strict=True)
        assert "{{Myshortcode}}" in out

    def test_unclosed_on_line_passthrough(self):
        out = render_slots("hi {{board.hosts there", {}, strict=True)
        assert "{{board.hosts" in out

    def test_fill(self):
        out = render_slots("hosts: {{board.hosts}}", {"hosts": "node-a: 8xGPU"}, strict=True)
        assert "node-a: 8xGPU" in out
        assert "{{board." not in out

    def test_no_recursive_render(self):
        out = render_slots("x {{board.a}}", {"a": "{{board.b}}"}, strict=True)
        assert out == "x {{board.b}}"

    def test_multiline_block(self):
        out = render_slots("line1\n{{board.rules}}\nline3", {"rules": "- rule one\n- rule two"}, strict=True)
        assert "- rule one" in out
        assert "line1" in out
        assert "line3" in out


# ── precedence / composition ──────────────────────────────────────────

class TestPrecedence:
    def test_no_board_zero_change(self, iso_home):
        _write_role_profile(iso_home, "role-a", soul="You are role-a.")
        ep = compose("role-a", None)
        assert ep.is_layered is False
        assert ep.board is None
        assert ep.soul_text == "You are role-a."
        assert ep.memory_bank is None  # no derivation when unlayered

    def test_unlayered_board_zero_change(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="You are role-a.")
        # board alpha exists but has no board.yaml → not layered
        ep = compose("role-a", "alpha")
        assert ep.is_layered is False
        assert ep.soul_text == "You are role-a."

    def test_board_base_memory(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {"version": 1, "memory": {"provider": "hindsight"}})
        ep = compose("role-a", "alpha")
        assert ep.is_layered is True
        assert ep.memory_provider == "hindsight"
        assert ep.memory_bank == "board-alpha-role-a"  # derived default

    def test_board_explicit_bank(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {"version": 1, "memory": {"bank": "mybank"}})
        ep = compose("role-a", "alpha")
        assert ep.memory_bank == "mybank"

    def test_overrides_win_over_base(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {
            "version": 1,
            "memory": {"provider": "hindsight", "bank": "base-bank"},
            "overrides": {"role-a": {"memory": {"bank": "override-bank"}}},
        })
        ep = compose("role-a", "alpha")
        assert ep.memory_bank == "override-bank"

    def test_pin_blocks_board(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["memory"]}})
        _write_board_yaml(board_alpha, {"version": 1, "memory": {"provider": "hindsight", "bank": "board-bank"}})
        ep = compose("role-a", "alpha")
        assert ep.memory_provider is None
        assert ep.memory_bank is None
        assert ep.provenance.get("memory") == "role:pinned"

    def test_pin_wins_over_overrides(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["model"]}})
        _write_board_yaml(board_alpha, {"version": 1, "overrides": {"role-a": {"model": "openrouter/auto", "reason": "bench"}}})
        ep = compose("role-a", "alpha")
        assert ep.model is None
        assert ep.provenance.get("model") == "role:pinned"

    def test_overrides_model_with_reason(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {"version": 1, "overrides": {"role-a": {"model": "openrouter/auto", "reason": "bench"}}})
        ep = compose("role-a", "alpha")
        assert ep.model == "openrouter/auto"

    def test_skills_delta_union(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"skills": ["skill-a", "skill-b"]})
        _write_board_yaml(board_alpha, {"version": 1, "skills": {"add": ["skill-c"], "remove": ["skill-a"]}})
        ep = compose("role-a", "alpha")
        assert "skill-c" in ep.skills_add
        assert "skill-a" in ep.skills_remove

    def test_skills_delta_union_with_overrides(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"skills": ["skill-a"]})
        _write_board_yaml(board_alpha, {
            "version": 1,
            "skills": {"add": ["skill-b"]},
            "overrides": {"role-a": {"skills": {"add": ["skill-c"]}}},
        })
        ep = compose("role-a", "alpha")
        assert "skill-b" in ep.skills_add
        assert "skill-c" in ep.skills_add

    def test_toolsets_replace_at_overrides(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"toolsets": ["default", "extra"]})
        _write_board_yaml(board_alpha, {
            "version": 1,
            "overrides": {"role-a": {"toolsets": {"replace": ["default", "kanban"]}, "reason": "lock down"}},
        })
        ep = compose("role-a", "alpha")
        assert ep.toolsets_replace == ["default", "kanban"]

    def test_toolsets_pin_blocks_replace(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["toolsets"]}, "toolsets": ["default"]})
        _write_board_yaml(board_alpha, {
            "version": 1,
            "overrides": {"role-a": {"toolsets": {"replace": ["kanban"]}, "reason": "x"}},
        })
        ep = compose("role-a", "alpha")
        assert ep.toolsets_replace is None
        assert ep.provenance.get("toolsets") == "role:pinned"

    def test_soul_append(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="You are role-a.")
        _write_soul_fragment(board_alpha, "Board alpha context.")
        _write_board_yaml(board_alpha, {"version": 1, "soul": {"fragment": "./SOUL.md"}})
        ep = compose("role-a", "alpha")
        assert "You are role-a." in ep.soul_text
        assert "Board alpha context." in ep.soul_text

    def test_soul_pin_no_append(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["soul"]}}, soul="You are role-a.")
        _write_soul_fragment(board_alpha, "Board context.")
        _write_board_yaml(board_alpha, {"version": 1, "soul": {"fragment": "./SOUL.md"}})
        ep = compose("role-a", "alpha")
        assert "Board context." not in (ep.soul_text or "")
        assert ep.soul_text == "You are role-a."

    def test_slot_in_soul_strict(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="Hosts: {{board.hosts}}")
        _write_board_yaml(board_alpha, {"version": 1, "soul": {"slots": {"hosts": "node-a"}}})
        ep = compose("role-a", "alpha", strict_slots=True)
        assert "node-a" in ep.soul_text
        assert "{{board." not in ep.soul_text

    def test_slot_missing_strict_error(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="Hosts: {{board.hosts}}")
        _write_board_yaml(board_alpha, {"version": 1})
        with pytest.raises(BoardLayerError, match="unfilled slot"):
            compose("role-a", "alpha", strict_slots=True)

    def test_slot_missing_tolerant_marker(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="Hosts: {{board.hosts}}")
        _write_board_yaml(board_alpha, {"version": 1})
        ep = compose("role-a", "alpha", strict_slots=False)
        assert "[UNFILLED SLOT" in ep.soul_text

    def test_env_manifest_exposed(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {"version": 1, "env": {"manifest": "./env/manifest.yaml"}})
        ep = compose("role-a", "alpha")
        assert ep.env_manifest == "./env/manifest.yaml"

    def test_env_pin(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"pin": ["env"]}})
        _write_board_yaml(board_alpha, {"version": 1, "env": {"manifest": "./env/manifest.yaml"}})
        ep = compose("role-a", "alpha")
        assert ep.env_manifest is None


# ── boards:all capability ─────────────────────────────────────────────

class TestUnboundSlotStrict:
    def test_slot_bearing_soul_no_board_strict_errors(self, iso_home):
        _write_role_profile(iso_home, "role-a", soul="Hello {{board.hosts}} world")
        with pytest.raises(BoardLayerError, match="unfilled slot"):
            compose("role-a", None, strict_slots=True)

    def test_slot_bearing_soul_no_board_tolerant_ok(self, iso_home):
        _write_role_profile(iso_home, "role-a", soul="Hello {{board.hosts}} world")
        ep = compose("role-a", None, strict_slots=False)
        assert "{{board.hosts}}" in (ep.soul_text or "")

    def test_slot_free_soul_no_board_strict_still_zero_change(self, iso_home):
        soul = "You are role-a.\nWith multiple lines.\n"
        _write_role_profile(iso_home, "role-a", soul=soul)
        ep = compose("role-a", None, strict_slots=True)
        assert ep.soul_text == soul.strip()
        assert ep.is_layered is False


class TestDeltaUnionOrdering:
    def test_base_remove_then_override_add_yields_present(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"toolsets": ["a", "x"]})
        _write_board_yaml(board_alpha, {
            "version": 1,
            "toolsets": {"remove": ["x"]},
            "overrides": {"role-a": {"toolsets": {"add": ["x"]}}},
        })
        from hermes_cli.board_layer import _effective_list
        eff, *_ = _effective_list(["a", "x"], {"remove": ["x"]}, {"add": ["x"]}, pinned=False)
        assert "x" in eff

    def test_base_add_then_override_remove_yields_absent(self):
        from hermes_cli.board_layer import _effective_list
        eff, *_ = _effective_list(["a"], {"add": ["y"]}, {"remove": ["y"]}, pinned=False)
        assert "y" not in eff


class TestCapability:
    def test_no_capability(self, iso_home):
        _write_role_profile(iso_home, "role-a", config={})
        ep = compose("role-a", None)
        assert ep.boards_capability is None

    def test_capability_all(self, iso_home):
        _write_role_profile(iso_home, "role-a", config={"boards": {"capability": "all", "granted_by": "operator", "granted_at": "2026-11-01"}})
        ep = compose("role-a", None)
        assert ep.boards_capability == "all"
        assert ep.boards_capability_granted is True

    def test_capability_all_ungranted(self, iso_home):
        _write_role_profile(iso_home, "role-a", config={"boards": {"capability": "all"}})
        ep = compose("role-a", None)
        assert ep.boards_capability == "all"
        assert ep.boards_capability_granted is False

    def test_capability_survives_layered(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", config={"boards": {"capability": "all", "granted_by": "op"}})
        _write_board_yaml(board_alpha, {"version": 1})
        ep = compose("role-a", "alpha")
        assert ep.boards_capability == "all"


# ── zero-change guarantee ─────────────────────────────────────────────

class TestZeroChange:
    def test_no_board_byte_identical_soul(self, iso_home):
        soul = "You are role-a.\nWith multiple lines.\n"
        _write_role_profile(iso_home, "role-a", soul=soul)
        ep_none = compose("role-a", None)
        # The role SOUL on disk, stripped, is what unbound returns
        assert ep_none.soul_text == soul.strip()
        assert ep_none.is_layered is False
        assert ep_none.provenance == {}

    def test_no_board_byte_identical_config(self, iso_home):
        cfg = {"model": {"provider": "openai", "model": "gpt-4o-mini"}, "toolsets": ["default"]}
        _write_role_profile(iso_home, "role-a", config=cfg, soul="hi")
        ep = compose("role-a", None)
        # No board-derived fields populated
        assert ep.model is None
        assert ep.provider is None
        assert ep.memory_provider is None
        assert ep.memory_bank is None
        assert ep.skills_add == []
        assert ep.toolsets_replace is None


# ── extraneous slot warning ───────────────────────────────────────────

class TestWarnings:
    def test_extraneous_slot_warns(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a", soul="No slots here.")
        _write_board_yaml(board_alpha, {"version": 1, "soul": {"slots": {"unused": "value"}}})
        ep = compose("role-a", "alpha")
        assert any("unused" in w for w in ep.warnings)

    def test_roles_allowlist_warning(self, iso_home, board_alpha):
        _write_role_profile(iso_home, "role-a")
        _write_board_yaml(board_alpha, {"version": 1, "roles": ["assistant"]})
        ep = compose("role-a", "alpha")
        assert any("not in board" in w for w in ep.warnings)
