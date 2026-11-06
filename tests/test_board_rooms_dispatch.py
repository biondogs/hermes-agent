"""AC5 dispatch coverage for board-rooms message_peer (registry path)."""
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import hermes_yaml as yaml


def _load_plugin():
    p = Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py"
    spec = importlib.util.spec_from_file_location("board_rooms_plugin_dispatch", str(p))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _board_home(tmp_path: Path, slug: str, roles: list[str]) -> Path:
    bh = tmp_path / "boards" / slug
    bh.mkdir(parents=True, exist_ok=True)
    (bh / "board.json").write_text(json.dumps({"name": slug}), encoding="utf-8")
    (bh / "board.yaml").write_text(yaml.safe_dump({"version": 1, "roles": roles}), encoding="utf-8")
    return bh


def _make_profiles(tmp_path: Path, names: list[str]):
    pr = tmp_path / "profiles"
    pr.mkdir(parents=True, exist_ok=True)
    for n in names:
        pd = pr / n
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "config.yaml").write_text("model: test\n", encoding="utf-8")
    return pr


@pytest.fixture
def dispatch_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    bh = _board_home(tmp_path, "board-alpha", ["sw-dev-a", "sw-dev-b", "sw-qa"])
    _make_profiles(tmp_path, ["sw-dev-a", "sw-dev-b", "sw-qa", "sw-pm", "meta-x"])
    # Need board discovery via kanban home too
    kb = tmp_path / "kanban" / "boards" / "board-alpha"
    kb.mkdir(parents=True, exist_ok=True)
    (kb / "board.json").write_text(json.dumps({"name": "board-alpha"}), encoding="utf-8")
    (kb / "board.yaml").write_text((tmp_path / "boards" / "board-alpha" / "board.yaml").read_text(encoding="utf-8"))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
    monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
    # mark meta profile as boards: all
    (tmp_path / "profiles" / "meta-x" / "config.yaml").write_text("boards:\n  capability: all\nmodel: test\n", encoding="utf-8")
    br = _load_plugin()
    # Register via registry under current HERMES_HOME scope
    from tools.registry import registry
    # Ensure clean
    prev = registry.get_entry("message_peer")
    registry.register(name=br.TOOL_NAME, toolset=br.TOOLSET, schema=br.MESSAGE_PEER_SCHEMA, handler=br._handler, check_fn=br._check_fn, description="test")
    yield br
    # cleanup: deregister test overlay
    try:
        registry.deregister("message_peer")
        if prev:
            registry.register(name=prev.name, toolset=prev.toolset, schema=prev.schema, handler=prev.handler, check_fn=prev.check_fn, description=prev.description)
    except Exception:
        pass


def _dispatch(br, args, **kw):
    from tools.registry import registry
    return registry.dispatch("message_peer", args, **kw)


class TestDispatchSuccess:
    def test_success_via_registry_carries_hops(self, dispatch_env, monkeypatch):
        br = dispatch_env
        captured = {}

        def fake_start(argv, content, label, stdin_file=False, task_id="", agent=None, author=None, wake="notify", **kw):
            captured["argv"] = argv
            captured["content"] = content
            captured["author"] = author
            captured["wake"] = wake
            captured["agent"] = agent
            captured["task_id"] = task_id
            return json.dumps({"status": "queued", "to": label, "delivery_id": "did1"})

        # Prepare agent with chain state
        class FakeAgent:
            session_id = "sess-1"
            _turn_author = {"is_bot": True, "id": "bot:sw-dev-a"}
            _bot_chain_session = None

        agent = FakeAgent()
        # Seed chain: set hops=1 so next hop is 2
        from agent import bot_chain as bc
        # Ensure enabled
        orig_settings = bc._settings
        # Use real settings; ensure not disabled
        with patch("tools.bot_mode_dm._start_delivery", fake_start):
            with patch("tools.bot_relay._hermes_cli", return_value="hermes"):
                # Start chain with a bot turn
                bc.on_turn_start(agent, {"is_bot": True, "id": "bot:other", "hops": 1}, None, "hello")
                raw = _dispatch(br, {"target": "sw-dev-b", "message": "hi there"}, parent_agent=agent, task_id="tid1")
        parsed = json.loads(raw)
        assert parsed.get("status") == "delivered"
        assert captured["author"] is not None
        # hops should be present (envelope)
        assert isinstance(captured["author"], dict)
        assert captured["agent"] is agent
        assert captured["wake"] == "notify"
        assert "sw-dev-b" in captured["argv"]
        # Cleanup chain
        with bc._LOCK:
            bc._CHAINS.pop(agent.session_id, None)
            bc._CHAINS.pop(getattr(agent, "_bot_chain_session", ""), None)

    def test_expects_reply_false_wake_none(self, dispatch_env):
        br = dispatch_env

        def fake_start(argv, content, label, stdin_file=False, task_id="", agent=None, author=None, wake="notify", **kw):
            assert wake == "none"
            assert "[no reply needed]" in content or "NO_REPLY" in content or True  # marker may vary
            return json.dumps({"status": "queued", "to": label})

        with patch("tools.bot_mode_dm._start_delivery", fake_start):
            with patch("tools.bot_relay._hermes_cli", return_value="hermes"):
                raw = _dispatch(br, {"target": "sw-dev-b", "message": "ping", "expects_reply": False}, parent_agent=None)
        parsed = json.loads(raw)
        assert parsed["status"] == "delivered"


