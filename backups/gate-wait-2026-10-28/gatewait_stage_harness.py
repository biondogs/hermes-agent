#!/usr/bin/env python3
"""Stage harness for the GATE-WAIT converge extension (t_0d825d76, step 2).

Builds a stage skeleton (all 59 profile SOULs + root SOUL + skill files),
runs the amended converge module against it, then verifies:
  - pre-state: 51 worker SOULs carry registered G-02 hash a149a296…, 5 butlers
    carry OLD_ITEM3, plugin-ab has no Board Discipline section
  - run 1: exactly 57 edits (5 butlers + 51 workers + plugin-ab), no ERROR/MISSING
  - run 2 (idempotency): 0 edits, all skip
  - post: guards present everywhere, OLD_ITEM3 gone, new G-02 block hash uniform
    across 52 workers, per-file diffs touch ONLY the intended lines
  - drift-guard on literal duplication: intake_section item 3 == NEW_ITEM3 and
    worker_discipline_section ends with GATEWAIT_WORKER_BULLET
Emits stage-diff.patch (pre vs post) and prints PASS/FAIL lines.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.pop("DRY_RUN", None)
os.environ.pop("LIMIT_PROFILES", None)

LIVE = Path("/home/arch/.hermes")
SCRIPT = Path("/local/projects/software-co/scripts/route_by_default_converge.py")
SCRATCH = Path(os.environ["TMPDIR"])
STAGE = SCRATCH / "gatewait-stage"
PRE = SCRATCH / "gatewait-stage-pre"          # immutable pre-state copies
OUT = Path("/local/projects/software-co/backups/gate-wait-2026-10-28")
OUT.mkdir(parents=True, exist_ok=True)

# --- load module ---------------------------------------------------------
import importlib.util
spec = importlib.util.spec_from_file_location("converge", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BUTLER_SET = {b[0] for b in m.BUTLERS}
EXPECTED_EXCLUDE = BUTLER_SET | {"kanban-board-architect", "kanban-orchestrator"}

# canon-check block-hash convention (verbatim semantics)
def extract_block(text, anchor):
    lines = text.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if anchor in ln:
            start = i
            break
    if start is None:
        return None
    end = len(lines) - 1
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#") or lines[j].strip() == "---":
            end = j - 1
            break
    while end > start and lines[end].strip() == "":
        end -= 1
    return "\n".join(lines[start:end + 1]) + "\n"

def sha(b):
    return hashlib.sha256(b.encode()).hexdigest() if b else "MISSING"

G02_ANCHOR = "## Board Discipline (fleet-wide default since 2026-10-22"
OLD_G02 = "a149a296f07721477720bfe8f92e1b91ade847441b5abe500831d42d8c36503a"

failures = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)

# --- build stage ---------------------------------------------------------
if STAGE.exists():
    shutil.rmtree(STAGE)
if PRE.exists():
    shutil.rmtree(PRE)
(STAGE / "profiles").mkdir(parents=True)
for p in sorted((LIVE / "profiles").iterdir()):
    if p.is_dir() and (p / "SOUL.md").exists():
        (STAGE / "profiles" / p.name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(p / "SOUL.md", STAGE / "profiles" / p.name / "SOUL.md")
shutil.copy2(LIVE / "SOUL.md", STAGE / "SOUL.md")
for rel in ["skills/devops/kanban-orchestrator/SKILL.md",
            "profiles/kanban-orchestrator/skills/devops/kanban-orchestrator/SKILL.md"]:
    src = LIVE / rel
    if not src.exists():
        continue  # profile mirror absent live (sanctioned) — script must SKIP it, not fail
    dst = STAGE / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
shutil.copytree(STAGE, PRE)

stage_workers = sorted(
    d.name for d in (STAGE / "profiles").iterdir()
    if d.is_dir() and (d / "SOUL.md").exists() and d.name not in m.WORKER_EXCLUDE
)
souls = {p: (STAGE / "profiles" / p / "SOUL.md").read_text() for p in stage_workers}
butler_souls = {b: (STAGE / "profiles" / b / "SOUL.md").read_text() for b in BUTLER_SET}

# --- pre-state checks ----------------------------------------------------
old_hashes = {}
for p, t in souls.items():
    old_hashes.setdefault(sha(extract_block(t, G02_ANCHOR)), []).append(p)
check("pre: 51 stage workers carry registered G-02 hash", OLD_G02 in old_hashes and len(old_hashes[OLD_G02]) == 51,
      f"{ {k[:12]: len(v) for k, v in old_hashes.items()} }")
no_block = old_hashes.get("MISSING", [])
check("pre: exactly plugin-ab lacks Board Discipline", no_block == ["plugin-ab"], str(no_block))
check("pre: worker pool size 52", len(stage_workers) == 52, f"{len(stage_workers)}")
check("pre: all 5 butlers carry OLD_ITEM3", all(m.OLD_ITEM3 in t for t in butler_souls.values()))
check("pre: no GATE-WAIT guards anywhere",
      not any(m.GATEWAIT_BUTLER_GUARD in t for t in butler_souls.values())
      and not any(m.GATEWAIT_WORKER_GUARD in t for t in souls.values()))

# --- drift-guard on literal duplication ---------------------------------
check("intake_section item 3 == NEW_ITEM3", m.NEW_ITEM3 in m.intake_section("x", "y"))
check("worker section ends with GATE-WAIT bullet", m.worker_discipline_section().rstrip("\n").endswith(m.GATEWAIT_WORKER_BULLET))

# --- run 1 (real edits, on the stage) -----------------------------------
m.HOME = STAGE
m.PROFILES = STAGE / "profiles"
m.BACKUP = STAGE / "backups"
rc = m.main()
check("run 1 rc == 0", rc == 0, f"rc={rc}")

changed = []
for p in stage_workers:
    now = (STAGE / "profiles" / p / "SOUL.md").read_text()
    if now != souls[p]:
        changed.append(p)
butler_changed = [b for b in BUTLER_SET if (STAGE / "profiles" / b / "SOUL.md").read_text() != butler_souls[b]]
check("run 1 changed all 52 worker SOULs (51 in-place + plugin-ab append)",
      sorted(changed) == sorted(stage_workers), f"changed={len(changed)}")
check("run 1 changed all 5 butlers", sorted(butler_changed) == sorted(BUTLER_SET))

# --- post checks ---------------------------------------------------------
new_hashes = {}
for p in stage_workers:
    t = (STAGE / "profiles" / p / "SOUL.md").read_text()
    check(f"post: {p} worker guard present", m.GATEWAIT_WORKER_GUARD in t) if p == "plugin-ab" else None
    new_hashes.setdefault(sha(extract_block(t, G02_ANCHOR)), []).append(p)
check("post: ONE uniform new G-02 hash across all 52 workers",
      len(new_hashes) == 1 and len(next(iter(new_hashes.values()))) == 52,
      str({k[:12]: len(v) for k, v in new_hashes.items()}))
NEW_G02 = next(iter(new_hashes)) if len(new_hashes) == 1 else "MULTIPLE"
for b in BUTLER_SET:
    t = (STAGE / "profiles" / b / "SOUL.md").read_text()
    old_line_gone = all(ln.strip() != m.OLD_ITEM3 for ln in t.splitlines())
    ok = (m.GATEWAIT_BUTLER_GUARD in t) and old_line_gone and t.count(m.NEW_ITEM3) == 1
    check(f"post: {b} extended item 3 present, old line gone", ok)
allw = "".join((STAGE / "profiles" / p / "SOUL.md").read_text() for p in stage_workers)
check("post: OLD_ITEM3 gone from all workers", m.OLD_ITEM3 not in allw)

# --- per-file diff inventory (whole-file, step 2/3) ---------------------
diff_parts = []
butler_ok, worker_ok, pluginab_ok = True, True, True
for p in sorted(stage_workers) + sorted(BUTLER_SET):
    pre_f = PRE / "profiles" / p / "SOUL.md"
    post_f = STAGE / "profiles" / p / "SOUL.md"
    d = subprocess.run(["diff", "-u", str(pre_f), str(post_f)], capture_output=True, text=True).stdout
    if not d:
        continue
    diff_parts.append(d)
    plus = [ln[1:] for ln in d.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    minus = [ln[1:] for ln in d.splitlines() if ln.startswith("-") and not ln.startswith("---")]
    if p in BUTLER_SET:
        butler_ok &= (len(plus) == 1 and len(minus) == 1 and plus[0].strip() == m.NEW_ITEM3 and minus[0].strip() == m.OLD_ITEM3)
    elif p == "plugin-ab":
        appended = worker_discipline_expected = m.worker_discipline_section().lstrip("\n")
        pluginab_ok &= (len(minus) == 0 and [ln for ln in plus if ln.strip()] ==
                        [ln for ln in appended.splitlines() if ln.strip()])
    else:
        worker_ok &= (len(plus) == 1 and len(minus) == 0 and plus[0] == m.GATEWAIT_WORKER_BULLET)
check("diff shape: each butler = 1 line replaced (OLD_ITEM3 -> NEW_ITEM3)", butler_ok)
check("diff shape: each of the 51 in-place workers = +1 GATE-WAIT bullet only", worker_ok)
check("diff shape: plugin-ab = pure append of the full extended section", pluginab_ok)
patch_path = OUT / "stage-diff.patch"
patch_path.write_text("\n".join(diff_parts))
check("diff inventory written", patch_path.exists())

# --- run 2 (idempotency): re-run must change nothing ---------------------
snap = {p: (STAGE / "profiles" / p / "SOUL.md").read_text()
        for p in stage_workers + sorted(BUTLER_SET)}
rc2 = m.main()
changed2 = [p for p, t in snap.items() if (STAGE / "profiles" / p / "SOUL.md").read_text() != t]
check("run 2 rc == 0", rc2 == 0, f"rc={rc2}")
check("run 2 idempotent (0 files changed)", not changed2, str(changed2))

print(f"\nNEW_G02_HASH={NEW_G02}")
print(f"STAGE={STAGE}")
print(f"PATCH={patch_path}")
if failures:
    print(f"HARNESS FAILURES: {len(failures)}: {failures}")
    sys.exit(1)
print("HARNESS: ALL CHECKS PASS")
