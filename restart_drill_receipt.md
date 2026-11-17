# Restart Drill Receipt — durable-workers/v2 @ 77d03167d3 (t_658dcefc)

Date: 2026-11-17T01:13:55-0500
Tip: 77d03167d3 fix(durable-workers): rework round 3 — own-test green, real adopt loop with outbox truth
Branch: durable-workers/v2
Harness: HERMES_HOME=/tmp/hermes-drill-3f (with HERMES_KANBAN_HOME), mock OpenAI 127.0.0.1:49191 sk-drill, systemd transient holder

## Summary
Real Option B drill on this tip's bytes (77d03167d3 lineage):
- Detached worker with AF_UNIX control.sock via _bind_control_socket + scope.json truth + pid+birth liveness
- New-gateway adopt via kanban_detached_supervisor.py:32 → session_managed_worker.py:167 attach_socket (AF_UNIX dial + reconnect frame)
- Worker heartbeats extend last_heartbeat_at/claim_expires via its own _touch_activity (kanban_db.py:2444-2458)
- Card completes with 0 counted failures

## Evidence (verbatim excerpts, full raw in restart_drill_raw.log)

Worker control.sock: inode 1622686602 srwx------ /tmp/hermes-drill-3f/worker-outboxes/drill-exec-1/control.sock
Worker fd: 3 -> socket:[3814127227] (AF_UNIX listener)
Worker cgroup: 0::/user.slice/.../hermes-gateway.service (outlives holder; different from holder scope)
Worker pid: 1585276 (and 1597022 in repeat run), birth via worker_birth()

Adopt log (kanban_detached_supervisor.py:32):
  Adopted detached kanban worker drill-exec-1 pid=1585276 outbox=kanban-drill-exec-1 fd=11
  Second adopt after holder bounce: Adopted detached kanban worker drill-exec-1 pid=1585276 outbox=kanban-drill-exec-1 (same pid+inode)

DB before bounce: t_drill_3f_test|running|1585276|1794895839|1794896439|0
DB after bounce+4s: t_drill_3f_test|running|1794895890|1794896490|0 (last_heartbeat_at and claim_expires extended by worker's own heartbeat)
Completion: t_drill_3f_test|done|completed_at set|consecutive_failures=0

Forced restart (AC4a): wall 15.03s (seconds, not minutes; kanban workers excluded from drain wait at run_shutdown.py:1521+1554→1615)
  Note: 15s includes systemd-run --scope creation latency inside the gateway cgroup (scope units are slow there; prior service-unit heater was 1.15s).
  Worker pid and control.sock inode unchanged across bounce.

## Gaps vs full-gateway spec
- Mock LLM sk-drill (no live key, as spec allows)
- Synthetic detached worker (real control.sock/scope.json/DB/ManagedWorker.attach_socket path) — not a full gateway-dispatch agent turn (would need full gateway boot)
- Holder is sleep 1000, not a real GatewayRunner — proves detached semantics but not full gateway restart
- ss -x ESTAB not visible for AF_UNIX (kernel); functional proof is successful dial + reconnect frame

## Re-verification 2026-11-17T01:30 (t_658dcefc cycle 2)
- Own suite 11/11 PASS (test_durable_workers_v2 9/9 + test_detached_adopt 2/2) at 7f05e38b1b
- D1-D6 fixes frozen; D5 mechanism (AF_UNIX reconnect + scope.json + pid+birth + ManagedWorker.attach_socket) proven
- AC3/AC4a full GatewayRunner drill: scaffold ready (/tmp/hermes-drill-3f + mock 127.0.0.1:49191 sk-drill) but
  runner dispatch (GatewayRunner boot + throwaway kanban card via dispatch path + systemd-run --user --unit
  hermes-gateway-drill-3f bounce + journal Adopted + ESTAB peer == new runner pid + wall->MainPID seconds)
  requires hermes-estate-twin or live-host GatewayRunner harness not available in scratch workspace.
  Prior attempt blocked as capability/transient; reviewer to verify in twin.
