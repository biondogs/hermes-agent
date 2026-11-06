"""Board layer: board.yaml parsing, validation and EffectiveProfile composition.

Pure stdlib + hermes_yaml + existing kanban board discovery. No daemon;
composition is a function of on-disk state at call time.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import hermes_yaml as yaml

# Pin vocabulary — RFC 8.4 closed list (+ "*")
ALLOWED_PINS: frozenset[str] = frozenset(
    {"memory", "sessions", "skills", "soul", "env", "model", "toolsets"}
)

# Top-level board.yaml keys — RFC 5.2 strict
ALLOWED_BOARD_KEYS: frozenset[str] = frozenset(
    {"version", "roles", "memory", "skills", "toolsets", "soul", "env", "overrides", "meta"}
)

# Keys allowed in overrides.<role> — RFC 5.1/5.2 plus x-* escape hatch
ALLOWED_OVERRIDE_KEYS: frozenset[str] = frozenset(
    {"model", "provider", "skills", "toolsets", "memory", "reason"}
)

# Keys allowed inside board base skills/toolsets blocks
_LIST_BLOCK_KEYS = frozenset({"add", "remove", "replace"})

# Only {{board.<slot>}} is special — RFC 6.2
_SLOT_RE = re.compile(r"\{\{board\.([a-zA-Z0-9_]+)\}\}")
# Detect any {{board. without a closing }} on same line — pass through verbatim per RFC
_OPEN_SLOT_RE = re.compile(r"\{\{board\.")
_CLOSE_RE = re.compile(r"\}\}")


class BoardLayerError(ValueError):
    """Schema or composition error with an actionable message."""


# ── Discovery ────────────────────────────────────────────────────────────────

def is_layered_board(board_slug: str | None) -> bool:
    """True when *board_slug* has a board.yaml (the layered marker, RFC D10)."""
    if not board_slug:
        return False
    from hermes_cli.kanban_db import board_dir

    try:
        return (board_dir(board_slug) / "board.yaml").is_file()
    except ValueError:
        return False


def board_yaml_path(board_slug: str) -> Path:
    """Path to board.yaml for *board_slug* (does not check existence)."""
    from hermes_cli.kanban_db import board_dir

    return board_dir(board_slug) / "board.yaml"


# ── Parsing & validation ───────────────────────────────────────────────────

def load_board_yaml(board_slug: str) -> dict[str, Any]:
    """Load and validate board.yaml for *board_slug*; raises BoardLayerError."""
    path = board_yaml_path(board_slug)
    if not path.is_file():
        raise BoardLayerError(f"board {board_slug!r} is not layered (no board.yaml at {path})")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except Exception as exc:
        raise BoardLayerError(f"board.yaml parse error for {board_slug!r}: {exc}") from exc
    if not isinstance(raw, dict):
        raise BoardLayerError(f"board.yaml for {board_slug!r} must be a mapping, got {type(raw).__name__}")
    validate_board_yaml(raw, board_slug=board_slug, board_dir_path=path.parent)
    return raw


def validate_board_yaml(doc: dict[str, Any], *, board_slug: str = "", board_dir_path: Path | None = None) -> None:
    """Validate *doc* per RFC 5.2; raise BoardLayerError on violation."""
    from hermes_cli.board_layer_validate import validate_board_yaml_impl
    return validate_board_yaml_impl(doc, board_slug=board_slug, board_dir_path=board_dir_path)

def _validate_profile_name(name: str, field: str = "") -> None:
    from hermes_constants import PROFILE_ID_RE

    if not PROFILE_ID_RE.match(name):
        where = f" in {field}" if field else ""
        raise BoardLayerError(f"board.yaml: invalid profile name {name!r}{where}")


def _validate_list_block(block: Any, label: str, *, allow_replace: bool = False, for_skills: bool = False) -> None:
    if not isinstance(block, dict):
        raise BoardLayerError(f"{label} must be a mapping with add/remove" + (" or replace" if allow_replace else ""))
    for k in block:
        if k not in _LIST_BLOCK_KEYS:
            raise BoardLayerError(f"{label}: unknown key {k!r}")
        if not isinstance(block[k], list):
            raise BoardLayerError(f"{label}.{k} must be a list")
    if "replace" in block:
        if not allow_replace:
            raise BoardLayerError(f"{label}: 'replace' is only allowed in overrides.<role>")
        if for_skills:
            raise BoardLayerError(f"{label}: 'replace' is not allowed for skills")
        if "add" in block or "remove" in block:
            raise BoardLayerError(f"{label}: 'replace' cannot be combined with add/remove")


def _collect_relative_paths(doc: dict) -> list[str]:
    """All path-shaped values that must stay inside board home."""
    paths: list[str] = []
    # skills.add path form
    for section in ("skills", "toolsets"):
        if section in doc and isinstance(doc[section], dict):
            for item in doc[section].get("add", []) or []:
                if isinstance(item, str) and item.startswith((".", "/")):
                    paths.append(item)
    # soul.fragment, env.manifest
    soul = doc.get("soul")
    if isinstance(soul, dict) and "fragment" in soul and isinstance(soul["fragment"], str):
        p = soul["fragment"]
        if p.startswith((".", "/")):
            paths.append(p)
    env = doc.get("env")
    if isinstance(env, dict) and "manifest" in env and isinstance(env["manifest"], str):
        p = env["manifest"]
        if p.startswith((".", "/")):
            paths.append(p)
    # overrides per-role paths
    ov = doc.get("overrides")
    if isinstance(ov, dict):
        for role_cfg in ov.values():
            if not isinstance(role_cfg, dict):
                continue
            for section in ("skills", "toolsets"):
                if section in role_cfg and isinstance(role_cfg[section], dict):
                    for item in role_cfg[section].get("add", []) or []:
                        if isinstance(item, str) and item.startswith((".", "/")):
                            paths.append(item)
    return paths


# ── Slot rendering ─────────────────────────────────────────────────────────

def render_slots(text: str, slots: dict[str, str], *, strict: bool = True, board_slug: str = "") -> str:
    """Substitute {{board.*}} slots in *text*.

    - Only {{board.<name>}} is special; other {{ }} pass through.
    - Missing closing }} on same line → pass through (prose safety).
    - Slot values are literal, no recursive rendering.
    - strict=True: unknown slot → BoardLayerError.
    - strict=False (dry-run): unknown slot → inline [UNFILLED SLOT ...] marker.
    """
    # Process line-by-line so an unclosed {{board. without }} on that line passes through.
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        # Only consider slots that have a closing }} on THIS line (RFC 6.2)
        def _repl(m: re.Match) -> str:
            name = m.group(1)
            if name in slots:
                return str(slots[name])
            if strict:
                raise BoardLayerError(
                    f"unfilled slot {{{{board.{name}}}}} — define soul.slots.{name} in {board_slug + '/' if board_slug else ''}board.yaml"
                )
            return f"[UNFILLED SLOT {{{{board.{name}}}}} — define soul.slots.{name} in {board_slug + '/' if board_slug else ''}board.yaml]"

        # Replace only tokens where both {{board. and }} are on this line
        # _SLOT_RE already requires }}, so unclosed ones are naturally skipped.
        line = _SLOT_RE.sub(_repl, line)
        out.append(line)
    return "\n".join(out)


# ── EffectiveProfile ───────────────────────────────────────────────────────

@dataclass
class EffectiveProfile:
    """Result of compose(role, board). Carries resolved values + provenance.

    Fields that are None / empty mean "use role's own".
    """

    role: str
    board: str | None  # None = unbound (zero-change path)
    is_layered: bool = False
    # Resolved scalar-ish
    model: str | None = None
    provider: str | None = None
    memory_provider: str | None = None
    memory_bank: str | None = None
    # Lists — effective values after delta-union
    skills_add: list[str] = field(default_factory=list)
    skills_remove: list[str] = field(default_factory=list)
    toolsets_add: list[str] = field(default_factory=list)
    toolsets_remove: list[str] = field(default_factory=list)
    toolsets_replace: list[str] | None = None  # set only via overrides replace
    # SOUL
    soul_text: str | None = None  # effective composed SOUL (role + fragment + slots rendered)
    soul_provenance: str = ""  # e.g. "role:pinned" / "board:alpha/SOUL.md"
    # Env manifest path (rendering is env-layer's job; we just expose it)
    env_manifest: str | None = None
    # Capability
    boards_capability: str | None = None  # "all" or None
    boards_capability_granted: bool = False
    # Pin set that was applied
    pinned_keys: set[str] = field(default_factory=set)
    # Provenance per key class
    provenance: dict[str, str] = field(default_factory=dict)
    # Raw layers for downstream consumers (e.g. profile effective renderer)
    board_doc: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


def _load_role_config(role: str) -> dict[str, Any]:
    """Load role's config.yaml dict (empty if missing)."""
    from hermes_constants import get_hermes_home

    cfg_path = Path(get_hermes_home()) / "profiles" / role / "config.yaml"
    alt = Path(get_hermes_home()) / "config.yaml" if role == "default" else None
    for p in (cfg_path, alt):
        if p and p.is_file():  # config-reader: ok -- board_layer mirrors role config for compose; canonical store is config_backend, this is a layered overlay read of the role home file
            try:
                return yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}  # config-reader: ok -- same overlay read as above
            except Exception:  # health: allow BLE001 -- fail-open overlay read: missing role config is not fatal, compose falls back
                return {}
    # Fallback: try hermes_cli.config.load_config under profile scope
    # For direct unit tests we just return whatever is on disk.
    return {}


