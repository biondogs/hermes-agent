"""hermes board subcommand — D9 grant-all with audit."""
from __future__ import annotations

import getpass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Callable


def build_board_parser(subparsers, *, cmd_board: Callable) -> None:
    p = subparsers.add_parser("board", help="Board-layer operations (RFC BOARD-LAYERS)")
    sp = p.add_subparsers(dest="board_action")
    g = sp.add_parser("grant-all", help="Grant boards:all capability to a role (operator audit)")
    g.add_argument("role", help="Profile/role name to grant")
    g.set_defaults(func=cmd_board)


def cmd_board(args) -> int:
    if getattr(args, "board_action", None) != "grant-all":
        print("Usage: hermes board grant-all <role>")
        return 2
    role = getattr(args, "role", "")
    if not role:
        print("error: role name required")
        return 2
    from hermes_cli.profiles import normalize_profile_name
    try:
        normalize_profile_name(role)
    except Exception as e:  # health: allow BLE001 -- fail-open role validation: normalize failure is handled as user error
        print(f"error: invalid role name {role!r}: {e}")
        return 2

    # Write boards.capability:all with audit into the role's config.yaml
    from hermes_constants import get_hermes_home
    import hermes_yaml as yaml

    role_home = Path(get_hermes_home()) / "profiles" / role
    # For default profile, config lives at HERMES_HOME/config.yaml
    if role == "default":
        cfg_path = Path(get_hermes_home()) / "config.yaml"
    else:
        cfg_path = role_home / "config.yaml"

    if not cfg_path.exists() and role != "default":  # config-reader: ok -- existence check for profile dir creation, not config value
        # Create minimal profile dir if missing
        role_home.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("", encoding="utf-8")

    try:
        doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() and cfg_path.stat().st_size else {}  # config-reader: ok -- grant-all reads role config for merge; write goes via atomic_config_write seam
    except Exception:  # health: allow BLE001 -- fail-open config read: grant-all must handle corrupt config as empty
        doc = {}
    if not isinstance(doc, dict):
        doc = {}

    boards = doc.get("boards")
    if not isinstance(boards, dict):
        boards = {}

    now = datetime.now(UTC).isoformat(timespec="seconds")
    user = getpass.getuser() if hasattr(getpass, "getuser") else "operator"
    try:
        user = getpass.getuser()
    except Exception:  # health: allow BLE001 -- fail-open getuser: audit user must not fail the grant, falls back to operator
        user = "operator"

    boards["capability"] = "all"
    boards["granted_by"] = user
    boards["granted_at"] = now
    doc["boards"] = boards

    from hermes_cli.config import atomic_config_write
    atomic_config_write(cfg_path, doc)
    print(f"Granted boards:all to {role!r} (by {user} at {now})")
    return 0
