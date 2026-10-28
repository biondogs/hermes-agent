#!/usr/bin/env python3
"""Stage harness for the NO-SELF-GATE converge extension (t_1a66c496, step 2).

Builds a stage skeleton (all live profile SOULs + root SOUL + skill files),
runs the amended converge module against it, then verifies:
  - pre: 52 workers carry registered G-02 hash 2036d5c2…, 5 butlers carry the
    GATE-WAIT item 3, zero NO-SELF-GATE guards anywhere
  - acceptance grep: the amended script carries the exact card texts for both
    carriers (NSG_WORKER_BULLET == card bullet; ITEM3_NSGLAW ends with the
    card's appended sentence)
  - run 1: exactly 57 edits (5 butlers item-3 replace + 52 workers +1 bullet),
    no ERROR/MISSING
  - run 2 (idempotency): 0 edits
  - post: NO-SELF-GATE guards everywhere, ONE uniform new G-02 block hash
    across 52 workers, per-file diffs touch ONLY the intended lines
  - carrier 3: distiller R6.4 pointer patch applied on the staged distiller
    SOUL, idempotent on re-run
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
STAGE = SCRATCH / "nsg-stage"
PRE = SCRATCH / "nsg-stage-pre"
OUT = Path("/local/projects/software-co/backups/no-self-gate-2026-10-28")
OUT.mkdir(parents=True, exist_ok=True)

import importlib.util
spec = importlib.util.spec_from_file_location("converge", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BUTLER_SET = {b[0] for b in m.BUTLERS}

# ---- exact card-quoted texts (t_1a66c496 body, verbatim) ----------------
CARD_NSG_BULLET = ("- NO-SELF-GATE (fleet law since 2026-10-28; "
                   "doc: software-co `docs/gate-wait-pattern-2026-10-28.md` R6): "
                   "a card whose title/body declares it a text/review GATE must "
                   "be assigned to an INDEPENDENT gate profile — `distiller` "
                   "for text gates, `sw-reviewer` for code review — never to the "
                   "creating lane or the author of the bytes under review. "
                   "A gate may not weaken its own check set: check sets come "
                   "from policy + operator directives; a deviation is a finding "
                   "to escalate, not to absorb. A PASS discovered to be "
                   "self-issued is void — stop the apply leg, annotate the "
                   "record, re-gate independently and make the new gate card "
                   "the apply card's true parent.")
CARD_NSG_SENTENCE = (" Gate cards are never assigned to the creating lane or "
                     "the bytes' author — assign text gates to `distiller`, "
                     "code-review gates to `sw-reviewer` (NO-SELF-GATE, same doc R6).")
CARD_DISTILLER_INSERT = ("   NO-SELF-GATE precondition (R6.4): if the gate card's assignee is not\n"
                         "   `distiller`, record NO verdict — comment exactly \"misassigned gate —\n"
                         "   reassign to distiller\" and block `needs_input` before any checklist run.")
DISTILLER_ANCHOR = ("1. `kanban_show()` the gate card; read its parent card (the work) and\n"
                    "   the artifact to be distilled.")
DISTILLER_GUARD = "NO-SELF-GATE precondition (R6.4)"

# canon-check block-hash convention (verbatim semantics, as in the script)
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
REG_G02 = "2036d5c2c3401f50446828a91d4b9754e5853f4c856adea84899c196eda643d2"

failures = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    if not cond:
        failures.append(name)

# --- acceptance grep (step: script contains both exact card texts) -------
script_text = SCRIPT.read_text()
check("accept: NSG_WORKER_BULLET == exact card bullet",
      m.NSG_WORKER_BULLET == CARD_NSG_BULLET)
check("accept: ITEM3_NSGLAW ends with exact card sentence",
      m.ITEM3_NSGLAW.endswith(CARD_NSG_SENTENCE) and m.ITEM3_NSGLAW.startswith(m.NEW_ITEM3))
check("accept: intake_section carries ITEM3_NSGLAW", m.ITEM3_NSGLAW in m.intake_section("x", "y"))
check("accept: worker section ends with NO-SELF-GATE bullet",
      m.worker_discipline_section().rstrip("\n").endswith(m.NSG_WORKER_BULLET))
check("accept: both texts present in script source (python-literal grep)",
      CARD_NSG_BULLET in script_text and CARD_NSG_SENTENCE.strip() in script_text)

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
for rel in ["skills/devops/kanban-orchestrator/SKILL.md"]:
    src = LIVE / rel
    if src.exists():
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
check("pre: all 52 stage workers carry registered G-02 hash",
      REG_G02 in old_hashes and len(old_hashes[REG_G02]) == 52,
      str({k[:12]: len(v) for k, v in old_hashes.items()}))
check("pre: worker pool size 52 (incl distiller)", len(stage_workers) == 52, f"{len(stage_workers)}")
check("pre: distiller in worker pool", "distiller" in stage_workers)
check("pre: all 5 butlers carry GATE-WAIT item 3",
      all(m.GATEWAIT_BUTLER_GUARD in t for t in butler_souls.values()))
check("pre: no NO-SELF-GATE guards anywhere",
      not any(m.NSG_BUTLER_GUARD in t for t in butler_souls.values())
      and not any(m.NSG_WORKER_GUARD in t for t in souls.values()))
check("pre: live butler item 3 == NEW_ITEM3 (replace will anchor)",
      all(m.NEW_ITEM3 in t for t in butler_souls.values()))

# --- run 1 (real edits, on the stage) -----------------------------------
m.HOME = STAGE
m.PROFILES = STAGE / "profiles"
m.BACKUP = STAGE / "backups"
rc = m.main()
check("run 1 rc == 0", rc == 0, f"rc={rc}")

changed = [p for p in stage_workers
           if (STAGE / "profiles" / p / "SOUL.md").read_text() != souls[p]]
butler_changed = [b for b in BUTLER_SET
                  if (STAGE / "profiles" / b / "SOUL.md").read_text() != butler_souls[b]]
check("run 1 changed all 52 worker SOULs", sorted(changed) == sorted(stage_workers), f"changed={len(changed)}")
check("run 1 changed all 5 butlers", sorted(butler_changed) == sorted(BUTLER_SET))

# --- post checks ---------------------------------------------------------
new_hashes = {}
for p in stage_workers:
    t = (STAGE / "profiles" / p / "SOUL.md").read_text()
    new_hashes.setdefault(sha(extract_block(t, G02_ANCHOR)), []).append(p)
check("post: ONE uniform new G-02 hash across all 52 workers",
      len(new_hashes) == 1 and len(next(iter(new_hashes.values()))) == 52,
      str({k[:12]: len(v) for k, v in new_hashes.items()}))
NEW_G02 = next(iter(new_hashes)) if len(new_hashes) == 1 else "MULTIPLE"
for b in BUTLER_SET:
    t = (STAGE / "profiles" / b / "SOUL.md").read_text()
    old_line_gone = all(ln.strip() != m.NEW_ITEM3 for ln in t.splitlines())
    ok = (m.NSG_BUTLER_GUARD in t) and old_line_gone and t.count(m.ITEM3_NSGLAW) == 1
    check(f"post: {b} NSGLAW item 3 present, GATEWAIT-only line gone", ok)
allw = "".join((STAGE / "profiles" / p / "SOUL.md").read_text() for p in stage_workers)
check("post: all 52 workers carry NSG_WORKER_GUARD", allw.count(m.NSG_WORKER_GUARD) == 52,
      f"{allw.count(m.NSG_WORKER_GUARD)}")
check("post: worker bullets ordered GATE-WAIT then NO-SELF-GATE",
      all(t.find(m.GATEWAIT_WORKER_GUARD) < t.find(m.NSG_WORKER_GUARD)
          for t in [(STAGE / "profiles" / p / "SOUL.md").read_text() for p in stage_workers]))

# --- carrier 3: distiller R6.4 pointer on the staged distiller SOUL ------
dp = STAGE / "profiles" / "distiller" / "SOUL.md"
dtext = dp.read_text()
check("c3 pre: distiller SOUL has anchor", DISTILLER_ANCHOR in dtext)
patcher = importlib.util.spec_from_file_location(
    "nsgdp", OUT / "nsg_distiller_patch.py")
dmod = importlib.util.module_from_spec(patcher)
try:
    patcher.loader.exec_module(dmod)
    dnew, act = dmod.patch_text(dtext)
except FileNotFoundError:
    sys.exit("FATAL: nsg_distiller_patch.py not yet written to OUT — write it first")
if act == "edit":
    dp.write_text(dnew)
dt2, act2 = dmod.patch_text(dp.read_text())
check("c3: distiller patch applied (edit)", act == "edit", act)
check("c3: distiller patch == exact card insert", CARD_DISTILLER_INSERT in dp.read_text())
check("c3: distiller patch idempotent (run 2 = skip)", act2 == "skip", act2)
dlines = dp.read_text().splitlines()
gi = next(i for i, ln in enumerate(dlines) if DISTILLER_GUARD in ln)
check("c3: pointer sits inside Process step 1 (after anchor, before step 2)",
      any("## Process" in ln for ln in dlines[:gi])
      and dlines[gi - 1].strip() == "the artifact to be distilled."
      and dlines[gi + 3].startswith("2."), f"line {gi}: {dlines[gi][:60]}")

# --- per-file diff inventory (whole-file, steps 2/3) ---------------------
diff_parts = []
butler_ok, worker_ok = True, True
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
        butler_ok &= (len(plus) == 1 and len(minus) == 1
                      and plus[0].strip() == m.ITEM3_NSGLAW and minus[0].strip() == m.NEW_ITEM3)
    elif p == "distiller":
        rest = [ln for ln in plus if ln != m.NSG_WORKER_BULLET]
        worker_ok &= (len(plus) == 4 and len(minus) == 0
                      and plus.count(m.NSG_WORKER_BULLET) == 1
                      and "".join(rest) == CARD_DISTILLER_INSERT.replace("\n", ""))
    else:
        worker_ok &= (len(plus) == 1 and len(minus) == 0 and plus[0] == m.NSG_WORKER_BULLET)
check("diff shape: each butler = 1 line replaced (GATEWAIT item3 -> NSGLAW item3)", butler_ok)
check("diff shape: each worker = +1 NO-SELF-GATE bullet only (distiller also +R6.4 pointer)", worker_ok)
patch_path = OUT / "stage-diff.patch"
patch_path.write_text("\n".join(diff_parts))
check("diff inventory written", patch_path.exists())

# --- run 2 (idempotency, includes carrier 3 re-check) --------------------
snap = {p: (STAGE / "profiles" / p / "SOUL.md").read_text()
        for p in stage_workers + sorted(BUTLER_SET)}
rc2 = m.main()
changed2 = [p for p, t in snap.items() if (STAGE / "profiles" / p / "SOUL.md").read_text() != t]
check("run 2 rc == 0", rc2 == 0, f"rc={rc2}")
check("run 2 idempotent (0 files changed, R6.4 pointer survives)", not changed2, str(changed2))

print(f"\nNEW_G02_HASH={NEW_G02}")
print(f"STAGE={STAGE}")
print(f"PATCH={patch_path}")
if failures:
    print(f"HARNESS FAILURES: {len(failures)}: {failures}")
    sys.exit(1)
print("HARNESS: ALL CHECKS PASS")
