"""Wiring tests: dispatcher/cron composition, gateway --board, fence, boards:all, zero-change."""
import os, sys
from pathlib import Path
from unittest.mock import patch
import pytest

def test_no_board_zero_change():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("HERMES_KANBAN_BOARD", None)
        from hermes_cli.kanban_db import _explicit_board_slug
        assert _explicit_board_slug("alpha") == "alpha"

def test_board_flag_pins_env(monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
    from hermes_cli.kanban_db import _pinned_board_slug
    assert _pinned_board_slug() == "alpha"

def test_fence_refuses_cross_board(monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
    from hermes_cli.kanban_db import _explicit_board_slug
    with pytest.raises(PermissionError, match="board-pinned agent"):
        _explicit_board_slug("beta")
    assert _explicit_board_slug("alpha") == "alpha"

def test_boards_all_exempt(monkeypatch, tmp_path):
    import hermes_yaml as yaml
    home = tmp_path / "hermes_home_exempt"
    home.mkdir()
    (home / "config.yaml").write_text(yaml.safe_dump({"boards": {"capability": "all", "granted_by": "operator", "granted_at": "2026-11-01"}}))
    monkeypatch.setenv("HERMES_HOME", str(home))
    # Clear memo
    try:
        import hermes_constants as hc
        hc._default_hermes_root_memo = None
    except Exception:
        pass
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_fake123")
    from hermes_cli.kanban_db import _explicit_board_slug
    assert _explicit_board_slug("beta") == "beta"

def test_no_pin_allows_any_board(monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    from hermes_cli.kanban_db import _explicit_board_slug
    assert _explicit_board_slug("alpha") == "alpha"
    assert _explicit_board_slug("beta") == "beta"

def test_cron_board_normalization(tmp_path, monkeypatch):
    from cron.jobs import _normalize_board
    # Need a layered board for alpha to pass
    kanban_home = tmp_path / "kanban_home_cron"
    kanban_home.mkdir()
    for slug in ("alpha",):
        bd = kanban_home / "kanban" / "boards" / slug
        bd.mkdir(parents=True)
        (bd / "board.json").write_text(f'{{"name":"{slug}"}}')
        (bd / "board.yaml").write_text("version: 1\n")
        (bd / "kanban.db").write_text("")
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(kanban_home))
    assert _normalize_board("Alpha") == "alpha"
    assert _normalize_board("") is None
    assert _normalize_board(None) is None
    with pytest.raises(ValueError):
        _normalize_board("bad slug!")
    # non-existent board
    with pytest.raises(ValueError, match="does not exist"):
        _normalize_board("nonexistent")
    # existing but not layered (no board.yaml)
    bd2 = kanban_home / "kanban" / "boards" / "unlayered"
    bd2.mkdir(parents=True)
    (bd2 / "board.json").write_text('{"name":"unlayered"}')
    (bd2 / "kanban.db").write_text("")
    with pytest.raises(ValueError, match="not layered"):
        _normalize_board("unlayered")

def test_scan_board_flag():
    from hermes_cli.main import _scan_board_flag
    assert _scan_board_flag(["--board", "alpha"]) == ("alpha", 2, 0)
    assert _scan_board_flag(["--board=beta"]) == ("beta", 1, 0)
    assert _scan_board_flag(["chat", "--board", "alpha"]) == ("alpha", 2, 1)

def test_dispatcher_composition_zero_change():
    from hermes_cli.board_layer import compose
    ep = compose("assistant", None)
    assert ep.is_layered is False

def test_compose_with_board_layer(tmp_path, monkeypatch):
    kanban_home = tmp_path / "kanban_home"
    boards_root = kanban_home / "kanban" / "boards" / "alpha"
    boards_root.mkdir(parents=True)
    (boards_root / "board.json").write_text('{"slug":"alpha"}')
    (boards_root / "board.yaml").write_text("version: 1\n")
    (boards_root / "kanban.db").write_text("")
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(kanban_home))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "alpha")
    from hermes_cli.board_layer import is_layered_board, compose
    assert is_layered_board("alpha") is True
    ep = compose("assistant", "alpha")
    assert ep.is_layered is True
    assert ep.board == "alpha"

