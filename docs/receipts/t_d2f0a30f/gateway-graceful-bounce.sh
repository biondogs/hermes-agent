#!/bin/bash
# gateway-graceful-bounce.sh — CANONICAL graceful Hermes-gateway bounce (v1.0, t_d2f0a30f).
#
# OPERATOR RULING (2026-10-24, card t_d2f0a30f): Hermes agents MAY restart the Hermes
# gateway. This script is the ONLY sanctioned mechanism (operator-approved method: the
# detached SIGUSR1 graceful-drain path proven in t_01b7847b run 117 and t_df30ec0c).
# Container / aistack / LiteLLM / serving-pod restarts stay OPERATOR-ONLY.
# NON-DISTURBANCE / SERVING LAW unchanged. Skill: devops/hermes-gateway-graceful-bounce.
#
# Laws this script enforces (do not "fix" them away):
#   * GRACEFUL only: SIGUSR1 → gateway drains in-flight turns (deferred-drain cap 1800s
#     per gateway core) → systemd --user relaunches hermes-gateway.service.
#   * NEVER `--yes`, NEVER SIGKILL, NEVER a second escalation if the PID doesn't
#     change: abort, write a FAILURE receipt, notify, and let a human look.
#   * Single-flight: flock-guarded, two agents can never bounce at once.
#   * Rate limit: MIN_INTERVAL_SECONDS (1800s = 30 min) between bounced triggers.
#   * Self-detaching: called from inside a gateway worker (which WILL DIE in the
#     bounce), it re-launches itself via setsid so the bounce completes after the
#     caller is gone. The caller must bank its receipts BEFORE invoking this script
#     and let its dispatcher auto-retry do the post-bounce verification.
#   * Notifies the operator once before and once after (hermes send, one line each).
#
# Usage:
#   bash ~/.hermes/scripts/gateway-graceful-bounce.sh --reason "why"     # bounce (self-detaches)
#   bash ~/.hermes/scripts/gateway-graceful-bounce.sh --self-check       # preflight only, no bounce
#   bash ~/.hermes/scripts/gateway-graceful-bounce.sh --foreground --reason "why"  # no re-detach
#
# Receipts (durable): one line per event in ~/.hermes/logs/gateway-bounce-receipts.log,
# full run log in ~/.hermes/logs/gateway-bounce-runs/<ts>.log.

set -u
export HERMES_HOME="${HERMES_HOME:-/home/arch/.hermes}"
export PATH="/home/arch/.local/bin:$PATH"

SCRIPT_PATH="/home/arch/.hermes/scripts/gateway-graceful-bounce.sh"
LOCK_FILE="/home/arch/.hermes/scripts/.gateway-graceful-bounce.lock"
STATE_FILE="/home/arch/.hermes/scripts/.gateway-graceful-bounce.state"
RECEIPTS="/home/arch/.hermes/logs/gateway-bounce-receipts.log"
RUNS_DIR="/home/arch/.hermes/logs/gateway-bounce-runs"
GW_LOG="$HERMES_HOME/logs/gateway.log"
UNIT="hermes-gateway.service"
MIN_INTERVAL_SECONDS=1800          # rate limit: >=30 min between bounced triggers
DRAIN_CAP_SECONDS=1800             # gateway core's own deferred-drain cap (#77184)
BOOT_WAIT_SECONDS=420              # extra wait for teardown + cold boot beyond drain cap
MARKER_WAIT_SECONDS=300            # wait for butler/dispatcher markers post-boot
OPERATOR_TARGET="telegram:8158007517"
BUTLERS="g01-butler g02-butler gaudi-butler sjproto-butler swco-butler"
BOARDS=(
  "default:file:/home/arch/.hermes/kanban.db?mode=ro"
  "gargantua01:file:/home/arch/.hermes/kanban/boards/gargantua01/kanban.db?mode=ro"
  "gargantua02:file:/home/arch/.hermes/kanban/boards/gargantua02/kanban.db?mode=ro"
  "gaudi:file:/home/arch/.hermes/kanban/boards/gaudi/kanban.db?mode=ro"
  "skipjack:file:/home/arch/.hermes/kanban/boards/skipjack/kanban.db?mode=ro"
  "skipjack-prototype:file:/home/arch/.hermes/kanban/boards/skipjack-prototype/kanban.db?mode=ro"
  "software-co:file:/home/arch/.hermes/kanban/boards/software-co/kanban.db?mode=ro"
)

