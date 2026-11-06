"""board-rooms.yaml loader — schema, validation, provenance.

Schema (card BR-1, BOARD-ROOMS-DESIGN §6):
  version: 1  (required)
  rooms: list[Room]
    name: str (required, non-empty)
    members: list[str] 2..6 profile names (required)
    lead: str (required, must be in members)
    routing: "everyone" | "lead" | "assigned" (default "assigned")
    purpose: str (required, 1..500 chars)

Rules:
  - Unknown keys anywhere = schema error (fail closed, RFC §5.2 doctrine).
  - No ".." in any path-like value (board home escape).
  - Validation: every members entry (incl. lead) must be in that board's
    board.yaml roles allowlist (+ butler/composer when declared).
  - Loader API: load_board_rooms(board_home) -> BoardRooms

Stdlib + hermes_yaml only, following board_layer.py grain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import hermes_yaml as yaml

ALLOWED_ROUTING = frozenset({"everyone", "lead", "assigned"})
ALLOWED_TOP_KEYS = frozenset({"version", "rooms"})
ALLOWED_ROOM_KEYS = frozenset({"name", "members", "lead", "routing", "purpose"})


class BoardRoomsError(ValueError):
    """Schema or validation error with actionable message."""


@dataclass
class BoardRoom:
    name: str
    members: list[str]
    lead: str
    routing: str = "assigned"
    purpose: str = ""
    # provenance: source file path for this room entry
    provenance: str = ""


@dataclass
class BoardRooms:
    version: int = 1
    rooms: list[BoardRoom] = field(default_factory=list)
    source_path: str = ""
    board_slug: str = ""


def _validate_profile_name(name: str, field_name: str = "") -> None:
    from hermes_constants import PROFILE_ID_RE

    if not PROFILE_ID_RE.match(name):
        where = f" in {field_name}" if field_name else ""
        raise BoardRoomsError(f"board-rooms.yaml: invalid profile name {name!r}{where}")


def _check_no_traversal(value: str, field_name: str) -> None:
    if ".." in Path(value).parts or ".." in value.split("/"):
        raise BoardRoomsError(f"board-rooms.yaml: path {value!r} in {field_name!r} escapes board home (.. not allowed)")


def _allowed_members_for_board(board_home: Path) -> set[str] | None:
    """Return allowed member set for board_home, or None if board is not layered / has no roles allowlist."""
    board_yaml = board_home / "board.yaml"
    if not board_yaml.is_file():
        return None
    try:
        doc = yaml.safe_load(board_yaml.read_text(encoding="utf-8-sig")) or {}
    except Exception:
        return None
    if not isinstance(doc, dict):
        return None
    roles = doc.get("roles")
    if roles is None:
        # Open board: any role may bind — no allowlist to check against.
        # For board-rooms we still need a roster: treat as no restriction (caller decides).
        return None
    if not isinstance(roles, list):
        return None
    allowed: set[str] = set()
    for r in roles:
        if isinstance(r, str):
            allowed.add(r)
    # Also include butler/composer profile when board declares one
    # Check for 'butler' key at top level or in meta, or look for board.yaml declaring butler-like role
    # The spec says "plus, when the board declares one, its butler/composer profile"
    # We check if board.yaml has a 'butler' key, or 'composer', or if any roles entry looks like butler/composer
    # More precisely: check for top-level keys that name a profile (butler, composer)
    for extra_key in ("butler", "composer"):
        if extra_key in doc and isinstance(doc[extra_key], str) and doc[extra_key].strip():
            allowed.add(doc[extra_key].strip())
        # Also if board.yaml has board-level butler/composer config as dict with profile name
        if extra_key in doc and isinstance(doc[extra_key], dict):
            # e.g. butler: {profile: swco-butler}
            for v in doc[extra_key].values():
                if isinstance(v, str) and v.strip():
                    # Only add if it looks like a profile name
                    try:
                        _validate_profile_name(v.strip())
                        allowed.add(v.strip())
                    except BoardRoomsError:
                        pass
    return allowed


def validate_board_rooms_doc(doc: dict[str, Any], *, source_path: str = "", board_home: Path | None = None) -> None:
    """Validate doc per schema; raise BoardRoomsError on violation."""
    if not isinstance(doc, dict):
        raise BoardRoomsError(f"board-rooms.yaml: must be a mapping, got {type(doc).__name__}")

    # Unknown top-level keys
    for k in doc:
        if k not in ALLOWED_TOP_KEYS:
            raise BoardRoomsError(f"board-rooms.yaml: unknown top-level key {k!r}")

    # version required
    if "version" not in doc:
        raise BoardRoomsError("board-rooms.yaml: missing required key 'version' (expected 1)")
    if doc["version"] != 1:
        raise BoardRoomsError(f"board-rooms.yaml: unknown version {doc['version']!r} (only 1 is defined)")

    # rooms required
    if "rooms" not in doc:
        raise BoardRoomsError("board-rooms.yaml: missing required key 'rooms'")
    rooms = doc["rooms"]
    if not isinstance(rooms, list):
        raise BoardRoomsError("board-rooms.yaml: 'rooms' must be a list")

    # Check no .. in top-level path-like values (defensive; none currently but future-proof)
    for p in _collect_path_values(doc):
        _check_no_traversal(p, "board-rooms.yaml")

    seen_names: set[str] = set()
    for idx, room in enumerate(rooms):
        label = f"rooms[{idx}]"
        if not isinstance(room, dict):
            raise BoardRoomsError(f"board-rooms.yaml: {label} must be a mapping")
        for k in room:
            if k not in ALLOWED_ROOM_KEYS:
                raise BoardRoomsError(f"board-rooms.yaml: unknown key {k!r} in {label}")

        # name required
        if "name" not in room:
            raise BoardRoomsError(f"board-rooms.yaml: {label} missing required key 'name'")
        name = room["name"]
        if not isinstance(name, str) or not name.strip():
            raise BoardRoomsError(f"board-rooms.yaml: {label}.name must be a non-empty string")
        _check_no_traversal(name, f"{label}.name")
        if name in seen_names:
            raise BoardRoomsError(f"board-rooms.yaml: duplicate room name {name!r}")
        seen_names.add(name)

        # members required 2..6
        if "members" not in room:
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) missing required key 'members'")
        members = room["members"]
        if not isinstance(members, list):
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) 'members' must be a list")
        if len(members) < 2 or len(members) > 6:
            raise BoardRoomsError(
                f"board-rooms.yaml: {label} ({name!r}) 'members' must have 2-6 entries, got {len(members)}"
            )
        for m in members:
            if not isinstance(m, str) or not m.strip():
                raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) members entry {m!r} must be a non-empty string")
            _validate_profile_name(m, field_name=f"{label}.members")
            _check_no_traversal(m, f"{label}.members")
        # uniqueness within room
        if len(set(members)) != len(members):
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) 'members' must be unique")

        # lead required, must be in members
        if "lead" not in room:
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) missing required key 'lead'")
        lead = room["lead"]
        if not isinstance(lead, str) or not lead.strip():
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) 'lead' must be a non-empty string")
        _validate_profile_name(lead, field_name=f"{label}.lead")
        if lead not in members:
            raise BoardRoomsError(
                f"board-rooms.yaml: {label} ({name!r}) 'lead' {lead!r} must be one of members {members}"
            )

        # routing optional, default assigned
        if "routing" in room:
            routing = room["routing"]
            if not isinstance(routing, str) or routing not in ALLOWED_ROUTING:
                raise BoardRoomsError(
                    f"board-rooms.yaml: {label} ({name!r}) 'routing' must be one of {sorted(ALLOWED_ROUTING)}, got {routing!r}"
                )

        # purpose required <=500
        if "purpose" not in room:
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) missing required key 'purpose'")
        purpose = room["purpose"]
        if not isinstance(purpose, str) or not purpose.strip():
            raise BoardRoomsError(f"board-rooms.yaml: {label} ({name!r}) 'purpose' must be a non-empty string")
        if len(purpose) > 500:
            raise BoardRoomsError(
                f"board-rooms.yaml: {label} ({name!r}) 'purpose' must be <=500 chars, got {len(purpose)}"
            )
        _check_no_traversal(purpose, f"{label}.purpose")

    # Cross-board validation: members must be in board.yaml roles allowlist
    if board_home is not None:
        allowed = _allowed_members_for_board(board_home)
        if allowed is not None:
            for idx, room in enumerate(rooms):
                label = f"rooms[{idx}] ({room.get('name', '?')!r})"
                for m in room.get("members", []):
                    if m not in allowed:
                        raise BoardRoomsError(
                            f"board-rooms.yaml: {label} member {m!r} is not in board's roles allowlist {sorted(allowed)} "
                            f"(board {board_home.name!r}); add {m!r} to board.yaml roles: or remove it from the room"
                        )
                # lead is already in members, but message separately if needed
                lead = room.get("lead")
                if isinstance(lead, str) and lead not in allowed:
                    raise BoardRoomsError(
                        f"board-rooms.yaml: {label} lead {lead!r} is not in board's roles allowlist {sorted(allowed)}"
                    )


def _collect_path_values(doc: dict[str, Any]) -> list[str]:
    """Collect any string values that look like paths for traversal check."""
    # Currently room names/members/purpose are checked individually; this is for
    # any future path-like top-level values.
    out: list[str] = []
    for k, v in doc.items():
        if isinstance(v, str) and ("/" in v or v.startswith(".")):
            out.append(v)
    return out


def load_board_rooms(board_home: Path | str) -> BoardRooms:
    """Load and validate board-rooms.yaml from board_home.

    board_home: Path to the board directory (containing board.yaml etc.)
    Returns BoardRooms with per-field provenance.
    Raises BoardRoomsError on schema or validation failure.
    Raises FileNotFoundError if board-rooms.yaml is absent.
    """
    bh = Path(board_home)
    source = bh / "board-rooms.yaml"
    if not source.is_file():
        raise FileNotFoundError(f"board-rooms.yaml not found at {source}")
    # Path must stay inside board home
    try:
        source.resolve().relative_to(bh.resolve())
    except ValueError:
        raise BoardRoomsError(f"board-rooms.yaml path {source} escapes board home {bh}")
    # Also reject if source path string contains ..
    if ".." in str(source):
        raise BoardRoomsError(f"board-rooms.yaml path {source!r} contains '..'")

    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8-sig")) or {}
    except BoardRoomsError:
        raise
    except Exception as exc:
        raise BoardRoomsError(f"board-rooms.yaml parse error at {source}: {exc}") from exc

    validate_board_rooms_doc(raw, source_path=str(source), board_home=bh)

    rooms: list[BoardRoom] = []
    for room_doc in raw.get("rooms", []):
        rooms.append(
            BoardRoom(
                name=room_doc["name"],
                members=list(room_doc["members"]),
                lead=room_doc["lead"],
                routing=room_doc.get("routing", "assigned"),
                purpose=room_doc["purpose"],
                provenance=str(source),
            )
        )

    return BoardRooms(
        version=raw["version"],
        rooms=rooms,
        source_path=str(source),
        board_slug=bh.name,
    )
