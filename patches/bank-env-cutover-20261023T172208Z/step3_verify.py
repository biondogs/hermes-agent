#!/usr/bin/env python3
"""ENV-BANK-CUTOVER step 3: fleet-wide verification sweep.

- readback every profile's effective bank (config.json carrier + active .env pin check)
- assert no profile binds to a detached mixed pool
- write the full intended-state table receipt
"""
import json
from pathlib import Path

TS = "20261023T172208Z"
BACKUP = Path(f"/home/arch/kanban-backups/env-bank-cutover-{TS}")
PROFILES = Path("/home/arch/.hermes/profiles")
MIXED = {"hb-infra-release", "hb-inference-bench", "Hermes q38", "hb-synapse-sdk"}

table = []
violations = []
for d in sorted(PROFILES.iterdir()):
    if not d.is_dir():
        continue
    f = d / "hindsight" / "config.json"
    env = d / ".env"
    bank = None
    if f.exists():
        cfg = json.loads(f.read_text())
        bank = cfg.get("bank_id")
    pin = None
    if env.exists():
        for line in env.read_text().splitlines():
            s = line.strip()
            if s.startswith("HINDSIGHT_BANK_ID="):
                pin = s.split("=", 1)[1].strip()
    table.append({"profile": d.name, "bank_id": bank, "active_env_pin": pin})
    if pin:
        violations.append(f"{d.name}: ACTIVE .env pin {pin} overrides config (#5171)")
    if bank in MIXED:
        violations.append(f"{d.name}: still bound to mixed pool {bank}")

(BACKUP / "post-flip-binding-table.json").write_text(json.dumps(table, indent=2))

print(f"profiles scanned: {len(table)}")
print(f"violations: {len(violations)}")
for v in violations:
    print("  ", v)

by_bank = {}
for row in table:
    by_bank.setdefault(row["bank_id"], []).append(row["profile"])
print("\nbank -> bound profiles:")
for bank in sorted(by_bank, key=lambda b: (b is None, b or "")):
    ps = by_bank[bank]
    print(f"  {bank!s:30} ({len(ps):2}): {', '.join(sorted(ps)[:8])}{' ...' if len(ps) > 8 else ''}")