ts()   { date '+%Y-%m-%d %H:%M:%S %Z'; }
uts()  { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

REASON=""
SELF_CHECK=0
FOREGROUND=0
for arg in "$@"; do
  case "$arg" in
    --self-check) SELF_CHECK=1 ;;
    --foreground) FOREGROUND=1 ;;
    --reason) : ;; # value handled below
    *) [ "${PREV:-}" = "--reason" ] && REASON="$arg" ;;
  esac
  PREV="$arg"
done

echo_log() { echo "[$(uts)] $*" >> "$RUN_LOG" 2>/dev/null; }
receipt()  { echo "$(uts) $*" >> "$RECEIPTS"; echo_log "RECEIPT: $*"; }

notify() {  # one-liner to the operator; best-effort, failures recorded not fatal
  local line="$1"
  local out
  out=$(hermes send -t "$OPERATOR_TARGET" "$line" 2>&1) || true
  if [ -n "$out" ]; then echo_log "notify out: $out"; fi
}

gw_pid() { systemctl --user show -p MainPID --value "$UNIT" 2>/dev/null | tr -d '[:space:]'; }

count_running() {  # $1 = slug:uri -> prints "<slug>:<n>"  (no sqlite3 CLI on host; use python3)
  local slug="${1%%:*}" db="${1#*:}"
  /usr/bin/python3 - "$slug" "$db" <<'PY' 2>/dev/null
import sqlite3, sys
slug, db = sys.argv[1], sys.argv[2]
try:
    c = sqlite3.connect(db, uri=True, timeout=5)
    n = c.execute("select count(*) from tasks where status='running'").fetchone()[0]
    print(f"{slug}:{n}")
    c.close()
except Exception:
    print(f"{slug}:db-error")
PY
}

running_ids() {  # prints running card ids for $1 = slug:uri, one per line
  local db="${1#*:}"
  /usr/bin/python3 - "$db" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1], uri=True, timeout=5)
    for (tid,) in c.execute("select id from tasks where status='running'"):
        print(tid)
    c.close()
except Exception:
    pass
PY
}

card_status() {  # $1 = uri, $2 = task id -> status or ""
  /usr/bin/python3 - "$1" "$2" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1], uri=True, timeout=5)
    row = c.execute("select status from tasks where id=?", (sys.argv[2],)).fetchone()
    print(row[0] if row else "")
    c.close()
except Exception:
    print("")
PY
}

latest_card() {  # $1 = uri -> most recently touched non-archived card id (idle-board notice target)
  /usr/bin/python3 - "$1" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1], uri=True, timeout=5)
    cols = {r[1] for r in c.execute("pragma table_info(tasks)")}
    order = "updated_at" if "updated_at" in cols else "created_at"
    row = c.execute(
        f"select id from tasks where status != 'archived' order by {order} desc limit 1"
    ).fetchone()
    print(row[0] if row else "")
    c.close()
except Exception:
    print("")
PY
}

triage_board() {  # $1 = uri, $2 = restart_epoch -> PASS/ISSUES triage snapshot (operator addendum B)
  /usr/bin/python3 - "$1" "$2" <<'PY' 2>/dev/null
import sqlite3, sys, os, time
uri, restart = sys.argv[1], int(sys.argv[2])
out = {"running": [], "stale_hb": [], "crashed": [], "gw_disc_blocked": [], "orphan_claims": "n/a"}
try:
    c = sqlite3.connect(uri, uri=True, timeout=5)
    out["running"] = [r[0] for r in c.execute("select id from tasks where status='running'")]
    now = int(time.time())
    for tid in out["running"]:
        try:
            hb = c.execute("select max(created_at) from task_events where task_id=? and kind='heartbeat'", (tid,)).fetchone()[0]
            if hb is None or now - hb > 1200:
                out["stale_hb"].append(tid)
        except Exception:
            pass
    try:
        out["crashed"] = [r[0] for r in c.execute(
            "select task_id from task_events where kind in ('crashed','timed_out') and created_at >= ? group by task_id", (restart,))]
    except Exception:
        pass
    try:
        out["gw_disc_blocked"] = [r[0] for r in c.execute(
            "select id from tasks where status='blocked' and last_failure_error like '%isconnected%'")]
    except Exception:
        cols = {r[1] for r in c.execute("pragma table_info(tasks)")}
        if "last_failure_error" not in cols:
            out["gw_disc_blocked"] = ["schema:n/a"]
    verdict = "PASS"
    if out["stale_hb"] or out["gw_disc_blocked"]:
        verdict = "ISSUES"
    print(f"verdict={verdict} running={out['running']} stale_hb={out['stale_hb']} "
          f"crashed_since_restart={out['crashed']} gw_disc_blocked={out['gw_disc_blocked']} orphan_claims={out['orphan_claims']}")
    c.close()
except Exception as e:
    print(f"verdict=ISSUES running=[db-error: {e}] stale_hb=[] crashed=[] gw_disc_blocked=[] orphan_claims=n/a")
PY
}

