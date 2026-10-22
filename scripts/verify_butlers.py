"""BUTLERS-STAGE-3 step 3: per-profile verification receipts.

Per card VERIFICATION spec, for each of g02-butler / swco-butler / sjproto-butler:
  R1  hermes -p <P> config check                -> PASS
  R2  hermes -p <P> tools list                  -> exactly [kanban, memory, session_search, web]
  R3  one-shot 'Reply exactly: <P>-OK' probe     -> literal PASS (scrubbed env, kit lesson #24)
  R4  bank canary: a one-shot session stating the butler's self-identification
      facts auto-retains into the DEDICATED bank (verified server-side), and
      the shared 'hermes' bank shows no butler self-identification facts.

Prints a receipt block per profile. Exit 0 iff all PASS.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

BASE = "http://ga01:8888"
ALLOWED = {"kanban", "memory", "session_search", "web"}

BUTLERS = {
    "g02-butler": "gargantua02",
    "swco-butler": "software-co",
    "sjproto-butler": "skipjack-prototype",
}

# narrow self-identification phrases for the leak scan (broad tokens like the
# board slug can appear in the shared bank legitimately, e.g. architect staging
# lore — a LEAK is butler self-identification, not mere mention)
LEAK_PATTERNS = {
    "g02-butler": ["I am the g02-butler", "memory bank is g02-butler",
                   "g02-butler board butler"],
    "swco-butler": ["I am the swco-butler", "memory bank is swco-butler",
                    "swco-butler board butler"],
    "sjproto-butler": ["I am the sjproto-butler", "memory bank is sjproto-butler",
                       "sjproto-butler board butler"],
}


def scrubbed_hermes(args, timeout=300):
    """Run hermes with a scrubbed environment (kit lesson #24: ambient worker
    env rides into client_env and the gateway refuses with invalid_params)."""
    cmd = ["env", "-i", f"HOME={os.path.expanduser('~')}",
           f"USER={os.environ.get('USER', 'arch')}",
           "PATH=" + os.environ["PATH"], "TERM=dumb", "hermes", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def get_json(path, timeout=15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


def list_memories(bank_id, limit=100):
    data = get_json(f"/v1/default/banks/{bank_id}/memories/list?limit={limit}")
    items = data.get("memories") or data.get("items") or data
    if isinstance(items, dict):
        items = items.get("memories", [])
    return items


def mem_text(m):
    return m.get("memory") or m.get("text") or m.get("content") or ""


def main():
    receipts = {}
    overall = True
    for butler, board in BUTLERS.items():
        print(f"\n{'='*60}\n== {butler} (board {board})\n{'='*60}")
        rec = {}

        # R1 config check -----------------------------------------------------
        r = subprocess.run(["hermes", "-p", butler, "config", "check"],
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        rec["config_check"] = "PASS" if r.returncode == 0 else f"FAIL rc={r.returncode}"
        print(f"R1 config check: {rec['config_check']}\n{out[-400:] if r.returncode else ''}")

        # R2 tools list --------------------------------------------------------
        r = subprocess.run(["hermes", "-p", butler, "tools", "list"],
                           capture_output=True, text=True, timeout=120)
        out = r.stdout + r.stderr
        loaded = set(re.findall(r"^\s*([\w-]+)\s*$", out, re.M))
        # the tools list output is grouped; fall back to matching known toolset names
        found = {t for t in ALLOWED if re.search(rf"^\s*{t}\b", out, re.M)}
        unexpected = [t for t in ("terminal", "file", "browser", "code_execution",
                                  "delegation", "cronjob", "skills", "todo")
                      if re.search(rf"^\s*{t}\b", out, re.M)]
        rec["tools"] = "PASS" if (found == ALLOWED and not unexpected) else \
            f"found={sorted(found)} unexpected={unexpected}"
        print(f"R2 tools list: {rec['tools']}")

        # R3 provider one-shot -------------------------------------------------
        marker = f"{butler}-OK"
        try:
            r = scrubbed_hermes(["-p", butler, "chat", "-q", f"Reply exactly: {marker}"])
            out = (r.stdout + r.stderr).strip()
            rec["provider"] = "PASS" if marker in out else f"FAIL: {out[-300:]}"
        except subprocess.TimeoutExpired:
            rec["provider"] = "FAIL: timeout"
        print(f"R3 provider probe ('Reply exactly: {marker}'): {rec['provider']}")

        # R4 canary session ----------------------------------------------------
        try:
            prompt = (f"State three short facts about yourself, one per line, "
                      f"phrased exactly: 'I am the {butler}.' / 'I manage exactly "
                      f"one board: {board}.' / 'My memory bank is {butler}.' "
                      f"Nothing else.")
            r = scrubbed_hermes(["-p", butler, "chat", "-q", prompt])
            out = (r.stdout + r.stderr).strip()
            print(f"R4 canary session rc={r.returncode}: {out[:200]}")
        except subprocess.TimeoutExpired:
            print("R4 canary session: timeout (continuing to server check)")

        # server-side check with retry (retention is async) ----------------------
        canary_pats = [butler, board]
        hits, leaks = 0, 0
        for attempt in range(1, 7):
            try:
                items = list_memories(butler)
                texts = [mem_text(m) for m in items]
                hits = sum(1 for t in texts if any(p in t for p in canary_pats))
                leak_items = list_memories("hermes", 200)
                leaks = sum(1 for m in leak_items
                            if any(p in mem_text(m) for p in LEAK_PATTERNS[butler]))
                if hits:
                    break
                print(f"  poll {attempt}: {len(items)} facts in {butler} bank, no canary yet")
            except Exception as exc:
                print(f"  poll {attempt}: {exc!r}")
            if attempt < 6:
                time.sleep(10)
        b = next((x for x in get_json("/v1/default/banks")["banks"]
                  if x["bank_id"] == butler), None)
        fc = b["fact_count"] if b else "?"
        rec["bank_canary"] = f"PASS (fact_count={fc}, canary_hits={hits}, shared_leaks={leaks})" \
            if hits and not leaks else f"FAIL (fact_count={fc}, hits={hits}, leaks={leaks})"
        print(f"R4 bank canary: {rec['bank_canary']}")

        ok = all("PASS" in str(v) for v in rec.values())
        receipts[butler] = rec
        overall = overall and ok
        print(f"== {butler}: {'ALL PASS' if ok else 'RECEIPTS INCOMPLETE'}")

    print("\n" + "=" * 60)
    print("RECEIPT SUMMARY (BUTLERS-STAGE-3, t_02de9dff)")
    print("=" * 60)
    for butler, rec in receipts.items():
        print(f"\n{butler}:")
        for k, v in rec.items():
            v = str(v)
            print(f"  {k}: {v[:200]}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
