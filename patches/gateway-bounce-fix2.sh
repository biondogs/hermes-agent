#!/bin/bash
# Deferred graceful gateway bounce — kanban-stream FIX2 (card t_df30ec0c), 2026-10-23.
# Launched detached (setsid) from the t_df30ec0c worker session BEFORE its
# kanban_complete, so the bounce runs at true shell level, after the worker
# sessions have drained naturally. Waits for the two cards to leave `running`,
# then drain-restarts the gateway via `hermes gateway restart` (SIGUSR1 drain,
# systemd relaunch — same command as the operator's proven restarts) and logs
# the full receipt for the Oct-25 collector.
export HERMES_HOME=/home/arch/.hermes
export PATH=/home/arch/.local/bin:$PATH
LOG=/local/projects/software-co/patches/gateway-bounce-fix2-2026-10-23.log
DB="file:/home/arch/.hermes/kanban.db?mode=ro"

log(){ echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') $*" >> "$LOG"; }

log "deferred bounce launcher started (pid $$)"

wait_for_not_running(){
  # $1 = task id, $2 = max polls (10s each)
  for i in $(seq 1 "$2"); do
    state=$(python3 - "$DB" "$1" <<'PY'
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1], uri=True, timeout=5)
    r = c.execute("SELECT status FROM tasks WHERE id = ?", (sys.argv[2],)).fetchone()
    print(r[0] if r else "gone")
except Exception:
    print("db-error")
PY
)
    case "$state" in
      running|ready) sleep 10 ;;
      *) echo "$state"; return ;;
    esac
  done
  echo "timeout"
}

st1=$(wait_for_not_running t_df30ec0c 60)
st2=$(wait_for_not_running t_40bf70a1 120)
log "t_df30ec0c state before bounce: $st1"
log "t_40bf70a1 (proof card) state before bounce: $st2"

oldpid=$(pgrep -f 'gateway run' | head -1)
log "gateway pid before bounce: ${oldpid:-none}"
log "pre-bounce status:"
hermes gateway status >> "$LOG" 2>&1

log "issuing graceful drain-restart: hermes gateway restart (SIGUSR1 drain, systemd relaunch)"
hermes gateway restart >> "$LOG" 2>&1
log "hermes gateway restart exit code: $?"

# Fallback: if the gateway pid is unchanged 2 min later, SIGUSR1 it directly.
sleep 120
newpid=$(pgrep -f 'gateway run' | head -1)
if [ -n "$oldpid" ] && [ "$oldpid" = "$newpid" ]; then
  log "pid unchanged after restart command ($oldpid) — sending direct SIGUSR1 drain"
  kill -USR1 "$oldpid" 2>> "$LOG"
  for i in $(seq 1 60); do
    sleep 10
    now=$(pgrep -f 'gateway run' | head -1)
    [ "$now" != "$oldpid" ] && break
  done
fi

log "gateway pid after bounce: $(pgrep -f 'gateway run' | head -1 || echo none)"
log "post-bounce status:"
hermes gateway status >> "$LOG" 2>&1
log "bounce sequence complete — FIX2 receipt ends"
