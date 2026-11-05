"""Board layer validation — extracted from board_layer.py for CC ratchet."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def _check_version(doc, BoardLayerError):
    if "version" not in doc:
        raise BoardLayerError("board.yaml: missing required key 'version' (expected 1)")
    if doc["version"] != 1:
        raise BoardLayerError(f"board.yaml: unknown version {doc['version']!r} (only 1 is defined)")

def _check_top_level(doc, ALLOWED_BOARD_KEYS, BoardLayerError):
    for k in doc:
        if k.startswith("x-"):
            continue
        if k not in ALLOWED_BOARD_KEYS:
            raise BoardLayerError(f"board.yaml: unknown top-level key {k!r}")

def _check_roles(doc, _validate_profile_name, BoardLayerError):
    if "roles" not in doc:
        return
    roles = doc["roles"]
    if not isinstance(roles, list):
        raise BoardLayerError("board.yaml: 'roles' must be a list")
    for entry in roles:
        if not isinstance(entry, str) or not entry.strip():
            raise BoardLayerError(f"board.yaml: roles entry {entry!r} must be a non-empty string")
        _validate_profile_name(entry, field="roles")

def _check_memory(doc, BoardLayerError):
    if "memory" not in doc:
        return
    mem = doc["memory"]
    if not isinstance(mem, dict):
        raise BoardLayerError("board.yaml: 'memory' must be a mapping")
    for k in mem:
        if k not in {"provider", "bank"}:
            raise BoardLayerError(f"board.yaml: unknown memory key {k!r}")

def _check_lists(doc, _validate_list_block):
    for block_name in ("skills", "toolsets"):
        if block_name in doc:
            _validate_list_block(doc[block_name], f"board.yaml: '{block_name}'")

def _check_soul(doc, BoardLayerError):
    if "soul" not in doc:
        return
    soul = doc["soul"]
    if not isinstance(soul, dict):
        raise BoardLayerError("board.yaml: 'soul' must be a mapping")
    for k in soul:
        if k not in {"fragment", "slots"}:
            raise BoardLayerError(f"board.yaml: unknown soul key {k!r}")
    if "slots" in soul and not isinstance(soul["slots"], dict):
        raise BoardLayerError("board.yaml: 'soul.slots' must be a mapping")

def _check_env_meta(doc, BoardLayerError):
    if "env" in doc:
        env = doc["env"]
        if not isinstance(env, dict):
            raise BoardLayerError("board.yaml: 'env' must be a mapping")
        for k in env:
            if k not in {"manifest"}:
                raise BoardLayerError(f"board.yaml: unknown env key {k!r}")
    if "meta" in doc and not isinstance(doc["meta"], dict):
        raise BoardLayerError("board.yaml: 'meta' must be a mapping")

def _check_overrides(doc, _validate_profile_name, _validate_list_block, ALLOWED_OVERRIDE_KEYS, BoardLayerError):
    if "overrides" not in doc:
        return
    ov = doc["overrides"]
    if not isinstance(ov, dict):
        raise BoardLayerError("board.yaml: 'overrides' must be a mapping")
    for role_name, role_overrides in ov.items():
        _validate_profile_name(role_name, field="overrides")
        if not isinstance(role_overrides, dict):
            raise BoardLayerError(f"board.yaml: overrides.{role_name} must be a mapping")
        for k in role_overrides:
            if k.startswith("x-"):
                continue
            if k not in ALLOWED_OVERRIDE_KEYS:
                raise BoardLayerError(f"board.yaml: unknown key {k!r} in overrides.{role_name}")
        if "skills" in role_overrides:
            _validate_list_block(role_overrides["skills"], f"board.yaml: 'overrides.{role_name}.skills'", allow_replace=True, for_skills=True)
        if "toolsets" in role_overrides:
            _validate_list_block(role_overrides["toolsets"], f"board.yaml: 'overrides.{role_name}.toolsets'", allow_replace=True, for_skills=False)
        if "memory" in role_overrides:
            mv = role_overrides["memory"]
            if not isinstance(mv, dict):
                raise BoardLayerError(f"board.yaml: overrides.{role_name}.memory must be a mapping")
            for k in mv:
                if k not in {"provider", "bank"}:
                    raise BoardLayerError(f"board.yaml: unknown overrides.{role_name}.memory key {k!r}")
        _has_replace = any(isinstance(role_overrides.get(k), dict) and "replace" in role_overrides[k] for k in ("toolsets", "skills"))
        if ("model" in role_overrides or "provider" in role_overrides or _has_replace) and "reason" not in role_overrides:
            raise BoardLayerError(f"board.yaml: overrides.{role_name} touches model/provider/replace and requires a sibling 'reason:' key")

def _check_paths(doc, board_dir_path, _collect_relative_paths, BoardLayerError):
    if board_dir_path is None:
        return
    home = board_dir_path.resolve()
    for p in _collect_relative_paths(doc):
        resolved = (board_dir_path / p).resolve()
        try:
            resolved.relative_to(home)
        except ValueError:
            raise BoardLayerError(f"board.yaml: path {p!r} escapes the board home")

def validate_board_yaml_impl(doc, board_slug="", board_dir_path=None, *, _ctx=None):
    # _ctx carries parent module symbols
    from hermes_cli.board_layer import ALLOWED_BOARD_KEYS, ALLOWED_OVERRIDE_KEYS, BoardLayerError, _validate_profile_name, _validate_list_block, _collect_relative_paths
    _check_version(doc, BoardLayerError)
    _check_top_level(doc, ALLOWED_BOARD_KEYS, BoardLayerError)
    _check_roles(doc, _validate_profile_name, BoardLayerError)
    _check_memory(doc, BoardLayerError)
    _check_lists(doc, _validate_list_block)
    _check_soul(doc, BoardLayerError)
    _check_env_meta(doc, BoardLayerError)
    _check_overrides(doc, _validate_profile_name, _validate_list_block, ALLOWED_OVERRIDE_KEYS, BoardLayerError)
    _check_paths(doc, board_dir_path, _collect_relative_paths, BoardLayerError)
