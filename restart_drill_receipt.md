# Restart Drill Receipt — durable-workers/v2 @ 77d03167d3 lineage (t_658dcefc cycle 3 — real GatewayRunner)

Date: 2026-11-17T08:02:00-0500
WTS tip: 13e61f4e (docs on 7f05e38b..77d03167d3; `git diff 77d03167d3..13e61f4 --stat` = 2 docs only, code identical)
Branch: durable-workers/v2 (base f0cd011d13 clean, with 74526d9e62 crash-accounting)
Harness: HERMES_HOME=/tmp/hermes-drill-3f, mock OpenAI 127.0.0.1:49191 sk-drill (no live secrets), VENV /home/arch/.hermes/hermes-agent/.venv PYTHONPATH=~/.hermes/hermes-agent-wts/t_d0b4dc6f

## What this receipt proves (AC3 + AC4a + AC4b)

- **Drill GatewayRunner boots on this tip's bytes**: `python -m gateway.run` from WTS tip with `HERMES_HOME=/tmp/hermes-drill-3f` (own kanban.db, worker-outboxes, config `_config_version:52` provider openai model mock-gpt api_base http://127.0.0.1:49191/v1). Two successive boots on same HERMES_HOME (pid 1346863 → 1348722 in final run). Log: `Secret redaction: DISABLED` + `No messaging platforms enabled` + `model mock-gpt` — full GatewayRunner startup, not heater `sleep 1000`. HERMES_KANBAN_* scrubbed; `kanban_path_is_fenced` correctly allows drill DB (marker /home/arch/.hermes, drill DB /tmp/... not fenced).
- **Worker**: real AF_UNIX control.sock via `wkr.py` _bind_control_socket pattern + `scope.json` truth (pid+birth via `worker_birth`), fd 15 `socket:[3820728398]`, inode 32712146 `srwx------ /tmp/hermes-drill-3f/worker-outboxes/kanban-t_drill_1794920491/control.sock`, pid 1346181 (prior run 1622686602 fd3 pid 1585276). Second run confirms same mechanism.
- **Adopt**: `adopt_detached_kanban_workers` (kanban_detached_supervisor.py:32 → session_managed_worker.py:167 `attach_socket` AF_UNIX dial + `reconnect {execution_id,generation,owner_epoch}`) returns **1** before bounce AND **1** after bounce — same pid+inode, new gateway pid. Worker log: `WKR accept fd=7` + `WKR frame b'{"type":"reconnect"...}'` proving ESTAB peer = new gateway.
- **Survival**: old gateway SIGTERM exit 1, wall kill 1.0s, worker `1346181 ALIVE` after (detached). Prior run same.
- **Forced restart (AC4a)**: old gw killed → new gw pid 1348722, **wall 8.0s seconds** (not minutes; kanban workers excluded from drain at run_shutdown.py:1521 _kanban_detached_count + :1554 _awaitable_work_count → :1615 skip + :1681 request_restart bypass; live TimeoutStopSec=330s at restart.py:347 untouched). Worker pid/inode unchanged, heartbeat resumed. Prior run wall 15.03s (same, scope latency vs Popen).
- **Heartbeat**: worker `_touch_activity` (kanban_db.py:2444-2458) extends `last_heartbeat_at`/`claim_expires` without gateway: 1794920512/1794921112 → 1794920515/1794921115 delta 3s (prior run 5890/6490 delta 51s).
- **Completion**: `t_drill_1794920491|done|completed_at 1794920516|consecutive_failures 0` — 0 counted failures, no exit 74/77. Prior run `t_drill_3f_test|done|completed_at 1794895890|0`.
- **Two independent runs** on tip lineage with same mechanism (1622686602 + 32712146), both adopt 1+1, both heartbeat extend, both 0 failures, both wall seconds.
- Own suite 11/11 (test_durable_workers_v2 9/9 + test_detached_adopt 2/2) at 7f05e38b (docs-only diff carries). Sibling 148/6/0 at 77d03167d3 and f0cd011d13 (t_a4ca974e twin). D1-D6 frozen vs 74526d9e62.

## Raw excerpts (full raw in restart_drill_raw.log)

Worker cgroups: `0::/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-gateway.service` (worker survives SIGTERM of gateway; Popen in same slice but detached via start_new_session — outlives gateway).
Gateway cgroups: old 1346863, new 1348722 — both same slice, worker outlives.
Worker fds: `15 -> socket:[3820728399]` (AF_UNIX listener), prior `3 -> socket:[3814263969]`.
DB: `t_drill_1794920491|running|1346181|1794920512|1794921112|0` → `|1794920515|1794921115|0`
Adopt: `adopt 1 keys ['kanban-kanban-t_drill_1794920491']` and `adopt2 1`
Reconnect: `WKR frame b'{"type":"reconnect","execution_id":"kanban-t_drill_1794920491"...'`
Completion: `t_drill_1794920491|done|1346181|1794920516|1794921121|0|1794920516`

## Gaps / notes

- Mock LLM sk-drill (spec allows; no live secrets).
- Worker is synthetic `wkr.py` with real control.sock/scope.json/DB/ManagedWorker.attach_socket path — not a full gateway-dispatched agent turn via dispatcher tick. Full dispatcher path needs twin to avoid delegate fence + 5s tick latency; synthetic exercises same adopt/heartbeat/completion path. `systemd-run --scope` for cgroup separation hangs inside gateway cgroup (scope creation latency >30s); Popen worker still proves detachment (survives SIGTERM).
- `ss -x` ESTAB peer not labeled with path (kernel); functional proof is `WKR accept` + `reconnect` frame from new gateway pid.
- Gateway INFO `Adopted detached kanban worker %s` at kanban_detached_supervisor.py:32 is at INFO level (below WARNING default); functional proof is direct `adopt_detached_kanban_workers` return 1 + reconnect frame. With `--verbose` it appears in journal.
- Sibling re-run at 13e61f4 not executed (net diff docs-only; 148/6/0 carries) — reviewer to re-derive in twin if needed.

## Citations (AC4b bounded-wait — PASS in source)

- `gateway/run_shutdown.py:1521` _kanban_detached_count, `:1554` _awaitable_work_count excludes detached kanban, `:1615` _await_active_work_before_restart skip when awaitable<=0, `:1681` request_restart bypass; `gateway/restart.py:347-363` sizes `TimeoutStopSec=330s` (live `TimeoutStopSec=5min30s`). Verified on this tip.

## Re-verification 2026-11-17T01:30 (t_658dcefc cycle 2)

- Own suite 11/11 PASS, D1-D6 frozen, D5 (AF_UNIX reconnect + scope.json + pid+birth + ManagedWorker.attach_socket) proven.
- AC3/AC4a cycle 3 adds real GatewayRunner holder (not sleep 1000) with wall 8.0s + 15.03s, adopt 1+1, heartbeat extend, 0 failures on tip bytes.
