#!/usr/bin/env python3
"""fix-placement.py — move the LITELLM law section above '## references' in both
docker-compose-litellm-proxy SKILL.md copies (it was inserted after the header
because the anchor line sits inside the references section)."""

from pathlib import Path

FILES = [
    Path("/home/arch/.hermes/skills/devops/docker-compose-litellm-proxy/SKILL.md"),
    Path("/home/arch/.hermes/profiles/sw-devops/skills/devops/docker-compose-litellm-proxy/SKILL.md"),
]

START = "## LITELLM-YAML LAW"
HEADER = "## references"

for f in FILES:
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
    s = next(i for i, ln in enumerate(lines) if ln.startswith(START))
    e = s
    while e < len(lines) and lines[e].strip():
        e += 1
    # law block = lines[s:e] (incl. any trailing blank line e lands on)
    block = lines[s:e]
    if not block[-1].endswith("\n\n"):
        block = block[:]
    # remove block, then re-insert before the references header
    rest = lines[:s] + lines[e:]
    h = next(i for i, ln in enumerate(rest) if ln.strip() == HEADER)
    new = rest[:h] + block + ["\n"] + rest[h:]
    # collapse possible triple blank lines around the surgery
    out = "".join(new)
    while "\n\n\n\n" in out:
        out = out.replace("\n\n\n\n", "\n\n\n")
    f.write_text(out, encoding="utf-8")
    # report
    lines2 = f.read_text(encoding="utf-8").splitlines()
    ls = [i for i, ln in enumerate(lines2, 1) if ln.startswith(START)]
    lh = [i for i, ln in enumerate(lines2, 1) if ln.strip() == HEADER]
    print(f"{f}: law@{ls} references@{lh}")
