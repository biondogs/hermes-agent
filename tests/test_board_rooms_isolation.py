"""Isolation battery for board-rooms (BR-2) — pytest + live gateway-in-container checks.

Covers DESIGN §6 required proofs + G1/G2 guards on TWO fixture boards (alpha/beta disjoint).

Run: pytest tests/test_board_rooms_isolation.py -v
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
import hermes_yaml as yaml


def _load_board_rooms_plugin():
    """Load plugins/board-rooms/__init__.py directly (dash in dir breaks package import)."""
    p = Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py"
    spec = importlib.util.spec_from_file_location("board_rooms_plugin", str(p))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["board_rooms_plugin"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── helpers ──────────────────────────────────────────────────────────────

def _board_home(tmp_path: Path, slug: str, roles: list[str]) -> Path:
    bh = tmp_path / "boards" / slug
    bh.mkdir(parents=True, exist_ok=True)
    (bh / "board.json").write_text(json.dumps({"name": slug}), encoding="utf-8")
    (bh / "board.yaml").write_text(yaml.safe_dump({"version": 1, "roles": roles}), encoding="utf-8")
    return bh


def _write_rooms(bh: Path, doc: dict) -> Path:
    p = bh / "board-rooms.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _make_profiles(tmp_path: Path, names: list[str], boards_all: list[str] | None = None) -> Path:
    profiles_root = tmp_path / "profiles"
    profiles_root.mkdir(parents=True, exist_ok=True)
    for name in names:
        pd = profiles_root / name
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "config.yaml").write_text("model: test\n", encoding="utf-8")
        if boards_all and name in boards_all:
            (pd / "config.yaml").write_text("boards:\n  capability: all\nmodel: test\n", encoding="utf-8")
    return profiles_root


ALPHA_ROLES = ["sw-dev-a", "sw-dev-b", "sw-qa", "swco-butler"]
BETA_ROLES = ["sw-pm", "sw-architect", "sw-reviewer"]


@pytest.fixture
def two_boards(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    bh_alpha = _board_home(tmp_path, "board-alpha", ALPHA_ROLES)
    bh_beta = _board_home(tmp_path, "board-beta", BETA_ROLES)
    all_roles = ALPHA_ROLES + BETA_ROLES + ["meta-observer"]
    _make_profiles(tmp_path, all_roles, boards_all=["meta-observer"])
    _write_rooms(bh_alpha, {
        "version": 1,
        "rooms": [{
            "name": "alpha floor",
            "members": ["sw-dev-a", "sw-dev-b"],
            "lead": "sw-dev-a",
            "routing": "assigned",
            "purpose": "Coordination only. Decisions land on cards. No cross-board talk.",
        }],
    })
    _write_rooms(bh_beta, {
        "version": 1,
        "rooms": [{
            "name": "beta floor",
            "members": ["sw-pm", "sw-architect"],
            "lead": "sw-pm",
            "routing": "assigned",
            "purpose": "Coordination only. Decisions land on cards. No cross-board talk.",
        }],
    })
    kanban_boards = tmp_path / "kanban" / "boards"
    kanban_boards.mkdir(parents=True, exist_ok=True)
    for slug in ("board-alpha", "board-beta"):
        bd = kanban_boards / slug
        bd.mkdir(parents=True, exist_ok=True)
        (bd / "board.json").write_text(json.dumps({"name": slug}), encoding="utf-8")
        src = tmp_path / "boards" / slug / "board.yaml"
        dst = bd / "board.yaml"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        src2 = tmp_path / "boards" / slug / "board-rooms.yaml"
        dst2 = bd / "board-rooms.yaml"
        dst2.write_text(src2.read_text(encoding="utf-8"), encoding="utf-8")
    return {"alpha": bh_alpha, "beta": bh_beta, "tmp": tmp_path}


# ── Tests: message_peer roster ─────────────────────────────────────────

class TestMessagePeerRoster:
    def test_alpha_agent_sees_alpha_peers(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        roster = br._board_roster("board-alpha")
        assert "sw-dev-a" in roster
        assert "sw-dev-b" in roster
        assert "sw-pm" not in roster
        assert "sw-architect" not in roster
        assert "meta-observer" not in roster
        peers = br._peer_roster_for_board("board-alpha", me="sw-dev-a")
        assert "sw-dev-b" in peers
        assert "sw-dev-a" not in peers

    def test_alpha_agent_refused_for_beta_targets(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        for target in BETA_ROLES:
            result = br._handler(target=target, message="hello")
            parsed = json.loads(result)
            assert "error" in parsed, f"expected refusal for cross-board target {target!r}, got {parsed}"
            assert "fence" in parsed["error"].lower() or "REFUSED" in parsed["error"]

    def test_unknown_target_refused(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        result = br._handler(target="nonexistent-profile", message="hello")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "fence" in parsed["error"].lower() or "REFUSED" in parsed["error"]

    def test_meta_profile_never_in_roster(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        br = _load_board_rooms_plugin()
        roster = br._board_roster("board-alpha")
        assert "meta-observer" not in roster
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        result = br._handler(target="meta-observer", message="hello")
        parsed = json.loads(result)
        assert "error" in parsed

    def test_meta_profile_never_in_beta_roster(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-beta")
        br = _load_board_rooms_plugin()
        roster = br._board_roster("board-beta")
        assert "meta-observer" not in roster


class TestCheckFn:
    def test_unbound_never_sees_tool(self, two_boards, monkeypatch):
        monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
        monkeypatch.delenv("HERMES_PROFILE", raising=False)
        br = _load_board_rooms_plugin()
        assert br._check_fn() is False

    def test_pinned_with_peers_sees_tool(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        assert br._check_fn() is True

    def test_pinned_no_peers_no_tool(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        bh = _board_home(tmp_path, "solo-board", ["solo-profile"])
        kanban_boards = tmp_path / "kanban" / "boards" / "solo-board"
        kanban_boards.mkdir(parents=True, exist_ok=True)
        (kanban_boards / "board.json").write_text(json.dumps({"name": "solo-board"}), encoding="utf-8")
        (kanban_boards / "board.yaml").write_text((tmp_path / "boards" / "solo-board" / "board.yaml").read_text(), encoding="utf-8")
        _make_profiles(tmp_path, ["solo-profile"])
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "solo-board")
        monkeypatch.setenv("HERMES_PROFILE", "solo-profile")
        br = _load_board_rooms_plugin()
        assert br._check_fn() is False


class TestMessageAgentAbsent:
    def test_message_agent_not_registered(self, two_boards):
        """Board-rooms plugin registers message_peer, NOT message_agent (BR-D1) — runtime tool-surface scan."""
        br = _load_board_rooms_plugin()
        assert br.TOOL_NAME == "message_peer"
        assert br.TOOLSET == "board_rooms"
        assert br.TOOL_NAME != "message_agent"
        # Runtime scan: plugin must never register message_agent via ctx
        calls = []

        class FakeCtx:
            def register_tool(self, name, toolset, schema, handler, check_fn=None, **kw):
                calls.append(name)

        br.register(FakeCtx())
        assert "message_agent" not in calls, f"plugin registered message_agent via runtime ctx: {calls}"
        assert calls == ["message_peer"]

    def test_no_hermes_bots_marker(self):
        text = (Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py").read_text()
        assert "hermes-bots" not in text
        assert '"Bot Chat"' not in text and "'Bot Chat'" not in text

    def test_tool_surface_scan_no_message_agent(self):
        """Runtime tool-surface scan: no registered tool is message_agent."""
        br = _load_board_rooms_plugin()
        registered = {}

        class ScanCtx:
            def register_tool(self, name, toolset, schema, handler, check_fn=None, **kw):
                registered[name] = toolset

        br.register(ScanCtx())
        assert "message_agent" not in registered
        # Also verify plugin file text never mentions registering it
        text = (Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py").read_text()
        assert 'register_tool(name="message_agent"' not in text
        assert "register_tool(name='message_agent'" not in text


class TestSeatingFence:
    def _fake_authority(self, profile_name, tmp_path):
        # Build a fake authority whose profile_id resolves to profile_name
        home = tmp_path / "profiles" / profile_name
        # Ensure profile dir exists for served_profile_name resolution
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.yaml").write_text("model: test\n", encoding="utf-8")

        class FakeAuth:
            profile_id = str(home)

        return FakeAuth()

    def _fake_actor(self, profile_name):
        class FakeActor:
            profile_id = profile_name

        return FakeActor()

    def test_cross_board_member_refused(self, two_boards, monkeypatch):
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        tmp = two_boards["tmp"]
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        members = [
            {"member_id": "m1", "profile": "sw-dev-a", "handle": "sw-dev-a", "target": {"kind": "local", "profile": "sw-dev-a"}},
            {"member_id": "m2", "profile": "sw-pm", "handle": "sw-pm", "target": {"kind": "local", "profile": "sw-pm"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, auth, actor, {})
        assert exc_info.value.reason == "board_fence"
        assert "sw-pm" in str(exc_info.value.detail)

    def test_same_board_members_allowed(self, two_boards, monkeypatch):
        from gateway.session_group_controls import _board_rooms_seating_fence

        tmp = two_boards["tmp"]
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        members = [
            {"member_id": "m1", "profile": "sw-dev-a", "handle": "sw-dev-a", "target": {"kind": "local"}},
            {"member_id": "m2", "profile": "sw-dev-b", "handle": "sw-dev-b", "target": {"kind": "local"}},
        ]
        _board_rooms_seating_fence(members, auth, actor, {})

    def test_vanilla_actor_no_fence(self, two_boards, monkeypatch):
        """Actor in 0 boards, no explicit board param → vanilla, no fence (scoped engagement)."""
        from gateway.session_group_controls import _board_rooms_seating_fence

        class FakeAuth:
            profile_id = "/tmp/nonexistent-profile-home"

        class FakeActor:
            profile_id = "ghost-profile-not-in-any-board"

        members = [
            {"member_id": "m1", "profile": "sw-pm", "handle": "sw-pm", "target": {"kind": "local"}},
        ]
        # Must NOT raise — vanilla actor keeps upstream behavior
        _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {})

    def test_underivable_with_explicit_board_refused(self, two_boards, monkeypatch):
        """Actor underivable + explicit board param → refused fail-closed (no anonymous pin)."""
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        class FakeAuth:
            profile_id = "/tmp/nonexistent-profile-home"

        class FakeActor:
            profile_id = "ghost-profile-not-in-any-board"

        members = [
            {"member_id": "m1", "profile": "sw-pm", "handle": "sw-pm", "target": {"kind": "local"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {"board": "board-alpha"})
        assert exc_info.value.reason == "board_fence"

    def test_multi_board_without_explicit_refused(self, two_boards, monkeypatch):
        """Actor in multiple boards without explicit board param → refused (ambiguous)."""
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        tmp = two_boards["tmp"]
        # Create a board where the same profile is in two boards
        from hermes_cli.kanban_db_boards import list_boards  # noqa: F401
        # Make a new board that also contains sw-dev-a (who is already in board-alpha)
        bh_extra = _board_home(tmp, "board-extra", ["sw-dev-a", "sw-pm"])
        kanban_boards = tmp / "kanban" / "boards" / "board-extra"
        kanban_boards.mkdir(parents=True, exist_ok=True)
        (kanban_boards / "board.json").write_text(json.dumps({"name": "board-extra"}), encoding="utf-8")
        (kanban_boards / "board.yaml").write_text((tmp / "boards" / "board-extra" / "board.yaml").read_text(), encoding="utf-8")
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        members = [
            {"member_id": "m1", "profile": "sw-dev-a", "handle": "sw-dev-a", "target": {"kind": "local"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, auth, actor, {})
        assert exc_info.value.reason == "board_fence"
        assert "multiple boards" in str(exc_info.value.detail).lower() or "explicit" in str(exc_info.value.detail).lower()

    def test_explicit_board_param_allows_cross_when_creator_validated(self, two_boards, monkeypatch):
        """Dispatch-level: actor board derivable via explicit board param → cross-board member refused."""
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        tmp = two_boards["tmp"]
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        members = [
            {"member_id": "m1", "profile": "sw-pm", "handle": "sw-pm", "target": {"kind": "local"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, auth, actor, {"board": "board-alpha"})
        assert exc_info.value.reason == "board_fence"

    def test_dispatch_level_seating_via_fence(self, two_boards, monkeypatch):
        """Dispatch-level groups.create simulation: derivable actor board → cross-board refused."""
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        tmp = two_boards["tmp"]
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        # This simulates what dispatch_group_control would do on groups.create
        members = [
            {"member_id": "m1", "profile": "sw-dev-b", "handle": "sw-dev-b", "target": {"kind": "local"}},
            {"member_id": "m2", "profile": "sw-pm", "handle": "sw-pm", "target": {"kind": "local"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, auth, actor, {})
        assert exc_info.value.reason == "board_fence"
        assert "fence" in str(exc_info.value.detail).lower()

    def test_meta_profile_never_seatable(self, two_boards, monkeypatch):
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError

        tmp = two_boards["tmp"]
        auth = self._fake_authority("sw-dev-a", tmp)
        actor = self._fake_actor("sw-dev-a")
        members = [
            {"member_id": "m1", "profile": "meta-observer", "handle": "meta-observer", "target": {"kind": "local"}},
        ]
        with pytest.raises(RuntimeStoreError) as exc_info:
            _board_rooms_seating_fence(members, auth, actor, {})
        assert exc_info.value.reason == "board_fence"


class TestPluginRegistration:
    def test_plugin_registers_one_tool(self):
        calls = []

        class FakeCtx:
            def register_tool(self, name, toolset, schema, handler, check_fn=None, **kw):
                assert kw.get("override") is not True
                calls.append((name, toolset))

        br = _load_board_rooms_plugin()
        br.register(FakeCtx())
        assert len(calls) == 1
        assert calls[0] == ("message_peer", "board_rooms")

    def test_no_override(self):
        text = (Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py").read_text()
        assert "override=True" not in text


class TestDispatchSeatingFence:
    """Dispatch-level groups.create seating fence — exercises _group() dispatch path (item 2).

    These tests fail when the fence call is removed from the create path.
    """

    def _fake_authority_for_group(self, profile_name, tmp_path, db_path):
        from types import SimpleNamespace

        class FakeDB:
            def __init__(self, p):
                self.db_path = str(p)

        home = tmp_path / "profiles" / profile_name
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.yaml").write_text("model: test\n", encoding="utf-8")
        return SimpleNamespace(profile_id=str(home), db=FakeDB(db_path), hosted_room_service=None, authority=SimpleNamespace())

    def _fake_actor(self, profile_name):
        class FakeActor:
            profile_id = profile_name
            capabilities = {"session:control"}

        return FakeActor()

    def test_dispatch_refuses_cross_board_member(self, two_boards, tmp_path, monkeypatch):
        from gateway.session_group_controls import _group
        from hermes_state_runtime import RuntimeStoreError

        # Need a real db file for _group path
        real_db = tmp_path / "real.db"
        real_db.write_text("")
        # Create temp HERMES_HOME for board resolution already set by two_boards
        # two_boards already set HERMES_HOME to its tmp; we need to keep that
        # Use two_boards tmp as base
        base_tmp = two_boards["tmp"]
        # Use a db_path under the fake authority's home resolution check will pass?
        # _group resolves db_path via authority.db.db_path and checks parent == home
        # So we need authority.profile_id to be parent of db_path
        from pathlib import Path as _P
        import tempfile, os as _os

        # Simpler: test via _board_rooms_seating_fence wiring check + _group integration
        # Create a minimal authority where db_path parent check passes
        home = base_tmp / "profiles" / "sw-dev-a"
        db_file = home / "state.db"
        db_file.touch()
        from types import SimpleNamespace

        class FakeDB2:
            db_path = str(db_file)

        auth = SimpleNamespace(profile_id=str(home), db=FakeDB2(), hosted_room_service=None)
        actor = self._fake_actor("sw-dev-a")
        # Also need member_roster to not block — we patch it
        from unittest.mock import patch as _patch

        # This call goes through _board_rooms_seating_fence inside _group.create()
        # We patch member_roster/refuse_unseatable/validate_roster to isolate fence
        with _patch("gateway.session_hosted_members.member_roster", return_value=([], set())), \
             _patch("gateway.session_hosted_members.refuse_unseatable"), \
             _patch("gateway.hosted_room_discussion.validate_roster", side_effect=RuntimeError("should not reach")):
            # Use a direct _group call that will hit fence before member_roster
            # If fence removed, it would reach validate_roster and raise RuntimeError
            try:
                _group(auth, actor, "groups.create", {
                    "room_id": "test-room",
                    "name": "Test",
                    "members": [
                        {"member_id": "m1", "profile": "sw-dev-a", "handle": "a", "target": {"kind": "local", "profile": "sw-dev-a"}},
                        {"member_id": "m2", "profile": "sw-pm", "handle": "b", "target": {"kind": "local", "profile": "sw-pm"}},
                    ],
                    "board": "board-alpha",
                })
            except RuntimeStoreError as exc:
                assert exc.reason == "board_fence", f"expected board_fence, got {exc.reason}: {exc.detail}"
                assert "sw-pm" in str(exc.detail)
                return
            except RuntimeError as exc:
                if "should not reach" in str(exc):
                    pytest.fail("fence did not engage — reached downstream validation (fence call missing)")
                raise
            pytest.fail("expected board_fence refusal, got success")

    def test_dispatch_vanilla_passthrough(self, two_boards, tmp_path):
        """Vanilla actor (0 boards) through dispatch → fence not engaged, reaches downstream."""
        from gateway.session_group_controls import _group
        from hermes_state_runtime import RuntimeStoreError
        from unittest.mock import patch as _patch

        base_tmp = two_boards["tmp"]
        home = base_tmp / "profiles" / "ghost-v"
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.yaml").write_text("model: test\n", encoding="utf-8")
        db_file = home / "state.db"
        db_file.touch()
        from types import SimpleNamespace

        class FakeDB2:
            db_path = str(db_file)

        auth = SimpleNamespace(profile_id=str(home), db=FakeDB2(), hosted_room_service=None)

        class FakeActor2:
            profile_id = "ghost-v-not-in-any-board"
            capabilities = {"session:control"}

        actor = FakeActor2()
        # Fence should NOT engage for vanilla → downstream validation reached
        with _patch("gateway.session_hosted_members.member_roster", return_value=([], set())), \
             _patch("gateway.session_hosted_members.refuse_unseatable"), \
             _patch("gateway.hosted_room_discussion.validate_roster", side_effect=RuntimeError("downstream reached")):
            with pytest.raises(RuntimeError, match="downstream reached"):
                _group(auth, actor, "groups.create", {
                    "room_id": "r2", "name": "R2",
                    "members": [{"member_id": "m1", "profile": "any", "handle": "a", "target": {"kind": "local"}}],
                })


class TestBringupScript:
    def test_dry_run(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(two_boards["tmp"]))
        # Simulate HERMES_HOME for kanban discovery
        # Use direct function after patching list_boards behavior
        spec = importlib.util.spec_from_file_location(
            "board_rooms_bringup_test",
            str(Path(__file__).resolve().parent.parent / "scripts" / "board_rooms_bringup.py"),
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results = mod._bringup_via_direct("board-alpha", dry_run=True)
        assert len(results) == 1
        assert results[0].get("dry_run") is True

    def test_bringup_script_exists(self):
        p = Path(__file__).resolve().parent.parent / "scripts" / "board_rooms_bringup.py"
        assert p.is_file()
        text = p.read_text()
        assert "groups.create" in text
        assert "128" in text
        assert "board-rooms.yaml" in text


class TestNoLoopSoak:
    def test_bot_chain_hop_cap_is_bounded(self):
        from agent.bot_chain import _settings

        s = _settings()
        # Real bound check, not tautology
        assert s.max_hops >= 1
        assert s.max_hops <= 10
        # If enabled, hop accounting must be active
        if s.enabled:
            assert s.max_hops >= 2

    def test_ping_pong_no_loop_soak(self):
        """Ping-pong soak driving real BotLoopGuard.chain_admit -- hop cap enforced."""
        from gateway.bot_loop_guard import BotLoopGuard, BotLoopGuardSettings
        guard = BotLoopGuard()
        guard._settings = lambda: BotLoopGuardSettings(enabled=True, max_hops=3, max_events=100, window_seconds=300, cooldown_seconds=600)
        conv = 'test-conv-pingpong'
        for i in range(3):
            ok, reason = guard.chain_admit(conv, f"bot-{i}", f"msg {i}", is_bot=True)
            assert ok, f"hop {i} should be admitted, got {reason}"
            guard.note_reply(conv, f"bot-{i}")
        ok, reason = guard.chain_admit(conv, 'bot-3', 'msg 3', is_bot=True)
        assert not ok and reason == 'max_hops', f"expected max_hops refusal, got {ok}/{reason}"
        guard.chain_admit(conv, 'human', 'human msg', is_bot=False)
        ok2, _ = guard.chain_admit(conv, 'bot-x', 'after human', is_bot=True)
        assert ok2, 'human should reset chain'
        guard2 = BotLoopGuard()
        guard2._settings = lambda: BotLoopGuardSettings(enabled=True, max_hops=999, max_events=100, window_seconds=300, cooldown_seconds=600)
        for i in range(10):
            ok, _ = guard2.chain_admit(conv + '-huge', f"bot-{i}", f"msg {i}", is_bot=True)
            assert ok, f"huge cap should admit hop {i}"
            guard2.note_reply(conv + '-huge', f"bot-{i}")
        from agent.bot_chain import _settings
        assert _settings().max_hops <= 10

    def test_room_round_caps_exist(self):
        try:
            from gateway.hosted_room_discussion import MAX_DISCUSSION_MEMBERS, MIN_DISCUSSION_MEMBERS

            assert MIN_DISCUSSION_MEMBERS == 2
            assert MAX_DISCUSSION_MEMBERS == 6
        except ImportError:
            pass
        from gateway.hosted_room_execution_policy import MAX_POLICY_ITERATIONS

        assert MAX_POLICY_ITERATIONS > 0

    def test_gateway_defaults_govern_member_turns(self):
        """Gateway defaults (approval manual, MAX_POLICY_ITERATIONS cap) govern member turns (C3)."""
        from gateway.hosted_room_execution_policy import MAX_POLICY_ITERATIONS, execution_policy_mapping

        assert MAX_POLICY_ITERATIONS > 0
        # Verify via explicit config branch (no live profile needed)
        policy = execution_policy_mapping(
            target_profile="any-profile",
            config={"agent": {}, "approvals": {}},
        )
        assert policy.get("approval_mode") == "manual"
        mi = policy.get("max_iterations")
        assert isinstance(mi, int) and mi > 0
        # Also verify smart mode override works (non-vacuous)
        policy_smart = execution_policy_mapping(
            target_profile="any-profile",
            config={"agent": {"max_turns": 5}, "approvals": {"mode": "smart"}},
        )
        assert policy_smart.get("approval_mode") == "smart"


class TestMentionIsolation:
    """@mention probe: non-seated / cross-board @mention never drives a member turn (BR-2 deliverable 4 / G1)."""

    def test_cross_board_mention_does_not_drive_member(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        # Cross-board target via @mention syntax should still be refused
        result = br._handler(target="sw-pm", message="@sw-pm please review")
        parsed = json.loads(result)
        assert "error" in parsed, f"cross-board @mention should be refused, got {parsed}"

    def test_non_seated_mention_never_drives_turn(self, two_boards, monkeypatch):
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
        br = _load_board_rooms_plugin()
        result = br._handler(target="ghost-profile", message="hello @ghost-profile")
        parsed = json.loads(result)
        assert "error" in parsed


class TestDeliveryFallback:
    """C4: delivery ImportError must not fake success."""

    def test_import_error_returns_error_not_queued(self, two_boards, monkeypatch):
        import builtins as _builtins

        br = _load_board_rooms_plugin()
        orig_import = _builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name in ("tools.bot_mode_dm", "agent.bot_chain"):
                raise ImportError(f"No module named '{name}' (test-injected)")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
        monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")

        monkeypatch.setattr(_builtins, "__import__", fake_import)
        # Need to reload to pick up patched import? Instead test _deliver_to_peer directly
        # _deliver_to_peer is called from _handler; patch inside it will be caught
        result = br._handler(target="sw-dev-b", message="hello")
        parsed = json.loads(result)
        # Must be error, not success queued
        assert "error" in parsed, f"expected error on ImportError, got success {parsed}"
        assert "status" not in parsed or parsed.get("status") != "queued"


class TestFenceScanErrorFailClosed:
    """Scan-error fail-closed probes — mirror reviewer r4 A2/A2b/A3 exactly."""

    def test_list_boards_runtime_error_refused(self, two_boards):
        from unittest.mock import patch as _patch
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError
        tmp = two_boards["tmp"]
        home = tmp / "profiles" / "sw-dev-a"
        class FakeAuth:
            profile_id = str(home)
        class FakeActor:
            profile_id = "sw-dev-a"
        members = [{"member_id": "m1", "profile": "sw-pm", "handle": "a", "target": {"kind": "local", "profile": "sw-pm"}}]
        with _patch("hermes_cli.kanban_db_boards.list_boards", side_effect=RuntimeError("injected scan failure")):
            with pytest.raises(RuntimeStoreError) as ei:
                _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {})
            assert ei.value.reason == "board_fence"

    def test_list_boards_permission_error_refused(self, two_boards):
        from unittest.mock import patch as _patch
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError
        tmp = two_boards["tmp"]
        home = tmp / "profiles" / "sw-dev-a"
        class FakeAuth:
            profile_id = str(home)
        class FakeActor:
            profile_id = "sw-dev-a"
        members = [{"member_id": "m1", "profile": "sw-pm", "handle": "a", "target": {"kind": "local", "profile": "sw-pm"}}]
        with _patch("hermes_cli.kanban_db_boards.list_boards", side_effect=PermissionError("injected perm failure")):
            with pytest.raises(RuntimeStoreError) as ei:
                _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {})
            assert ei.value.reason == "board_fence"

    def test_own_board_yaml_corrupt_refused(self, two_boards):
        from unittest.mock import patch as _patch
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError
        tmp = two_boards["tmp"]
        home = tmp / "profiles" / "sw-dev-a"
        import hermes_cli.board_layer as _bl
        orig_load = _bl.load_board_yaml
        def fake_load(slug):
            if slug == "board-alpha":
                raise OSError("injected corrupt board.yaml")
            return orig_load(slug)
        class FakeAuth:
            profile_id = str(home)
        class FakeActor:
            profile_id = "sw-dev-a"
        members = [{"member_id": "m1", "profile": "sw-pm", "handle": "a", "target": {"kind": "local", "profile": "sw-pm"}}]
        with _patch("hermes_cli.board_layer.load_board_yaml", side_effect=fake_load):
            with pytest.raises(RuntimeStoreError) as ei:
                _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {})
            assert ei.value.reason == "board_fence"

    def test_other_board_corrupt_still_fences(self, two_boards):
        from unittest.mock import patch as _patch
        from gateway.session_group_controls import _board_rooms_seating_fence
        from hermes_state_runtime import RuntimeStoreError
        tmp = two_boards["tmp"]
        home = tmp / "profiles" / "sw-dev-a"
        import hermes_cli.board_layer as _bl
        orig_load = _bl.load_board_yaml
        def fake_load(slug):
            if slug == "board-beta":
                raise OSError("injected corrupt other board")
            return orig_load(slug)
        class FakeAuth:
            profile_id = str(home)
        class FakeActor:
            profile_id = "sw-dev-a"
        members = [{"member_id": "m1", "profile": "sw-pm", "handle": "a", "target": {"kind": "local", "profile": "sw-pm"}}]
        with _patch("hermes_cli.board_layer.load_board_yaml", side_effect=fake_load):
            with pytest.raises(RuntimeStoreError) as ei:
                _board_rooms_seating_fence(members, FakeAuth(), FakeActor(), {})
            assert ei.value.reason == "board_fence"


class TestBoardParamWiring:
    """Board param reaches handler via both contracts."""

    def test_canonical_contract_accepts_board(self):
        from tui_gateway.contracts.canonical_projections import CanonicalRoomCreateParams
        raw = {"room_id": "r1", "name": "R1", "members": [], "board": "board-alpha"}
        p = CanonicalRoomCreateParams(**raw)
        assert p.board == "board-alpha"

    def test_groups_create_contract_accepts_board(self):
        from tui_gateway.contracts.groups_bot_relay import GroupsCreateParams
        raw = {"room_id": "r1", "name": "R1", "members": [], "board": "board-alpha"}
        p = GroupsCreateParams(**raw)
        assert p.board == "board-alpha"

    def test_gateway_fields_include_board(self):
        from gateway.session_group_controls import _FIELDS
        assert "board" in _FIELDS["groups.create"]

    def test_canonical_wire_accepts_board_param(self):
        """Real wire contract: groups.create with board must not be invalid_params (R2 failure mode)."""
        from tui_gateway.contracts.registry import CANONICAL_METHODS, canonical_param_problems
        contract = CANONICAL_METHODS.get("groups.create")
        assert contract is not None, "groups.create canonical contract missing"
        params = {"room_id": "r1", "name": "R1", "members": [], "board": "board-alpha"}
        problems = canonical_param_problems(contract, params)
        assert problems == [], f"board param should be accepted by canonical wire, got problems {problems}"
        # Without board must also be accepted (opt-in)
        problems2 = canonical_param_problems(contract, {"room_id": "r1", "name": "R1", "members": []})
        assert problems2 == []