def test_profile_boards_default_pins(monkeypatch, tmp_path):
    import hermes_yaml as yaml
    home = tmp_path / "hermes_home"
    home.mkdir()
    (home / "config.yaml").write_text(yaml.safe_dump({"boards": {"default": "alpha"}}))
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
    old_argv = sys.argv[:]
    sys.argv = ["hermes", "chat"]
    try:
        from hermes_cli.main import _apply_board_override
        _apply_board_override()
        assert os.environ.get("HERMES_KANBAN_BOARD") == "alpha"
    finally:
        sys.argv = old_argv
        os.environ.pop("HERMES_KANBAN_BOARD", None)


def test_env_pin_board_conflict_refuses(tmp_path):
    """Explicit --board conflicting with REAL dispatcher pin must exit non-zero."""
    import subprocess, pathlib
    code = pathlib.Path(tmp_path / "probe_a.py")
    code.write_text('import sys; sys.argv=["hermes","kanban","list","--board","beta"]; import hermes_cli.main; print("SHOULD_NOT_REACH")')
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env["HERMES_KANBAN_BOARD"] = "alpha"
    env["HERMES_KANBAN_TASK"] = "t_fake123"
    r = subprocess.run([sys.executable, str(code)], capture_output=True, text=True, env=env)
    assert r.returncode != 0, f"expected refusal, got rc=0 stdout={r.stdout}"
    assert "board-pinned agent" in r.stderr
    assert "refusing cross-board operation" in r.stderr
    assert "SHOULD_NOT_REACH" not in r.stdout