def _load_role_soul(role: str) -> str:
    from hermes_constants import get_hermes_home

    for base in (Path(get_hermes_home()) / "profiles" / role, Path(get_hermes_home())):
        p = base / "SOUL.md"
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8-sig").strip()
            except OSError:
                return ""
    return ""


def _parse_pin_set(role_cfg: dict[str, Any]) -> set[str]:
    boards = role_cfg.get("boards")
    if not isinstance(boards, dict):
        return set()
    pin = boards.get("pin")
    if pin is None:
        return set()
    if not isinstance(pin, list):
        raise BoardLayerError(f"role config: boards.pin must be a list, got {type(pin).__name__}")
    if len(pin) == 1 and pin[0] == "*":
        return set(ALLOWED_PINS) | {"*"}
    out: set[str] = set()
    for entry in pin:
        if not isinstance(entry, str):
            raise BoardLayerError(f"role config: boards.pin entry {entry!r} must be a string")
        if entry not in ALLOWED_PINS:
            raise BoardLayerError(f"role config: unknown pin key {entry!r} (allowed: {sorted(ALLOWED_PINS)} + '*')")
        out.add(entry)
    return out


def _parse_capability(role_cfg: dict[str, Any]) -> tuple[str | None, bool]:
    boards = role_cfg.get("boards")
    if not isinstance(boards, dict):
        return None, False
    cap = boards.get("capability")
    if cap is None:
        return None, False
    if cap == "all":
        granted = bool(boards.get("granted_by") or boards.get("granted_at"))
        return "all", granted
    return None, False