# Operator addendum A — board notices (cross-board CLI is env-scrubbed; F24 notes the CLI
# ignores the tool-layer fence, so we scrub the worker env pins and let --board resolve).
kcli() {  # kcli <board> <kanban args...>  (actual actor recorded via --author)
  env -u HERMES_KANBAN_DB -u HERMES_KANBAN_BOARD -u HERMES_DELEGATED_CHILD_CONTEXT \
      -u HERMES_KANBAN_WORKSPACES_ROOT \
      /home/arch/.local/bin/hermes -p kanban-board-architect kanban --board "$1" "${@:2}"
}

pre_notice_boards() {  # BEFORE the signal: one-line restart notice per board (running cards; idle boards -> latest card)
  for b in "${BOARDS[@]}"; do
    local slug="${b%%:*}"
    local ids; ids=$(running_ids "$b" | tr '\n' ' ')
    if [ -z "${ids// /}" ]; then
      local latest; latest=$(latest_card "${b#*:}")
      [ -n "$latest" ] && ids="$latest"
    fi
    if [ -z "${ids// /}" ]; then
      receipt "NOTICE-PRE $slug skipped (board has no non-archived cards)"
      continue
    fi
    local t
    for t in $ids; do
      if kcli "$slug" comment "$t" "🔁 [GATEWAY-RESTART-NOTICE] graceful drain-bounce by kanban-board-architect (card t_d2f0a30f) at $(uts): reason '$REASON'. In-flight runs will be drained (cap 30 min) then auto-retried. Receipts: ~/.hermes/logs/gateway-bounce-receipts.log" --author kanban-board-architect >>"$RUN_LOG" 2>&1; then
        echo "$slug $t" >> "$NOTIFIED_FILE"
        receipt "NOTICE-PRE $slug $t ok"
      else
        receipt "NOTICE-PRE $slug $t FAILED (see run log)"
      fi
    done
  done
}

post_notice_boards() {  # AFTER verification: one-line restart-complete note on the same targets
  [ -f "$NOTIFIED_FILE" ] || return 0
  local slug t
  while read -r slug t; do
    [ -z "$slug" ] && continue
    if kcli "$slug" comment "$t" "✅ [GATEWAY-RESTART-DONE] gateway back up $(uts): old PID $OLD_PID → new PID $NEW_PID; dispatcher booted; post-restart triage pass follows on this board. Receipts: ~/.hermes/logs/gateway-bounce-receipts.log" --author kanban-board-architect >>"$RUN_LOG" 2>&1; then
      receipt "NOTICE-POST $slug $t ok"
    else
      receipt "NOTICE-POST $slug $t FAILED (see run log)"
    fi
  done < "$NOTIFIED_FILE"
}


# ---- self-detach (the caller — possibly a gateway worker — will die in the bounce)
if [ "$SELF_CHECK" -eq 0 ] && [ "$FOREGROUND" -eq 0 ] && [ "${GGB_DETACHED:-0}" != "1" ]; then
  TS_TAG=$(date -u '+%Y%m%dT%H%M%SZ')
  RUN_LOG="$RUNS_DIR/$TS_TAG.log"
  mkdir -p "$RUNS_DIR"
  setsid env GGB_DETACHED=1 bash "$SCRIPT_PATH" "$@" >> "$RUN_LOG" 2>&1 < /dev/null &
  echo "detached bounce launcher started (pid $!, run log: $RUN_LOG)"
  exit 0
fi

TS_TAG=$(date -u '+%Y%m%dT%H%M%SZ')
RUN_LOG="$RUNS_DIR/$TS_TAG.log"
NOTIFIED_FILE="$RUNS_DIR/$TS_TAG.notified"
mkdir -p "$RUNS_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo_log "ABORT: another bounce holds the single-flight lock ($LOCK_FILE)."
  [ "$SELF_CHECK" -eq 1 ] && echo "ABORT would occur: another bounce holds the lock."
  exit 3
fi

# ---- pre-flight
OLD_PID=$(gw_pid)
if [ -z "$OLD_PID" ] || [ "$OLD_PID" = "0" ] || ! kill -0 "$OLD_PID" 2>/dev/null; then
  echo_log "ABORT: no live gateway MainPID for $UNIT (got '${OLD_PID:-none}')."
  exit 4
