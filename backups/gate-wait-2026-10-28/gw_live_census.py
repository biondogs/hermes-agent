import hashlib, subprocess
from pathlib import Path
LIVE = Path("/home/arch/.hermes/profiles")
PRE = Path("/local/projects/software-co/backups/gate-wait-2026-10-28/pre/profiles")
OUT = Path("/local/projects/software-co/backups/gate-wait-2026-10-28/live-diff.patch")
BUTLERS = ["g01-butler", "g02-butler", "gaudi-butler", "swco-butler", "sjproto-butler"]
META = {"kanban-board-architect", "kanban-orchestrator"}
BUTLER_GUARD = "(GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1\u2013R3)"
WORKER_GUARD = "GATE-WAIT PATTERN \u2014 link-before-block (fleet law since 2026-10-28"
OLD_ITEM3 = "3. If the request names prerequisites on this board, encode them with `parents=[...]` at create time (never gate-then-link)."
NEW_ITEM3 = OLD_ITEM3 + " A worker that must wait on a card it did not create at create time must `kanban_link(parent, self)` **before** blocking or parking on that dependency (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1\u2013R3)."
NEW_ITEM3 = ("3. If the request names prerequisites on this board, encode them with "
             "`parents=[...]` at create time (never gate-then-link). "
             "A worker that must wait on a card it did not create at create time must "
             "`kanban_link(parent, self)` **before** blocking or parking on that "
             "dependency (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1\u2013R3).")
G02_ANCHOR = "## Board Discipline (fleet-wide default since 2026-10-22"
OLD_HASH = "a149a296f07721477720bfe8f92e1b91ade847441b5abe500831d42d8c36503a"
EXPECT_NEW = "2036d5c2c3401f50446828a91d4b9754e5853f4c856adea84899c196eda643d2"

def extract_block(text, anchor):
    lines = text.split("\n"); start = None
    for i, ln in enumerate(lines):
        if anchor in ln: start = i; break
    if start is None: return None
    end = len(lines) - 1
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#") or lines[j].strip() == "---": end = j - 1; break
    while end > start and lines[end].strip() == "": end -= 1
    return "\n".join(lines[start:end + 1]) + "\n"

workers = sorted(d.name for d in LIVE.iterdir()
                 if d.is_dir() and (d/"SOUL.md").exists()
                 and d.name not in META and d.name not in BUTLERS)
but_ok = True
for b in BUTLERS:
    t = (LIVE/b/"SOUL.md").read_text()
    gone = all(ln.strip() != OLD_ITEM3 for ln in t.splitlines())
    but_ok &= (t.count(NEW_ITEM3) == 1 and BUTLER_GUARD in t and gone)
    print(f"butler {b}: extended-item3={t.count(NEW_ITEM3) == 1} old-line-gone={gone}")

hashes = {}
for w in workers:
    t = (LIVE/w/"SOUL.md").read_text()
    hashes.setdefault(hashlib.sha256(extract_block(t, G02_ANCHOR).encode()).hexdigest(), []).append(w)
print(f"worker G-02 block hash census: {[(k[:12], len(v)) for k, v in hashes.items()]}")
new_ok = list(hashes) == [EXPECT_NEW] and len(hashes[EXPECT_NEW]) == 52
old_gone = OLD_HASH not in hashes
guard_all = all(WORKER_GUARD in (LIVE/w/"SOUL.md").read_text() for w in workers)
print(f"uniform new hash 52/52: {new_ok}; old hash gone: {old_gone}; guard in all 52: {guard_all}")

# whole-file diff vs pre-snapshot for every one of the 57 saved files
diffs, extra_delta = [], []
for f in sorted(PRE.glob("*.SOUL.md")):
    prof = f.name[:-len(".SOUL.md")]
    cur = LIVE/prof/"SOUL.md"
    d = subprocess.run(["diff", "-u", str(f), str(cur)], capture_output=True, text=True).stdout
    if d:
        diffs.append(d)
OUT.write_text("\n".join(diffs))
changed = set()
for d in diffs:
    for ln in d.splitlines():
        if ln.startswith("+++"):
            changed.add(Path(ln[3:].split("\t")[0]).name[:-len(".SOUL.md")])
print(f"changed files vs pre-snapshot: {len(changed)} (expect 57)")
plus = sum(1 for d in diffs for ln in d.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
minus = sum(1 for d in diffs for ln in d.splitlines() if ln.startswith("-") and not ln.startswith("---"))
# expected: butlers 5x(1+1), workers 51x(+1), plugin-ab append(+9 or so)
print(f"diff lines: +{plus} -{minus} (expect 5 butler replaces + 52 worker additions incl. plugin-ab full-section append)")
print("CENSUS:", "ALL PASS" if (but_ok and new_ok and old_gone and guard_all and len(changed) == 57) else "FAILED")
