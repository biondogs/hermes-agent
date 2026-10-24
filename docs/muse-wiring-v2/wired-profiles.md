# MUSE-WIRING-V2 — wired profiles (strength-match justification)

Operator GO 2026-10-22, card `default/t_5c5305bf`. Law: `default=muse` ONLY on
high-throughput mechanical lanes; orchestrator/reviewer/judgment seats stay on
glm53 / qwen38-flash-fp8 (1.9× TTFT drift and temp-lane volatility do not
belong on the command path).

| Profile | Board / role | Why it qualifies |
|---|---|---|
| kanban-worker | all boards — global `default_assignee` | Highest-volume grunt lane; mechanical fallback execution, short tool loops. Biggest throughput win. |
| g01-scribe | gargantua01 | Runbook/decision-log prose at high card cadence; no command authority (delegation disabled). |
| g02-scribe | gargantua02 | Same scribe lane on the production k8s board. |
| sw-docs | software-co | Docs engineering from merged code; mechanical transform, explicitly not a judgment seat. *(inclusion re-confirmed by operator ruling 2026-10-24 — see note below)* |
| sw-dev-a | software-co | Implementer lane A: mechanical implementation against sw-architect's spec. |
| sw-dev-b | software-co | Implementer lane B: parallel mechanical lane. |
| sw-qa | software-co | Test-ladder authoring/execution with receipts; mechanical loop work. |
| sw-devops | software-co | Build/deploy/teardown execution; deny-listed from production containers at the approvals layer. |

## Deliberately NOT wired

- **Command path**: kanban-orchestrator (`kanban.orchestrator_profile`, global
  decomposer), kanban-board-architect, g0[12]-orchestrator, g0[12]-planner,
  sw-architect, sw-reviewer, g01-orchestrator/planner — glm53 judgment seats.
- **Serial law / observe-and-decide seats**: g01-ops, g02-ops, sj[.]-ops,
  sjp-ops — kept on qwen38-flash-fp8 by design (command-path law).
- **Watcher/auditor seats** (g0[12]-watcher, g0[12]-auditor, gaudi-auditor,
  sj[.]-auditor, sjp-auditor): low-volume judgment/rerun-determinism lanes.
- **Gaudi decision seats** (gaudi-arch/planner/orchestrator/perfeng/
  benchrunner/deployer/liaison/synapse/sysadmin — glm53): campaign judgment.
- **research**: open-ended synthesis, not a mechanical lane.
- **distiller, sampling-test, default**: special-purpose / test seats — left
  alone to keep the blast radius minimal.

Every wired profile's next spawned worker resolves `default=muse` with ctx
pin 262144 and Hermes-side fallback to qwen38-flash-fp8 (see rollback
manifests/ for prior state and revert commands).

**Note — sw-docs (operator ruling 2026-10-24):** sw-docs inclusion in the muse
temp lane was briefly ruled out by an operator disposition of 2026-10-24
morning (would have made this a 7-profile lane); that ruling was **RESCINDED
later the same day** ("Sw-docs can use muse") after the operator confirmed
sw-docs — a software-co board member — is allowed on the muse temp lane. The
lane therefore remains **8 profiles**; sw-docs' config was never changed
(`default=muse`, fallback qwen38-flash-fp8, verified by readback), and the
rollback manifest for sw-docs still describes the original pre-muse state.
