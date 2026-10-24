#!/usr/bin/env bash
# cc-board-alert.sh — board-lane usage alert (t_b83974bc §7-4, shipped at wiring t_0f3b5c1e).
# Runs from the kanban-board-architect cron (no-agent). Emits alert lines on stdout ONLY when
# a 50/80/100% threshold of the board-lane caps is newly crossed (or a quota wall is written),
# so silence means "lane healthy". State in $BOARD_DIR/alert-state.json dedupes per window.
BOARD_DIR="${CC_BOARD_DIR:-$HOME/.claude-board}"
LEDGER="$BOARD_DIR/ledger.jsonl"; CAPS="$BOARD_DIR/caps.json"
WALL="$BOARD_DIR/quota-wall.json"; STATE="$BOARD_DIR/alert-state.json"
[ -f "$LEDGER" ] || exit 0
python3 - "$LEDGER" "$CAPS" "$WALL" "$STATE" <<'PYEOF'
import sys, json, time, os
ledger, capsf, wallf, statef = sys.argv[1:5]
try:
    caps = json.load(open(capsf))
    cap5 = float(caps["cap_5h_usd"]); cap7 = float(caps["cap_7d_usd"])
except Exception:
    cap5, cap7 = 2.00, 10.00
now = time.time(); c5 = c7 = 0.0; per = {}
for line in open(ledger):
    line = line.strip()
    if not line: continue
    try: e = json.loads(line)
    except Exception: continue
    cost = e.get("cost_usd", 0) or 0; age = now - e.get("ts", 0)
    if age <= 5*3600:
        c5 += cost; per[e.get("profile","?")] = per.get(e.get("profile","?"), 0) + cost
    if age <= 7*24*3600: c7 += cost

def band(frac):
    if frac >= 1.0: return "100"
    if frac >= 0.8: return "80"
    if frac >= 0.5: return "50"
    return "0"

state = {}
try: state = json.load(open(statef))
except Exception: pass
cur = {"5h": band(c5/cap5 if cap5 else 0), "7d": band(c7/cap7 if cap7 else 0)}
alerts = []
for w, cost, cap in (("5h", c5, cap5), ("7d", c7, cap7)):
    if cur[w] != state.get(w, "0") and cur[w] != "0":
        alerts.append(f"CC-BOARD ALERT: {w} board-lane usage ${cost:.2f}/${cap:.2f} ({int(cost/cap*100)}% of cap) — crossed {cur[w]}% threshold.")
    state[w] = cur[w]
# operator-protection tripwires: wall + cap refusals since last check
lastts = state.get("last_wall_check", 0); newest = lastts
evf = os.path.join(os.path.dirname(ledger), "events.jsonl")
if os.path.exists(evf):
    for line in open(evf):
        try: ev = json.loads(line)
        except Exception: continue
        if ev.get("ts", 0) <= lastts: continue
        newest = max(newest, ev.get("ts", 0))
        if ev.get("kind") == "quota_wall":
            alerts.append(f"CC-BOARD ALERT: QUOTA WALL written (profile {ev.get('profile')}) — Anthropic usage-limit-class failure; wired profiles are refusing and falling back until cooldown expires.")
        if ev.get("kind") == "refused_cap":
            alerts.append(f"CC-BOARD ALERT: cap refusal (profile {ev.get('profile')}) — board lane is at its ceiling and profiles are running on their own models.")
state["last_wall_check"] = newest
try: json.dump(state, open(statef, "w"))
except Exception: pass
if alerts:
    print(f"[cc-board {time.strftime('%Y-%m-%d %H:%M %Z', time.localtime(now))}]")
    for a in alerts: print(a)
PYEOF
exit 0
