## Why

On the unified gateway runtime, a gateway-owned cron admission commits the run's `local-*` session row at submit — **before** `run_job`'s early gates run. Every early return skipped finalization entirely, because the `finally` block only finalizes a store the run itself opened:

- monitor no-change suppression
- `wakeAgent=false`
- blocked/empty payload
- config refusal
- failed store acquisition

The row stays `started` with zero messages forever, until session prune happens to reclaim it. A monitor job on a short interval leaks one never-active row per suppressed tick: #140222 reports it for monitor-gated jobs ("gate runs after canonical admission"), and #143785 measured 484 never-active rows in 16h — 95% of that deployment's profile sessions.

Fixes #140222. Fixes #143785.

## What changes

2 files, +70, of which 26 lines are tests. One new function and two hook points; no change to any run's outcome.

`_end_suppressed_cron_session()` ends the pre-committed row as `cron_suppressed` so session prune can reclaim it:

- writes through the **owner's lent handle** under the bounded proxy — never acquires a second borrow, never closes or releases the borrowed store;
- titles the row (job name + date, same shape as `_finalize_cron_session`) and stamps the resolved job workdir, so the row is identifiable in the sessions view instead of an untitled stub;
- best-effort and bounded, same contract as `_finalize_cron_session`: cleanup failures log at DEBUG and never change the run's result nor hold the dispatch guard.

Hooked at both early-exit points in `run_job`:

- the `early is not None` return (every early gate), and
- the `finally` path where the run raised or was blocked before its own store opened — or store acquisition failed — on a gateway-owned execution.

CLI-owned fires (`owner_execution is None`) never pre-commit an admission row, so the hook is a no-op there.

## Test plan and results

- New regression test `test_monitor_suppressed_tick_ends_owner_session_row`: a no-change monitor tick on a gateway-owned execution must `end_session(cron_suppressed)` the owner's row — the old code left it started forever. Passes on the branch.
- Full `tests/cron/` suite vs a main baseline on the same host: the set of failing test files is identical to the baseline — zero new failures. (The baseline itself has environment-dependent failures in this checkout; they are byte-for-byte the same set on both bases.)
- `scripts/check`: 12 checks ok; code health vs the merge base: 0 blocking, 0 advisory.
