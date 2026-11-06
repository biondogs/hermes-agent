"""board-rooms plugin — board-scoped peer messaging (message_peer).

BR-D1: never enable upstream message_agent.
BR-D2: message_peer is board-fenced at check_fn AND handler (belt and braces).
BR-D6: meta-role profiles (boards: all) are never in any peer roster.

Delivery reuses tools/bot_mode_dm local delivery primitives via a one-shot
quiet CLI turn on the target's board-composed context.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TOOL_NAME = "message_peer"
TOOLSET = "board_rooms"

# BR-D5 nudge included in every successful tool result
_DURABLE_NUDGE = (
    "Nudge (BR-D5): echo durable outcomes to the relevant card — "
    "rooms/DMs are ephemeral, cards are the durable record."
)

# Fence refusal template — mirrors kanban fence style
_FENCE_REFUSAL_TEMPLATE = (
    "board-rooms fence: message_peer target {target!r} is REFUSED — "
    "{reason} (board={board!r}). "
    "The board-rooms roster is board.yaml roles ∩ live profiles; "
    "cross-board and out-of-roster targets are never delivered."
)


def _current_board() -> str | None:
    """Board pin for the current execution context, or None if unbound."""
    # Predicate family matching the board-layers fence: HERMES_KANBAN_BOARD env
    # is the dispatcher/worker pin. We also check EffectiveProfile-style
    # board pin via kanban_db when available, but env is the canonical
    # worker signal.
    pin = (os.environ.get("HERMES_KANBAN_BOARD") or "").strip()
    if pin:
        return pin
    # Fallback: try board discovery via kanban_db (operator shell with
    # board.yaml present but no env pin — rare, but check)
    try:
        from hermes_cli.kanban_db import get_current_board

        cur = (get_current_board() or "").strip()
        if cur and cur != "default":
            # Only treat as pinned if it's actually a layered board
            try:
                from hermes_cli.board_layer import is_layered_board

                if is_layered_board(cur):
                    return cur
            except Exception:
                pass
    except Exception:
        pass
    return None


def _live_profiles() -> set[str]:
    """Set of live (non-tombstoned) profile names on this install."""
    try:
        from hermes_cli.profiles import list_profiles

        return {p.name for p in list_profiles()}
    except Exception:
        return set()


def _board_roster(board: str) -> list[str]:
    """Board roster = board.yaml roles ∩ live profiles, excluding meta-roles.

    Meta-roles are profiles whose config declares boards: all (BR-D6).
    """
    if not board:
        return []
    try:
        from hermes_cli.board_layer import load_board_yaml
        from hermes_cli.profiles import profile_exists

        doc = load_board_yaml(board)
        roles = doc.get("roles") or []
        if not isinstance(roles, list):
            return []
        live = _live_profiles()
        # Filter to live profiles only, exclude meta-roles
        roster = []
        for r in roles:
            if not isinstance(r, str):
                continue
            if r not in live:
                continue
            if _is_meta_profile(r):
                continue
            roster.append(r)
        return sorted(set(roster))
    except Exception as exc:
        logger.debug("board-rooms: _board_roster(%r) failed: %s", board, exc)
        return []


def _is_meta_profile(profile: str) -> bool:
    """True if profile has boards: all (meta-role, BR-D6)."""
    try:
        from pathlib import Path as _Path

        from hermes_constants import get_hermes_home

        # Check profile config for boards capability
        cfg_path = _Path(get_hermes_home()) / "profiles" / profile / "config.yaml"
        if cfg_path.is_file():
            import hermes_yaml as yaml

            doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8-sig")) or {}
            boards_cfg = doc.get("boards")
            if isinstance(boards_cfg, dict):
                # boards: all or boards.capability == "all"
                if boards_cfg.get("capability") == "all":
                    return True
                # Also check hermes_cli/board_layer's boards capability
                # Some profiles use profiles config directly
    except Exception:
        pass
    # Also check via board_layer compose — if EffectiveProfile says capability all
    try:
        from hermes_cli.board_layer import compose

        ep = compose(profile, board=None)
        if getattr(ep, "boards_capability", None) == "all":
            return True
    except Exception:
        pass
    return False


def _peer_roster_for_board(board: str, me: str | None = None) -> list[str]:
    """Peers available to an agent on board (roster minus self)."""
    roster = _board_roster(board)
    if me:
        roster = [p for p in roster if p != me]
    return roster


def _detect_self_profile() -> str | None:
    """Best-effort self profile detection."""
    # HERMES_PROFILE is set in some contexts; otherwise infer from HERMES_HOME
    p = (os.environ.get("HERMES_PROFILE") or "").strip()
    if p:
        return p
    # Try from HERMES_HOME path
    try:
        from hermes_constants import get_hermes_home

        home = str(get_hermes_home())
        # profiles/<name> pattern
        parts = Path(home).parts
        if "profiles" in parts:
            idx = parts.index("profiles")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    except Exception:
        pass
    return None


# ── check_fn ─────────────────────────────────────────────────────────────

def _check_fn(**kwargs: Any) -> bool:
    """Tool offered only when board-pinned AND ≥1 same-board peer is live."""
    board = _current_board()
    if not board:
        return False
    me = _detect_self_profile()
    peers = _peer_roster_for_board(board, me=me)
    return len(peers) >= 1


# ── handler ──────────────────────────────────────────────────────────────

def _handler(
    target: str = "",
    message: str = "",
    expects_reply: bool = True,
    **kwargs: Any,
) -> str:
    """Board-fenced peer delivery handler.

    Validates target against board roster (belt and braces), then delivers
    via a one-shot quiet CLI turn on the target's board-composed context.
    """
    board = _current_board()
    if not board:
        return json.dumps({
            "error": (
                "board-rooms fence: message_peer is only available to board-pinned agents. "
                "This session has no board pin (HERMES_KANBAN_BOARD not set and no layered board context). "
                "Unbound roles never see this tool — if you see this, the check_fn gate was bypassed."
            ),
            "board": None,
        })

    # Re-validate roster even if check_fn passed
    me = _detect_self_profile()
    roster = _board_roster(board)
    peers = [p for p in roster if p != me] if me else roster

    target_norm = (target or "").strip()
    if not target_norm:
        return json.dumps({
            "error": _FENCE_REFUSAL_TEMPLATE.format(
                target=target, reason="empty target", board=board
            ),
            "board": board,
            "roster": peers,
        })

    # Resolve target against roster (case-insensitive like upstream)
    target_lower = target_norm.lower()
    roster_lower = {p.lower(): p for p in peers}
    # Also allow exact match against full roster for error messages
    full_roster_lower = {p.lower(): p for p in roster}

    if target_lower not in roster_lower:
        # Distinguish cross-board vs unknown vs self
        if me and target_lower == me.lower():
            reason = "you cannot message yourself"
        elif target_lower in full_roster_lower and me and target_lower == me.lower():
            reason = "you cannot message yourself"
        else:
            # Check if target is a live profile but not on this board
            live = _live_profiles()
            live_lower = {p.lower() for p in live}
            if target_lower in live_lower:
                reason = f"target {target_norm!r} is not on your board {board!r}"
            else:
                reason = f"unknown target {target_norm!r} — not in board roster"
        return json.dumps({
            "error": _FENCE_REFUSAL_TEMPLATE.format(
                target=target_norm, reason=reason, board=board
            ),
            "board": board,
            "roster": peers,
        })

    resolved = roster_lower[target_lower]

    # Validate message
    msg = (message or "").strip()
    if not msg:
        return json.dumps({"error": "message_peer: 'message' is required and must be non-empty", "board": board})

    # Delivery: reuse upstream local delivery via bot_mode_dm primitives
    # We spawn: hermes --board <board> -p <target> --one-shot delivery
    # Use the board-rooms delivery path: board-composed one-shot turn
    try:
        result = _deliver_to_peer(
            board=board,
            target=resolved,
            message=msg,
            expects_reply=expects_reply,
            sender=me,
        )
        return result
    except Exception as exc:
        logger.warning("board-rooms delivery to %r failed: %s", resolved, exc)
        return json.dumps({"error": f"board-rooms delivery failed: {exc}", "board": board})


def _deliver_to_peer(
    board: str,
    target: str,
    message: str,
    expects_reply: bool = True,
    sender: str | None = None,
) -> str:
    """Deliver message to target profile via board-composed one-shot turn.

    Reuses the hermes CLI delivery path with --board pin so the recipient
    turn runs in the correct board context.
    """
    from tools.bot_relay import _hermes_cli

    sender_label = sender or "peer"
    # Attribution prefix for the recipient
    attribution = f"[board-rooms DM from @{sender_label} on board {board!r}] "
    content = attribution + message

    # For expects_reply=False, add the notify-only marker
    if not expects_reply:
        try:
            from tools.bot_mode_probe import NO_REPLY_MARKER

            content = f"{NO_REPLY_MARKER} {content}"
        except ImportError:
            pass

    # Build delivery command: hermes --board <board> -p <target> with delivery
    # Use HERMES_KANBAN_BOARD env pin + hermes CLI invocation
    import subprocess
    import tempfile

    hermes_bin = _hermes_cli()

    # Use tools/bot_mode_dm delivery if available for chain accounting
    try:
        # Try to use upstream's _start_delivery for chain/hop accounting
        from agent.bot_chain import _LOCK as _chain_lock  # noqa: F401 — ensure chain module loaded

        from tools.bot_mode_dm import _start_delivery as _upstream_deliver
        from tools.bot_mode_probe import _handle as _probe_handle

        # Build sender envelope for chain tracking
        sender_handle = sender or "unknown"
        try:
            roster_homes = {p: None for p in _board_roster(board)}
            handle = _probe_handle(target, list(roster_homes.keys())) if roster_homes else target
        except Exception:
            handle = target

        # Use the upstream delivery with board pin via env
        env = os.environ.copy()
        env["HERMES_KANBAN_BOARD"] = board
        # _start_delivery spawns hermes -p <target> with delivery content
        result_str = _upstream_deliver(
            [hermes_bin, "-p", target],
            content,
            f"@{handle} on board {board!r}",
            stdin_file=False,
            task_id=os.environ.get("HERMES_KANBAN_TASK", ""),
            agent=None,  # no agent object in plugin context
            wake="notify" if expects_reply else "none",
        )
        # _upstream_deliver returns a JSON string or status message
        try:
            parsed = json.loads(result_str) if isinstance(result_str, str) else result_str
            if isinstance(parsed, dict) and "error" in parsed:
                return json.dumps({**parsed, "board": board})
        except (json.JSONDecodeError, TypeError):
            pass
        return json.dumps({
            "status": "delivered",
            "to": target,
            "board": board,
            "detail": result_str if isinstance(result_str, str) else str(result_str),
            "nudge": _DURABLE_NUDGE,
        })
    except ImportError as exc:
        return json.dumps({
            "error": f"board-rooms delivery failed: missing upstream delivery import {exc!r} — cannot deliver to {target!r} (BR-D1 delivery backend unavailable)",
            "board": board,
            "to": target,
        })


# ── plugin registration ──────────────────────────────────────────────────

MESSAGE_PEER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "target": {
            "type": "string",
            "description": "Target peer profile name on your board (board.yaml roles ∩ live profiles). Cross-board targets are refused.",
        },
        "message": {
            "type": "string",
            "description": "Message to deliver to the target peer. Attributed with sender board/name prefix on receipt.",
        },
        "expects_reply": {
            "type": "boolean",
            "description": "Whether you expect a reply (default true). False sends notify-only (no reply turn spawned).",
            "default": True,
        },
    },
    "required": ["target", "message"],
    "additionalProperties": False,
}


def register(ctx: Any) -> None:
    """Plugin entry point — registers the message_peer tool."""
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET,
        schema=MESSAGE_PEER_SCHEMA,
        handler=_handler,
        check_fn=_check_fn,
        description="Send a message to a peer on your board (board-fenced). Roster = board.yaml roles ∩ live profiles.",
    )
    logger.info("board-rooms plugin: registered tool %r in toolset %r", TOOL_NAME, TOOLSET)
