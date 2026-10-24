# PILOT TASK — g02-ops lane replay (Claude Code vs qwen38-flash-fp8 track record)

You are composing review-only infrastructure artifacts (governance: PROPOSE ONLY, apply nothing). Offline exercise — no cluster access is available; a production run would validate every expression on the live Prometheus before hand-off.

## Facts (verbatim from the card)
gpu417 /mnt/models (3.5T xfs, holds the containerd imagefs root) was 93% → ~82% after deleting GLM-5.3-Int4-Int8Mix (378G). Remaining composition: 2308G Muse-Spark battery-critical (hf/rnd5-muse-spark/**, non-disturb lane), 469G Beam serving live, ~66G misc, containerd 4G. Free space is on a structurally declining trajectory: any future model stage onto 417 hits the same imagefs DiskPressure wall (kubelet default imagefs.available<15%, no evictionHard override), and non-critical pods (local-volume-provisioner DS) absorb the evictions.

## TASK: propose a capacity-trend guard for /mnt/models on gpu417
1. Baseline: weekly du snapshot of /mnt/models top-level trees + df%, stored where receipts are already kept; align with the existing Prometheus/Grafana stack on the obs node via a node-exporter filesystem metric for the xfs mount if one exists — otherwise a cron du snapshot. Deliver the snapshot script.
2. Alert proposal: warn at /mnt/models ≥80% used, critical ≥85% (85% is the image-GC high threshold; alert must fire BEFORE kubelet evicts). Specify the exact mechanism (Prometheus recording/alerting rules; note the stack deliberately runs no Alertmanager — rules must be visible in Grafana/API anyway). Assume standard node-exporter (node_filesystem_*) and kube-state-metrics metric names; make coverage independent of any single exporter where reasonable, and guard the metrics-blind-spot case (rule firing when telemetry is missing).
3. Governance: deliver everything as proposed artifacts (files) + a short proposal doc; apply NOTHING, no cluster mutations, no assumptions that anything will be installed.
4. Also include one paragraph trade-off note: raising evictionHard vs moving the containerd root off /mnt/models as the cleaner structural fix.
5. THE HAIRY PART — think carefully about kubelet eviction semantics: when imagefs DiskPressure evicts pods from the node, which of your artifacts would actually survive, and what is the correct mechanism to keep node-exporter (the metric source for these alerts) alive through an eviction episode? Several plausible-sounding mechanisms do NOT work here; reason from kubelet's actual eviction behavior (it is not the scheduler, and taints/tolerations do not bind it). Choose the correct mechanism for the artifact file and justify it in the proposal doc.

## Deliverables (files in this directory)
- proposed-alerting-rules yaml (all rules, exact PromQL)
- proposed node-exporter protection artifact (the mechanism you determined for item 5)
- proposed capacity snapshot script (bash)
- PROPOSAL.md: mechanisms, thresholds, per-rule rationale, effort estimate, the trade-off paragraph, the eviction-survivability justification
Do NOT: modify anything outside this directory, run network commands, or attempt cluster access.
