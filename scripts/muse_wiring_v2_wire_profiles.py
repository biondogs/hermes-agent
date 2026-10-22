#!/usr/bin/env python3
"""MUSE-WIRING-V2 Leg B: wire default=muse on strength-matched mechanical
profiles. Keeps a per-profile verbatim prior-block for the rollback manifest.

Non-negotiable edge cases:
- reject if the profile's default is not qwen38-flash-fp8 + custom:LiteLLM
  (guards against wiring an orchestrator/judgment seat by mistake)
- reject profiles matching the judgment-seat name law
- skip (idempotent) profiles already migrated
- EXPLICIT context_length pin from the serving config: 262144
- preserve original YAML formatting via targeted text edits, NOT a full
  yaml.safe_dump rewrite (a dump would reflow every long line and list
  indent in the file - cosmetic churn that breaks byte-comparisons and
  review diffs; verified on sw-dev-a where a dump rewrote 50 lines)
"""
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

PROFILES_ROOT = Path("/home/arch/.hermes/profiles")
BACKUP_ROOT = Path("/tmp/muse-wiring-v2/profile-backups")
CTX_PIN = 262144
WIRED = [
    "kanban-worker",
    "g01-scribe",
    "g02-scribe",
    "sw-docs",
    "sw-dev-a",
    "sw-dev-b",
    "sw-qa",
    "sw-devops",
]
BANNED_SUBSTR = ("orchestrator", "reviewer", "auditor", "planner", "architect", "judge")
EXPECTED_DEFAULT = "qwen38-flash-fp8"
EXPECTED_PROVIDER = "custom:LiteLLM"


def text_patch_model_block(raw, ctx_pin=CTX_PIN):
    """Targeted textual edits inside the leading `model:` block ONLY."""
    m = re.match(r"^(model:\n)((?:[ \t]+.*\n|\n)*?)(?=(\w|#))", raw, re.M)
    if not m:
        return None
    head, block = m.group(1), m.group(2)
    if "  default: muse\n" in block:
        return raw  # already wired
    new_block = block.replace(f"  default: {EXPECTED_DEFAULT}\n", "  default: muse\n", 1)
    if new_block == block:
        return None  # unexpected default
    if "  context_length:" in new_block:
        new_block = re.sub(
            r"  context_length: \d+\n", f"  context_length: {ctx_pin}\n",
            new_block, count=1,
        )
    else:
        new_block += f"  context_length: {ctx_pin}\n"
    return head + new_block + raw[m.end(2):]


def providers_models_insert(raw, ctx_pin=CTX_PIN):
    """Insert `muse:` under providers.litellm.models with the ctx pin,
    keeping the file's own list-item indentation style."""
    mm = re.search(r"(\n([ \t]+)models:\n((?:\2[ \t]+.*\n|\n)*))", raw)
    if not mm or "muse:" in mm.group(3):
        return raw  # no models map (nothing to pin) or already present
    indent2 = mm.group(2) + "  "
    return raw[: mm.end(1)] + f"{indent2}muse:\n{indent2}  context_length: {ctx_pin}\n" + raw[mm.end(1):]


def fallback_append(raw):
    if "\nfallback_model:" in raw:
        return raw
    return (
        raw.rstrip("\n")
        + "\n\n# MUSE-WIRING-V2 (temp lane) - fallback chain: if the muse upstream\n"
        + "# is down, fall back to qwen38-flash-fp8 via the same LiteLLM provider.\n"
        + "fallback_model:\n  - provider: LiteLLM\n    model: qwen38-flash-fp8\n"
    )


def wire(profile):
    cfg_path = PROFILES_ROOT / profile / "config.yaml"
    raw = cfg_path.read_text()
    cfg = yaml.safe_load(raw)

    for bad in BANNED_SUBSTR:
        if bad in profile:
            return ("REFUSED-BANNED-SEAT", profile)

    model = cfg.get("model", {})
    if model.get("default") == "muse":
        return ("ALREADY-WIRED-SKIP", profile)
    if model.get("default") != EXPECTED_DEFAULT or model.get("provider") != EXPECTED_PROVIDER:
        return ("REFUSED-UNEXPECTED-PRIOR", profile, model.get("default"), model.get("provider"))

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_ROOT / f"{profile}.config.yaml.pre-muse"
    if not backup.exists():
        shutil.copy2(cfg_path, backup)

    prior = {
        "model": json.dumps(cfg.get("model", {}), indent=2),
        "fallback_model": json.dumps(cfg.get("fallback_model")),
        "providers_litellm": json.dumps(cfg.get("providers", {}).get("litellm", {}), indent=2),
    }

    new_raw = text_patch_model_block(raw)
    if new_raw is None:
        return ("REFUSED-MODEL-BLOCK-NOT-MATCHED", profile)
    new_raw = providers_models_insert(new_raw)
    new_raw = fallback_append(new_raw)

    # validate: parseable AND exactly the intended semantic changes
    new_cfg = yaml.safe_load(new_raw)
    assert new_cfg["model"]["default"] == "muse"
    assert new_cfg["model"]["context_length"] == CTX_PIN
    assert new_cfg["model"]["provider"] == EXPECTED_PROVIDER
    assert new_cfg.get("fallback_model") == [{"provider": "LiteLLM", "model": "qwen38-flash-fp8"}]
    assert new_cfg["providers"]["litellm"]["models"].get("muse", {}).get(
        "context_length"
    ) in (CTX_PIN, None) or "muse" not in cfg.get("providers", {}).get("litellm", {}).get("models", {})
    shared = set(cfg) & set(new_cfg)
    drift = [
        k
        for k in shared
        if k not in ("model", "providers", "fallback_model")
        and cfg[k] != new_cfg[k]
    ]
    assert not drift, f"unexpected drift: {drift}"
    assert cfg["providers"]["litellm"]["api"] == new_cfg["providers"]["litellm"]["api"]
    diff_models = {
        k: (cfg["providers"]["litellm"]["models"].get(k), new_cfg["providers"]["litellm"]["models"].get(k))
        for k in set(cfg["providers"]["litellm"]["models"]) | set(new_cfg["providers"]["litellm"]["models"])
    }
    changed_models = {k: v for k, v in diff_models.items() if v[0] != v[1]}
    assert set(changed_models) <= {"muse"}, f"unexpected model-map changes: {changed_models}"

    cfg_path.write_text(new_raw)
    return ("WIRED", profile, prior)


def main():
    report = {}
    for p in WIRED:
        report[p] = wire(p)
        print(report[p][0], p)
    (BACKUP_ROOT / "report.json").write_text(json.dumps(report, indent=2))
    print("backups:", BACKUP_ROOT)


if __name__ == "__main__":
    main()
