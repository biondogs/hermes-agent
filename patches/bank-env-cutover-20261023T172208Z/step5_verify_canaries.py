#!/usr/bin/env python3
"""ENV-BANK-CUTOVER step 5: server-side canary verification.

- each new bank must contain its own marker (polls for async extraction)
- every other new bank must NOT contain that marker (cross-env leak check)
- alias banks verified via both alias and underlying bank_id
- detached mixed pools: fact_count snapshot for the report/deathwatch
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

TS = "20261023T172208Z"
BACKUP = Path(f"/home/arch/kanban-backups/env-bank-cutover-{TS}")
API = "http://ga01:8888/v1/default/banks"

CANARIES = [
    ("g01-infra", "EBX23G01INFRA", None),
    ("g02-infra", "EBX23G02INFRA", None),
    ("skipjack-infra", "EBX23SJINFRA", None),
    ("skipjack-prototype-infra", "EBX23SJPINFRA", None),
    ("gaudi-hpu", "EBX23GAUDIHPU", None),
    ("gaudi-hpu-perf", "EBX23GAUDIPERF", None),
    ("gaudi-hpu-sdk", "EBX23GAUDISDK", None),
    ("gaudi-hpu-hostops", "EBX23HOSTOPS", "hb-host-ops"),
    ("gaudi-hpu-upstream", "EBX23UPSTREAM", "hb-upstream-comm"),
]
DETACHED = ["hb-infra-release", "hb-inference-bench", "Hermes q38", "hb-synapse-sdk"]


def search(bank, q):
    url = f"{API}/{urllib.parse.quote(bank)}/memories/list?limit=10&q={urllib.parse.quote(q)}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r).get("total", 0)


def bank_counts():
    with urllib.request.urlopen(API, timeout=30) as r:
        return {b["bank_id"]: b for b in json.load(r)["banks"]}


# poll for own-marker (async extraction) up to 6 min
deadline = time.time() + 360
own = {}
while time.time() < deadline:
    own = {bank: search(bank, m) for bank, m, _ in CANARIES}
    if all(v >= 1 for v in own.values()):
        break
    print("extracting... current own-marker hits:", own)
    time.sleep(30)

print("\n== own-marker verification")
own_ok = True
for (bank, m, under), n in zip(CANARIES, [own[b] for b, _, _ in CANARIES]):
    status = "OK" if n >= 1 else "MISSING"
    if n < 1:
        own_ok = False
    print(f"  {bank}: {n} hit(s) for {m} [{status}]")
    if under:
        n2 = search(under, m)
        print(f"    (via underlying {under}: {n2} hit(s)) {'OK' if n2 == n else 'ALIAS DIVERGENCE!'}")

print("\n== cross-env leak check")
leaks = []
for bank, m, _ in CANARIES:
    for other, _, _ in CANARIES:
        if other == bank:
            continue
        n = search(other, m)
        if n:
            leaks.append((m, bank, other, n))
print("  leaks found:", len(leaks))
for l in leaks:
    print("   LEAK:", l)

counts = bank_counts()
(BACKUP / "post-canary-banks.json").write_text(json.dumps(counts, indent=2, sort_keys=True))
print("\n== bank inventory after canaries (%d banks)" % len(counts))
for bid in sorted(counts):
    b = counts[bid]
    print(f"  {bid:28} facts={b['fact_count']:6}  aliases={[a['alias'] for a in (b.get('matched_aliases') or [])]}")
print("\n== detached mixed pools deathwatch snapshot")
for bid in DETACHED:
    b = counts[bid]
    print(f"  {bid}: fact_count={b['fact_count']} last_write={b['last_write_at']}")

print("\nVERDICT:", "PASS" if own_ok and not leaks else "FAIL")
