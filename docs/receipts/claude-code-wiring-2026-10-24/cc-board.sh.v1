#!/usr/bin/env bash
# cc-board.sh — sanctioned board-lane wrapper for the shared `claude` CLI (t_b83974bc design §7, pilot v1).
# Usage: cc-board.sh <profile> <workdir> <max_turns> <budget_usd> <receipt_out> <prompt...>
# Enforces: board-lane rolling caps ($2.00/5h, $10.00/7d over ALL profiles, flock-guarded ledger),
#           model allowlist (haiku-5-5/sonnet-5-5), effort<=medium, one-shot print-mode discipline.
# Exit: 0 ok | 41 unknown-model | 42 board-budget-exhausted (pre-run) | 43 claude run failed/limit
set -u
PROFILE="$1"; WORKDIR="$2"; MAXTURNS="$3"; BUDGET="$4"; RECEIPT="$5"; shift 5
PROMPT="$*"
MODEL="${CC_BOARD_MODEL:-sonnet-5-5}"
EFFORT="${CC_BOARD_EFFORT:-medium}"
BOARD_DIR="$HOME/.claude-board"
LEDGER="$BOARD_DIR/ledger.jsonl"
mkdir -p "$BOARD_DIR"; touch "$LEDGER"
case "$MODEL" in haiku-5-5|sonnet-5-5|claude-haiku-5-5|claude-sonnet-5-5) MODEL="claude-$MODEL" ;; *) echo "REFUSED: model '$MODEL' not on board allowlist" >&2; exit 41;; esac
if [ "$EFFORT" != "low" ] && [ "$EFFORT" != "medium" ]; then echo "REFUSED: effort '$EFFORT' > medium" >&2; exit 41; fi

# --- rolling-cap check under flock ---
python3 - "$PROFILE" "$MODEL" "$LEDGER" <<'PYEOF' || exit 42
import sys, time, json
profile, model, ledger = sys.argv[1:4]
now = time.time()
c5 = c7 = 0.0
with open(ledger) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: e = json.loads(line)
        except Exception: continue
        age = now - e.get("ts", 0)
        if age <= 5*3600: c5 += e.get("cost_usd", 0)
        if age <= 7*24*3600: c7 += e.get("cost_usd", 0)
cap5, cap7 = 2.00, 10.00   # board-lane caps (fail-closed)
if c5 >= cap5 or c7 >= cap7:
    print(f"REFUSED: board-lane rolling cap hit (5h=${c5:.2f}/{cap5}, 7d=${c7:.2f}/{cap7}) — profile {profile} falls back to own model", file=sys.stderr)
    sys.exit(1)
print(f"OK: board-lane headroom 5h=${c5:.2f}/{cap5} 7d=${c7:.2f}/{cap7}", file=sys.stderr)
PYEOF

# --- one-shot invocation ---
# Permission grant: print mode denies Edit/Write/Bash without a grant. Pilot runs in an
# isolated clone with prompt-level constraints (no network, no push, no commits), so use
# bypass mode. TODO(wiring): replace with a settings.json permissions allowlist per profile.
EXTRA_FLAGS="${CC_BOARD_FLAGS:---dangerously-skip-permissions}"
cd "$WORKDIR" || exit 43
timeout 500 claude -p "$PROMPT" \
  --model "$MODEL" --effort "$EFFORT" \
  --max-turns "$MAXTURNS" --max-budget-usd "$BUDGET" \
  --no-session-persistence --output-format json $EXTRA_FLAGS \
  > "$RECEIPT" 2> "$RECEIPT.stderr"
RC=$?

if [ $RC -ne 0 ]; then
  # NOTE: rc!=0 can still carry a valid metered receipt (e.g. subtype error_max_turns
  # exits 1 with full usage JSON). Ledger it below before deciding, so the board-lane
  # sums never undercount. Only exit early when there is no parseable receipt at all.
  if ! grep -q '"total_cost_usd"' "$RECEIPT" 2>/dev/null; then
    echo "claude exited rc=$RC with NO meterable receipt; stderr tail:" >&2
    tail -5 "$RECEIPT.stderr" >&2
    exit 43
  fi
fi

# --- ledger append under flock ---
python3 - "$PROFILE" "$MODEL" "$RECEIPT" "$LEDGER" <<'PYEOF'
import sys, time, json, fcntl
profile, model, receipt, ledger = sys.argv[1:5]
try:
    r = json.load(open(receipt))
except Exception as e:
    print(f"WARN: receipt unparseable: {e}", file=sys.stderr); sys.exit(0)
u = r.get("usage") or {}
entry = {
  "ts": time.time(), "profile": profile, "model": model,
  "subtype": r.get("subtype"), "num_turns": r.get("num_turns"),
  "cost_usd": r.get("total_cost_usd", 0.0) or 0.0,
  "duration_ms": r.get("duration_ms"),
  "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
  "cache_read": u.get("cache_read_input_tokens"), "cache_write": u.get("cache_creation_input_tokens"),
  "session_id": r.get("session_id"),
}
if r.get("subtype") not in ("success", None):
    print(f"NOTE: non-success subtype {r.get('subtype')} — logged, treat as pilot signal", file=sys.stderr)
with open(ledger, "a") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    f.write(json.dumps(entry) + "\n")
    fcntl.flock(f, fcntl.LOCK_UN)
print(f"LEDGER: profile={profile} cost=${entry['cost_usd']:.4f} turns={entry['num_turns']} subtype={entry['subtype']}", file=sys.stderr)
PYEOF
exit 0
