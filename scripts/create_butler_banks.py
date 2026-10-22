"""Create the per-board butler banks on the hindsight server (idempotent).

PUT /v1/default/banks/{bank_id} (upsert semantics per openapi). Empty banks by
design — no migration, operator-accepted (card t_fd8ca6f0 spec #4/#5).
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://ga01:8888"


def get_json(path, timeout=15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


def bank_exists(bank_id):
    banks = get_json("/v1/default/banks")["banks"]
    return any(b["bank_id"] == bank_id for b in banks), banks


def put_bank(bank_id, mission):
    body = json.dumps({"name": bank_id, "mission": mission}).encode()
    req = urllib.request.Request(
        f"{BASE}/v1/default/banks/{bank_id}",
        data=body,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f"PUT {bank_id}: HTTP {r.status}")
        return json.load(r)


BANKS = {
    "gaudi-butler": "Isolated memory bank for the gaudi-butler Topology-B board butler (gaudi board front-end). Per-board butler banks per operator-approved policy — butler memories stay isolated, never in shared banks.",
    "g01-butler": "Isolated memory bank for the g01-butler Topology-B board butler (gargantua01 board front-end). Per-board butler banks per operator-approved policy — butler memories stay isolated, never in shared banks.",
}

rc = 0
for bank_id, mission in BANKS.items():
    try:
        exists, _ = bank_exists(bank_id)
        if exists:
            print(f"{bank_id}: already exists — leaving untouched")
            continue
        put_bank(bank_id, mission)
    except urllib.error.HTTPError as exc:
        print(f"{bank_id}: HTTPError {exc.code}: {exc.read().decode()[:300]}")
        rc = 1
    except Exception as exc:
        print(f"{bank_id}: {exc!r}")
        rc = 1

# final readback
print("\n== readback ==")
ok = True
banks = get_json("/v1/default/banks")["banks"]
ids = sorted(b["bank_id"] for b in banks)
for bank_id in BANKS:
    found = [b for b in banks if b["bank_id"] == bank_id]
    if found:
        b = found[0]
        print(f"{bank_id}: fact_count={b['fact_count']} created_at={b['created_at']}")
    else:
        print(f"{bank_id}: MISSING")
        ok = False
print(f"\n({len(ids)} banks total: {', '.join(ids)})")
sys.exit(0 if ok and rc == 0 else 1)