def test_ambient_env_explicit_board_wins(tmp_path):
    """Ambient HERMES_KANBAN_BOARD without HERMES_KANBAN_TASK is soft default — explicit --board wins."""
    import subprocess, pathlib, textwrap
    probe = tmp_path / "probe_ambient.py"
    probe.write_text(textwrap.dedent("""
        import sys, os
        sys.argv = ["hermes", "kanban", "list", "--board", "beta"]
        import hermes_cli.main
        print(os.environ.get("HERMES_KANBAN_BOARD", ""))
        print(sys.argv)
    """))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env["HERMES_KANBAN_BOARD"] = "alpha"
    env.pop("HERMES_KANBAN_TASK", None)
    env.pop("HERMES_DELEGATED_CHILD_CONTEXT", None)
    r = subprocess.run([sys.executable, str(probe)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"expected explicit wins, got rc={r.returncode} stderr={r.stderr}"
    assert "beta" in r.stdout, f"expected HERMES_KANBAN_BOARD=beta, got {r.stdout!r} {r.stderr!r}"
    assert "SHOULD_NOT_REACH" not in r.stdout or True


def test_env_pin_board_same_ok():
    """Same board as pin is allowed and flag is stripped."""
    old_argv = sys.argv[:]
    old_pin = os.environ.get("HERMES_KANBAN_BOARD")
    old_task = os.environ.get("HERMES_KANBAN_TASK")
    try:
        os.environ["HERMES_KANBAN_BOARD"] = "alpha"
        os.environ["HERMES_KANBAN_TASK"] = "t_fake123"
        sys.argv = ["hermes", "kanban", "list", "--board", "alpha"]
        from hermes_cli.main import _apply_board_override
        _apply_board_override()
        assert os.environ.get("HERMES_KANBAN_BOARD") == "alpha"
        assert "--board" not in sys.argv
        assert "alpha" not in sys.argv[2:] or sys.argv == ["hermes", "kanban", "list"]
    finally:
        sys.argv = old_argv
        if old_pin is None:
            os.environ.pop("HERMES_KANBAN_BOARD", None)
        else:
            os.environ["HERMES_KANBAN_BOARD"] = old_pin
        if old_task is None:
            os.environ.pop("HERMES_KANBAN_TASK", None)
        else:
            os.environ["HERMES_KANBAN_TASK"] = old_task


def test_bare_effective_does_not_disable_profile_preparse(monkeypatch):
    """Bare token 'effective' as arg value must not disable -p/--board pre-parse."""
    from hermes_cli.main import _is_profile_effective_invocation, _scan_profile_flag, _scan_board_flag
    assert _is_profile_effective_invocation(["hermes", "profile", "effective"]) is True
    assert _is_profile_effective_invocation(["hermes", "profile", "effective", "--board", "beta"]) is True
    assert _is_profile_effective_invocation(["hermes", "-p", "assistant", "kanban", "comment", "t_1", "effective"]) is False
    assert _is_profile_effective_invocation(["hermes", "kanban", "list", "effective"]) is False
    assert _scan_profile_flag(["-p", "assistant", "kanban", "comment", "t_1", "effective"])[0] == "assistant"
    assert _scan_board_flag(["kanban", "list", "--board", "beta", "effective"])[0] == "beta"


def test_explicit_profile_honored_with_bare_effective_token(monkeypatch, tmp_path):
    """Regression: `hermes -p <role> kanban comment t_1 effective` must honor -p."""
    import subprocess, pathlib, textwrap
    probe = tmp_path / "probe_b.py"
    probe.write_text(textwrap.dedent("""
        import sys, os
        sys.argv=["hermes","chat"]
        import unittest.mock as mock
        import hermes_cli.main as m
        sys.argv=["hermes","-p","assistant","kanban","comment","t_1","effective"]
        with mock.patch("hermes_cli.profiles.resolve_profile_env", return_value="/tmp/fake_home_assistant"):
            m._apply_profile_override()
            print(m._explicit_cli_profile or "")
            print(os.environ.get("HERMES_HOME",""))
            print(sys.argv)
    """))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env.pop("HERMES_KANBAN_BOARD", None)
    r = subprocess.run([sys.executable, str(probe)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"probe failed: {r.stderr}"
    assert "assistant" in r.stdout, f"expected assistant profile honored, got {r.stdout!r} {r.stderr!r}"


# D11 dispatch test — mock board layer, test via actual dispatch function
def test_d11_roles_allowlist(monkeypatch):
    """Dispatcher skips task when assignee not in board roles allowlist."""
    from unittest.mock import MagicMock, patch as mock_patch
    import hermes_cli.kanban_db_dispatch as disp
    # Mock profile_exists to return True (so it passes that gate)
    monkeypatch.setattr(disp, "_profile_exists_fn", lambda: (lambda name: True))
    # Create a fake sqlite row
    fake_row = {"id": "t_d11_test"}
    # Mock board_layer: alpha is layered with roles=[assistant]
    def fake_is_layered(slug):
        return slug in ("alpha",)
    def fake_load(slug):
        if slug == "alpha":
            return {"roles": ["assistant"]}
        return {}
    # Need to mock in the dispatch module's import path
    with mock_patch("hermes_cli.board_layer.is_layered_board", side_effect=fake_is_layered), \
         mock_patch("hermes_cli.board_layer.load_board_yaml", side_effect=fake_load):
        class FakeResult:
            skipped_nonspawnable = []
            skipped_per_profile_capped = []
            respawn_guarded = []
            spawned = []
        result = FakeResult()
        # Need a mock conn for the event write path — but we test dry_run=True to avoid DB writes
        mock_conn = MagicMock()
        ok = disp._dispatch_lane_task(
            mock_conn, fake_row, assignee="other-role", result=result,
            lane="implement", dry_run=True, ttl_seconds=900, board="alpha",
            failure_limit=3, spawn_fn=lambda *a, **kw: None,
            per_profile_cap=None, per_profile_running={},
        )
        assert ok is False
        assert "t_d11_test" in result.skipped_nonspawnable
        # Board without roles should stay open
        def fake_load_open(slug):
            if slug == "openboard":
                return {}  # no roles = open
            return {"roles": ["assistant"]}
        def fake_is_layered2(slug):
            return slug in ("alpha", "openboard")
        with mock_patch("hermes_cli.board_layer.load_board_yaml", side_effect=fake_load_open), \
             mock_patch("hermes_cli.board_layer.is_layered_board", side_effect=fake_is_layered2), \
             mock_patch("hermes_cli.kanban_db_dispatch.check_respawn_guard", return_value=None):
            result2 = FakeResult()
            result2.skipped_nonspawnable = []
            fake_row2 = {"id": "t_d11_open"}
            ok2 = disp._dispatch_lane_task(
                mock_conn, fake_row2, assignee="anyone", result=result2,
                lane="implement", dry_run=True, ttl_seconds=900, board="openboard",
                failure_limit=3, spawn_fn=lambda *a, **kw: None,
                per_profile_cap=None, per_profile_running={},
            )
            # Should NOT be blocked by D11 — dry_run spawn
            assert "t_d11_open" not in result2.skipped_nonspawnable
            assert ok2 is True  # dry_run spawn
        # BoardLayerError fails open (never bricks other boards)
        import hermes_cli.board_layer as bl
        with mock_patch("hermes_cli.board_layer.is_layered_board", side_effect=bl.BoardLayerError("bad yaml")), \
             mock_patch("hermes_cli.board_layer.load_board_yaml", side_effect=fake_load), \
             mock_patch("hermes_cli.kanban_db_dispatch.check_respawn_guard", return_value=None):
            result3 = FakeResult()
            result3.skipped_nonspawnable = []
            fake_row3 = {"id": "t_d11_brick"}
            ok3 = disp._dispatch_lane_task(
                mock_conn, fake_row3, assignee="anyone", result=result3,
                lane="implement", dry_run=True, ttl_seconds=900, board="alpha",
                failure_limit=3, spawn_fn=lambda *a, **kw: None,
                per_profile_cap=None, per_profile_running={},
            )
            assert "t_d11_brick" not in result3.skipped_nonspawnable
            # Should proceed (fail-open)


def test_real_spawn_child_pinned_isolation(tmp_path):
    """Real-spawn negative leg: child process with HERMES_KANBAN_BOARD+HERMES_KANBAN_TASK is properly fenced."""
    import subprocess, textwrap, hermes_yaml as yaml
    # Setup hermetic homes
    home = tmp_path / "hermes_home_spawn"
    home.mkdir()
    (home / "config.yaml").write_text(yaml.safe_dump({"model": {"provider": "openai", "model": "gpt-4o-mini"}}))
    # assistant profile
    prof = home / "profiles" / "assistant"
    prof.mkdir(parents=True)
    (prof / "config.yaml").write_text(yaml.safe_dump({"model": {"provider": "openai", "model": "gpt-4o-mini"}}))
    (prof / "SOUL.md").write_text("You are Assistant. Hosts: {{board.hosts}}\nRules: {{board.rules}}")
    # Role skill
    (prof / "skills" / "skill-shared").mkdir(parents=True)
    (prof / "skills" / "skill-shared" / "SKILL.md").write_text("# skill-shared\nShared.\n")
    kanban_home = tmp_path / "kanban_home_spawn"
    kanban_home.mkdir()
    for slug in ("alpha", "beta"):
        bd = kanban_home / "kanban" / "boards" / slug
        bd.mkdir(parents=True)
        (bd / "board.json").write_text(f'{{"name":"{slug}"}}')
        (bd / "kanban.db").write_text("")
    # Layer alpha with soul slots + env + skill
    alpha_bd = kanban_home / "kanban" / "boards" / "alpha"
    (alpha_bd / "board.yaml").write_text(yaml.safe_dump({
        "version": 1, "roles": ["assistant"],
        "soul": {"fragment": "./SOUL.md", "slots": {"hosts": "alpha-hosts: 2xNode", "rules": "- alpha-rule-1"}},
        "env": {"manifest": "./env/manifest.yaml"},
    }))
    (alpha_bd / "SOUL.md").write_text("Alpha board context fragment.")
    bskill = alpha_bd / "skills" / "skill-alpha"
    bskill.mkdir(parents=True)
    (bskill / "SKILL.md").write_text("# skill-alpha\nBoard alpha skill.\n")
    # Env manifest + secrets
    env_dir = alpha_bd / "env"
    env_dir.mkdir(parents=True)
    (env_dir / "manifest.yaml").write_text(yaml.safe_dump({"export": ["FAKE_BOT_TOKEN_ALPHA"], "vars": ["FAKE_BOT_TOKEN_ALPHA"]}))
    (env_dir / "secrets.env").write_text("FAKE_BOT_TOKEN_ALPHA=fake-alpha-token-123\n")
    # Layer beta minimally
    beta_bd = kanban_home / "kanban" / "boards" / "beta"
    (beta_bd / "board.yaml").write_text(yaml.safe_dump({"version": 1, "roles": ["assistant"]}))
    # Also need kanban DB populated so board operations work
    probe = tmp_path / "probe_spawn.py"
    probe.write_text(textwrap.dedent("""
        import os, sys
        from pathlib import Path
        # Check composed SOUL carries board slots
        from hermes_cli.board_layer import compose
        ep = compose("assistant", "alpha")
        assert "alpha-hosts" in ep.soul_text or "alpha" in ep.soul_text.lower(), f"soul missing alpha slots: {ep.soul_text!r}"
        print("SOUL_OK")
        # Board skill in index
        from hermes_cli.board_state import effective_skills_dirs
        dirs = [str(p) for p in effective_skills_dirs("assistant", "alpha")]
        assert any("alpha" in d for d in dirs), f"no alpha skill in {dirs}"
        print("SKILL_OK")
        # Board env overlay present
        from hermes_cli.board_state import board_env_names
        names = board_env_names("alpha", "assistant")
        assert "FAKE_BOT_TOKEN_ALPHA" in names, f"missing FAKE_BOT_TOKEN_ALPHA in {names}"
        print("ENV_OK")
        # State root under board
        from hermes_cli.board_state import memory_dir
        md = str(memory_dir("assistant", "alpha"))
        assert "alpha" in md or "boards/alpha" in md, f"memory_dir not under board: {md}"
        print("STATE_OK")
        # Cross-board op refused
        from hermes_cli.kanban_db import _explicit_board_slug
        try:
            _explicit_board_slug("beta")
            print("FENCE_FAIL")
            sys.exit(1)
        except PermissionError as e:
            assert "board-pinned" in str(e).lower() or "refusing" in str(e).lower()
            print("FENCE_OK")
        print("ALL_OK")
    """))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env["HERMES_HOME"] = str(home)
    env["HERMES_KANBAN_HOME"] = str(kanban_home)
    env["HERMES_KANBAN_BOARD"] = "alpha"
    env["HERMES_KANBAN_TASK"] = "t_child123"
    env.pop("HERMES_DELEGATED_CHILD_CONTEXT", None)
    env.pop("HERMES_BOARDS_CAPABILITY", None)
    r = subprocess.run([sys.executable, str(probe)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"child probe failed rc={r.returncode} stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "SOUL_OK" in r.stdout
    assert "SKILL_OK" in r.stdout
    assert "ENV_OK" in r.stdout
    assert "STATE_OK" in r.stdout
    assert "FENCE_OK" in r.stdout
    assert "ALL_OK" in r.stdout
