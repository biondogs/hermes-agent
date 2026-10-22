#!/usr/bin/env python3
"""MUSE-WIRING-V2 teardown (Leg B): restore all wired profiles from the
committed byte-exact backups. Idempotent by cmp; run as-is on operator
teardown order (temp-lane law of default/t_5c5305bf)."""
import hashlib
from pathlib import Path

BACKUPS = Path("/local/projects/software-co/docs/muse-wiring-v2/rollback-manifests/backups")
PROFILES = Path("/home/arch/.hermes/profiles")

WIRED = ["kanban-worker", "g01-scribe", "g02-scribe", "sw-docs",
         "sw-dev-a", "sw-dev-b", "sw-qa", "sw-devops"]

for p in WIRED:
    backup = BACKUPS / f"{p}.config.yaml.pre-muse"
    cfg = PROFILES / p / "config.yaml"
    if cfg.read_bytes() == backup.read_bytes():
        print(p, "already-reverted")
        continue
    cfg.write_bytes(backup.read_bytes())
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    print(p, "restored", digest[:16], "…")
