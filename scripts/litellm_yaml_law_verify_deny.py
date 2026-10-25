#!/usr/bin/env python3
"""verify-deny.py — functional proof that approvals.deny blocks commands
touching the aistack litellm config.yaml, for unattended profiles (t_2fa0d71d)."""

import os
import subprocess
import sys

PATH_ = "/local/compose/aistack/litellm/config.yaml"
CASES = [
    # (HERMES_HOME, command, expected substring in verdict or None=fail-any)
    ("/home/arch/.hermes/profiles/sw-devops", f"sed -i s/old/new/ {PATH_}", "user-deny"),
    ("/home/arch/.hermes/profiles/kanban-worker", f"cp /tmp/newcfg {PATH_}", "user-deny"),
    ("/home/arch/.hermes/profiles/research", f"cat {PATH_}", "user-deny"),
    ("/home/arch/.hermes", f"echo x >> {PATH_}", "user-deny"),
    # deobfuscation variant: quote-splitting must NOT sidestep the rule
    ("/home/arch/.hermes/profiles/kanban-worker",
     f'echo x >> /local/compose/aist""ack/litellm/config.yaml', "user-deny"),
    # unrelated command stays unaffected
    ("/home/arch/.hermes/profiles/research", "ls /tmp", "allow"),
]

fails = 0
for home, cmd, expect in CASES:
    env = dict(os.environ)
    env["HERMES_HOME"] = home
    env["PATH"] = "/home/arch/.local/bin:/usr/local/bin:/usr/bin:/bin"
    r = subprocess.run(["hermes", "approvals", "test", cmd],
                       capture_output=True, text=True, env=env)
    blob = (r.stdout or "") + (r.stderr or "")
    verdict = None
    for line in blob.splitlines():
        if '"verdict"' in line or "verdict" in line.split(":")[0]:
            verdict = line.strip()
    ok = expect in blob
    if not ok:
        fails += 1
    print(f"[{'PASS' if ok else 'FAIL'}] home={home.replace('/home/arch/.hermes/', '') or 'ROOT'} expect={expect}")
    print(f"       {verdict or blob[:200]!r}")

sys.exit(1 if fails else 0)
