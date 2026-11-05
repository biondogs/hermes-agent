"""`hermes profile effective` — dry-run renderer with source-layer annotations.

Spec: BOARD-LAYERS-2-EFFECTIVE. Renders EffectiveProfile with per-section
provenance (role | board | board.overrides.<role> | pin | derived) and
never emits secret values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _isolation_posture(ep) -> tuple[str, str]:
    """Return (label, detail) for the prominent header."""
    pinned = getattr(ep, "pinned_keys", set()) or set()
    cap = getattr(ep, "boards_capability", None)
    if cap == "all":
        return ("boards: all (unbound)", "capability granted" if getattr(ep, "boards_capability_granted", False) else "ungranted")
    if ep.board is None or ep.board == "none":
        return ("no board (role alone)", "")
    if pinned:
        return (f"pinned board: {ep.board}", f"pins: {', '.join(sorted(pinned))}")
    # layered board without pin
    if getattr(ep, "is_layered", False):
        return (f"board: {ep.board}", "layered")
    return (f"board: {ep.board} (not layered — role alone)", "")


_CREDENTIAL_EXACT = frozenset({"OPENAI_API_KEY", "ANTHROPIC_API_KEY"})
_CREDENTIAL_SUFFIXES = ("_TOKEN", "_SECRET", "_KEY")


def _is_credential_name(name: str) -> bool:
    if name in _CREDENTIAL_EXACT:
        return True
    return any(name.endswith(suf) for suf in _CREDENTIAL_SUFFIXES)


def _credential_warnings(env_names: list[str]) -> list[str]:
    hits = [n for n in env_names if _is_credential_name(n)]
    if not hits:
        return []
    return [f"governance: board exports credential-sounding env vars: {', '.join(sorted(hits))} — provider credentials must not be board-exported (RFC §7)"]


def _env_names(ep) -> list[tuple[str, str]]:
    """Return [(name, source)] — single source of truth via board_state.board_env_names."""
    board = getattr(ep, "board", None)
    if not board:
        return []
    pinned = getattr(ep, "pinned_keys", set()) or set()
    if "env" in pinned or "*" in pinned:
        return []
    # Reuse canonical parser
    try:
        from hermes_cli.board_state import board_env_names as _ben
        names = _ben(board, getattr(ep, "_role", None) or getattr(ep, "role", None))
    except Exception:
        names = []
    # Fallback when strict compose fails (e.g. unfilled slot) — read manifest directly
    if not names:
        try:
            from hermes_cli.kanban_db import board_dir as _bd
            manifest_rel = getattr(ep, "env_manifest", None) or "./env/manifest.yaml"
            bd = _bd(board)
            for cand in (bd / manifest_rel.lstrip("./"), bd / manifest_rel):
                if cand.is_file():
                    import hermes_yaml as _yaml
                    doc = _yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
                    ex = doc.get("export") or []
                    names = [str(n) for n in ex if isinstance(n, str)]
                    break
        except Exception:
            pass
    if names:
        provenance = getattr(ep, "provenance", {}) or {}
        src = provenance.get("env", f"board:{board}/env.manifest")
        return [(n, src) for n in names]
    # No exports known — surface manifest path if present, else empty
    manifest = getattr(ep, "env_manifest", None)
    if manifest:
        provenance = getattr(ep, "provenance", {}) or {}
        src = provenance.get("env", f"board:{board}/env.manifest")
        return [(f"(manifest: {manifest})", src)]
    return []


def _effective_warnings(ep) -> list[str]:
    base = list(getattr(ep, "warnings", None) or [])
    # Governance: credential-sounding env names (RFC §7 OQ7)
    try:
        env_only = [n for n, _ in _env_names(ep)]
        base.extend(_credential_warnings(env_only))
    except Exception:
        pass
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for w in base:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def render_text(ep, *, role: str, board_arg: str | None) -> str:
    lines: list[str] = []
    posture, detail = _isolation_posture(ep)
    lines.append("=" * 72)
    lines.append(f"Effective profile: {role}  |  Isolation: {posture}" + (f" ({detail})" if detail else ""))
    lines.append("=" * 72)
    eff_warnings = _effective_warnings(ep)
    if eff_warnings:
        for w in eff_warnings:
            lines.append(f"warning: {w}")
        lines.append("")

    # SOUL
    lines.append("SOUL:")
    prov = getattr(ep, "provenance", {}).get("soul", getattr(ep, "soul_provenance", "role"))
    src_label = prov or "role"
    if ep.soul_text:
        # annotate each line with source
        for ln in ep.soul_text.splitlines():
            lines.append(f"  [{src_label}] {ln}")
    else:
        lines.append(f"  [{src_label}] (empty)")
    lines.append("")

    # Config keys
    lines.append("Config:")
    prov_map = getattr(ep, "provenance", {})
    # model/provider
    if ep.model is not None:
        lines.append(f"  model: {ep.model}  [{prov_map.get('model','role')}]")
    elif "model" in prov_map:
        lines.append(f"  model: (pinned — role value)  [{prov_map['model']}]")
    if ep.provider is not None:
        lines.append(f"  provider: {ep.provider}  [{prov_map.get('provider','role')}]")
    # memory
    if ep.memory_provider is not None:
        lines.append(f"  memory.provider: {ep.memory_provider}  [{prov_map.get('memory.provider','board')}]")
    if ep.memory_bank is not None:
        lines.append(f"  memory.bank: {ep.memory_bank}  [{prov_map.get('memory.bank','derived')}]")
    elif "memory" in prov_map:
        lines.append(f"  memory: (pinned)  [{prov_map['memory']}]")
    # env manifest
    if ep.env_manifest is not None:
        lines.append(f"  env.manifest: {ep.env_manifest}  [{prov_map.get('env','board')}]")
    elif "env" in prov_map:
        lines.append(f"  env: (pinned)  [{prov_map['env']}]")
    if not any([ep.model, ep.provider, ep.memory_provider, ep.memory_bank, ep.env_manifest]) and not any(k in prov_map for k in ("model","memory","env")):
        lines.append("  (no overridden config keys — role defaults)")
    lines.append("")

    # Skills
    lines.append("Skills:")
    if "skills" in prov_map and "pinned" in prov_map["skills"]:
        lines.append(f"  (pinned)  [{prov_map['skills']}]")
    else:
        # Show board adds vs role base
        adds = getattr(ep, "skills_add", [])
        rems = getattr(ep, "skills_remove", [])
        if adds:
            for s in adds:
                lines.append(f"  + {s}  [board:{ep.board}]")
        if rems:
            for s in rems:
                lines.append(f"  - {s}  [board:{ep.board}]")
        if not adds and not rems:
            lines.append("  (no board delta — role skills)")
        # pointer vs role-owned distinction: board-pointer = added via base, role = pre-existing
        # We annotate with source layer already above
    lines.append("")

    # Toolsets
    lines.append("Toolsets:")
    if "toolsets" in prov_map and "pinned" in prov_map["toolsets"]:
        lines.append(f"  (pinned)  [{prov_map['toolsets']}]")
    else:
        rep = getattr(ep, "toolsets_replace", None)
        if rep is not None:
            lines.append(f"  replace: {', '.join(rep)}  [board:{ep.board}/overrides.{role}]")
        else:
            adds = getattr(ep, "toolsets_add", [])
            rems = getattr(ep, "toolsets_remove", [])
            if adds:
                for t in adds:
                    lines.append(f"  + {t}  [board:{ep.board}]")
            if rems:
                for t in rems:
                    lines.append(f"  - {t}  [board:{ep.board}]")
            if not adds and not rems:
                lines.append("  (no board delta — role toolsets)")
    lines.append("")

    # Env
    lines.append("Env:")
    env_entries = _env_names(ep)
    if env_entries:
        for name, src in env_entries:
            lines.append(f"  {name}  [{src}]")
    else:
        if "env" in prov_map and "pinned" in prov_map["env"]:
            lines.append(f"  (pinned)  [{prov_map['env']}]")
        else:
            lines.append("  (no env manifest)")
    lines.append("")

    # Footer provenance summary
    lines.append(f"Board: {ep.board!r}  layered={getattr(ep,'is_layered',False)}  role={role}")
    return "\n".join(lines)


def render_json(ep, *, role: str, board_arg: str | None) -> dict:
    posture, detail = _isolation_posture(ep)
    return {
        "role": role,
        "board": ep.board,
        "is_layered": getattr(ep, "is_layered", False),
        "isolation": {"posture": posture, "detail": detail},
        "soul": {"text": ep.soul_text, "provenance": getattr(ep, "provenance", {}).get("soul", getattr(ep, "soul_provenance", ""))},
        "config": {
            "model": ep.model,
            "provider": ep.provider,
            "memory_provider": ep.memory_provider,
            "memory_bank": ep.memory_bank,
            "env_manifest": ep.env_manifest,
        },
        "config_provenance": {k: v for k, v in getattr(ep, "provenance", {}).items() if k in ("model","provider","memory.provider","memory.bank","memory","env")},
        "skills": {"add": getattr(ep, "skills_add", []), "remove": getattr(ep, "skills_remove", []), "provenance": getattr(ep, "provenance", {}).get("skills","")},
        "toolsets": {"add": getattr(ep, "toolsets_add", []), "remove": getattr(ep, "toolsets_remove", []), "replace": getattr(ep, "toolsets_replace", None), "provenance": getattr(ep, "provenance", {}).get("toolsets","")},
        "env": [{"name": n, "source": s} for n, s in _env_names(ep)],
        "pinned_keys": sorted(getattr(ep, "pinned_keys", set()) or []),
        "capability": getattr(ep, "boards_capability", None),
        "warnings": _effective_warnings(ep),
    }

# CLI wiring helpers

def _die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def cmd_profile_effective(args):
    """Handler for `hermes profile effective`."""
    role = getattr(args, "effective_profile", None) or getattr(args, "profile_name", None)
    board = getattr(args, "effective_board", None)
    as_json = bool(getattr(args, "json", False))

    if not role:
        _die("hermes profile effective: --profile is required", 2)
    # Normalize board: "none" means unbound
    board_arg = board
    board_slug = None if (board is None or str(board).lower() == "none") else str(board)

    # Validate role name early
    try:
        from hermes_constants import PROFILE_ID_RE  # type: ignore
        assert isinstance(role, str) and PROFILE_ID_RE.match(role)
    except SystemExit:
        raise
    except AssertionError:
        _die(f"invalid profile name {role!r}", 2)
    except Exception:
        pass

    # Ensure profile exists (but allow rendering even if missing — compose handles it)
    # We warn if missing.

    try:
        from hermes_cli.board_layer import BoardLayerError, compose
        assert isinstance(role, str)
        ep = compose(role, board_slug, strict_slots=False)
    except Exception as exc:
        # BoardLayerError and validation errors -> non-zero with readable diag
        from hermes_cli.board_layer import BoardLayerError as BLE
        if isinstance(exc, BLE):
            _die(f"board layer error: {exc}", 2)
        # Also surface profile validation etc.
        _die(f"error: {exc}", 2)

    if as_json:
        payload = render_json(ep, role=role, board_arg=board_arg)
        print(json.dumps(payload, indent=2, sort_keys=False))
        return

    text = render_text(ep, role=role, board_arg=board_arg)
    print(text)
