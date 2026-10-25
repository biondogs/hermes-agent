#!/usr/bin/env python3
"""converge-deny.py — LITELLM-YAML LAW enforcement layer (t_2fa0d71d item 4).

Adds the approvals.deny glob '*aistack/litellm/config.yaml*' to the ROOT home
and every profile home that has a config.yaml. Mechanism (tools/approval_floors.py
_match_user_deny_rule): fnmatch globs matched case-insensitively over the same
normalized/deobfuscated command variants the dangerous-pattern detector uses,
and they fire BEFORE yolo / approvals.mode=off — i.e. an unconditional
agent-side block on any shell command touching that path, in every session.

Idempotent: homes already carrying the glob are skipped. Existing deny lists
(if any) are preserved and merged.
"""

import json
import subprocess
import sys
from pathlib import Path

GLOB = "*aistack/litellm/config.yaml*"
HOMES = [Path("/home/arch/.hermes")]
HOMES += sorted(p for p in Path("/home/arch/.hermes/profiles").iterdir() if (p / "config.yaml").exists())

updated, already, skipped = [], [], []
for home in HOMES:
    env = {"HERMES_HOME": str(home), "PATH": "/home/arch/.local/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/home/arch"}
    r = subprocess.run(["hermes", "config", "get", "approvals.deny"],
                       capture_output=True, text=True, env=env)
    current = []
    out = (r.stdout or "").strip()
    if out and out not in ("None", "null", ""):
        try:
            parsed = json.loads(out)
            current = parsed if isinstance(parsed, list) else []
        except Exception:
            current = []
    if GLOB in current:
        already.append(str(home))
        continue
    new = current + [GLOB]
    r2 = subprocess.run(["hermes", "config", "set", "approvals.deny", json.dumps(new)],
                        capture_output=True, text=True, env=env)
    if r2.returncode != 0:
        skipped.append((str(home), r2.stderr.strip() or r2.stdout.strip()))
        continue
    updated.append(str(home))

print(f"total_homes_with_config={len(HOMES)}")
print(f"set={len(updated)} already_had={len(already)} failed={len(skipped)}")
for h in updated:
    print("SET  ", h)
for h in skipped:
    print("FAIL ", h)
if skipped:
    sys.exit(1)
