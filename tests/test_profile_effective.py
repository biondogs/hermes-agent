"""Golden tests for `hermes profile effective` — fixtures alpha/beta x role-a/assistant.

Also: redaction, no-board, validation error exit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import hermes_yaml as yaml

from hermes_cli.board_layer import BoardLayerError, compose


@pytest.fixture
def iso_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_RUNTIME_DIR", str(tmp_path / "runtime"))
    khome = tmp_path / "kanban-home"
    khome.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(khome))
    monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
    monkeypatch.delenv("HERMES_KANBAN_DB", raising=False)
    try:
        import hermes_constants as hc
        hc._default_hermes_root_memo = None  # type: ignore
    except Exception:
        pass
    return home


def _write_board_yaml(board_slug: str, doc: dict):
    from hermes_cli.kanban_db import board_dir
    p = board_dir(board_slug) / "board.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _write_board_soul(board_slug: str, content: str):
    from hermes_cli.kanban_db import board_dir
    p = board_dir(board_slug) / "SOUL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _write_profile(iso_home: Path, role: str, config: dict | None = None, soul: str | None = None):
    prof = iso_home / "profiles" / role
    prof.mkdir(parents=True, exist_ok=True)
    if config is not None:
        (prof / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    else:
        (prof / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    (prof / "SOUL.md").write_text(soul or f"You are {role}.", encoding="utf-8")
    return prof


def _seed_layered_fixture(iso_home: Path) -> None:
    from hermes_cli.kanban_db import board_dir
    for slug, name in (("alpha", "Alpha"), ("beta", "Beta")):
        d = board_dir(slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "board.json").write_text(f'{{"name": {name!r}}}', encoding="utf-8")
    _write_profile(iso_home, "role-a")
    _write_profile(iso_home, "assistant")

    _write_board_yaml("alpha", {
        "version": 1,
        "roles": ["role-a", "assistant"],
        "skills": {"add": ["alpha-skill"]},
        "toolsets": {"add": ["alpha-tools"]},
        "soul": {"fragment": "./SOUL.md", "slots": {"team": "AlphaTeam"}},
        "overrides": {
            "role-a": {"skills": {"add": ["alpha-role-skill"]}, "reason": "test override"},
            "assistant": {"toolsets": {"replace": ["assistant-tools"]}, "reason": "assistant pin"},
        },
        "env": {"manifest": ".env.alpha"},
    })
    _write_board_soul("alpha", "Board Alpha fragment with {{board.team}}.")
    _write_board_yaml("beta", {
        "version": 1,
        "roles": ["role-a"],
        "soul": {"slots": {"team": "BetaTeam"}},
    })
    _write_board_soul("beta", "Beta board.")


def _env_lines(text: str) -> list[str]:
    lines = text.splitlines()
    try:
        i = lines.index("Env:")
    except ValueError:
        return []
    out: list[str] = []
    for ln in lines[i + 1:]:
        if not ln.startswith("  "):
            break
        if ln.strip() == "(no env manifest)" or ln.strip().startswith("(pinned)"):
            continue
        stripped = ln.strip()
        if stripped.startswith("Board:"):
            break
        out.append(ln)
    return out


def test_effective_renderer_text_has_isolation_header(iso_home):
    _seed_layered_fixture(iso_home)
    from hermes_cli.profile_effective import render_text
    ep = compose("role-a", "alpha", strict_slots=False)
    out = render_text(ep, role="role-a", board_arg="alpha")
    assert "Isolation:" in out
    assert "Effective profile: role-a" in out
    assert "SOUL:" in out and "Config:" in out and "Skills:" in out and "Env:" in out


def test_effective_renderer_no_board(iso_home):
    _seed_layered_fixture(iso_home)
    from hermes_cli.profile_effective import render_text, render_json
    ep = compose("role-a", None, strict_slots=False)
    out = render_text(ep, role="role-a", board_arg="none")
    assert "no board" in out.lower() or "role alone" in out.lower()
    j = render_json(ep, role="role-a", board_arg="none")
    assert j["board"] is None
    assert j["is_layered"] is False


def test_effective_renderer_none_string_treated_as_no_board(iso_home):
    _seed_layered_fixture(iso_home)
    from hermes_cli.board_layer import compose as _c
    ep = _c("role-a", None, strict_slots=False)
    assert ep.is_layered is False


def test_effective_json_and_text_never_leak_secret_values(iso_home):
    _seed_layered_fixture(iso_home)
    _write_board_yaml("alpha", {
        "version": 1,
        "roles": ["role-a"],
        "soul": {"fragment": "./SOUL.md"},
        "overrides": {"role-a": {"skills": {"add": ["x"]}, "reason": "ok"}},
        "env": {"manifest": "./env/manifest.yaml"},
    })
    from hermes_cli.kanban_db import board_dir
    md = board_dir("alpha") / "env" / "manifest.yaml"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(yaml.safe_dump({"export": ["SECRET_TOKEN"], "vars": ["SECRET_TOKEN"]}), encoding="utf-8")
    (board_dir("alpha") / "env" / "secrets.env").write_text("SECRET_TOKEN=supersecretvalue123\n", encoding="utf-8")

    from hermes_cli.profile_effective import render_text, render_json
    ep = compose("role-a", "alpha", strict_slots=False)
    text = render_text(ep, role="role-a", board_arg="alpha")
    j = render_json(ep, role="role-a", board_arg="alpha")
    assert "supersecretvalue123" not in text
    assert "supersecretvalue123" not in json.dumps(j)
    env_ls = _env_lines(text)
    assert any(ln.strip().startswith("SECRET_TOKEN ") for ln in env_ls), f"expected SECRET_TOKEN in Env section, got {env_ls}"
    assert not any(ln.strip().startswith("version:") for ln in env_ls), f"garbage YAML leaked: {env_ls}"
    assert not any(ln.strip().startswith("- ") for ln in env_ls), f"garbage YAML list leaked: {env_ls}"
    assert any(e["name"] == "SECRET_TOKEN" for e in j["env"])


def test_effective_env_yaml_not_parsed_as_dotenv(iso_home):
    """Regression for B6: YAML manifest must not be mis-parsed as .env KEY=VALUE lines."""
    _seed_layered_fixture(iso_home)
    _write_board_yaml("alpha", {
        "version": 1,
        "roles": ["role-a"],
        "soul": {"fragment": "./SOUL.md"},
        "env": {"manifest": "./env/manifest.yaml"},
    })
    from hermes_cli.kanban_db import board_dir
    md = board_dir("alpha") / "env" / "manifest.yaml"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(yaml.safe_dump({"version": 1, "vars": ["TELEGRAM_BOT_TOKEN"], "export": ["TELEGRAM_BOT_TOKEN"]}), encoding="utf-8")
    from hermes_cli.profile_effective import render_text, render_json
    ep = compose("role-a", "alpha", strict_slots=False)
    text = render_text(ep, role="role-a", board_arg="alpha")
    j = render_json(ep, role="role-a", board_arg="alpha")
    env_ls = _env_lines(text)
    assert len(env_ls) == 1, f"expected single Env line, got {env_ls}"
    assert env_ls[0].strip().startswith("TELEGRAM_BOT_TOKEN ")
    for bad in ("version:", "vars:", "export:", "- TELEGRAM"):
        assert not any(bad in ln for ln in env_ls), f"garbage {bad!r} leaked in {env_ls}"
    assert j["env"] == [{"name": "TELEGRAM_BOT_TOKEN", "source": j["env"][0]["source"]}]


def test_effective_credential_warning_flagged(iso_home):
    """RFC §7 OQ7: exporting provider-credential names must emit loud warning."""
    _seed_layered_fixture(iso_home)
    _write_board_yaml("alpha", {
        "version": 1,
        "roles": ["role-a"],
        "soul": {"fragment": "./SOUL.md"},
        "env": {"manifest": "./env/manifest.yaml"},
    })
    from hermes_cli.kanban_db import board_dir
    md = board_dir("alpha") / "env" / "manifest.yaml"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(yaml.safe_dump({"export": ["OPENAI_API_KEY", "MY_TOKEN"], "vars": ["OPENAI_API_KEY", "MY_TOKEN"]}), encoding="utf-8")
    from hermes_cli.profile_effective import render_text, render_json
    ep = compose("role-a", "alpha", strict_slots=False)
    text = render_text(ep, role="role-a", board_arg="alpha")
    j = render_json(ep, role="role-a", board_arg="alpha")
    assert "credential" in text.lower() and "OPENAI_API_KEY" in text
    assert any("credential" in w.lower() for w in j["warnings"])
    md.write_text(yaml.safe_dump({"export": ["BOARD_HOST"], "vars": ["BOARD_HOST"]}), encoding="utf-8")
    ep2 = compose("role-a", "alpha", strict_slots=False)
    text2 = render_text(ep2, role="role-a", board_arg="alpha")
    assert "credential" not in text2.lower()


def test_effective_board_validation_error_nonzero_via_compose(iso_home):
    from hermes_cli.kanban_db import board_dir as _bd
    _seed_layered_fixture(iso_home)
    (_bd("alpha") / "board.yaml").write_text("version: 999\n", encoding="utf-8")
    with pytest.raises(BoardLayerError):
        compose("role-a", "alpha", strict_slots=False)

    import types
    args = types.SimpleNamespace(effective_profile="role-a", effective_board="alpha", json=False)
    from hermes_cli.profile_effective import cmd_profile_effective
    with pytest.raises(SystemExit) as ei:
        cmd_profile_effective(args)
    assert ei.value.code == 2


def test_effective_cli_golden_alpha_role_a_text(iso_home, capsys):
    _seed_layered_fixture(iso_home)
    import types
    from hermes_cli.profile_effective import cmd_profile_effective
    args = types.SimpleNamespace(effective_profile="role-a", effective_board="alpha", json=False)
    cmd_profile_effective(args)
    out = capsys.readouterr().out
    assert "[board:alpha" in out or "[board:alpha/SOUL.md]" in out or "alpha-skill" in out.lower() or "+ alpha" in out.lower()
    assert "AlphaTeam" in out


def test_effective_cli_golden_json_shape(iso_home, capsys):
    _seed_layered_fixture(iso_home)
    import types
    from hermes_cli.profile_effective import cmd_profile_effective
    args = types.SimpleNamespace(effective_profile="assistant", effective_board="alpha", json=True)
    cmd_profile_effective(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["role"] == "assistant"
    assert payload["board"] == "alpha"
    assert "isolation" in payload and "soul" in payload and "skills" in payload
    assert payload["toolsets"]["replace"] == ["assistant-tools"]
