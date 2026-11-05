"""Board-layers e2e fixture: assistant × {alpha,beta} with SOUL slots, memory, env, skills.

Reusable helpers for the 9 acceptance legs in the integration report.
"""
from __future__ import annotations
from pathlib import Path
import pytest
import hermes_yaml as yaml

ASSISTANT_SOUL = "You are Assistant, the team coordinator. Board hosts: {{board.hosts}}\nRules: {{board.rules}}"
ALPHA_SOUL = "Alpha board context: manages the Alpha fleet."
BETA_SOUL = "Beta board context: manages the Beta fleet."

def _write_profile(home: Path, role: str, soul: str, config: dict | None = None):
    prof = home / "profiles" / role
    prof.mkdir(parents=True, exist_ok=True)
    cfg = config or {"model": {"provider": "openai", "model": "gpt-4o-mini"}}
    (prof / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (prof / "SOUL.md").write_text(soul, encoding="utf-8")
    return prof

def _write_board(board_slug: str, doc: dict, soul_fragment: str | None = None, env_manifest: str | None = None):
    from hermes_cli.kanban_db import board_dir
    d = board_dir(board_slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "board.json").write_text(f'{{"name":"{board_slug}"}}', encoding="utf-8")
    p = d / "board.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    if soul_fragment:
        (d / "SOUL.md").write_text(soul_fragment, encoding="utf-8")
    # board skill
    bskill = d / "skills" / f"skill-{board_slug}"
    bskill.mkdir(parents=True, exist_ok=True)
    (bskill / "SKILL.md").write_text(f"# skill-{board_slug}\nBoard {board_slug} skill.\n", encoding="utf-8")
    if env_manifest:
        # env_manifest like "./env/manifest.yaml" -> write manifest + secrets
        env_dir = d / "env"
        env_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = d / env_manifest.lstrip("./")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        var_name = f"FAKE_BOT_TOKEN_{board_slug.upper()}"
        # manifest lists exported var names
        manifest_path.write_text(yaml.safe_dump({"export": [var_name], "vars": [var_name]}), encoding="utf-8")
        (env_dir / "secrets.env").write_text(f"{var_name}=fake-{board_slug}-token-123\n", encoding="utf-8")

@pytest.fixture
def e2e_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))
    try:
        import hermes_constants as hc
        hc._default_hermes_root_memo = None
    except Exception:
        pass
    # also isolate kanban home under tmp
    kanban_home = tmp_path / "kanban-home"
    kanban_home.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(kanban_home))
    for slug in ("alpha", "beta"):
        from hermes_cli.kanban_db import board_dir
        bd = board_dir(slug)
        bd.mkdir(parents=True, exist_ok=True)
        (bd / "board.json").write_text(f'{{"name":"{slug}"}}', encoding="utf-8")
        # ensure a kanban.db exists so kanban ops work
        (bd / "kanban.db").write_text("", encoding="utf-8")
    return home

@pytest.fixture
def assistant_alpha_beta(e2e_home):
    """Seed assistant + alpha/beta layered boards per acceptance story."""
    # role skill (shared)
    role_skill = e2e_home / "profiles" / "assistant" / "skills" / "skill-shared"
    role_skill.mkdir(parents=True, exist_ok=True)
    # assistant profile with SOUL slots
    _write_profile(e2e_home, "assistant", ASSISTANT_SOUL)

    # Alpha board: SOUL slots, env, skill
    _write_board("alpha", {
        "version": 1,
        "roles": ["assistant"],
        "soul": {"fragment": "./SOUL.md", "slots": {"hosts": "alpha-hosts: 2xNode", "rules": "- alpha-rule-1"}},
        "env": {"manifest": "./env/manifest.yaml"},
    }, soul_fragment=ALPHA_SOUL, env_manifest="./env/manifest.yaml")

    _write_board("beta", {
        "version": 1,
        "roles": ["assistant"],
        "soul": {"fragment": "./SOUL.md", "slots": {"hosts": "beta-hosts: 4xNode", "rules": "- beta-rule-1"}},
        "env": {"manifest": "./env/manifest.yaml"},
    }, soul_fragment=BETA_SOUL, env_manifest="./env/manifest.yaml")

    # shared skill on role
    (e2e_home / "profiles" / "assistant" / "skills" / "skill-shared").mkdir(parents=True, exist_ok=True)
    (e2e_home / "profiles" / "assistant" / "skills" / "skill-shared" / "SKILL.md").write_text(
        "# skill-shared\nShared assistant skill.\n", encoding="utf-8")

    return e2e_home
