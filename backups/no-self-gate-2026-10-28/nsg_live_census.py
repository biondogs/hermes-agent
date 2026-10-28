#!/usr/bin/env python3
"""Live census for the NO-SELF-GATE sync (t_1a66c496, fleet-change step 7)."""
import hashlib
import subprocess
import sys
from pathlib import Path

LIVE = Path("/home/arch/.hermes")
STAGE = Path("/home/arch/.hermes/profiles/kanban-board-architect/cache/scratch/nsg-stage")
PRE = Path("/local/projects/software-co/backups/no-self-gate-2026-10-28/pre")
OUT = Path("/local/projects/software-co/backups/no-self-gate-2026-10-28")
SCRIPT = Path("/local/projects/software-co/scripts/route_by_default_converge.py")

import importlib.util
spec = importlib.util.spec_from_file_location("converge", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BUTLERS = [b[0] for b in m.BUTLERS]
G02_ANCHOR = "## Board Discipline (fleet-wide default since 2026-10-22"
REG_OLD = "2036d5c2c3401f50446828a91d4b9754e5853f4c856adea84899c196eda643d2"
EXPECT_NEW = "c07b6d6bd53539230512e8cee16e065c1c6daaed9d62034a531e7625cf558530"

def extract_block(text, anchor):
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if anchor in ln)
    end = len(lines) - 1
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#") or lines[j].strip() == "---":
            end = j - 1
            break
    while end > start and lines[end].strip() == "":
        end -= 1
    return "\n".join(lines[start:end + 1]) + "\n"

workers = sorted(
    d.name for d in (LIVE / "profiles").iterdir()
    if d.is_dir() and (d / "SOUL.md").exists() and d.name not in m.WORKER_EXCLUDE
)

failures = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    if not cond:
        failures.append(name)

# 1. butler sentence census
butler_ok = [b for b in BUTLERS if m.NSG_BUTLER_GUARD in (LIVE / "profiles" / b / "SOUL.md").read_text()]
check("census: 5/5 butler SOULs carry the appended item-3 sentence", len(butler_ok) == 5, str(butler_ok))
check("census: each butler item 3 is exactly ITEM3_NSGLAW",
      all((LIVE / "profiles" / b / "SOUL.md").read_text().count(m.ITEM3_NSGLAW) == 1 for b in BUTLERS))

# 2. worker bullet census + uniform hash
nsg_workers = [p for p in workers if m.NSG_WORKER_GUARD in (LIVE / "profiles" / p / "SOUL.md").read_text()]
check("census: 52/52 worker SOULs carry the NO-SELF-GATE bullet",
      len(workers) == 52 and len(nsg_workers) == 52, f"{len(nsg_workers)}/{len(workers)}")
hashes = {}
for p in workers:
    t = (LIVE / "profiles" / p / "SOUL.md").read_text()
    h = hashlib.sha256(extract_block(t, G02_ANCHOR).encode()).hexdigest()
    hashes.setdefault(h, []).append(p)
check("census: ONE uniform new G-02 block hash on 52/52 carriers",
      len(hashes) == 1 and next(iter(hashes)) == EXPECT_NEW and len(next(iter(hashes.values()))) == 52,
      str({k[:12]: len(v) for k, v in hashes.items()}))
check("census: old registered hash 2036d5c2… absent", EXPECT_NEW != REG_OLD and REG_OLD not in hashes)
check("census: bullets ordered GATE-WAIT before NO-SELF-GATE in all 52",
      all((LIVE / "profiles" / p / "SOUL.md").read_text().find(m.GATEWAIT_WORKER_GUARD)
          < (LIVE / "profiles" / p / "SOUL.md").read_text().find(m.NSG_WORKER_GUARD) for p in workers))

# 3. distiller carrier 3
dt = (LIVE / "profiles" / "distiller" / "SOUL.md").read_text()
check("census: distiller SOUL carries the R6.4 precondition", "NO-SELF-GATE precondition (R6.4)" in dt)

# 4. byte-identical to stage for ALL 57 targets
mismatch = [p for p in workers + BUTLERS
            if not (STAGE / "profiles" / p / "SOUL.md").read_bytes()
            == (LIVE / "profiles" / p / "SOUL.md").read_bytes()]
check("census: all 57 live files byte-identical to stage-computed state", not mismatch, str(mismatch))

# 5. nothing else changed: iterate ALL live SOULs, any whose content differs
#    from pre-snapshot must be in the 57; any outside must equal pre (no snapshot = untouched)
changed_set, extra = [], []
for d in sorted((LIVE / "profiles").iterdir()):
    if not d.is_dir() or not (d / "SOUL.md").exists():
        continue
    name, cur = d.name, (d / "SOUL.md").read_bytes()
    pre_f = PRE / "profiles" / name / "SOUL.md"
    if pre_f.exists():
        if cur != pre_f.read_bytes():
            changed_set.append(name)
    else:
        extra.append(name)  # no pre-snapshot: must be untouched (excludes)
check("census: changed files == exactly the 57 targeted (I1 census)",
      sorted(changed_set) == sorted(workers + BUTLERS), f"changed={len(changed_set)}")
check("census: untargeted SOUL files (architect/orchestrator) untouched, plus root SOUL",
      sorted(extra) == ["kanban-board-architect", "kanban-orchestrator"], str(extra))

# 6. live-diff.patch (pre -> live) receipt
parts = []
for p in sorted(changed_set):
    d = subprocess.run(["diff", "-u", str(PRE / "profiles" / p / "SOUL.md"),
                        str(LIVE / "profiles" / p / "SOUL.md")],
                       capture_output=True, text=True).stdout
    if d:
        parts.append(d)
patch = OUT / "live-diff.patch"
patch.write_text("\n".join(parts))
plus_total = sum(1 for ln in "\n".join(parts).splitlines() if ln.startswith("+") and not ln.startswith("+++"))
minus_total = sum(1 for ln in "\n".join(parts).splitlines() if ln.startswith("-") and not ln.startswith("---"))
check(f"live-diff.patch written ({plus_total}+/ {minus_total}-)", patch.exists())
print(f"\nlive+={plus_total} live-={minus_total} files={len(parts)}")
if failures:
    print(f"CENSUS FAILURES: {failures}")
    sys.exit(1)
print("CENSUS: ALL CHECKS PASS")
