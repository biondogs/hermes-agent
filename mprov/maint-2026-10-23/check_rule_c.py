#!/usr/bin/env python3
"""Rule C mechanical check: every filed body <=150 words, five sections in order."""
import re, sys, pathlib

WS = pathlib.Path("/home/arch/.hermes/kanban/boards/software-co/workspaces/t_43e4e008")
PACKS = {"APPROVED-FILING-CC.md": 11, "APPROVED-FILING-JS.md": 14,
         "APPROVED-FILING-SCR.md": 8, "APPROVED-FILING-MASH.md": 3}
SECTIONS = ["symptom:", "evidence:", "root cause:", "proposed fix:", "severity:"]
LABEL_RE = re.compile(r"^### ([A-Z0-9-]+) — labels: `([^`]*)`$", re.M)

ok = True
total = 0
words_all = []
for fname, expected in PACKS.items():
    text = (WS / fname).read_text()
    blocks = re.findall(r"```text\n(.*?)```", text, re.S)
    ids = [m[0] for m in LABEL_RE.findall(text)]
    labels = [m[1] for m in LABEL_RE.findall(text)]
    print(f"== {fname}: {len(blocks)} bodies (expected {expected}), ids={ids}")
    if len(blocks) != expected or len(ids) != expected:
        ok = False; print("  !! count mismatch")
    for bid, body, lab in zip(ids, blocks, labels):
        wc = len(body.split())
        words_all.append((wc, bid))
        flat = " ".join(body.splitlines())
        pos = [flat.find(s) for s in SECTIONS]
        ordered = all(p >= 0 for p in pos) and pos == sorted(pos)
        starts = flat.startswith("symptom:")
        if wc > 150 or not ordered or not starts:
            ok = False
            print(f"  !! {bid}: words={wc} ordered={ordered} starts_ok={starts}")
        # label sanity
        if "review-found" not in lab or not re.search(r"s[1-4]-(blocker|functional|robustness|hygiene)", lab):
            ok = False; print(f"  !! {bid}: bad labels '{lab}'")
        total += 1

words_all.sort(reverse=True)
print(f"\nTotal bodies checked: {total}")
print("Top-5 wordiest:", words_all[:5])
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
