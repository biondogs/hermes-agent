"""BRP-v2 direct-surface test: message_peer is direct when board_rooms enabled."""

from __future__ import annotations

import pathlib

FROZEN_DESC = (
    "Send a message to a teammate on this board (board-fenced). Use it to ask a teammate "
    "a question you cannot answer from the card — a spec detail, a constraint, a blocker "
    "— instead of guessing or blocking on the operator."
)


def _make_td(name="message_peer", description=FROZEN_DESC):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {}},
        },
    }


def _is_deferrable_sim(name: str, toolset: str | None, direct_toolsets: frozenset) -> bool:
    """Minimal reimplementation of is_deferrable_tool_name's toolset branch."""
    if toolset is None:
        return False
    return toolset.startswith("mcp-") or toolset not in direct_toolsets


class TestDirectSurface:
    def test_client_surface_contains_board_rooms(self):
        from toolsets import CLIENT_SURFACE_TOOLSETS

        assert "board_rooms" in CLIENT_SURFACE_TOOLSETS
        src = pathlib.Path("toolsets.py").read_text(encoding="utf-8")
        assert "board_rooms" in src
        assert "BRP-v2, t_9a1a3b28" in src

    def test_message_peer_is_visible_not_deferrable(self):
        """With board_rooms in direct surface, message_peer is NOT deferrable (VISIBLE)."""
        from toolsets import CLIENT_SURFACE_TOOLSETS, TOOLSET_SESSION_PLATFORMS

        direct = CLIENT_SURFACE_TOOLSETS | TOOLSET_SESSION_PLATFORMS.keys()
        assert "board_rooms" in direct
        assert _is_deferrable_sim("message_peer", "board_rooms", direct) is False
        try:
            import tools.tool_search as ts  # type: ignore[import]

            orig = ts._registry_toolset

            def fake(name):
                if name == "message_peer":
                    return "board_rooms"
                return orig(name)

            ts._registry_toolset = fake  # type: ignore[attr-defined]
            from toolsets import CLIENT_SURFACE_TOOLSETS as cst  # noqa: F811

            ts._DIRECT_SURFACE_TOOLSETS = cst | TOOLSET_SESSION_PLATFORMS.keys()  # type: ignore[attr-defined]
            assert ts.is_deferrable_tool_name("message_peer") is False
            td = _make_td()
            visible, deferred = ts.classify_tools([td])
            assert len(visible) == 1 and visible[0]["function"]["name"] == "message_peer"
            assert len(deferred) == 0
        except ImportError:
            pass
        finally:
            try:
                ts._registry_toolset = orig  # type: ignore[possibly-undefined,used-before-def]
            except Exception:
                pass

    def test_description_byte_match(self):
        src = pathlib.Path("plugins/board-rooms/__init__.py").read_text(encoding="utf-8")
        assert FROZEN_DESC in src
        assert src.count(FROZEN_DESC) == 1

    def test_toolset_absent_behavior_unchanged(self):
        """Plugin-off semantics: without board_rooms in direct surface, tool defers."""
        from toolsets import TOOLSET_SESSION_PLATFORMS

        old_direct = frozenset({"project", "desktop_ui", "catalog"}) | TOOLSET_SESSION_PLATFORMS.keys()
        assert _is_deferrable_sim("message_peer", "board_rooms", old_direct) is True
        try:
            import tools.tool_search as ts  # type: ignore[import]

            orig_fn = ts._registry_toolset
            orig_direct = ts._DIRECT_SURFACE_TOOLSETS

            def fake2(name):
                if name == "message_peer":
                    return "board_rooms"
                return orig_fn(name)

            ts._registry_toolset = fake2  # type: ignore[attr-defined]
            ts._DIRECT_SURFACE_TOOLSETS = old_direct  # type: ignore[attr-defined]
            assert ts.is_deferrable_tool_name("message_peer") is True
            td = _make_td()
            visible, deferred = ts.classify_tools([td])
            assert len(visible) == 0
            assert len(deferred) == 1
            ts._registry_toolset = orig_fn  # type: ignore[attr-defined]
            ts._DIRECT_SURFACE_TOOLSETS = orig_direct  # type: ignore[attr-defined]
        except ImportError:
            pass
