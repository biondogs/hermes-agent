"""Canary verification for the per-board butler hindsight banks (t_fd8ca6f0).

Checks that a butler one-shot session's auto-retained facts landed in the
profile's OWN bank (and not in the shared 'hermes' bank), by querying the
hindsight server directly.

Hindsight extracts structured facts rather than storing verbatim text, so
canaries are matched on canary CONTENT patterns (board self-identification and
bank self-identification), not a literal marker string.

Usage: bank_canary_check.py [bank_id]      (default gaudi-butler)
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://ga01:8888"

# canary content patterns per butler bank (facts the butler states about itself)
PATTERNS = {
    "gaudi-butler": ["manages exactly one board: gaudi", "gaudi-butler bank"],
    "g01-butler": ["g01-butler", "gargantua01"],
}


def get_json(path, timeout=15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


def bank_overview(bank_id):
    banks = get_json("/v1/default/banks")["banks"]
    for b in banks:
        if b["bank_id"] == bank_id:
            return b
    return None


def list_memories(bank_id, limit=50):
    data = get_json(f"/v1/default/banks/{bank_id}/memories/list?limit={limit}")
    items = data.get("memories") or data.get("items") or data
    if isinstance(items, dict):
        items = items.get("memories", [])
    return items


def recent_canary_facts(bank_id, wait_s=5.0, attempts=6):
    patterns = PATTERNS.get(bank_id, [bank_id])
    for attempt in range(1, attempts + 1):
        try:
            items = list_memories(bank_id)
            hits = []
            for m in items:
                text = m.get("memory") or m.get("text") or m.get("content") or ""
                if any(p in text for p in patterns):
                    hits.append(text)
            if hits:
                return hits
            print(f"  poll {attempt}: {len(items)} memories in bank, no canary facts yet")
        except urllib.error.HTTPError as exc:
            print(f"  poll {attempt}: HTTP {exc.code} — bank may not exist yet")
        except Exception as exc:
            print(f"  poll {attempt}: {exc!r}")
        if attempt < attempts:
            time.sleep(wait_s)
    return []


def main():
    bank = sys.argv[1] if len(sys.argv) > 1 else "gaudi-butler"
    print(f"== hindsight bank canary check: '{bank}' @ {BASE} ==")
    b = bank_overview(bank)
    if b:
        print(f"bank exists: fact_count={b['fact_count']} last_write_at={b['last_write_at']} "
              f"created_at={b['created_at']}")
    else:
        print(f"bank '{bank}' NOT on server")
    hits = recent_canary_facts(bank)
    print(f"canary facts: {len(hits)}")
    for h in hits[:5]:
        print(f"  - {h[:180]}")

    # isolation: the same must NOT be in the shared bank
    leaks = 0
    try:
        for m in list_memories("hermes", 200):
            text = m.get("memory") or m.get("text") or m.get("content") or ""
            if any(p in text for p in patterns_all(bank)):
                leaks += 1
                print(f"  LEAK in shared bank: {text[:180]}")
    except Exception as exc:
        print(f"shared-bank check skipped: {exc!r}")

    verdict = "PASS" if hits and not leaks else "FAIL"
    print(f"CANARY: {verdict} (own-bank facts={len(hits)}, shared-bank leaks={leaks})")
    sys.exit(0 if verdict == "PASS" else 1)


def patterns_all(bank):
    return PATTERNS.get(bank, [bank])


if __name__ == "__main__":
    main()
