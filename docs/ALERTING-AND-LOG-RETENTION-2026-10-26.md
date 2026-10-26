> Status: current. Source for hermes-estate/docs/OPERATIONS.md §4 (2026-10-26).

# Alerting (gateway dead-man + alt sinks) & Log Retention — 2026-10-26

Card **t_6d5d076f** (ER-5+6; operator picks 2026-10-26 from
`ESTATE-REVIEW-2026-10-26-SYNTHESIS.md`, items 5+6 adopted, 7 deferred).
Implements estate-review **GAP-2** (single alert channel, no dead-man switch)
and **GAP-3** (zero log rotation, logs excluded from all mirrors).

## 1. ER-5 — Gateway dead-man switch + alternate alert sink

### 1.1 Why it is a SYSTEM crontab entry, not a hermes cron job
The Hermes cron scheduler is an **in-process daemon thread inside the gateway**
(`hermes-agent/cron/scheduler_thread.py`: *"The gateway (and the Desktop
backend) run InProcessCronScheduler.start on a bare daemon thread"*). A
dead-man registered in the hermes cron registry would die with the very
process it watches. The watchdog therefore lives in the **arch user's system
crontab** (OS cron daemon — no Hermes dependency at all):

```
*/5 * * * * flock -n $HOME/.hermes/scripts/.gateway-deadman.lock \
  /usr/bin/python3 $HOME/.hermes/scripts/gateway-deadman.py \
  >> $HOME/.hermes/logs/gateway-deadman.log 2>&1
```

### 1.2 Liveness model (`~/.hermes/scripts/gateway-deadman.py`)
- Reads `~/.hermes/state/gateway.heartbeat` (JSON, rewritten ~every 15 s).
- **DEAD** if heartbeat age > **2700 s (45 min)** — comfortably above the
  ≤1800 s sanctioned graceful-bounce drain, so a bounce cannot false-positive —
  or if the recorded pid is gone while age > 300 s (crash + systemd
  `Restart=always` failed to bring it back).
- The systemd unit `hermes-gateway.service` has `Restart=always`, so the
  deadly case this watchdog exists for is the **wedged** gateway (alive pid,
  stalled loop, stale heartbeat).
- Re-alerts every 6 h while the incident stands; on recovery sends a TG line
  and **comments + closes** the gh incident issue.
- State: `~/.hermes/state/gateway-deadman-state.json`; run log:
  `~/.hermes/logs/gateway-deadman.log` (rotated).

