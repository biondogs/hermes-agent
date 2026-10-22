"""R2 receipt: enabled built-in toolsets must be exactly kDB [kanban, memory,
session_search, web] for each of the three butlers."""
import re
import subprocess
import sys

ALLOWED = {"kanban", "memory", "session_search", "web"}
BUTLERS = ["g02-butler", "swco-butler", "sjproto-butler"]

ok = True
for butler in BUTLERS:
    r = subprocess.run(["hermes", "-p", butler, "tools", "list"],
                       capture_output=True, text=True, timeout=120)
    out = r.stdout + r.stderr
    # only the built-in cli section (stop before plugin toolsets)
    builtin = out.split("Plugin toolsets")[0]
    enabled = set(re.findall(r"enabled\s+([\w-]+)", builtin))
    verdict = "PASS" if enabled == ALLOWED else f"FAIL enabled={sorted(enabled)}"
    print(f"{butler} R2 tools: {verdict}")
    ok = ok and (enabled == ALLOWED)
sys.exit(0 if ok else 1)
