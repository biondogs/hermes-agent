"""Board-scoped state resolution: memory / sessions / Hindsight bank / skills / env.

All paths derive from the board home (RFC §4/§8) and are hermetic per
(role, board). No board → identity with today's behaviour (zero-change).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from hermes_cli.board_layer import BoardLayerError, compose, is_layered_board


def _board_state_root(role: str, board: str | None) -> Path | None:
    """State root for (role, board) or None when unbound."""
    if not board or not is_layered_board(board):
        return None
    from hermes_cli.kanban_db import board_dir
    return board_dir(board) / "state" / role


def state_root(role: str, board: str | None) -> Path | None:
    """Public: board-scoped state root, or None (use profile home)."""
    return _board_state_root(role, board)


def memory_dir(role: str, board: str | None) -> Path:
    """Path to memories dir (where MEMORY.md / USER.md live)."""
    sr = _board_state_root(role, board)
    if sr is not None:
        return sr / "memories"
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "memories"


def memory_file(role: str, board: str | None, filename: str) -> Path:
    """MEMORY.md or USER.md resolved hermetically."""
    return memory_dir(role, board) / filename


def session_db_path(role: str, board: str | None) -> Path:
    """state.db path for (role, board)."""
    sr = _board_state_root(role, board)
    if sr is not None:
        return sr / "state.db"
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "state.db"


def sessions_dir(role: str, board: str | None) -> Path:
    """Gateway sessions dir for (role, board)."""
    sr = _board_state_root(role, board)
    if sr is not None:
        return sr / "sessions"
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "sessions"


def hindsight_bank(role: str, board: str | None) -> str | None:
    """Hindsight bank name for (role, board). None when unbound/pinned."""
    if not board or not is_layered_board(board):
        return None
    ep = compose(role, board)
    # Pinned memory → role's own bank (not board-derived)
    if "memory" in ep.pinned_keys or "*" in ep.pinned_keys:
        return None
    return ep.memory_bank


def board_skills_dir(board: str | None) -> Path | None:
    """Board skills dir when layered, else None."""
    if not board or not is_layered_board(board):
        return None
    from hermes_cli.kanban_db import board_dir
    return board_dir(board) / "skills"


def effective_skills_dirs(role: str, board: str | None) -> list[Path]:
    """Ordered skill index roots: role first (wins), board second.

    When memory/skills is pinned, board skills are excluded.
    """
    from hermes_constants import get_hermes_home
    role_skills = get_hermes_home() / "profiles" / role / "skills"
    # Also support get_skills_dir() shape (flat home). Prefer profile dir if it exists.
    # The caller (skill_utils) will filter to existing dirs.
    dirs = [role_skills]
    if board and is_layered_board(board):
        ep = compose(role, board)
        if "skills" not in ep.pinned_keys and "*" not in ep.pinned_keys:
            bd = board_skills_dir(board)
            if bd is not None:
                dirs.append(bd)
    return dirs


def board_env_names(board: str | None, role: str | None = None) -> list[str]:
    """Exported env var NAMES from board manifest (names-only, never values)."""
    if not board or not is_layered_board(board):
        return []
    ep = compose(role or "", board) if role else compose("default", board)
    # If env pinned, board contributes no env names
    if ep.pinned_keys and ("env" in ep.pinned_keys or "*" in ep.pinned_keys):
        return []
    # Read manifest export list directly for accuracy (compose only stores path)
    from hermes_cli.kanban_db import board_dir
    import hermes_yaml as yaml
    manifest_rel = ep.env_manifest or "./env/manifest.yaml"
    # board_dir / manifest_rel (handle ./ prefix)
    bd = board_dir(board)
    mp = bd / manifest_rel.lstrip("./")
    if not mp.is_file():
        mp = bd / manifest_rel
    if mp.is_file():
        try:
            doc = yaml.safe_load(mp.read_text(encoding="utf-8")) or {}
            ex = doc.get("export") or []
            return [str(n) for n in ex if isinstance(n, str)]
        except Exception:
            return []
    return []


def compose_env(role: str, board: str | None, base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Overlay board env onto base_env (board wins for exported names only).

    Values are read from the board's secrets file; only exported names enter.
    No value is ever logged.
    """
    env = dict(base_env or {})
    if not board or not is_layered_board(board):
        return env
    ep = compose(role, board)
    if ep.pinned_keys and ("env" in ep.pinned_keys or "*" in ep.pinned_keys):
        return env
    if not ep.env_manifest:
        return env
    from hermes_cli.kanban_db import board_dir
    import hermes_yaml as yaml
    bd = board_dir(board)
    # Load manifest
    mp = bd / ep.env_manifest.lstrip("./")
    if not mp.is_file():
        mp = bd / ep.env_manifest
    if not mp.is_file():
        return env
    try:
        doc = yaml.safe_load(mp.read_text(encoding="utf-8")) or {}
    except Exception:
        return env
    exports = doc.get("export") or []
    vars_cfg = doc.get("vars") or {}
    # vars may be list of names (simple) or dict of name->spec
    for name in exports:
        if not isinstance(name, str):
            continue
        spec = vars_cfg.get(name) if isinstance(vars_cfg, dict) else None
        if isinstance(spec, dict) and "value" in spec:
            env[name] = str(spec["value"])
        elif isinstance(vars_cfg, list) and name in vars_cfg:
            # bare name → read from secrets.env
            env[name] = _read_secret(bd, name)
        elif isinstance(spec, dict):
            # explicit secret file ref
            env[name] = _read_secret(bd, name, spec=spec)
        else:
            env[name] = _read_secret(bd, name)
    return env


def _read_secret(board_home: Path, name: str, spec: dict | None = None) -> str:
    """Read one secret from board's secrets file (stub-friendly)."""
    secrets_path = board_home / "env" / "secrets.env"
    if spec and isinstance(spec.get("path"), str):
        p = spec["path"].lstrip("./")
        secrets_path = board_home / p
    if not secrets_path.is_file():
        return ""
    try:
        for line in secrets_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == name:
                    return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return ""
