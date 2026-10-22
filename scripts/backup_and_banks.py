"""BUTLERS-STAGE-3 step 1: timestamped backup of the three butler profiles'
pre-mutation state + idempotent creation of the three dedicated banks.

Read-only on success except: tarball under ~/kanban-backups/ and (only when a
bank is missing) a PUT upsert on the hindsight server.
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

PROFILES = os.path.expanduser("~/.hermes/profiles")
BUTLERS = ["g02-butler", "swco-butler", "sjproto-butler"]
BASE = "http://ga01:8888"
BACKUP_ROOT = os.path.expanduser("~/kanban-backups/butlers-stage-3")

BANK_MISSION = (
    "Isolated memory bank for the {b} Topology-B board butler "
    "({board} board front-end). Per-board butler banks per operator-approved "
    "policy — butler memories stay isolated, never in shared banks."
)
BOARD_OF = {
    "g02-butler": "gargantua02",
    "swco-butler": "software-co",
    "sjproto-butler": "skipjack-prototype",
}


def main():
    ts = subprocess.run(["date", "-u", "+%Y%m%dT%H%M%SZ"],
                        capture_output=True, text=True).stdout.strip()
    bdir = f"{BACKUP_ROOT}-{ts}"
    os.makedirs(bdir, exist_ok=True)

    # ---- backup the mutable files of each butler (tokens stay on disk, never in git)
    for b in BUTLERS:
        src = f"{PROFILES}/{b}"
        dst = f"{bdir}/{b}"
        os.makedirs(dst, exist_ok=True)
        for name in (".env", "SOUL.md", "config.yaml"):
            p = f"{src}/{name}"
            if os.path.exists(p):
                subprocess.run(["cp", "-p", p, f"{dst}/{name}"], check=True)
                print(f"backed up {b}/{name}")
            else:
                print(f"absent (expected for some): {b}/{name}")
    print(f"backup dir: {bdir}")

    # ---- banks: create only if missing
    with urllib.request.urlopen(BASE + "/v1/default/banks", timeout=15) as r:
        banks = json.load(r)["banks"]
    have = {b["bank_id"] for b in banks}
    created = []
    for b in BUTLERS:
        if b in have:
            print(f"bank {b}: already exists — leaving untouched")
            continue
        body = json.dumps({
            "name": b,
            "mission": BANK_MISSION.format(b=b, board=BOARD_OF[b]),
        }).encode()
        req = urllib.request.Request(
            f"{BASE}/v1/default/banks/{b}", data=body, method="PUT",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"PUT {b}: HTTP {r.status}")
        created.append(b)

    # ---- readback
    with urllib.request.urlopen(BASE + "/v1/default/banks", timeout=15) as r:
        banks = json.load(r)["banks"]
    ok = True
    for b in BUTLERS:
        found = [x for x in banks if x["bank_id"] == b]
        if found:
            print(f"readback {b}: fact_count={found[0]['fact_count']} "
                  f"created_at={found[0]['created_at']}")
        else:
            print(f"readback {b}: MISSING")
            ok = False
    print(f"({len(banks)} banks total on server)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
