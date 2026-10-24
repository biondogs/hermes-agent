---
name: hermes-gateway-graceful-bounce
description: "Use when the Hermes gateway needs a graceful drain-bounce."
version: 1.0.0
author: kanban-board-architect
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, restart, sigusr1, graceful, bounce, kanban]
    related_skills: [hermes-agent, kanban-orchestrator]
---

# Hermes Gateway Graceful Bounce (operator ruling 2026-10-24)

**OPERATOR RULING (2026-10-24, card t_d2f0a30f):** Hermes agents MAY restart the **Hermes gateway**. The approved method is the detached SIGUSR1 graceful-drain bounce (proven t_df30ec0c 2026-10-23 and t_01b7847b run 117 2026-10-24). This supersedes "gateway restarts are operator-only" **for the Hermes gateway ONLY** — container / aistack / LiteLLM / serving-pod restarts remain OPERATOR-ONLY, and the NON-DISTURBANCE/SERVING LAW is unchanged.

## When to Use

- The gateway needs a restart (config/plugin hotfix activation, dispatcher wedged).
- A card demands a "gateway bounce".
- `hermes gateway restart` gets blocked by approvals — the block means "use this skill", never "find another way".

## The one sanctioned path

```bash
# preflight / status (never bounces, safe anytime):
bash ~/.hermes/scripts/gateway-graceful-bounce.sh --self-check

# the bounce (self-detaches via setsid; survives the caller's death):
bash ~/.hermes/scripts/gateway-graceful-bounce.sh --reason "<why - goes in the audit receipt>"
```