def _effective_list(
    role_values: list[str],
    base_block: dict | None,
    override_block: dict | None,
    *,
    pinned: bool,
) -> tuple[list[str], list[str], list[str], list[str] | None]:
    """Delta-union for a list key. Returns (effective, add, remove, replace).

    When pinned, returns role_values untouched.
    """
    if pinned:
        return list(role_values), [], [], None
    if override_block and "replace" in override_block:
        return list(override_block["replace"]), [], [], list(override_block["replace"])
    base_add = (base_block or {}).get("add", []) or []
    base_remove = (base_block or {}).get("remove", []) or []
    ov_add = (override_block or {}).get("add", []) or []
    ov_remove = (override_block or {}).get("remove", []) or []
    # RFC §9.3 formula: (role ∪ base.add − base.remove ∪ override.add − override.remove)
    # Apply base.remove before override.add so override can re-add what base removed.
    after_base = [v for v in list(role_values) + list(base_add) if v not in set(base_remove)]
    ordered: list[str] = []
    seen: set[str] = set()
    for v in after_base + list(ov_add):
        if v not in seen and v not in set(ov_remove):
            seen.add(v)
            ordered.append(v)
    add = list(base_add) + list(ov_add)
    remove = list(base_remove) + list(ov_remove)
    return ordered, add, remove, None


