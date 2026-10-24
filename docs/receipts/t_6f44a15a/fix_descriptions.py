#!/usr/bin/env python3
"""AS-BUILT-REMEDIATION-1 (t_6f44a15a): fix mis-copied agent.description fields
in distiller (F1) and sw-ux (F2) config.yaml. Surgical single-line splices only,
with pre-edit backups and hard guarantees that nothing else changed."""
import os, shutil, datetime, json, sys

BACKUP_ROOT = os.path.expanduser("~/.hermes/config-backups")
ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bdir = os.path.join(BACKUP_ROOT, f"desc-fix-{ts}")
os.makedirs(bdir, exist_ok=True)

NEW = {
    "distiller": ("Outbound artifact and sanity/distillation gate: reviews artifacts a lane "
        "produces before they cross toward a repository or upstream audience (commits, patches, "
        "PRs, issues, comments, messages) for patch-to-spec match, minimality, repo etiquette, "
        "message hygiene, and leak scanning; returns PASS or REJECT with numbered, concrete, "
        "verifiable fixes. Memory-light by design: judges form, fit, and footprint only. "
        "Never authors or applies fixes, never pushes/merges/publishes, never profile/board/fleet meta-work."),
    "sw-ux": ("Front-End & UX Engineer: turns card specs into interfaces (components, pages, "
        "styling, interaction, accessibility) against the repo's design-system tokens, owning the "
        "visual verification loop (local serve, dogfood browse, browser_vision screenshots at named "
        "breakpoints) and recording style decisions as design-md ADRs for sibling lanes. "
        "Never backend services, API design, or data modeling; never merges or deploys; never sw-dev-a/b lane cards."),
}

receipts = {}
for prof, desc in NEW.items():
    cfg = os.path.expanduser(f"~/.hermes/profiles/{prof}/config.yaml")
    assert os.path.isfile(cfg), f"missing {cfg}"
    with open(cfg) as f:
        before = f.read()

    bup = os.path.join(bdir, f"{prof}-config.yaml")
    shutil.copy2(cfg, bup)

    lines = before.splitlines(keepends=True)
    in_agent = False
    idx = None
    for i, ln in enumerate(lines):
        if ln.rstrip("\n") == "agent:":
            in_agent = True
            continue
        if in_agent:
            s = ln.strip()
            if s and not ln[0].isspace():
                in_agent = False
                continue
            if s.startswith("description:"):
                idx = i
                break
    if idx is None:
        sys.exit(f"ABORT: no agent.description found in {prof}; nothing written")

    old_line = lines[idx]
    escaped = desc.replace("'", "''")
    new_line = f"  description: '{escaped}'\n"
    lines[idx] = new_line
    after = "".join(lines)

    # Guarantees before write
    assert after.count("description:") == before.count("description:")
    assert len(after.splitlines()) == len(before.splitlines())
    assert after.replace(new_line, old_line, 1) == before, "splice is not reversible -> bug"

    with open(cfg, "w") as f:
        f.write(after)

    # Readback
    with open(cfg) as f:
        reread = f.read()
    assert reread == after
    receipts[prof] = {
        "backup": bup,
        "old": old_line.strip(),
        "new": new_line.strip(),
        "nlines": (len(before.splitlines()), len(reread.splitlines())),
    }

print("BACKUP_DIR:", bdir)
for k, v in receipts.items():
    print(f"\n=== {k} ({v['nlines'][0]} -> {v['nlines'][1]} lines) ===")
    print("OLD:", v["old"])
    print("NEW:", v["new"])
print("\nOK: both profiles spliced, readback verified")
