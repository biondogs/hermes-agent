#!/usr/bin/env python3
"""litellm-config-tripwire.py — alert-only change tripwire for the aistack
LiteLLM config.yaml (LITELLM-YAML LAW, operator law 2026-10-25, card t_2fa0d71d).

Cron driver (root registry, no-agent, telegram:8158007517). WATCHDOG PATTERN:
prints to stdout ONLY when the watched file CHANGED since the last run — the
cron delivers stdout only when non-empty, so silent == unchanged.

Alert contents: old/new sha256 + ADDED/REMOVED model names ONLY. Never file
contents, never keys, never URLs — the file's sensitive values (secrets, key
refs) are excluded by construction (regex extracts only `model_name:` values).

After alerting, the baseline REBASES to the new state so one change alerts
exactly once (the operator's response/revert is not re-alerted every 5 min).

Never edits the watched file. Self-test hooks (used by card t_2fa0d71d against
a COPY only): LITELLM_TRIPWIRE_TARGET, LITELLM_TRIPWIRE_STATE env overrides.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_TARGET = "/local/compose/aistack/litellm/config.yaml"
DEFAULT_STATE = "/home/arch/.hermes/state/litellm-config-tripwire.json"
MODEL_NAME_RE = re.compile(r"^\s*(?:-\s*)?model_name:\s*[\"']?([^\s\"']+)", re.MULTILINE)


def main() -> int:
    target = Path(os.environ.get("LITELLM_TRIPWIRE_TARGET") or DEFAULT_TARGET)
    state_path = Path(os.environ.get("LITELLM_TRIPWIRE_STATE") or DEFAULT_STATE)

    if not target.exists():
        print(f"⚠️ LITELLM TRIPWIRE: {target} IS MISSING (deleted or moved) — "
              "operator attention required. No auto-action taken.")
        return 0

    new_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    new_models = sorted(set(MODEL_NAME_RE.findall(target.read_text(encoding="utf-8", errors="replace"))))

    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = None
    else:
        state = None

    if state is None:
        # First-ever run: seed the baseline SILENTLY (alert-only watchdog; a
        # fresh install must not cry wolf on the file it was armed against).
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(
            {"sha256": new_sha, "models": new_models}, indent=1), encoding="utf-8")
        return 0

    if state.get("sha256") != new_sha:
        old_sha = (state or {}).get("sha256", "<no baseline>")
        old_models = (state or {}).get("models", [])
        added = [m for m in new_models if m not in old_models]
        removed = [m for m in old_models if m not in new_models]
        lines = [
            f"⚠️ LITELLM TRIPWIRE: {target} CHANGED",
            f"old sha256: {old_sha}",
            f"new sha256: {new_sha}",
        ]
        if added:
            lines.append("models ADDED: " + ", ".join(added))
        if removed:
            lines.append("models REMOVED: " + ", ".join(removed))
        if not added and not removed:
            lines.append(f"model names unchanged ({len(new_models)} entries) — "
                         "non-model config change (keys/settings)")
        lines.append("Per LITELLM-YAML LAW (2026-10-25): any model-entry change "
                     "needs the operator's explicit request + 2 confirmations. "
                     "Alert-only; no auto-revert. (model names only; secrets "
                     "never shown)")
        print("\n".join(lines))
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(
            {"sha256": new_sha, "models": new_models}, indent=1), encoding="utf-8")
        return 0

    # unchanged — silent (alert-only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
