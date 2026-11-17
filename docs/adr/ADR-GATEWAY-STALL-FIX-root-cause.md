# ADR: Root-cause analysis — recurring gateway-stall false positives + the 05:19 false "failed" alert

**Status:** Accepted — diagnosis complete, implementation cards filed
**Date:** 2026-11-17
**Card:** `t_d478965e` (GATEWAY-STALL-FIX)
**Author:** sw-architect
**Related:** `t_b5e645e7` (crash RCA, 14/48 "gave up" = 20–60 s stalls), `t_506ca319` (durable-workers apply), `t_e11c48e1` (early-tier stall-watch)
**Worktree / branch:** `wt/t_d478965e-gateway-stall-fix` at `72475f092a` + ADR commit (see Handoff)

---

## 1. What was observed

* **106 early-tier dumps** (`~/.hermes/logs/gateway-stall-dumps-early/`): 32 on 2026-11-16, 74 on 2026-11-17 by 12:50 UTC, nominally "about one every 10 min" (e.g. 07:20, 07:30, 07:40).
* **One false "failed" alert** at 2026-11-17 05:19:39 for cron `bf4a11d10802` (`g02-wake-driver-vigil`, every 20 min delivered to `g02-butler`). The same turn completed at 05:19:59; every later run shows `ok`.
* **Cron timeline for the false alert:**
  * 05:18:20 — restart-safe worker `pid 4004545` handed the execution.
  * 05:19:07 — `Cron bf4a11d10802 paused with unverified admission ... Gateway connection failed; no local fallback`.
  * 05:19:36 — `Restart-safe cron worker exited with status 1 after adopting this execution, without writing a durable terminal state`.
  * 05:19:39 — failure alert to operator.
  * 05:19:59 — `Job 'g02-wake-driver-vigil' completed successfully` (side effects ran; the bookkeeping path is what broke).

---

## 2. What is actually stalled (and what is not)

### 2a. The "every 10 min" pattern is a rate-limiter artefact, not the stall cadence

| Fact | Evidence |
|------|----------|
| The early tier's dump throttle is `EARLY_DUMP_MIN_INTERVAL = 600 s` (`gateway-stall-watch.py:87`). | A heartbeat that naturally sits at 22–27 s for ~10 s every 30 s cycle therefore produces *at most one dump per 600 s*. |
| The underlying cadence is visible in the raw log, not the file list. On the live host at 07:52–07:56 the 5 s sampler shows `17s -> 22s (rate-limited) -> 27s (rate-limited) -> 2s -> 7s -> 12s -> 17s -> ...` every 30 s. | `~/.hermes/logs/gateway-stall-watch.log` 07:52–07:56 (8 cycles); same pattern 18:40–12:50 window. |

**Conclusion:** the file-per-10-min series is an alias of the sampling/throttle policy. The question is why the heartbeat spends ~10 s per cycle above 20 s at all.

### 2b. Why the heartbeat routinely reaches 20–30 s

The loop-liveness heartbeat is `gateway/shutdown_watchdog.py:loop_heartbeat_forever` — an asyncio task:

```
while True:
    await asyncio.to_thread(write_loop_heartbeat, ...)   # atomic_json_write via thread pool
    await asyncio.sleep(30.0)                             # DEFAULT_HEARTBEAT_INTERVAL_S
```

Nominal peak age is therefore `30 s + write time`. With the early threshold at `20 s` (`gateway-stall-watch.py:86`) the heartbeat is "stalled" for `10 s` of every `30 s` window even in perfectly healthy operation: 4,205 of 13,010 early samples on 2026-11-16/17 logged as `early stall age 2Xs`, with only 108 dumps kept by the 600 s throttle (`grep -c "early stall"` vs `grep -c "early dump"` in the window).

**File:line:** `gateway/shutdown_watchdog.py:34` (`DEFAULT_HEARTBEAT_INTERVAL_S = 30.0`) vs `~/.hermes/scripts/gateway-stall-watch.py:86` (`EARLY_STALL_SECS = 20`).

### 2c. Real event-loop blocks do occur, on the same code every dump points at

Three or more dumps agree on the hot path (all `pid 160054`, 2026-11-17):

