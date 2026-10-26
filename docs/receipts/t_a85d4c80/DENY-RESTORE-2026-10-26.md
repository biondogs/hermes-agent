# DENY-RESTORE receipt — t_a85d4c80 (2026-10-26)

**Operator GO** (2026-10-26, via clarify, verbatim pick): "GO: restore the 28 lost blocked-command lists from the backup copy".

**Defect**: the LITELLM-YAML LAW sweep t_2fa0d71d (2026-10-25 ~10:39) REPLACED `approvals.deny` on 28 profiles with its single new entry instead of merging. Pre-swipe lists recovered from the estate mirror `~/hermes-estate` at commit `b86dbb92^` (path `hermes-home/profiles/<p>/config.yaml`).

**Restore rule**: `deny = <pre-sweep list, verbatim order> + ['*aistack/litellm/config.yaml*']` (law entry appended last). Line-level edit: every line outside the deny item block byte-identical (prefix/suffix line-diff verified, plus semantic YAML equality outside `approvals.deny`).

## Restored profiles (28/28)

| profile | pre-sweep count | live count before | after count |
|---|---|---|---|
| g01-ops | 14 | 1 | 15 |
| g01-planner | 5 | 1 | 6 |
| g01-watcher | 19 | 1 | 20 |
| g02-ops | 14 | 1 | 15 |
| g02-planner | 5 | 1 | 6 |
| g02-watcher | 19 | 1 | 20 |
| gaudi-arch | 14 | 1 | 15 |
| gaudi-deployer | 14 | 1 | 15 |
| gaudi-dockerops | 20 | 1 | 21 |
| gaudi-liaison | 19 | 1 | 20 |
| gaudi-perfeng | 19 | 1 | 20 |
| gaudi-planner | 5 | 1 | 6 |
| gaudi-synapse | 14 | 1 | 15 |
| gaudi-sysadmin | 27 | 1 | 28 |
| gaudi-watcher | 19 | 1 | 20 |
| kanban-worker-full | 4 | 1 | 5 |
| kanban-worker | 4 | 1 | 5 |
| sj-ops | 14 | 1 | 15 |
| sj-planner | 5 | 1 | 6 |
| sj-watcher | 19 | 1 | 20 |
| sjp-ops | 14 | 1 | 15 |
| sjp-planner | 5 | 1 | 6 |
| sjp-watcher | 19 | 1 | 20 |
| sw-dev-a | 4 | 1 | 5 |
| sw-dev-b | 4 | 1 | 5 |
| sw-devops | 18 | 1 | 19 |
| sw-qa | 4 | 1 | 5 |
| sw-ux | 4 | 1 | 5 |
| **total** | **345** | **28** | **373** |

## Untouched configs (32/60)

No pre-sweep `approvals.deny` at `b86dbb92^` — their current single law entry is correct as-is:

(root), distiller, g01-auditor, g01-butler, g01-orchestrator, g01-scribe, g02-auditor, g02-butler, g02-orchestrator, g02-scribe, gaudi-analyst, gaudi-auditor, gaudi-benchrunner, gaudi-butler, gaudi-orchestrator, gaudi-scribe, kanban-board-architect, kanban-orchestrator, plugin-ab, research, sj-auditor, sj-orchestrator, sj-scribe, sjp-auditor, sjp-orchestrator, sjp-scribe, sjproto-butler, sw-architect, sw-docs, sw-pm, sw-reviewer, swco-butler.

## Procedure & verification

- Run under `flock ~/kanban-backups/deny-restore-2026-10-26/.deny-restore.lock` (single lock file).
- Backups: 28 files at `~/kanban-backups/deny-restore-2026-10-26/<profile>.config.yaml.bak`, byte-verified against live before every write; backup count (28) == files changed (28).
- Two-pass: all 28 targets validated (parse, block location, cur == [law entry]) before any write; then per-file: pre-write candidate verification (YAML parses, deny == target, non-deny config semantically identical, line-diff confined to the deny block), write, post-write re-read verification.
- Attempt 1 hit a PyYAML pitfall (`yaml.safe_dump` per-scalar emits `...` document-end markers, corrupting the files post-write); all 28 were rolled back from the verified backups and rewritten with manual scalar quoting + a parse-before-write gate. Net result verified clean.
- `hermes -p <p> config check`: **28/28 PASS** (g01-ops, g01-planner, g01-watcher, g02-ops, g02-planner, g02-watcher, gaudi-arch, gaudi-deployer, gaudi-dockerops, gaudi-liaison, gaudi-perfeng, gaudi-planner, gaudi-synapse, gaudi-sysadmin, gaudi-watcher, kanban-worker-full, kanban-worker, sj-ops, sj-planner, sj-watcher, sjp-ops, sjp-planner, sjp-watcher, sw-dev-a, sw-dev-b, sw-devops, sw-qa, sw-ux).
- Sample diff (gaudi-sysadmin): purely additive deny item lines, law entry last; all other lines identical.
- No gateway restart (deny lists load on spawn). `/local/compose/aistack/litellm/config.yaml` never touched.
- Note: gaudi-sysadmin's pre-sweep list contained duplicate entries (`mount *` x2, `modprobe *` x2); restored verbatim per "restore the lost lists" — after count 27+1=28 preserves them.

Generated 2026-10-26 17:55:08  from receipt.json by t_a85d4c80 run.
