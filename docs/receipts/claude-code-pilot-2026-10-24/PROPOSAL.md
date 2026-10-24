# Proposal: capacity-trend guard for /mnt/models on gpu417

Status: PROPOSED, review only. Nothing applied, no cluster access, nothing validated on a live
Prometheus or with promtool. All placeholders are listed at the top of each artifact.

## Artifacts
| File | Purpose |
|---|---|
| `proposed-alerting-rules.yaml` | Recording + alerting rules (exact PromQL) |
| `proposed-node-exporter-static-pod.yaml` | Eviction-resistant node-exporter (item 5) |
| `proposed-capacity-snapshot.sh` | Weekly du/df snapshot: TSV receipt + textfile metrics |

## 1. Baseline
- Primary: `node_filesystem_{avail,size}_bytes{mountpoint="/mnt/models",fstype="xfs"}` from node-exporter
  (assumed present; confirm the mount isn't excluded by `mount-points-exclude`).
- node-exporter only gives whole-mount totals, so the weekly cron script adds per-tree sizes
  (depth 2, so `hf/rnd5-muse-spark` is separate from Beam and misc). It writes a TSV receipt
  and a `models_capacity.prom` textfile (`models_tree_bytes{tree=...}`), so the trend is graphable in Grafana.
- Receipt location is a placeholder (`RECEIPT_DIR`); point it to the existing receipts store. The script
  refuses to write onto the monitored filesystem.
- Cron `17 3 * * 0`, `nice`/`ionice` idle; du on a few huge files is cheap.

## 2. Alerts and thresholds
Mechanism: Prometheus rule file (or PrometheusRule CRD). No Alertmanager, so "firing" is observed via
`/api/v1/alerts`, the `ALERTS` series and Grafana. Nothing is pushed anywhere; someone/something must look.

| Rule | Condition | Rationale |
|---|---|---|
| ModelsFsUsedWarning | used >= 80% for 15m | Spec warn. **Already true today (~82%)**, so it fires immediately on load. That is correct, but expect it to be permanently on until space is freed. |
| ModelsFsUsedCritical | used >= 85% for 2m | Spec critical. |
| ModelsFsEvictionImminent | used >= 83% for 5m | See below. |
| ModelsFsWillHit85Within24h | `predict_linear(bytes_to_85pct[6h], 86400) < 0` | Catches the declining trajectory, e.g. a stage-in, before the level thresholds. |
| NodeDiskPressure | kube-state-metrics DiskPressure condition | Independent of node-exporter; the episode is underway. |
| PodsEvictedRecently | `kube_pod_status_reason{reason="Evicted"}` | Cluster-wide (metric has no node label); tighten on live data. |
| *SeriesMissing / TelemetryBlind / NodeExporterDown | `absent()` / `up==0` | Blind-spot guard: missing data must alert, not look healthy. Blind = both sources absent -> critical. |
| ModelsFsSnapshotStale | snapshot timestamp >8d or absent | Guards the cron itself. |

**Finding: the 85% critical has no lead time.** Kubelet evicts at `imagefs.available < 15%`, which is
used > 85%, and image GC's high threshold is also 85%. An alert at >= 85% (+ `for: 2m`) fires at or after the
kubelet starts. So I added the 83% rule and the predictive rule; recommend making the 83% rule the actual
paging threshold. Arithmetic: with ~3.5T capacity, 85% is ~2975G and current use is ~2850G, so headroom is
only ~125G, roughly one mid-size model stage.

Independence of exporters: used-ratio is recorded from node-exporter *and* from kubelet cAdvisor
(`container_fs_usage_bytes / container_fs_limit_bytes` on the imagefs device; device regex is a placeholder),
combined with `max by (node)`. kube-state-metrics gives the DiskPressure condition. Kubelet's own metrics
survive a node-exporter eviction.

Also note: node-level reclaim (image/container GC) cannot help here. containerd is 4G; the other ~2.8T is
non-container data, so the kubelet's reclaim finds nothing and moves straight to evicting pods, repeatedly.

## 3. Governance
All items are files in this directory. Applying needs: (a) a rules file/CRD on the obs Prometheus + reload;
(b) a root-owned cron + script on gpu417; (c) a static-pod manifest dropped into gpu417's kubelet
`staticPodPath` and a scrape config. Each is a separate, human-approved change; none is assumed present.

## 4. Trade-off: raise evictionHard vs. move the containerd root
Raising/overriding `evictionHard` (or lowering `imageGCHighThresholdPercent`) is cheap and reversible, but it
only moves the wall. If anything it makes it worse: raising `imagefs.available` makes the node evict *earlier*,
while lowering it (e.g. 5%) buys headroom but leaves the kubelet with little disk margin before real ENOSPC on a
filesystem that mostly holds non-reclaimable 2.3T battery-critical data and a live 469G serving tree. It's a kubelet
restart/config change per node and drifts from the rest of the fleet. Moving the containerd root (and kubelet
ephemeral dirs) off `/mnt/models` to a small dedicated disk/partition fixes the coupling: the imagefs signal
then measures only images (4G), model staging can't cause pod evictions, and `/mnt/models` filling up becomes
an application capacity problem that fails a stage-in instead of evicting pods. It costs a node drain, a containerd data
migration/re-pull and a spare device. **Recommendation:** the root move is the cleaner structural fix; use a
temporary evictionHard relaxation only as a bridge while the work is scheduled, and keep the alerts either way.

## 5. Eviction survivability (the hard part)
Kubelet node-pressure eviction is a node-local loop. It is not the scheduler. On `imagefs.available<15%`
it first tries reclaim (nothing here), then ranks pods and kills them: first those using more of the starved
resource than they requested, then by pod priority, then by overage relative to requests. It ignores PDBs and
taints/tolerations (tolerations only affect scheduling and the NoExecute taint manager, not this loop).

What survives:
- Rules (Prometheus on obs node), receipts, cron and script (host files/crond): not pods, unaffected. Not
  affected unless the script itself fills the disk (it writes KBs; and it is guarded to not write to /mnt/models).
- node-exporter as a normal DaemonSet pod: **does not reliably survive**. It is non-critical, so it is evicted
  under the ranking, and the DS controller recreating it is useless: while DiskPressure is set the kubelet's
  admit handler rejects non-critical new pods, so it stays down for the whole episode, exactly when the alerts matter.
  The textfile metrics go with it.

Mechanisms that sound right but do not work:
- Tolerating `node.kubernetes.io/disk-pressure` (DS controllers already add it): affects scheduling only.
- PodDisruptionBudget: eviction-API only; node-pressure eviction ignores it.
- Affinity/nodeSelector/preemption/QoS class alone: scheduler concepts or rank inputs, not immunity. QoS
  Guaranteed doesn't shield you for disk, where ranking is usage-vs-request of the starved resource.
- The removed `scheduler.alpha.kubernetes.io/critical-pod` annotation.
- `priorityClassName: system-node-critical` on a DaemonSet alone: better ranking, and maybe skipped as
  critical, but still API/controller-managed and version-dependent. Acceptable fallback, not the primary answer.

Chosen mechanism: **a kubelet static pod with explicit `spec.priority: 2000001000`** (plus matching
`priorityClassName`), tiny ephemeral-storage request/limit, `imagePullPolicy: IfNotPresent` (image must already
be on the node; a pull under pressure could fail), and the textfile directory on a hostPath. Reasons:
1. Kubelet owns the lifecycle directly: it restarts it even with the API server or DS controller unavailable,
   and it is not subject to the controller-recreate -> admission-rejection loop.
2. Critical/static pods are the class the eviction manager is built to exempt (and the admit handler lets
   through under pressure). Static pods don't get priorityClass resolution, so the value is set directly.
3. Even if a given kubelet version ranks it normally, a ~0-usage pod with 64Mi ephemeral request and top priority
   is last in the ranking.
4. hostPath textfile dir, not emptyDir, so snapshot metrics outlive the pod.

Caveat: I can't verify the kubelet version's exact behavior offline; check that the cluster's eviction manager
skips critical/static pods (source `eviction_manager.go` / test by `kubectl` on a scratch node) before relying on it.
Residual risk: the guard shares the starved imagefs; the pod's image must be pre-pulled and `/var/lib/kubelet`
needs write space for logs. True ENOSPC can still kill it, hence the cAdvisor/kube-state-metrics sources and the
`absent()` blind-spot rules as backstops.

## Effort estimate
- Rules: ~2h with live validation (promtool check, real label names, cadvisor device).
- Snapshot script + cron + receipt location: ~1h, plus one dry run.
- Static pod + scrape job + port/coexistence with existing exporter: ~2-3h incl. a staged test on a non-critical node.
- Version check of kubelet eviction behavior: ~1h.
- (Optional) containerd root move: ~1 day per node plus a drain window (the Muse-Spark lane is non-disturb, so schedule with its owner).
