#!/usr/bin/env python3
"""ENV-BANK-CUTOVER step 1: backup, pre-state snapshot, create fresh env banks.

Idempotent: re-runs converge (backup skipped if marker exists; bank PUT is upsert).
"""
import json
import shutil
import tarfile
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path

TS = "20261023T172208Z"
BACKUP = Path(f"/home/arch/kanban-backups/env-bank-cutover-{TS}")
PROFILES = Path("/home/arch/.hermes/profiles")
API = "http://ga01:8888/v1/default/banks"

NEW_BANKS = {
    "g01-infra": "Gargantua01 hardware-environment bank (prototype k8s). Single bank for every g01 lane profile (orchestrator, planner, auditor, scribe, ops, watcher). Fresh start 2026-10-23 per operator ruling — deliberately empty, repopulates from live g01 runs only; never mix other environments.",
    "g02-infra": "Gargantua02 hardware-environment bank (production k8s on Azure VMs 413-418). Single bank for every g02 lane profile (orchestrator, planner, auditor, scribe, ops, watcher). Fresh start 2026-10-23 per operator ruling — deliberately empty, repopulates from live g02 runs only; never mix other environments.",
    "skipjack-infra": "Skipjack hardware-environment bank (HPC/AI hybrid cluster, mgmt02). Single bank for every sj lane profile (orchestrator, planner, auditor, scribe, ops, watcher). Fresh start 2026-10-23 per operator ruling — deliberately empty, repopulates from live skipjack runs only; never mix other environments.",
    "skipjack-prototype-infra": "Skipjack Prototype hardware-environment bank (k8s on gh207+gh208). Single bank for every sjp lane profile (orchestrator, planner, auditor, scribe, ops, watcher). Fresh start 2026-10-23 per operator ruling — deliberately empty, repopulates from live sjp runs only; never mix other environments.",
    "gaudi-hpu": "Gaudi host (ga01, Habana HPU) environment bank — general board/infra lane for gaudi orchestrator, planner, auditor, scribe, deployer. Fresh start 2026-10-23 per operator ruling; deliberately empty, repopulates from live gaudi runs only. Sister banks: gaudi-hpu-perf (bench/inference), gaudi-hpu-sdk (SDK/kernel), gaudi-hpu-hostops, gaudi-hpu-upstream.",
    "gaudi-hpu-perf": "Gaudi host inference/bench lane bank — gaudi analyst, benchrunner, watcher. Preserves the operator ORCH-AMEND doctrine (inference knowledge stays out of general board knowledge) inside the env-axis taxonomy. Fresh start 2026-10-23; deliberately empty, repopulates from live runs only.",
    "gaudi-hpu-sdk": "Gaudi SynapsePT/SDK/kernel engineering lane bank — gaudi arch, perfeng, synapse. Fresh start 2026-10-23 per operator ruling (replaces mixed-pool hb-synapse-sdk); deliberately empty, repopulates from live runs only.",
}


def snapshot_banks():
    with urllib.request.urlopen(API, timeout=30) as r:
        return {b["bank_id"]: {"fact_count": b["fact_count"],
                               "last_write_at": b["last_write_at"]}
                for b in json.load(r)["banks"]}


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    marker = BACKUP / "BACKED-UP"
    if not marker.exists():
        # Backup every profile's hindsight/config.json + .env
        with tarfile.open(BACKUP / "pre-cutover-profile-configs.tar.gz", "w:gz") as tar:
            for d in sorted(PROFILES.iterdir()):
                for name in ("hindsight/config.json", ".env"):
                    f = d / name
                    if f.exists():
                        tar.add(f, arcname=f"{d.name}/{name}")
        print("backup written:", BACKUP / "pre-cutover-profile-configs.tar.gz")
        marker.write_text("done\n")
    else:
        print("backup already exists, skipping")

    pre = snapshot_banks()
    (BACKUP / "pre-state-banks.json").write_text(json.dumps(pre, indent=2, sort_keys=True))
    print(f"pre-state snapshot: {len(pre)} banks")

    for bank_id, mission in NEW_BANKS.items():
        body = json.dumps({"mission": mission}).encode()
        req = urllib.request.Request(f"{API}/{urllib.parse.quote(bank_id)}",
                                     data=body, method="PUT",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
            created = json.load(r)
        ok = created.get("bank_id") == bank_id and bool(created.get("mission"))
        print(f"created/ensured {bank_id}: http={code} mission_ack={ok}")

    post = snapshot_banks()
    (BACKUP / "post-create-banks.json").write_text(json.dumps(post, indent=2, sort_keys=True))
    new_ids = sorted(set(post) - set(pre))
    print("new banks:", new_ids)


if __name__ == "__main__":
    main()
