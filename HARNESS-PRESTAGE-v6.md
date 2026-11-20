# Harness Pre-stage v6 — DURABLE-WORKERS-3n (t_813ee499)

## S-4 Layout Decision

**Finding:** Turn process `agent.managed_worker` runs in unit cgroup
(`hjob-*.service`), not in `hermes-worker-kanban-*.scope`. On a real unit
stop with `KillMode=mixed, TimeoutStopSec=330`, systemd cgroup teardown kills
the worker regardless of F1/F2 process-level guards.

**Decision:**
- For production unit `hermes-drill-3f.service`: `KillMode` change is
  required (to `control-group` or `process` so remaining processes survive stop).
  `TimeoutStopSec=330` stays frozen per binding rule. **This is an OPERATOR decision**
  -- NOT applied here; re-drill card will carry the `needs_input` ask with exact
  drop-in needed.
- For throwaway drill (hjob unit): unit is created with `KillMode=process`
  (transient property via `systemd-run -p KillMode=process`) so the worker outlives
  the hjob unit stop. This is the layout used for S-2 proof.

## Fresh Worktree

`/tmp/wt-v4` on tip `fc04c19a` (v6). Verified clean.

## Throwaway Card Design

- New card title `DRILL-v6-kanban-survive` assignee `sw-dev-a`,
  body: foreground-compatible hold via `terminal` tool (timeout within limit),
  then `kanban_complete` scripted before final answer. Min duration 10 min.
- `t_27ff3bf6` is archived -- not reused.

## Mock Redesign (S-5)

- Shared mock on `:49191` was archived/down. New mock: per-drill throwaway mock
  server on ephemeral port, started by drill driver.
- Hold mechanism: Use tool with timeout < foreground limit (60s), loop via model
  iteration, not `sleep 620`/700 which auto-backgrounds and leaks 2 proc/s.
- Terminal step: mock scripts `kanban_complete` tool call then final response.

## Exact Re-point Command (POSTED, NOT RUN)

See card comment for the full systemd-run + PYTHONPATH=/tmp/wt-v4 drill sequence
with HERMES_HOME=/tmp/hermes-drill-v6, fresh card, hjob unit lifecycle via
python driver (as reviewer did in /tmp/drill3m_driver.py pattern).

NOT executed this run (binding rule: live drill on operator GO).

## Cleanup Plan for /tmp/hermes-drill-3m

- `/tmp/hermes-drill-3m`: left by reviewer (archived cards, idle pid 1206436
  self-exits at 600s). Safe to rm -rf after operator GO.
- Leaked `sleep 620` wrappers: ~800 pids from reviewer drill, auto-decay ~11m.
