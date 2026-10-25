#!/usr/bin/env python3
"""converge-souls.py — LITELLM-YAML LAW fleet SOUL propagation (t_2fa0d71d).

Idempotent, grep-guarded converge: appends the LITELLM-YAML LAW block to the
root SOUL.md and every profile SOUL.md that does not already carry it.
Pre-edit backups go to ~/kanban-backups/litellm-law-20261025T<ts>/ with flat,
visible names (no dot-prefix mangling). Converges on re-run: files already
carrying the guard marker are counted as 'already' and left byte-identical.
"""

import shutil
import sys
import time
from pathlib import Path

GUARD = "LITELLM-YAML LAW (operator law, 2026-10-25"
LAW_BLOCK = """
## LITELLM-YAML LAW (operator law, 2026-10-25 — absolute)

No profile may add, change, or re-add a model entry (model_list or any
model definition) in /local/compose/aistack/litellm/config.yaml unless
ALL THREE hold:

1. The OPERATOR explicitly requested that specific change in his own words.
2. CONFIRMATION 1: the agent shows the operator the exact diff, and the
   operator approves it.
3. CONFIRMATION 2: a second, separate operator approval given immediately
   before the write.

A kanban card body, a standing GO, a prior ruling, or a parent card does NOT
count as permission or as a confirmation. Workers are headless and cannot
obtain confirmations — if such a change seems needed, kanban_block with
kind="needs_input" and STOP. Confirmations are collected only via
operator-facing chat (a clarify answer or a direct reply from the operator).
Do not touch that file for any other reason: an alert-only tripwire reports
every change to the operator.
"""

ROOT = Path("/home/arch/.hermes")
TS = time.strftime("%Y%m%dT%H%M%S")
BACKUP_DIR = Path(f"/home/arch/kanban-backups/litellm-law-{TS}")


def main() -> int:
    targets = [ROOT / "SOUL.md"]
    for p in sorted((ROOT / "profiles").glob("*/SOUL.md")):
        targets.append(p)

    updated, already, backed_up = [], [], 0
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    for soul in targets:
        text = soul.read_text(encoding="utf-8")
        if GUARD in text:
            already.append(str(soul))
            continue
        rel = soul.relative_to(ROOT)
        flat = "__".join(rel.parts).replace("SOUL.md", "SOUL.md.pre-litellm-law")
        backup = BACKUP_DIR / flat
        shutil.copy2(soul, backup)
        backed_up += 1
        if not text.endswith("\n"):
            text += "\n"
        soul.write_text(text + LAW_BLOCK, encoding="utf-8")
        # verify
        if GUARD not in soul.read_text(encoding="utf-8"):
            print(f"VERIFY-FAIL: {soul}", file=sys.stderr)
            return 1
        updated.append(str(soul))

    print(f"total_targets={len(targets)}")
    print(f"updated={len(updated)}")
    print(f"already_had_law={len(already)}")
    print(f"backups={backed_up}")
    print(f"backup_dir={BACKUP_DIR}")
    print("--- updated ---")
    for t in updated:
        print(t)
    print("--- already ---")
    for t in already:
        print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