def compose(  # health: allow CC -- board-layer composition is phased per RFC; validate already extracted, further split deferred
    role: str,
    board: str | None,
    *,
    strict_slots: bool = True,
) -> EffectiveProfile:
    """Produce the EffectiveProfile for (role, board|None).

    Zero-change guarantee: if board is None or not layered, returns an
    EffectiveProfile whose resolved fields mirror the role alone (is_layered=False).
    """
    from hermes_constants import PROFILE_ID_RE

    if not PROFILE_ID_RE.match(role):
        raise BoardLayerError(f"invalid role name {role!r}")

    role_cfg = _load_role_config(role)
    role_soul = _load_role_soul(role)

    # Unbound / unlayered → zero-change, but slot-bearing SOUL with strict is an error (RFC §6.3)
    if not board or not is_layered_board(board):
        if strict_slots and _SLOT_RE.search(role_soul):
            raise BoardLayerError(
                f"unfilled slot in role {role!r} SOUL with no board — "
                f"define soul.slots in board.yaml or launch with a board that provides them"
            )
        cap, granted = _parse_capability(role_cfg)
        # Even unlayered we surface boards:all capability parsed from role config
        return EffectiveProfile(
            role=role,
            board=board,
            is_layered=False,
            soul_text=role_soul if role_soul else None,
            soul_provenance="role" if role_soul else "",
            boards_capability=cap,
            boards_capability_granted=granted,
            provenance={},
        )

    board_doc = load_board_yaml(board)
    pinned = _parse_pin_set(role_cfg)
    is_fully_pinned = "*" in pinned

    def is_pinned(key: str) -> bool:
        return is_fully_pinned or key in pinned

    ep = EffectiveProfile(role=role, board=board, is_layered=True, board_doc=board_doc, pinned_keys=pinned)

    # Capability (role-side)
    cap, granted = _parse_capability(role_cfg)
    ep.boards_capability = cap
    ep.boards_capability_granted = granted

    # Roles allowlist — warning if role not listed (RFC OQ3 provisional: warning not error)
    roles_allowlist = board_doc.get("roles")
    if isinstance(roles_allowlist, list) and role not in roles_allowlist:
        ep.warnings.append(f"role {role!r} is not in board {board!r} roles allowlist")

    # Overrides for this role
    overrides = (board_doc.get("overrides") or {}).get(role) or {}
    base_skills = board_doc.get("skills")
    base_toolsets = board_doc.get("toolsets")
    ov_skills = overrides.get("skills")
    ov_toolsets = overrides.get("toolsets")

    # Model / provider — only via overrides (base has no model); pin blocks
    if is_pinned("model"):
        ep.provenance["model"] = "role:pinned"
    else:
        if "model" in overrides:
            ep.model = overrides["model"]
            ep.provenance["model"] = f"board:{board}/overrides.{role}.model"
        elif "provider" in overrides:
            ep.provider = overrides["provider"]
            ep.provenance["provider"] = f"board:{board}/overrides.{role}.provider"
        # provider as companion to model override
        if "provider" in overrides and "model" in overrides:
            ep.provider = overrides["provider"]

    # Memory
    if is_pinned("memory"):
        ep.provenance["memory"] = "role:pinned"
    else:
        mem_base = board_doc.get("memory") or {}
        mem_ov = overrides.get("memory") or {}
        # override wins over base
        merged_mem = {**mem_base, **mem_ov}
        if "provider" in merged_mem:
            ep.memory_provider = merged_mem["provider"]
            ep.provenance["memory.provider"] = f"board:{board}"
        if "bank" in merged_mem:
            ep.memory_bank = merged_mem["bank"]
            ep.provenance["memory.bank"] = f"board:{board}"
        # default bank when layered and not explicitly set: board-<slug>-<role> (RFC 8.3)
        if not ep.memory_bank:
            # Only set default bank if board is layered (we are in layered branch)
            # RFC says default is board-<slug>-<role> when no explicit bank
            # But don't override if mem was pinned — already handled.
            # We set it always in layered mode so consumers have a value.
            if "bank" not in merged_mem:
                ep.memory_bank = f"board-{board}-{role}"
                ep.provenance["memory.bank"] = "derived:board-<slug>-<role>"

    # Skills — delta-union
    if is_pinned("skills"):
        ep.provenance["skills"] = "role:pinned"
    else:
        # role's current skills list — read from config if present
        role_skills = []
        # config may have skills as list or not present
        raw_skills = role_cfg.get("skills")
        if isinstance(raw_skills, list):
            role_skills = raw_skills
        _eff, add, rem, _rep = _effective_list(role_skills, base_skills, ov_skills, pinned=False)
        ep.skills_add = add
        ep.skills_remove = rem
        # For skills rep is always None (forbidden)
        if add or rem:
            ep.provenance["skills"] = f"board:{board}"

    # Toolsets — delta-union with replace at overrides
    if is_pinned("toolsets"):
        ep.provenance["toolsets"] = "role:pinned"
    else:
        role_toolsets: list[str] = []
        raw_ts = role_cfg.get("toolsets")
        if isinstance(raw_ts, list):
            role_toolsets = raw_ts
        elif isinstance(role_cfg.get("toolsets"), dict):
            # some configs have toolsets as dict — treat as empty for now
            role_toolsets = []
        _eff_ts, add_ts, rem_ts, rep_ts = _effective_list(role_toolsets, base_toolsets, ov_toolsets, pinned=False)
        ep.toolsets_add = add_ts
        ep.toolsets_remove = rem_ts
        ep.toolsets_replace = rep_ts
        if add_ts or rem_ts or rep_ts is not None:
            ep.provenance["toolsets"] = f"board:{board}"

    # Env
    if is_pinned("env"):
        ep.provenance["env"] = "role:pinned"
    else:
        env_cfg = board_doc.get("env")
        if isinstance(env_cfg, dict) and "manifest" in env_cfg:
            ep.env_manifest = env_cfg["manifest"]
            ep.provenance["env"] = f"board:{board}/env.manifest"

    # SOUL
    if is_pinned("soul"):
        ep.soul_text = role_soul if role_soul else None
        ep.soul_provenance = "role:pinned"
        ep.provenance["soul"] = "role:pinned"
    else:
        fragment = ""
        soul_cfg = board_doc.get("soul") or {}
        frag_ref = soul_cfg.get("fragment", "./SOUL.md")
        # frag_ref is a path relative to board home; default ./SOUL.md
        if frag_ref:
            from hermes_cli.kanban_db import board_dir

            frag_path = (board_dir(board) / frag_ref.lstrip("./")).resolve() if isinstance(frag_ref, str) else None
            # Also try literal relative join for "./SOUL.md" style
            if frag_path and not frag_path.is_file():
                # fallback: board_dir / frag_ref without stripping
                alt = (board_dir(board) / frag_ref).resolve() if isinstance(frag_ref, str) else None
                if alt and alt.is_file():
                    frag_path = alt
            if frag_path and frag_path.is_file():
                try:
                    fragment = frag_path.read_text(encoding="utf-8-sig").strip()
                except OSError:
                    fragment = ""
        # Compose
        if role_soul and fragment:
            raw_soul = role_soul + "\n\n" + fragment
            ep.soul_provenance = f"role + board:{board}/SOUL.md"
        elif fragment:
            raw_soul = fragment
            ep.soul_provenance = f"board:{board}/SOUL.md"
        elif role_soul:
            raw_soul = role_soul
            ep.soul_provenance = "role"
        else:
            raw_soul = ""
            ep.soul_provenance = ""
        # Slot substitution
        slots = soul_cfg.get("slots") or {} if isinstance(soul_cfg, dict) else {}
        if not isinstance(slots, dict):
            slots = {}
        # Normalize slot values to str
        str_slots = {k: str(v) for k, v in slots.items()}
        if raw_soul and str_slots:
            raw_soul = render_slots(raw_soul, str_slots, strict=strict_slots, board_slug=board)
        elif raw_soul and _SLOT_RE.search(raw_soul):
            # Role SOUL has slots but board defines none — strict fails, tolerant marks
            raw_soul = render_slots(raw_soul, str_slots, strict=strict_slots, board_slug=board)
        ep.soul_text = raw_soul if raw_soul else None
        if raw_soul:
            ep.provenance["soul"] = ep.soul_provenance

    # Extraneous slots warning: board defines slot no role uses
    if ep.soul_text is not None and isinstance(board_doc.get("soul"), dict):
        defined_slots = set((board_doc["soul"].get("slots") or {}).keys())
        if defined_slots:
            used_in_role = set(_SLOT_RE.findall(role_soul))
            extraneous = defined_slots - used_in_role
            if extraneous:
                ep.warnings.append(f"board {board!r} defines unused slots: {sorted(extraneous)}")

    # Pin set
    ep.pinned_keys = pinned

    return ep