| Dump | Main-loop thread | Executor thread(s) |
|------|-----------------|---------------------|
| `early-20261117T062346Z-age23s` | **active** — `agent/secret_scope.py:386 load_env_file` -> `build_profile_secret_scope` -> `tui_gateway/launch_profile_policy.py:167 owner_secret_scope` -> `gateway/run.py:1814 _profile_runtime_scope` -> `gateway/session_hosted_service.py:259 _ensure_hosted_service` -> `gateway/run_startup.py:884 _hosted_room_worker_watcher` | — |
| `early-20261117T071421Z-age28s` | **active** — `pathlib resolve` -> `_is_process_home` -> `owner_secret_scope` -> same `_profile_runtime_scope` / `_ensure_hosted_service` / `_hosted_room_worker_watcher` | — |
| `early-20261117T104836Z-age29s` | **active** — `genericpath:isdir` -> `pathlib:is_dir` -> `gateway/session_authorities.py:343 owner_scope` -> same `_ensure_hosted_service` / `_hosted_room_worker_watcher` | — |
| `early-20261117T073451Z-age27s`, `074516Z-age22s`, `041121Z-age21s`, `085631Z-age26s`, `105901Z-age23s`, `115946Z-age27s`, `124046Z-age23s` | idle (`select`/`run_forever`) | `gateway/hosted_rooms_common.py:142 table_columns` -> `hosted_rooms.py:401 _schema_is_current` -> `467 _read_connection` -> `926 list_rooms` -> `tui_gateway/hosted_room_service.py:225 bindings` -> `gateway/session_hosted_service.py:100 bindings` -> `tui_gateway/hosted_room_driver.py:481 _run_cycle` (up to 4 concurrent room threads, 5 s poll) |

Every dump with an active stack is either:

* the **main asyncio thread blocked on synchronous filesystem I/O** inside the 1 Hz hosted-room watcher (`run_startup.py:881 _hosted_room_worker_watcher, interval=1.0` -> `session_hosted_service.ensure_hosted_service` -> `owner_secret_scope` does `load_env_file` + `is_dir` + `realpath` inline on the loop), or
* a **burst of `hosted_room_driver._run_cycle` bindings checks** — each opens a SQLite connection and runs `PRAGMA table_info`/`table_columns` — queued on the gateway's thread pool and contending with `shutdown_watchdog.write_loop_heartbeat`'s `asyncio.to_thread` hop for the same pool. When the executor saturates, a 30 s heartbeat slips to 32–35 s apparent age; with the 20 s threshold that registers as a 20–30 s "stall."

Neither requires a pathological slow disk: a burst of 2–4 SQLite `table_columns` probes plus a single `load_env_file` is enough to push one heartbeat past the 20 s line.

---

## 3. How this maps to the 05:19 false cron failure

The failing code path is `cron/scheduler_authority.py:run_canonical_job -> observe()`:

* The firer writes `cron/admissions/<hash>.json`, then `connect_gateway()` + `rpc('cron.submit', ...)` to admit the run on `g02-butler`.
* If that RPC drops (`GatewayRPCError`) it tries **one** `recover()` call. If that also misses (gateway's event loop mid-`owner_secret_scope` or its heartbeat executor hop queued — see above), it raises `CronExecutionUnknown` immediately.
* The caller (`cron/scheduler.py:3461`) catches `CronExecutionUnknown` -> `pause_for_unknown()` + `give_up_execution()` -> logs `paused with unverified admission ... Gateway connection failed; no local fallback` -> the waiter (`_wait_for_external_cron_worker`) sees worker exit 1 and emits `external_worker_exited_reason()` (`cron/scheduler_worker_failure.py:49`) -> Telegram alert.
* The side effect (71 s terminal command) finishes on `g02-butler` — the admission had landed, the worker just gave up proving it.

A few seconds of event-loop hiccup is amplified into a user-visible "failed" alert by a single-attempt recovery.

---

## 4. Decision

### 4a. Stall signal — make it truthful (no false 20–30 s "stalls")

**(i) Lower the heartbeat interval to 15 s.** At 30 s a 20 s threshold has zero slack (10 s of every 30 s window is above it). At 15 s a 20 s age is genuinely late (needs one missed write + queuing). `EARLY_STALL_SECS` stays `20` so the alert still covers the 20–60 s window; the early and 60 s tiers are reconciled rather than re-tuned in opposite directions. Alternative rejected: raising to 32 s alone halves detection of real stalls; lowering only the threshold to 32 s hides the 20–30 s class the operator asked to catch.

* Files: `gateway/shutdown_watchdog.py:34` (`DEFAULT_HEARTBEAT_INTERVAL_S`), `~/.hermes/scripts/gateway-stall-watch.py:86` unchanged.
* Revisit when: heartbeat-mtime is replaced by the tick-socket scheduling witness.

**(ii) Stop blocking the event loop with synchronous filesystem I/O in the fast path.** Offload `ensure_hosted_service`'s `owner_secret_scope` / `owner_scope` probes (and `load_env_file` / `is_dir` / `realpath` they call) onto `run_in_executor` / `housekeeping_executor`. Route `GatewayStartupMixin._hosted_room_worker_watcher` and `_ensure_hosted_room_worker` through an off-loop helper.

* Files: `gateway/run_startup.py:875-885` (`_ensure_hosted_room_worker`, `_hosted_room_worker_watcher`), `gateway/session_hosted_service.py:253-259`.
* Revisit when: the hosted-room fast path is re-homed off the 1 Hz watcher entirely (follow-up in `t_506ca319`).

**(iii) If twin repro still shows heartbeat slip under a many-room config, cap concurrent `table_columns` probes or cache `_schema_is_current` per driver generation** — low-priority, not gating this ADR.

### 4b. Cron false alert — tolerate a brief gateway outage

**One retry with backoff before `CronExecutionUnknown`.** In `cron/scheduler_authority.py:run_canonical_job.observe()` on the `GatewayRPCError -> recover()` path, retry `recover()` up to 2 more times with `0.5 s` then `2 s` sleep (total budget <= 60 s). Only if all attempts return `missing` raise `CronExecutionUnknown`.

* Covers the 20–30 s stall window plus margin without changing the durable-state contract (`unknown` still means "may have run — never re-fire or book as failed").
* Files: `cron/scheduler_authority.py:81-116` (`observe` inside `run_canonical_job`), no change to `cron/scheduler.py:3461` caller.
* Test: `tests/cron/test_cron_authority_recover_retry.py` — 60 s disconnect mid-run ends `completed` with no alert; genuinely `missing` still alerts+pauses.
* Revisit when: cron transport moves off gateway RPC (follow-up under `t_506ca319`).

Alert gating for true failures (`scheduler_worker_failure.external_worker_exited_reason`, `record_unknown_worker_outcome`) is unchanged; only the transient-hiccup path no longer fires.

---

## 5. Consequences

* Positive: early-tier dumps become selective for real stalls (expect near-zero in steady state vs 106 in 18 h); operator stops receiving false cron "failed" alerts for brief gateway blips; hosted-room watcher no longer adds latency to every turn.
* Negative: heartbeat writes 2x as frequent (15 s vs 30 s) — negligible I/O; at most 2.5 s extra delay on the unverified-admission path.
* Risk: if 15 s heartbeat is itself delayed by fsync, it still has 5 s slack vs zero. Existing two-witness (`loop_tick_socket`) covers sustained fs stalls.

---

## 6. Alternatives rejected

* **Raise only `EARLY_STALL_SECS` to 32 s:** hides 20–30 s stalls the operator explicitly asked to cover; leaves 1 Hz sync-I/O block.
* **Rewrite probe to tick socket only:** correct long-term, but not the cause of false positives (threshold/interval mismatch is).
* **Mute cron alert on `unknown` altogether:** would suppress genuine never-admitted failures.
* **Move hosted-room watcher to a thread unconditionally:** larger behavioral change; minimal fix is to offload just the sync probe.

---

## 7. Non-goals (explicitly out of scope)

* Replacing `atomic_json_write` or eliminating `table_columns` probes wholesale.
* Changing cron transport away from gateway RPC (owned by `t_506ca319`).
* Upstream filing — gated pipeline only, per constraint.

---

## 8. Coordination with `t_506ca319` (durable-workers)

`durable-workers/v2` touches `cron/scheduler.py`, `cron/scheduler_authority.py`, `cron/executions.py`, `cron/jobs.py`, `agent/managed_worker.py`, `agent/runtime_session_store.py`. To avoid a merge tangle:

* This fix overlaps only on `cron/scheduler_authority.py` (20-line retry in `observe()` isolated from handoff/ownership changes). Land either first; the other rebases with a one-hunk conflict.
* This fix does **not** touch `cron/scheduler.py` waiter bookkeeping or `agent/*`.
* Sequencing: `t_d478965e` dev cards land as the next PR on `main` after `t_506ca319` apply if both ready, or ahead with a rebase. Live bounce goes through `kanban-board-architect` graceful drain; single-flight bounce lock enforces ordering. The bounce must not block or delay an operator-requested restart (standing condition 2026-11-16, `drain_control.py`).

---

## 9. Handoff

* Design branch: `wt/t_d478965e-gateway-stall-fix` — this ADR + optional `docs/design/GATEWAY-STALL-FIX.md`.
* Implementation cards filed from this card: `GATEWAY-STALL-A` (heartbeat + off-loop, `sw-dev-a`) and `GATEWAY-STALL-B` (cron retry + regression test, `sw-dev-b`), with review gate `sw-reviewer`.
* Twin verification: `hermes-estate-twin` red->green + stall-rate before/after on live once landed (dev card acceptance).
* Commit hash of this ADR recorded in `kanban_complete` metadata below.