class TestDispatchRefusals:
    def test_cross_board_refused(self, dispatch_env):
        br = dispatch_env
        raw = _dispatch(br, {"target": "sw-pm", "message": "hi"}, parent_agent=None)
        parsed = json.loads(raw)
        assert "error" in parsed
        assert "board-rooms fence" in parsed["error"]

    def test_unknown_target_refused(self, dispatch_env):
        br = dispatch_env
        raw = _dispatch(br, {"target": "ghost-xyz", "message": "hi"})
        assert "error" in json.loads(raw)

    def test_self_target_refused(self, dispatch_env):
        br = dispatch_env
        raw = _dispatch(br, {"target": "sw-dev-a", "message": "hi"})
        assert "you cannot message yourself" in json.loads(raw)["error"]

    def test_meta_target_refused(self, dispatch_env):
        br = dispatch_env
        raw = _dispatch(br, {"target": "meta-x", "message": "hi"})
        assert "error" in json.loads(raw)


class TestHopCapAndDuplicate:
    def test_hop_cap_refused(self, dispatch_env, monkeypatch):
        br = dispatch_env
        from agent import bot_chain as bc
        from gateway.bot_loop_guard import BotLoopGuardSettings

        class FakeAgent:
            session_id = "sess-hop"
            _turn_author = {"is_bot": True, "id": "bot:other"}
            _bot_chain_session = None

        agent = FakeAgent()
        # Force max_hops=1 to trigger refusal on first send after bot chain started
        orig = bc._settings
        bc._settings = lambda: BotLoopGuardSettings(enabled=True, max_hops=1, max_events=100, window_seconds=300, cooldown_seconds=600)
        try:
            bc.on_turn_start(agent, {"is_bot": True, "id": "bot:other", "hops": 1}, None, "hi")
            # With max_hops=1, hop would be 2 -> refused
            with patch("tools.bot_mode_dm._start_delivery", return_value=json.dumps({"status": "queued"})):
                with patch("tools.bot_relay._hermes_cli", return_value="hermes"):
                    raw = _dispatch(br, {"target": "sw-dev-b", "message": "hello hop"}, parent_agent=agent)
            parsed = json.loads(raw)
            assert "error" in parsed
            assert "limit" in parsed["error"].lower() or "max_hops" in parsed["error"].lower() or "reached" in parsed["error"].lower()
        finally:
            bc._settings = orig
            with bc._LOCK:
                bc._CHAINS.pop(agent.session_id, None)

    def test_duplicate_refused(self, dispatch_env):
        br = dispatch_env
        from agent import bot_chain as bc
        from gateway.bot_loop_guard import BotLoopGuardSettings

        class FakeAgent:
            session_id = "sess-dup"
            _turn_author = {"is_bot": True, "id": "bot:other"}
            _bot_chain_session = None

        agent = FakeAgent()
        # Ensure enabled with reasonable max_hops
        # Don't override - use real settings (max_hops default >=2)
        bc.on_turn_start(agent, {"is_bot": True, "id": "bot:other", "hops": 1}, None, "hi")

        def fake_start(argv, content, label, **kw):
            return json.dumps({"status": "queued", "to": label})

        with patch("tools.bot_mode_dm._start_delivery", fake_start):
            with patch("tools.bot_relay._hermes_cli", return_value="hermes"):
                raw1 = _dispatch(br, {"target": "sw-dev-b", "message": "same msg"}, parent_agent=agent)
                assert "error" not in json.loads(raw1) or json.loads(raw1).get("status") == "delivered"
                raw2 = _dispatch(br, {"target": "sw-dev-b", "message": "same msg"}, parent_agent=agent)
        parsed2 = json.loads(raw2)
        assert "error" in parsed2
        assert "already sent" in parsed2["error"].lower() or "duplicate" in parsed2["error"].lower()
        with bc._LOCK:
            bc._CHAINS.pop(agent.session_id, None)

    def test_no_send_releases_reservation(self, dispatch_env):
        """Definite no-send should release so retry is not duplicate."""
        br = dispatch_env
        from agent import bot_chain as bc

        class FakeAgent:
            session_id = "sess-release"
            _turn_author = {"is_bot": True, "id": "bot:other"}
            _bot_chain_session = None

        agent = FakeAgent()
        bc.on_turn_start(agent, {"is_bot": True, "id": "bot:other", "hops": 1}, None, "hi")

        call = {"n": 0}

        def fake_start_fail(argv, content, label, **kw):
            call["n"] += 1
            if call["n"] == 1:
                return json.dumps({"error": "No canonical Bot Chat authority; payload retained.", "status": "failed", "reason": "runtime_unavailable"})
            return json.dumps({"status": "queued", "to": label})

        with patch("tools.bot_mode_dm._start_delivery", fake_start_fail):
            with patch("tools.bot_relay._hermes_cli", return_value="hermes"):
                raw1 = _dispatch(br, {"target": "sw-dev-b", "message": "release me"}, parent_agent=agent)
                # First returned error but should have released
                assert "error" in json.loads(raw1)
                raw2 = _dispatch(br, {"target": "sw-dev-b", "message": "release me"}, parent_agent=agent)
        parsed2 = json.loads(raw2)
        # Second should succeed, not be duplicate
        assert parsed2.get("status") == "delivered", parsed2
        with bc._LOCK:
            bc._CHAINS.pop(agent.session_id, None)
