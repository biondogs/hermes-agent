# RFE DRAFT — Kanban dispatcher worker checkpoint/resume on graceful drain/restart

**Status: DRAFT ONLY — not filed. Upstream submission goes through the operator final gate
(distiller gate → OPERATOR GO → sha256 match → agent files byte-exact).**
**Origin: estate review 2026-10-26, restart-kills-workers item, ER-1(c). Prepared for
NousResearch/hermes-agent. Target surface: GitHub issue/feature request (not a PR).**

---

## Title (one line)

Kanban dispatcher workers: checkpoint-and-resume (or at minimum drain-wait) on
graceful gateway drain/restart, instead of orphaning in-flight runs

## Body

### Problem

A graceful gateway restart (SIGUSR1 deferred drain, systemd stop, dashboard
restart) drains its *active work aggregate* before exiting:
`gateway/run_shutdown.py::_drain_active_agents` waits (up to
`agent.restart_drain_timeout`) for in-flight chat turns, cron jobs, API runs and
deferred agent workers, and only then interrupts the remainder.

**Dispatcher-spawned Kanban worker processes are not part of that aggregate.**
Kanban workers are one-shot agent sessions launched by the embedded dispatcher
(`kanban_worker_client` → a fresh agent run per claimed card, often 100k+ tokens
of accumulated context). When the gateway exits:

1. In-flight workers are orphaned (reparented, then dead or wedged) — the next
   gateway's dispatcher reaps them as zombies (`reap_worker_zombies`), which is
   where the classic "zombie worker flood" log lines come from.
2. Every interrupted card loses the *entire* run's progress; the dispatcher
   retries it from scratch on the new gateway. On a heavily loaded host this is
   the single largest recurring token waste: a long-lived deployment with
   continuous multi-agent load can reap hundreds of orphaned workers in a
   couple of days, each reap representing a full session of input tokens spent
   for nothing.
3. The interruption is booked as a worker crash and consumes the card's
   consecutive-failure budget, so a restart window can park cards
   `gave_up` without them ever having run to completion under their own steam.

Today the only knobs are contextual: `agent.restart_drain_timeout` bounds the
drain for the work the gateway *does* track, and downstream users patch the
dispatcher locally to hold claim/spawn ticks while the drain is pending. None
of that saves in-flight worker sessions.

### Requested behavior

Treat dispatcher workers as first-class drainable work, with a
checkpoint/resume path rather than an orphan-and-retry path:

1. **Drain membership**: include live claimed workers in
   `_drain_work_counts()` / `_drain_active_agents()`, bounded by a separate,
   smaller budget (workers are long; the drain should not block the full
   `restart_drain_timeout` on them, e.g. a `agent.worker_drain_timeout` floor
   of 60–300 s).
2. **Checkpoint request**: when a worker's drain budget expires, send it a
   checkpoint request instead of (or before) SIGKILL:
   - the worker's conversation transcript is already durable in
     `state.db`; what is missing is a *resume pointer*: stop at the next
     tool-call boundary, record
     `(task_id, run_id, session_id, last_message_id, exit_status='drained')`,
     and exit cleanly;
   - expose a lifecycle hook (`on_drain_checkpoint`) so worker logic can
     flush partial artifacts / external side effects before exiting.
3. **Resume, not cold retry**: after restart, the dispatcher re-queues a
   `drained` card with a resume hint (prior session id) so the worker
   reconstruction path continues the transcript instead of re-reading the
   card and re-doing completed steps.
4. **Budget honesty**: a `drained` interruption must be a non-counting
   requeue — it must not consume `consecutive_failures` (suggested sentinel
   exit code, distinct from quota/config sentinels, recognized by the
   dispatcher's exit-decode path).

### Suggested interface sketch

```text
agent.restart_drain_timeout      # existing: chat/cron/API/deferred budget
agent.worker_drain_timeout: 120  # NEW (default 0 = today's behaviour)
tasks table:  + drain_state TEXT   -- NULL | 'checkpoint_pending' | 'checkpointed'
events kind:  'worker_checkpointed' {session_id, last_message_id}
worker exit:  0 on clean checkpoint; sentinel exit code (e.g. 76) on drained-kill
lifecycle:    on_drain_checkpoint(worker) -> flush, then exit
```

### Alternatives considered (and why insufficient)

- **Bigger `restart_drain_timeout`**: only delays; workers routinely run
  longer than any acceptable drain bound, so a hard cutoff is still needed.
- **Dispatcher-side "no spawn while draining"**: prevents *new* spawns from
  burning budgets during the window (a common local patch) but does nothing
  for in-flight sessions.
- **Planning-with-files discipline** (workers persist their own plan/state
  files and rebuild): workable stopgap that repo-level conventions can adopt
  today, but it is per-workflow discipline, not infrastructure — every lane
  has to opt in, and nothing enforces the resume contract.

### Out of scope / non-goals

- Generic process-level CRIU-style snapshots — too heavyweight and
  platform-bound; a transcript-level resume pointer is portable.
- Changing retry/reclaim semantics for genuine crashes — only
  drain-attributed interruptions become non-counting.

---

## Filing checklist (for the operator-gate card, NOT for this draft)

1. Distiller gate on this text → gated bytes frozen → sha256 recorded.
2. OPERATOR GO comment on the filing card (operator's own words, verbatim).
3. Byte-exact submission by an agent to the upstream repo (issue), read-back
   verification, `killed-by-decision` chain close on a No.
4. Leak scan must pass before the gate: no internal hostnames/paths, no fleet
   or board identifiers, generic metrics only (already applied to this draft).

*Draft prepared 2026-10-26 by the estate lane; no upstream API calls made.*