Everything else is **forbidden**:
- `hermes gateway restart` — approval-blocked in single-query mode; do NOT retry it, do NOT use `--yes`.
- `kill -USR1 <pid>` by hand — what run 117 did after the block, back when no sanctioned path existed; do not repeat it. (Note: the approval detector does NOT flag bare `kill -USR1` — the gate is this skill's process rule, not the detector.)
- Hand-rolled per-card bounce scripts (gateway-bounce-v110.sh / gateway-bounce-fix2.sh are retired specimens, kept only as receipts under /local/projects/software-co/patches/).
- NO escalation EVER: if the PID doesn't change within the drain cap, the script aborts with a FAILURE receipt — never `--yes`, never SIGKILL, never a second signal. A failed bounce goes to a human (kanban_block, kind=needs_input).

## When an approval block stops any OTHER dangerous command

Do NOT work around it. No setsid escape hatches, no alternate kill paths, no chaining through scripts. `kanban_block` the card with the exact blocked command and hand the action to the operator. The approval gate is law for everything except this script's sanctioned path.

## The initiating worker WILL die — the death-march pattern

The gateway drains and restarts, killing in-flight worker runs (they auto-retry; proven twice). Therefore:

1. **Bank first**: post the receipt `kanban_comment` on your card BEFORE triggering — what you changed, commit hashes, and the instruction "retry run: verify from ~/.hermes/logs/gateway-bounce-receipts.log and complete". A `kanban_heartbeat(note=...)` with the same pointer also survives.
2. **Trigger detached**: invoke `bash ~/.hermes/scripts/gateway-graceful-bounce.sh --reason "..."` from a terminal call; it self-detaches (setsid) and returns immediately. Never run it with `--foreground` from inside a worker.
3. **Let the retry verify**: your run exits with unknown outcome and the dispatcher re-queues the card. The retry run reads the durable receipts and completes — including the **full addendum-B triage round** and the operator summary (see the triage section above).

## Board notices — operator addendum A (2026-10-24, declared mid-t_d2f0a30f)

Every agent-initiated restart notifies **all 7 boards**, not just the operator:
- **BEFORE triggering** (the script does this automatically between pre-flight and the signal): a one-line `[GATEWAY-RESTART-NOTICE]` comment on every **running** card of each board — those are exactly the runs the restart can interrupt. A board with no running cards gets its notice on the most recently touched non-archived card; a completely empty/archived board gets a receipt-line notice instead (documented in the receipts as `NOTICE-PRE <board> skipped`). Path picked and documented: the env-scrubbed cross-board hermes CLI (`hermes -p kanban-board-architect kanban --board <slug> comment <id> <text> --author kanban-board-architect`), which reaches the card threads (retrying workers read them) and the per-board audit history. Content: initiator, reason, expected drain window (≤30 min), card/receipt pointer.
- **AFTER the restart is verified**: a one-line `[GATEWAY-RESTART-DONE]` comment on the same targets (`NOTICE-POST` receipt lines). One line each, no spam — never a second ping for the same event.

## Post-restart triage round — operator addendum B (2026-10-24)

After the gateway is verified back up, EVERY board gets a triage pass. The script auto-emits the read-only snapshot (running count, running-without-heartbeat >20 min, crashed/timed-out since the bounce epoch, blocked cards carrying "gateway disconnected" errors) as `TRIAGE <board> …` receipt lines with a PASS/ISSUES verdict. The **initiating card's retry run** then completes the full pass on all 7 boards:
- interrupted cards: retried and re-claimed, or stranded? (re-queue stranded cards via the sanctioned env-scrubbed CLI `unblock`/`promote`, with receipts)
- stale/orphaned claims (dispatcher stale-reclaim is 4 h — reap sooner only via sanctioned CLI `reclaim`, with receipts)
- runs crashed/timed out since the restart; cards stuck `running` with no heartbeat; blocked cards with new "gateway disconnected" errors
- missed notifications and butler/bot reachability per board (log greps: `✓ telegram connected (profile: <butler>)`; delivered-event lines in the owner profile's `gateway.log` per the crossboard-ops rule)
- safe hygiene may be fixed directly WITH receipts; anything structural becomes a recommendation for the operator
- deliverables: per-board PASS/ISSUES table appended to the restart receipt (`~/.hermes/logs/gateway-bounce-receipts.log` or the run log) + a short operator summary (one Telegram line via the bounce script's post line, or a `hermes send` if something needs attention)

## What the script enforces (do not defeat)

- **Single-flight**: flock at `~/.hermes/scripts/.gateway-graceful-bounce.lock`; a concurrent bounce aborts (exit 3).
- **Rate limit**: **1800 s (30 min)** minimum interval between bounce triggers; earlier attempts abort (exit 6) and still notify the operator.
- **Pre-flight**: counts running cards on ALL 7 boards + managed workers; prefers a quiet window but does NOT abort on in-flight work — the gateway's own deferred drain (cap 1800 s, core #77184) finishes live chat turns before stop(). Kanban worker runs die and auto-retry; that is the accepted cost, so don't bounce without cause.
- **Graceful signal, once**: `kill -USR1 <MainPID>` → gateway logs "SIGUSR1 received … graceful gateway restart", drains, exits; `systemd --user` relaunches `hermes-gateway.service`.
- **Post-bounce verification** (script-side, into the receipts): new MainPID ≠ old; unit `active` + journal `Started` marker; gateway.log boot banner "Starting Hermes Gateway..."; dispatcher boot marker "kanban dispatcher: holding singleton dispatcher lock"; default-bot "✓ telegram connected" + same for all 5 butlers (g01-butler, g02-butler, gaudi-butler, sjproto-butler, swco-butler); per-card status of every pre-bounce running card (running=respawned / ready=re-queued / done).
- **Operator notifications**: exactly ONE line before (starting … reason) and ONE after (complete … PIDs … butlers … cards … triage headline) via `hermes send -t telegram:8158007517`, PLUS the addendum-A board notices above. The gateway also sends its own shutdown notification; don't add more.

## Receipts

- One line per event: `~/.hermes/logs/gateway-bounce-receipts.log` (START / HANDOVER / VERIFY / SUCCESS|PARTIAL / FAILURE / ABORT).
- Full run log: `~/.hermes/logs/gateway-bounce-runs/<UTC-ts>.log`.
- End state must read SUCCESS in the receipts before you declare victory in card metadata.

## Allowlist / ownership

`command_allowlist` of kanban-board-architect carries the explicit sanction entry naming this script (the terminal invocation `bash ~/.hermes/scripts/gateway-graceful-bounce.sh …` is not flagged by the approval detector; the entry is the declarative, auditable sanction required by the ruling). **kanban-board-architect owns the bounce**; every other profile escalates to it (do not fan the skill or the allowlist entry out — butlers and workers shall not bounce).

## Truthful receipts (companion law)

Receipts must attribute actions to their **actual actor**. Never record an action you (or an agent) performed as "performed by the operator" — run 119's `gateway_restart: "OPERATOR-ONLY; performed by operator"` on t_01b7847b was false (run 117 did it itself via a detached script) and had to be corrected by comment. If the actor can't be determined from evidence, write "unattributed (evidence: …)".
