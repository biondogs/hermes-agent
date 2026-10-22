"""FRESH-BANK-CUTOVER execution (rows 2-7 + 8-10 of FRESH-BANK-CUTOVER.md §4).

Operator GO 2026-10-22: default root KEEPS bank_id 'hermes' (row 1 DROPPED —
default-on-'hermes' is the operator-ratified end state, not drift). Execute:
  rows 2-7 : create 6 banks server-side (PUT upsert), flip each profile's
             hindsight/config.json bank_id + banks{} block to the new bank.
  rows 8-10: comment out HINDSIGHT_BANK_ID in g02/swco/sjproto-butler .env
             (config-disarm the pin-wins landmine, agreeing-pair → config-only).

Idempotent + converge-safe: every step checks current state first, timestamped
backups to ~/kanban-backups/fresh-bank-cutover-<ts>/ before any mutation,
lossless rollback = copy backups back.

Usage: python3 fresh_bank_cutover_converge.py [--apply]
       (default is dry-run: prints planned actions, mutates nothing)
"""
import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.error

BASE = "http://ga01:8888"
PROFILES = os.path.expanduser("~/.hermes/profiles")
TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
BACKUP_DIR = os.path.expanduser(f"~/kanban-backups/fresh-bank-cutover-{TS}")
DRY_RUN = True

# Bank name -> (profile it serves, bank_mission text used on server PUT)
NEW_BANKS = {
    "hb-orchestrator": ("kanban-orchestrator",
        "Memory bank for the kanban-orchestrator profile: kanban dispatch, routing, "
        "task-graph and board-ops knowledge from orchestrator-lane runs. Fresh start "
        "2026-10-22 per operator GO — deliberately empty, repopulates from live runs only."),
    "hb-architect": ("kanban-board-architect",
        "Memory bank for the kanban-board-architect profile: profile/board provisioning, "
        "memory-bank routing, SOUL/toolset design knowledge from architect-lane runs. "
        "Fresh start 2026-10-22 per operator GO — deliberately empty, repopulates from live runs only."),
    "hb-kanban-worker": ("kanban-worker",
        "Memory bank for the kanban-worker profile: general kanban task-execution knowledge. "
        "Fresh start 2026-10-22 per operator GO — deliberately empty, repopulates from live runs only."),
    "hb-research": ("research",
        "Memory bank for the research profile: research digests, source-monitoring and "
        "reconnaissance knowledge. Fresh start 2026-10-22 per operator GO — deliberately "
        "empty, repopulates from live runs only."),
    "hb-distiller": ("distiller",
        "Memory bank for the distiller profile: cross-board memory curation and distillation "
        "knowledge. Fresh start 2026-10-22 per operator GO — deliberately empty, repopulates "
        "from live runs only."),
    "hb-sampling-test": ("sampling-test",
        "Memory bank for the sampling-test profile: throwaway test lane, safe to delete "
        "freely. Fresh start 2026-10-22 per operator GO."),
}

BUTLER_ENV_PINS = ["g02-butler", "swco-butler", "sjproto-butler"]

ACTIONS = []  # (kind, label, detail)


def act(kind, label, detail=""):
    ACTIONS.append((kind, label, detail))
    print(f"[{kind:^7}] {label}" + (f" — {detail}" if detail else ""))


def get_json(path, timeout=20):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


def banks_map():
    return {b["bank_id"]: b for b in get_json("/v1/default/banks")["banks"]}


def put_bank(bank_id, mission):
    body = json.dumps({"name": bank_id, "mission": mission}).encode()
    req = urllib.request.Request(
        f"{BASE}/v1/default/banks/{bank_id}", data=body, method="PUT",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.load(r)


def backup(rel_path):
    src = os.path.expanduser(rel_path)
    dst = os.path.join(BACKUP_DIR, rel_path.replace("~/.hermes/", "").replace("/", "__"))
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def converge_bank(profile, new_bank):
    cfg_path = f"{PROFILES}/{profile}/hindsight/config.json"
    cfg = json.load(open(cfg_path))
    if cfg.get("bank_id") == new_bank and new_bank in cfg.get("banks", {}):
        act("noop", f"{profile}: config already converged on {new_bank}")
        return
    if DRY_RUN:
        act("plan", f"{profile}: config.json bank_id '{cfg.get('bank_id')}' -> '{new_bank}'")
        return
    backup(cfg_path)
    cfg["bank_id"] = new_bank
    cfg["banks"] = {new_bank: {"bankId": new_bank, "budget": cfg.get("recall_budget", "mid"), "enabled": True}}
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    act("apply", f"{profile}: config.json bank_id -> '{new_bank}' (backed up)")


def main():
    global DRY_RUN
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="execute mutations (default: dry-run)")
    args = ap.parse_args()
    DRY_RUN = not args.apply

    print(f"== FRESH-BANK-CUTOVER converge ({'APPLY' if not DRY_RUN else 'DRY-RUN'}) ts={TS} ==")
    server = banks_map()
    for bank_id, (profile, mission) in NEW_BANKS.items():
        if bank_id in server and not server[bank_id].get("mission", ""):
            # exists but unmissioned? leave alone (shouldn't happen for new banks)
            pass
        if bank_id in server:
            act("noop", f"bank '{bank_id}' already exists server-side (fact_count={server[bank_id]['fact_count']})")
        else:
            if DRY_RUN:
                act("plan", f"create bank '{bank_id}' server-side (PUT upsert, mission set)")
            else:
                status, body = put_bank(bank_id, mission)
                act("apply", f"created bank '{bank_id}' (HTTP {status})")
        converge_bank(profile, bank_id)

    # rows 8-10: butler .env-pin normalization
    for butler in BUTLER_ENV_PINS:
        env_path = f"{PROFILES}/{butler}/.env"
        text = open(env_path).read()
        m = re.search(rf"^HINDSIGHT_BANK_ID={re.escape(butler)}\s*$", text, re.M)
        if not m:
            if "HINDSIGHT_BANK_ID" in text and DRY_RUN:
                act("plan", f"{butler}: comment out non-standard .env pin form")
            else:
                act("noop", f"{butler}: .env pin already disarmed")
            continue
        if DRY_RUN:
            act("plan", f"{butler}: comment out .env HINDSIGHT_BANK_ID pin")
        else:
            backup(env_path)
            text = re.sub(rf"^(HINDSIGHT_BANK_ID={re.escape(butler)})\s*$",
                          r"# \1 commented out by fresh_bank_cutover (t_0fbb3c61) — config.json carrier governs",
                          text, flags=re.M)
            with open(env_path, "w") as f:
                f.write(text)
            act("apply", f"{butler}: .env pin commented out (config.json carrier governs)")

    print(f"\nplanned={sum(1 for k,_,_ in ACTIONS if k=='plan')} "
          f"applied={sum(1 for k,_,_ in ACTIONS if k=='apply')} "
          f"noop={sum(1 for k,_,_ in ACTIONS if k=='noop')}")
    if not DRY_RUN:
        print(f"backups: {BACKUP_DIR}")
        print("readback banks:", ", ".join(sorted(b for b in banks_map())))


if __name__ == "__main__":
    main()
