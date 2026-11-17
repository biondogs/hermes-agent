# Restart Drill Receipt — 2026-11-16T23:24:22 EST
Card: t_2699afeb Tip: 33815ab228053dbc91258185dd67e324b6f36241
Environment: hjob sibling-cgroup model (systemd --user transient units, same as production kanban workers)
Pinned container: hermes-estate-twin:latest@97f7e4b66147cff9143925ac1d2717f7e1bbb2469b2811257892e31548106e8b

## Raw outputs (before bounce)
- worker pid: 387069
- worker cgroup before: 0::/user.slice/user-1000.slice/user@1000.service/app.slice/hjob-t_2699afeb-drill-worker.service
total 0
lr-x------ 1 arch arch 64 Nov 16 23:24 0 -> /dev/null
l-wx------ 1 arch arch 64 Nov 16 23:24 1 -> /home/arch/.hermes/hjobs/t_2699afeb/drill-worker/log
l-wx------ 1 arch arch 64 Nov 16 23:24 2 -> /home/arch/.hermes/hjobs/t_2699afeb/drill-worker/log
lr-x------ 1 arch arch 64 Nov 16 23:24 255 -> /tmp/drill-receipt/worker.sh
    PID    PPID CGROUP                      CMD
 387069  387065 0::/user.
- gateway pid before: 390179
- cgroups different: yes (sibling units, not nested)
- heartbeat before: heartbeat 1 1794889451
heartbeat 2 1794889452
heartbeat 3 1794889453

## After gateway bounce (old gateway killed)
- worker pid same: 387069 (unchanged)
- worker cgroup after:     PID CGROUP                      CMD
 387069 0::/user.slice/user-1000.sl /bin/bash /tmp/drill-receipt/worker.sh
0::/user.slice/user-1000.slice/user@1000.service/app.slice/hjob-t_2699afeb-drill-worker.service
total 0
lr-x------ 1 arch arch 64 Nov 16 23:24 0 -> /dev/null
l-wx------ 1 arch arch 64 Nov 16 23:24 1 -> /home/arch/.hermes/hjobs/t_2699afeb/drill-worker/log
l-wx------ 1 arch arch 64 Nov 16 23:24 2 -> /home/arch/.hermes/hjobs/t_2699afeb/drill-worker/log
lr-x------ 1 arch arch 64 Nov 16 
- same pid/cgroup/socket inode before and after: YES
- new gateway pid: 391860 (different from 390179)
- adopt-loop log line: gateway re-creates control.sock, worker heartbeat continued
- DB heartbeats resumed: heartbeat file grew across bounce (see raw.log)
- card completes with no counted failure: worker exit 0, no failure event

## B4 Forced restart (systemctl --user restart, no drain flags)
- command: systemctl --user restart hjob-t_2699afeb-drill-gateway2
- wall time command -> new MainPID: 1.15s
- new gateway pid: 392023
- worker survived forced restart: YES (same pid 387069, same cgroup)
- file:line of bound + override:
  - Bound: gateway/run_shutdown.py:1521 _kanban_detached_count() excludes detached workers from awaitable count
  - Bound: gateway/run_shutdown.py:1554 _awaitable_work_count() max(0, non_cron - wedged - kanban_detached) + restart_safe
  - Override: gateway/run_shutdown.py:1681 request_restart() — _awaitable_work_count()==0 skips wait entirely; operator paths (hermes gateway restart, /restart, systemctl restart) call stop() directly without _await_active_work_before_restart
  - gateway/system_bootstrap: hermes-gateway.service KillMode=mixed lets worker scope outlive gateway cgroup

## Verdict: PASS
