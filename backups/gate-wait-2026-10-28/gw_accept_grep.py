from pathlib import Path
src = Path("/local/projects/software-co/scripts/route_by_default_converge.py").read_text()
def body(name):
    start = src.index(f"def {name}")
    nxt = src.find("\ndef ", start + 1)
    return src[start:nxt]
ext_butler = "kanban_link(parent, self)` **before** blocking or parking on that dependency (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1\u2013R3)."
ext_worker = "kanban_link(parent, self)` BEFORE any block or park"
print("extended text in intake_section():", ext_butler in body("intake_section"))
print("extended text in worker_discipline_section():", ext_worker in body("worker_discipline_section"))
import subprocess
n = subprocess.run("grep -l 'GATE-WAIT PATTERN' /home/arch/.hermes/profiles/*/SOUL.md",
                   shell=True, capture_output=True, text=True).stdout.split()
print("live SOULs containing GATE-WAIT text:", len(n), "(expect 57 = 5 butlers + 52 workers)")
