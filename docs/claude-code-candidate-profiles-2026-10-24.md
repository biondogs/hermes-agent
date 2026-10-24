# Claude Code Candidate Profiles — 2026-10-24 (t_104ef76d)

**Question:** Operator stands up standalone `claude` CLI (OAuth'd, Pro-tier) on ga01. Which board profiles would see a *substantial* quality/capability improvement from delegating their card work to Claude Code vs their current model — and which would not?

**Method.** Read-only analysis; no profile config touched. Evidence base:
- Full profile roster + default models from `hermes profile list` and per-profile descriptions (`hermes profile describe`), 2026-10-24.
- Per-assignee task/run/event aggregates queried directly (read-only SQLite) across all 7 board DBs: `~/.hermes/kanban.db` (default) + `~/.hermes/kanban/boards/{gaudi,gargantua01,gargantua02,skipjack,skipjack-prototype,software-co}/kanban.db`. ~975 cards, all `task_runs.outcome` and `task_events.kind` records, `consecutive_failures`, `last_failure_error` text on every task.
- Signal hygiene: rerun counts are inflated by lane conventions. Most x2 `blocked → completed` runs are operator-GO gates (g02/sw FIX lanes), and sw-pm/watcher "runs" are scheduled wake-ups (one sw-pm card shows 38 runs — all wake ticks). Real struggle signals counted: `crashed`, `timed_out` (iteration-budget exhaustion), `reclaimed`, `changes_requested` rework loops, live `consecutive_failures > 0`, hallucination markers.

**What Claude Code actually buys** (per fleet skill `autonomous-ai-agents:claude-code`): an autonomous multi-step file-edit/test/commit loop with iterative self-correction. It does NOT buy: single-shot judgment quality (review/audit/distill lanes), long physical-runtime babysitting (bench windows, Azure deallocate windows), or infra stability (gateway disconnects happen above the model).

---

## Ranked candidates

### 1. sw-dev-a (software-co implementer lane A) — model: muse — STRONGEST CANDIDATE
**Workload fit: perfect.** 39 cards of exactly Claude Code's sweet spot: the mprov FIX series (real bug fixes + tests + changelog, one logical change per commit — mash#23/25/27, mprov_jobserver#168–177, mprov_control_center#313–332 …) and METATRON W1/W2 build-out (event spine, provider layer, browser editor front end). Full loop: worktree → code → run tests → commit → structured handoff.
**Struggle evidence (worst in fleet):**
- 7 `crashed` runs of 63 (11%) + 4 `reclaimed` + 2 review cycles — highest absolute crash count of any worker profile.
- **One card currently dead on the board:** t_6e194773 (METATRON-QA-READY) — crashed 3×, hit the dispatcher give-up limit (`gave_up: failures=3`), now blocked with `consecutive_failures=3`. Last outputs show the worker deep in a multi-step QA bring-up (browser `/editor/ws` 403s, dual-writer state-log issues) when it died — a long self-correcting debug loop where muse + helper crashes repeatedly stall out. The METATRON-W2-P5 editor card also took `crashed,crashed,crashed,completed` (4 runs) before landing.
- Caveat (honest): several crash errors read `Kanban owner refused: Gateway disconnected` — infra-level, which Claude Code delegation would *inherit*, not fix. But the near-miss completions (worker exits rc=1 after producing real QA findings, without landing the terminal kanban call) are the multi-step-loop fragility Claude Code's loop is built for.
**Verdict:** pilot first here. A ready-made A/B exists: re-run the stuck METATRON-QA-READY card type via Claude Code print-mode vs muse's 3-crash track record.

### 2. sw-dev-b (software-co implementer lane B) — model: muse — STRONG CANDIDATE
**Workload fit: identical to lane A** (32 cards: parallel half of the mprov FIX series, METATRON W1-3 provider layer, SCR answer threads).
**Struggle evidence:**
- 7 `reclaimed` runs of 54 (13%) — several WAVE0 cards (CC003/CC004/CC040) went `reclaimed,reclaimed → archived`, i.e. abandoned after reclaim, not landed.
- 1 genuine quality rework loop: METATRON-W1-3 (provider layer, OpenAI/Anthropic-compat endpoints) took `review_requested → changes_requested → review_requested → completed` (4 runs) — sw-reviewer required rework on a plumb-into-protocol piece.
- Zero cleanly-crashed runs (contrast lane A), so its failure mode is stalls/rework rather than crashes.
**Verdict:** pilot alongside lane A for a same-lane comparison; if account ceiling (t_b83974bc) only allows 2 profiles, pilot lane A + g02-ops instead and infer lane B from lane A.

### 3. g02-ops (gargantua02 infra-ops engineer) — model: qwen38-flash-fp8 (8B-class) — STRONG CANDIDATE, with scope caveat
**Workload fit: partial but high-value.** 117 cards (highest in fleet) of Azure production k8s ops: containerd data-root relocations, NVMe restaging, airgap pushes, vLLM smoke/chart ports, model batteries. The script/chart/debug composition (helm charts, ported gargantua-infra vllm charts, fstab/quota runbook items) is coding-adjacent and benefits from an agentic loop; live Azure mutations are operator-GO-gated, so Claude Code adds nothing there (by design).
**Struggle evidence:**
- 5 crashed + 1 timed_out + 1 changes_requested rework (t_7c1d2e12 capacity-trend guard: review → changes → review → completed) of 142 runs.
- **Structural model-capability failures visible in worker logs:** t_0524da73 dies mid-way with repeated `⚠️ Response truncated (finish_reason='length') — model hit max output tokens` (the 8B model can't sustain the dense change-ops reasoning chunks); t_cd00b936 shows 3× "worker exited cleanly (rc=0) without kanban_complete/block/review — protocol violation"; plus one logged `completion_blocked_hallucination` event. t_3323eb33 burned its full 500-iteration budget.
**Verdict:** strong candidate for the *engineering* fraction of its lane; the biggest single upside if wired, but pilot should use a scripting/chart-composition card, not a GO-gated mutation.

### 4. gaudi-benchrunner (gaudi board; also active on gargantua02) — model: glm53 — MODERATE CANDIDATE
**Workload fit: mixed.** Core work is protocol-driven container launches + long benchmark batteries (poor Claude Code fit — the bottleneck is physical run time and watch windows, not agent loop). BUT the GAUDI-CONTRIB-3 lane ("land fix PRs for our own #1855/#1846/#1860 (TDD, fork→ng)") is genuine TDD fix-PR coding, where the current model took `blocked,blocked,blocked → completed` (4 runs).
**Struggle evidence:** 4 `timed_out` runs, all `Iteration budget exhausted (300/300)` on battery cards (t_deb6eb11, t_880b805f, t_34b981b8, t_bf220396) — the agent burns hundreds of turns orchestrating long runs; a tighter loop could matter, but timeouts are partly bench-window physics. Archived predecessor q38p-benchrunner (72 cards) showed the same pattern (5 timed_out, 4 crashed) — this lane has historically run at the edge of its iteration budget.
**Verdict:** tier-2. Pilot only if budget allows a 3rd profile, and target the fix-PR sublane, not the benchmark batteries the card hypothesized. (Earlier assumptions that gaudi-perfeng is a top candidate don't hold: it has run 2 cards total, 1 reclaimed — no evidence.)

### 5. sw-ux (software-co front-end/UX engineer) — model: qwen38-flash-fp8 (weakest coder model in fleet) — WATCHLIST
Perfect workload fit (component code, styling, a11y, screenshot-verified UI work) running on the least capable coding model in the fleet, and 1 crash in only 2 software-co runs (plus 1 crash + 1 timeout in 3 g02 runs). Evidence volume is too small to rank higher (routing sends front-end-dominant cards elsewhere or dev lanes absorb markup). Wire opportunistically once wiring exists for sw-dev-a, before any further degradation of its workload.

---

## Explicit non-candidates (and why)

| Profile(s) | Why not |
|---|---|
| **distiller** (outbound gate, glm53) | Best-behaved profile on the host: 59/59 cards completed, 0 crashes, 0 reclaims, max 1 run/task. Single-shot verdicts — a bigger model adds nothing. |
| **sw-reviewer, sw-qa, all auditors (g01/g02/gaudi/sj/sjp)** | Read-only single-shot judgment lanes; all performing cleanly (sw-reviewer 13/13, sw-qa 2/2, g01-ops aside). Claude Code's autonomy is not the bottleneck. |
| **sw-pm** | 84 runs looks alarming until you see 44 `scheduled` outcomes — wake-driver ticks, not retries. Spec/intake prose; no code loop. |
| **sw-architect, all planners (g01/g02/sj/sjp/gaudi)** | Design/spec prose; single-shot. No struggle signal beyond ordinary blocks. |
| **butlers (all), watchers (all), scribes (all)** | Chat front-ends, monitoring wake-loops, transcription. Single-shot by construction; performing fine. |
| **g01-ops, sj-ops, sjp-ops** | Multi-step ops like g02-ops BUT no meaningful struggle signal (g01-ops: 15 completed / 1 crash; sj-ops: 28 completed / 1 reclaim; sjp-ops: 1 card). No case for spend. |
| **gaudi-synapse** | Best raw workload fit on the gaudi board (Habana TPC kernel / Synapse dev) but only ~2–5 runs ever, mostly reclaimed/archived. Insufficient evidence; re-evaluate when the lane gets volume. |
| **gaudi-arch / -perfeng / -analyst / -liaison** | Research, modeling, drafting lanes; single-shot. (liaison had 3 crashes on g02 — but it drafts prose, where Claude Code's loop doesn't apply.) |
| **kanban-board-architect, kanban-orchestrator, kanban-worker, plugin-ab, research, default** | Meta/orchestration/test lanes, not product coding. |
| **q38p-\* fleet** | Predecessor fleet, profiles no longer exist (72 archived benchrunner cards). Excluded — not live. |

---

## Recommendation for the pilot (t_93b6f033)

Pilot **2–3** profiles, in this order:
1. **sw-dev-a** — highest-value test: A/B a muse-troubled METATRON-style bring-up/QA card (or the still-stuck t_6e194773 type) via Claude Code print-mode vs the 3-crash muse track record.
2. **g02-ops** — tests the ops-engineering fraction: pick a chart-port / script-composition / runbook-implementation card (not a GO-gated Azure mutation).
3. **sw-dev-b** *(only if t_b83974bc's ceiling allows a third)* — a changes_requested-rework-style card (provider-layer equivalence) to test whether Claude Code ends review loops first-try.

Sequencing: sequential runs per the shared-account caution in t_93b6f033's design constraints; every invocation hard-bounded (`--max-turns`, budget cap).

Do NOT pilot: gaudi-benchrunner batteries, any butler/watcher lane, or the distiller gate.

---
*Source data: SQLite aggregates over all 7 board DBs, generated 2026-10-24 ~13:40 EDT; probe scripts in scratch workspace t_104ef76d. Research-only artifact — no profile config modified (per task constraint). Gate for t_93b6f033 (with t_b83974bc).*