### 1.3 Alert channels (`~/.hermes/scripts/alert-sink.sh`)
Both are **completely gateway-independent** ("must not depend on the gateway
it watches" — card body):

| Channel | Mechanism | Notes |
|---|---|---|
| **tg** | direct `curl` to the Telegram Bot API with the **KANBAN-STREAM ops bot** (token in root `.env` line 525, `KANBAN_STREAM_OPS_CHAT_ID` == 8158007517, verified) → DM 8158007517 | works with the gateway dead |
| **gh** | issue on **private** `biondogs/hermes-estate` | hard privacy gate (mirrors estate-sync's: refuses if repo ever goes public); **one open issue per tag**, re-alerts append comments; auto-comment+close on recovery |

**himalaya/email was not used**: himalaya is not installed on ga01 (checked
2026-10-26; `which himalaya` empty). The card allowed email "if configured,
else propose" — the **gh issue on the operator's private repo** is the
proposed and implemented alternate sink (also the review's own suggestion,
GAP-2 fix line). The dead-man uses **both** channels; the 5 critical jobs use
the **gh** channel as their alternate (their primary Telegram line still rides
the gateway — the gh copy covers the Telegram-outage case while the gateway is
alive; the dead-man covers the gateway-dead case).

`alert-sink.sh` never exits non-zero and never blocks its caller; all
outcomes receipt to `~/.hermes/logs/critical-alerts.log`.

### 1.4 Alternate sink wired into the 5 critical jobs
Selection: the review named no specific five, so the five **estate-keeping,
no-agent, alert-capable** jobs were chosen (the watchdog layer whose silence
hides estate failure):

| Job (hermes cron) | Script | Patch point |
|---|---|---|
| estate-hourly-sync | `estate-sync.sh` | `fail()` |
| estate-nightly-mirror | `estate-nightly.sh` | `fail()` |
| session-gc | `session-gc.sh` | failure output path |
| compression-tripwire | `compression-tripwire.py` | `emit_alert()` at both cron-driven alert sites |
| litellm-config-tripwire | `litellm-config-tripwire.py` | `emit_alert()` at change + missing-file sites |

Backups of all six edited scripts: `*.bak-20261026-t6d5d076f` beside them.

### 1.5 Test receipts (all 2026-10-26, gateway never touched)
- `--dry-run`: `dead=False, heartbeat age 10s (pid 2028136, alive)`.
- `--simulate-stale`: full path exercised — **real TG DM delivered**
  (chat 8158007517, message from `ga01_kanbanops_23_bot`), **gh issue #2
  created → auto-commented → CLOSED** by the self-test; live state file
  untouched (`{}`).
- alert-sink gh channel alone: issue **#1** created → commented → **CLOSED**.
- litellm-tripwire wiring: synthetic target (scratch `fake-litellm.yaml`) →
  alert printed AND gh issue **#3** created → closed with explanatory comment.
- system-crontab tick: `16:55:01 alive: heartbeat age 8s` in
  `logs/gateway-deadman.log` — runs standalone, gateway-independent.

## 2. ER-6 — Log rotation, RAID mirroring of logs, card-log prune

### 2.1 logrotate (user-mode, no system paths)
Deliberately **not** `/etc/logrotate.d` (writing system config paths is
operator-gated; all targets are inside `~/.hermes`, owned by arch, so no root
is involved — a strictly smaller privilege footprint):

- config: `~/.hermes/scripts/logrotate-hermes.conf`
- targets: `/home/arch/.hermes/logs/*.log` **and**
  `/home/arch/.hermes/profiles/*/logs/*.log`
- policy: `weekly`, `maxsize 20M` (early rotation on size), `rotate 8`,
  `compress`, `delaycompress`, **`copytruncate`** (live gateway/agents hold
  open fds — files are copied then truncated in place, never moved),
  `missingok`, `notifempty`, `dateext`.
- driver (arch crontab, **daily 02:50**, before the 03:17 estate nightly):
```
50 2 * * * /usr/sbin/logrotate -s $HOME/.hermes/state/logrotate.status \
  $HOME/.hermes/scripts/logrotate-hermes.conf >> $HOME/.hermes/logs/logrotate.log 2>&1
```
- **Dry-run first** (`logrotate -d`): ~700 log files enumerated across root +
  all profiles, everything correctly "does not need rotating", the one size
  breach (23.6 M `tui_gateway_crash.log`) showed the exact copy→truncate plan.
- **Real first run (receipted)**: `tui_gateway_crash.log` 23,679,846 B →
  `tui_gateway_crash.log-20261026`, live file truncated to 0, gateway
  heartbeat fresh throughout (16:51:52) — copytruncate proven safe on the
  running gateway. No bounce.

### 2.2 Rotated logs in the nightly RAID copy, NOT in the GitHub mirror
`estate-nightly-target.sh` (`push_nightly`) now also copies, into every dated
nightly set at `/local/backups/hermes-estate/nightly-<date>/` (0700,
owner-only, 14-set retention):
- `logs/root/` ← whole `~/.hermes/logs` (live + rotated `.gz` + the card-log
  prune archive below)
- `logs/profiles/` ← every `profiles/*/logs` tree (include-filtered rsync,
  prune-empty-dirs; leakage-checked: 0 non-log files)

Non-fatal on rsync failure (a logs-only failure must not lose the DB sets).

**GitHub mirror stays clean** (redaction is deliberately OFF — logs carry
secrets): estate-sync's exclude list already drops every `logs/` dir and
`*.log` file. Proven post-change by replicating the exact `RSYNC_EXCLUDES`
array in dry-run: **0** paths touching `logs/`, `.log`, or
`card-log-archive` would transfer.

Isolated end-to-end `push_nightly` test (scratch target, fake repo/big args):
254 M nightly set built with all log components present, perms 700, `push_rc=0`.

### 2.3 Card-log prune (14 d, tar-verified, GRAVEYARD-style pairing)
Extended `session-gc.sh` (daily 02:30, root registry — no new cron):
- Scope: `t_*.log` **older than 14 days** across `~/.hermes/kanban/logs` and
  the whole `~/.hermes/kanban/boards` tree (archived boards included).
- **ARCHIVE-NOT-DELETE canon**: files are tarred to
  `~/.hermes/logs/card-log-archive/card-logs-pruned-<date>.tar.gz` and every
  entry is **verified inside the tar before any deletion** (diff of sorted
  lists; on any mismatch nothing is deleted).
- The archive tars ride the RAID logs copy (see 2.2) and are themselves
  pruned after **90 days** by the same step.
- One-line receipt per prune ("Non-empty stdout = deliver a notice").

**First real run (receipted 2026-10-26 16:53)**: 362 card logs >14 d
(31 MB raw; all under `boards/_archived/*`) →
`card-logs-pruned-2026-10-26.tar.gz` (30.9 MB, gzip-verified, 362/362
entries), files deleted, `find -mtime +14` now returns **0** fleet-wide.

## 3. Operational notes / follow-ups
- The dead-man and logrotate live in the **system crontab**, so they do NOT
  appear in `hermes cron list` — the AS-BUILT cron table re-stamp (ER-12,
  card t_4b0f48d6) should add both rows (crontab source kept at
  `~/.hermes/scripts/.crontab-arch-t6d5d076f`; pre-change backup at
  `~/.hermes/backups/crontab-arch.bak-20261026-t6d5d076f`).
- Threshold tuning: dead-man stale = 45 min, re-alert = 6 h; logrotate
  maxsize = 20 M / weekly / rotate 8; card-log prune = 14 d / 90 d archive.
  All are single-constant edits.
- gh-issue dedupe is per-tag with one open issue; operators closing an issue
  mid-incident causes the next alert to open a fresh issue (by design).
- ER-7 (DR drill) deferred by operator pick — not done here.