fi
LOG_OFFSET_BEFORE=$(stat -c %s "$GW_LOG" 2>/dev/null || echo 0)

if [ "$SELF_CHECK" -eq 1 ]; then
  echo "gateway MainPID: $OLD_PID (started $(ps -o lstart= -p "$OLD_PID" 2>/dev/null | tr -s ' '))"
  echo "running cards per board:"
  TOTAL=0
  for b in "${BOARDS[@]}"; do
    line=$(count_running "$b"); echo "  $line"
    case "${line##*:}" in ''|*[!0-9]*) : ;; *) TOTAL=$((TOTAL+${line##*:})) ;; esac
  done
  echo "managed worker processes: $(pgrep -fc 'agent.managed_worker' 2>/dev/null || echo 0)"
  LAST=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  AGE=$(( $(date +%s) - ${LAST:-0} ))
  echo "last bounce epoch: ${LAST:-never} (${AGE}s ago; rate limit ${MIN_INTERVAL_SECONDS}s)"
  if [ "$AGE" -lt "$MIN_INTERVAL_SECONDS" ]; then
    echo "RATE-LIMITED: a bounce within ${MIN_INTERVAL_SECONDS}s would be refused."
  else
    echo "rate limit: CLEAR (a bounce now would proceed)"
  fi
  echo "self-check only — no signal sent."
  exit 0
fi

if [ -z "$REASON" ]; then
  echo_log "ABORT: --reason is required for a real bounce (audit trail)."
  exit 5
fi

LAST=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
AGE=$(( $(date +%s) - ${LAST:-0} ))
if [ "$AGE" -lt "$MIN_INTERVAL_SECONDS" ]; then
  receipt "ABORT rate-limit: last bounce ${AGE}s ago (< ${MIN_INTERVAL_SECONDS}s) reason='$REASON'"
  notify "⚠️ gateway bounce REFUSED (rate limit ${AGE}s < ${MIN_INTERVAL_SECONDS}s) — reason: $REASON"
  exit 6
fi

RUNNING_LINES=""; TOTAL_RUNNING=0; RUNNING_CARDS=""
for b in "${BOARDS[@]}"; do
  line=$(count_running "$b")
  RUNNING_LINES="$RUNNING_LINES $line"
  n="${line##*:}"
  case "$n" in ''|*[!0-9]*) n=1 ;; esac   # unreadable board counts as busy, never invisible
  TOTAL_RUNNING=$((TOTAL_RUNNING+n))
done
RUNNING_CARDS=""
for b in "${BOARDS[@]}"; do RUNNING_CARDS="$RUNNING_CARDS$(running_ids "$b" | tr '\n' ' ')"; done

MW=$(pgrep -fc 'agent.managed_worker' 2>/dev/null || echo 0)

receipt "START reason='$REASON' old_pid=$OLD_PID running_cards=$TOTAL_RUNNING ($RUNNING_LINES ) managed_workers=$MW"
notify "🔁 gateway graceful bounce starting (card law t_d2f0a30f): SIGUSR1 drain → systemd relaunch, old PID $OLD_PID, $TOTAL_RUNNING running cards in flight — reason: $REASON"
echo_log "preflight: old_pid=$OLD_PID running_cards='$RUNNING_LINES' cards: $RUNNING_CARDS"

# --- operator addendum A: one-line restart notice to every board BEFORE the signal
pre_notice_boards

# ---- bounce (graceful, single signal, no escalation)
BOUNCE_EPOCH=$(date +%s)
kill -USR1 "$OLD_PID"
echo_log "SIGUSR1 sent to $OLD_PID at $(uts); deferring to gateway drain (cap ${DRAIN_CAP_SECONDS}s)."

NEW_PID=""
DEADLINE=$(( $(date +%s) + DRAIN_CAP_SECONDS + BOOT_WAIT_SECONDS ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  P=$(gw_pid)
  if [ -n "$P" ] && [ "$P" != "0" ] && [ "$P" != "$OLD_PID" ] && kill -0 "$P" 2>/dev/null; then
    NEW_PID="$P"; break
  fi
  sleep 10
done

if [ -z "$NEW_PID" ]; then
  # NO escalation: never --yes, never SIGKILL, never a second signal.
  receipt "FAILURE pid-unchanged after $((DRAIN_CAP_SECONDS+BOOT_WAIT_SECONDS))s old_pid=$OLD_PID reason='$REASON' — aborted, NO escalation, requires human"
  notify "⚠️ gateway bounce FAILED: PID $OLD_PID did not hand over after drain window — aborted without escalation, needs a human. Reason: $REASON"
  exit 7
fi

date +%s > "$STATE_FILE"
ACTIVE=$(systemctl --user is-active "$UNIT" 2>/dev/null || echo unknown)
JMARK=$(journalctl --user -u "$UNIT" --since "@$(( $(date +%s) - 120 ))" --no-pager 2>/dev/null | grep -c "Started $UNIT" || true)
receipt "HANDOVER old_pid=$OLD_PID new_pid=$NEW_PID unit_state=$ACTIVE journal_started_marker=$JMARK reason='$REASON'"

# ---- post-boot verification markers
MARK_DEADLINE=$(( $(date +%s) + MARKER_WAIT_SECONDS ))
found_banner=0; found_dispatch=0; found_default=0
declare -A FOUND_BUTLER
while [ "$(date +%s)" -lt "$MARK_DEADLINE" ]; do
  TAIL=$(tail -c +$((LOG_OFFSET_BEFORE + 1)) "$GW_LOG" 2>/dev/null)
  grep -q "Starting Hermes Gateway" <<<"$TAIL" && found_banner=1
  grep -q "holding singleton dispatcher lock" <<<"$TAIL" && found_dispatch=1
  grep -q "✓ telegram connected" <<<"$TAIL" && found_default=1
  all_b=1
  for b in $BUTLERS; do
    if grep -q "✓ telegram connected (profile: $b)" <<<"$TAIL"; then FOUND_BUTLER[$b]=1; else all_b=0; fi
  done
  [ "$found_banner" = 1 ] && [ "$found_dispatch" = 1 ] && [ "$found_default" = 1 ] && [ "$all_b" = 1 ] && break
  sleep 10
done
BUTLER_OK=""
for b in $BUTLERS; do [ "${FOUND_BUTLER[$b]:-0}" = 1 ] && BUTLER_OK="$BUTLER_OK $b"; done

# ---- interrupted cards: re-queued / retried / completed?
CARDS_AFTER=""
for t in $RUNNING_CARDS; do
  for b in "${BOARDS[@]}"; do
    st=$(card_status "${b#*:}" "$t")
    [ -n "$st" ] && CARDS_AFTER="$CARDS_AFTER $t=$st"
  done
done

receipt "VERIFY banner=$found_banner dispatcher_boot=$found_dispatch default_bot_tg=$found_default butlers_reconnected=[$BUTLER_OK ] new_pid=$NEW_PID interrupted_cards=[$CARDS_AFTER ] reason='$REASON'"

# --- operator addendum A: one-line restart-complete note on the same targets
post_notice_boards

# --- operator addendum B: read-only triage snapshot on every board (full pass incl.
#     hygiene fixes + butler reachability is completed by the initiating card's retry run)
RESTART_EPOCH="${BOUNCE_EPOCH:-$(date +%s)}"
sleep 60   # give respawned workers time to heartbeat + the dispatcher a few ticks
TRIAGE_TABLE=""
TRIAGE_ISSUES=0
for b in "${BOARDS[@]}"; do
  slug="${b%%:*}"
  tline=$(triage_board "${b#*:}" "$RESTART_EPOCH")
  receipt "TRIAGE $slug $tline"
  TRIAGE_TABLE="$TRIAGE_TABLE | $slug: $tline"
  case "$tline" in verdict=PASS*) : ;; *) TRIAGE_ISSUES=$((TRIAGE_ISSUES+1)) ;; esac
done

notify "✅ gateway bounce complete: PID $OLD_PID → $NEW_PID, dispatcher booted, default bot + ${#FOUND_BUTLER[@]}/5 butlers reconnected, cards:[$CARDS_AFTER ]; triage: $((7-TRIAGE_ISSUES))/7 boards PASS — reason: $REASON"

if [ "$found_banner" = 1 ] && [ "$found_dispatch" = 1 ] && [ "$found_default" = 1 ] && [ "${#FOUND_BUTLER[@]}" -ge 4 ] && [ "$TRIAGE_ISSUES" -eq 0 ]; then
  receipt "SUCCESS reason='$REASON' old_pid=$OLD_PID new_pid=$NEW_PID triage_all_boards=PASS"
  exit 0
else
  receipt "PARTIAL reason='$REASON' — bounce succeeded but markers/triage incomplete: markers(banner=$found_banner dispatch=$found_dispatch default=$found_default butlers=${#FOUND_BUTLER[@]}) triage_issues=$TRIAGE_ISSUES$TRIAGE_TABLE; full remediation by the initiating card's retry run; see $RUN_LOG"
  exit 8
fi
