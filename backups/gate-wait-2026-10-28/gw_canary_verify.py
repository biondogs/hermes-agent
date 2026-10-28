import hashlib, subprocess
from pathlib import Path
P = Path("/home/arch/.hermes/profiles")
canaries = ["sjproto-butler", "sjp-ops", "sw-docs", "kanban-worker"]
BUTLER_GUARD = "(GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1\u2013R3)"
WORKER_GUARD = "GATE-WAIT PATTERN \u2014 link-before-block (fleet law since 2026-10-28"
OLD_ITEM3 = ("3. If the request names prerequisites on this board, encode them with "
             "`parents=[...]` at create time (never gate-then-link).")
NEW_SUFFIX = "A worker that must wait on a card it did not create at create time must"
G02_ANCHOR = "## Board Discipline (fleet-wide default since 2026-10-22"
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
ok = True
for c in canaries:
    t = (P / c / "SOUL.md").read_text()
    if c.endswith("butler"):
        good = BUTLER_GUARD in t and NEW_SUFFIX in t and t.count(BUTLER_GUARD) == 1
    else:
        h = hashlib.sha256(extract_block(t, G02_ANCHOR).encode()).hexdigest()
        good = WORKER_GUARD in t and h == EXPECT_NEW
        print(f"{c}: block hash {h[:16]}… match={h == EXPECT_NEW}")
    ok &= good
    print(f"{c}: guard-present={good}")
print("CANARY READBACK:", "ALL PASS" if ok else "FAILED")
