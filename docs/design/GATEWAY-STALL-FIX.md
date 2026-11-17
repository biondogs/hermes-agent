# GATEWAY-STALL-FIX — Implementation Design (supplement to ADR)

> **ADR:** `docs/adr/ADR-GATEWAY-STALL-FIX-root-cause.md` (commit `abd01dab8a`)
> This doc is the task DAG + per-card change list the implementers execute. No new
> decisions here — it expands the ADR into files-touched / tests / forbidden zones.

## DAG

```
t_d478965e (sw-architect) ── ADR committed (abd01dab8a)
   ├─► GATEWAY-STALL-A  (sw-dev-a)  heartbeat + off-loop watcher
   └─► GATEWAY-STALL-B  (sw-dev-b)  cron recover retry + regression test
            \_____________► GATEWAY-STALL-REVIEW (sw-reviewer) parents=[A,B]
                              └─► t_506ca319 coordination + live bounce via kanban-board-architect
```

* A and B are independent (different file sets; B touches `cron/scheduler_authority.py` which
  also appears in `durable-workers/v2` — see ADR §8 for merge plan).
* Both must pass on `hermes-estate-twin` before the review gate fires.

## Card A — heartbeat interval + off-loop watcher

**Files to change:**
* `gateway/shutdown_watchdog.py:34` — `DEFAULT_HEARTBEAT_INTERVAL_S = 30.0` → `15.0`
* `gateway/run_startup.py:875-885` — introduce `_ensure_hosted_service_offloop()` helper
  that runs `session_hosted_service.ensure_hosted_service` via `asyncio.to_thread`
  (or `_run_in_executor_with_context` where context propagation matters); route
  `_ensure_hosted_room_worker` and `_hosted_room_worker_watcher` through it.
* `gateway/session_hosted_service.py:253-259` — no structural change; document that
  `ensure_hosted_service` is now always called off-loop (add comment).

**Files NOT to change:** `~/.hermes/scripts/gateway-stall-watch.py` (estate script, not
in this checkout; threshold stays 20 s — the interval fix makes it selective).

**Tests:**
* `tests/gateway/test_loop_heartbeat_interval.py` — assert 15 s interval; twin red→green
  by temporarily reverting to 30 s.
* Existing `tests/gateway/test_gateway_heartbeat*` and `tests/gateway/test_shutdown*`
  must still pass.

**Twin repro (red→green):** with `DEFAULT_HEARTBEAT_INTERVAL_S=30` + synthetic
`hosted_room_driver` load (4 concurrent `table_columns` bursts), early-tier false stalls
fire every cycle; with `15 s` + off-loop watcher they stop.

## Card B — cron recover retry

**Files to change:**
* `cron/scheduler_authority.py:81-116` (`observe()` inside `run_canonical_job`) —
  on `GatewayRPCError → recover()` returning `missing`, retry `recover()` up to 2 more
  times with `0.5 s` then `2 s` sleep (total window ≤ 60 s inclusive). Only if all
  return `missing` raise `CronExecutionUnknown`. Update docstring.
* No change to `cron/scheduler.py:3461` caller (still catches `CronExecutionUnknown`
  → `pause_for_unknown`/`give_up_execution`).

**Tests (new):**
* `tests/cron/test_cron_authority_recover_retry.py`
  * `test_brief_gateway_disconnect_is_retried` — mock gateway RPC to drop for 10 s
    then recover `queued`; run completes `completed`, no `CronExecutionUnknown`, no pause.
  * `test_60s_disconnect_still_recovers` — drop for 25 s then recover `started` → completed.
  * `test_genuinely_missing_still_fails` — `recover()` returns `missing` 3 times →
    `CronExecutionUnknown` → `pause_for_unknown` called, execution `unknown`, alert emitted.
  * `test_real_failure_still_alerts` — worker exits 1 with `missing` terminal ledger →
    review that the durable-worker alert path still fires (not silently swallowed).

**Twin repro:** inject a `connect_gateway` transport failure for 20 s during a cron fire;
before the fix the run ends `unknown` with an operator alert, after it ends `completed`.

## Common constraints

* Twin first; `~/.hermes/scripts/hjob` or `ci/hermes-upstream/run-branch.sh` for twin,
  `twin-test` for estate twin.
* No `~/.hermes` live writes from tests; no upstream filing without gated pipeline.
* `hermes-estate-twin` image tag+sha receipt required on each dev card.
* Coordination with `t_506ca319` per ADR §8 (single overlap file `cron/scheduler_authority.py`).
