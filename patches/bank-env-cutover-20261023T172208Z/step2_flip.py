#!/usr/bin/env python3
"""ENV-BANK-CUTOVER step 2: flip 38 fleet profile bindings to env-axis banks.

Edits hindsight/config.json only (config.json carrier governs — #5171 law:
.env HINDSIGHT_BANK_ID must stay unset). Idempotent: skips profiles already at
target. Writes receipts JSON to the backup dir.
"""
import json
from pathlib import Path

TS = "20261023T172208Z"
BACKUP = Path(f"/home/arch/kanban-backups/env-bank-cutover-{TS}")
PROFILES = Path("/home/arch/.hermes/profiles")

BINDING = {}
for fleet, bank in [
    ("g01", "g01-infra"),
    ("g02", "g02-infra"),
    ("sj", "skipjack-infra"),
    ("sjp", "skipjack-prototype-infra"),
]:
    for role in ["orchestrator", "planner", "auditor", "scribe", "ops", "watcher"]:
        BINDING[f"{fleet}-{role}"] = bank
for p in ["gaudi-orchestrator", "gaudi-planner", "gaudi-auditor", "gaudi-scribe", "gaudi-deployer"]:
    BINDING[p] = "gaudi-hpu"
for p in ["gaudi-analyst", "gaudi-benchrunner", "gaudi-watcher"]:
    BINDING[p] = "gaudi-hpu-perf"
for p in ["gaudi-arch", "gaudi-perfeng", "gaudi-synapse"]:
    BINDING[p] = "gaudi-hpu-sdk"
for p in ["gaudi-dockerops", "gaudi-sysadmin"]:
    BINDING[p] = "gaudi-hpu-hostops"
BINDING["gaudi-liaison"] = "gaudi-hpu-upstream"

receipts = []
flipped = skipped = 0
for profile, target in sorted(BINDING.items()):
    cfg_path = PROFILES / profile / "hindsight" / "config.json"
    env_path = PROFILES / profile / ".env"
    rec = {"profile": profile, "bank_id": None, "changed": False, "error": None}
    try:
        cfg = json.loads(cfg_path.read_text())
        old = cfg.get("bank_id")
        if old == target:
            skipped += 1
            rec.update({"bank_id": old, "changed": False})
            receipts.append(rec)
            continue
        # sanity: assert no active .env pin would override (#5171)
        active_pin = False
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                s = line.strip()
                if s.startswith("HINDSIGHT_BANK_ID="):
                    active_pin = True
        assert not active_pin, f"{profile}: ACTIVE .env HINDSIGHT_BANK_ID pin would override config!"
        # preserve budget/enabled from the existing banks entry
        budget, enabled = "mid", True
        for entry in (cfg.get("banks") or {}).values():
            budget = entry.get("budget", budget)
            enabled = entry.get("enabled", enabled)
            break
        cfg["bank_id"] = target
        cfg["banks"] = {target: {"bankId": target, "budget": budget, "enabled": enabled}}
        cfg_path.write_text(json.dumps(cfg, indent=2))
        # readback
        rb = json.loads(cfg_path.read_text())
        assert rb.get("bank_id") == target, "readback mismatch"
        rec.update({"bank_id": rb["bank_id"], "changed": True, "old_bank_id": old})
        flipped += 1 if old != target else 0
    except Exception as e:  # noqa: BLE001
        rec["error"] = str(e)
    receipts.append(rec)

(BACKUP / "flip-receipts.json").write_text(json.dumps(receipts, indent=2))
errs = [r for r in receipts if r["error"]]
print(f"flipped={flipped} already-at-target={skipped} errors={len(errs)}")
for r in errs:
    print("  ERROR:", r["profile"], r["error"])
