> Status: superseded by hermes-estate/docs/OPERATIONS.md — receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# PERF-PORT R6c — Session-reset discipline + 1-week token measurement

**Card:** t_f7c462b2 (PROMPT-DIET-ARCH) · **Date:** 2026-10-24 · **Lane:** kanban-board-architect
**Authority:** OPERATOR GO 2026-10-24 on the full plan of `docs/HERMES-PERF-PORTABILITY-STUDY.md` (757b729), item R6(c).
**Rules honored:** SOUL/skill edits only; no gateway restart; card parked with an armed wake driver instead of being held open.

---

## 1. What changed (receipt 1 of 2)

**A. SOUL.md — session-discipline section appended to all 10 heavy lanes**
(architect variant for `kanban-board-architect`; worker variant, byte-identical across all nine, for `sw-architect, sw-dev-a, sw-dev-b, sw-devops, sw-docs, sw-pm, sw-qa, sw-reviewer, sw-ux`):

> ## Long-Card Session Discipline (token budget — PERF-PORT R6c, 2026-10-24)
> This lane's sessions run multi-million cumulative input tokens when one card is ground out in a single sitting (fleet measurement 2026-10-24: sw lanes 1.3–4.2M toks/session avg, architect 5.06M; sessions reaching 174–223K context between compressions, each compression a 12–24 s blocking stall). Sessions are the cost unit — treat them like a budget:
> - **Bank receipts early.** After each completed step of a long card, `kanban_comment` the state: what is done, exact file paths, decisions made, the exact next action. A retry run or a fresh session must be able to continue from the card thread alone — nothing essential may live only in your in-session context.
> - **Checkpoint, then finish or hand off — don't grind.** When the remaining work is a separable phase, or context is getting heavy (many long tool outputs, compression approaching), stop cleanly: comment a checkpoint, then either `kanban_complete` with an explicit handoff (spawn a follow-up child card on the SAME board with `parents=[this]` for the remainder) or block with an armed wake driver for a time-gated continuation. A fresh session resuming from a banked checkpoint is cheaper and faster than a bloated context limping into compression.
> - **One card ≈ one sitting.** If the card needs more than one sitting, say so in the handoff and split — don't grind past the token cliff.
> - Scratch deliverables must be declared in `kanban_complete(artifacts=[...])` before the run ends.

The architect variant (`profiles/kanban-board-architect/SOUL.md`) replaces the first line with the lane-specific figures (5.06–5.09M avg, n≈100; 174–223K between compressions; 12–24 s p99 stall) and adds "Design decompositions so each card fits one sitting; split at create time — phase chains beat marathon cards."

**B. Skill — `devops/kanban-orchestrator` (authoring side)**, identical insert in BOTH copies (master `~/.hermes/skills/devops/kanban-orchestrator/SKILL.md` and `profiles/kanban-orchestrator/skills/devops/kanban-orchestrator/SKILL.md`, after "Skill-pin law"):

> ## Long-Card Session Budget (token diet — PERF-PORT R6c, 2026-10-24)
> Measured 2026-10-24 (t_cc6843d3 / t_f7c462b2): heavy lanes burn 1.3–5.1M cumulative input tokens per session (architect 5.06–5.09M avg, n≈100) running to 174–223K context between compressions; each compression stalls 12–24 s (the operator-visible p99). Sessions are the cost unit.
> - **Split multi-sitting cards at CREATE time** into a chain of phase cards (`parents=[...]`), never one marathon card; name the receipt cadence in the body ("comment a checkpoint after each phase — a retry run must be able to continue from the card thread alone").
> - **Prefer handoff over grinding:** when a worker's session runs long or a card has a separable remaining phase, the right move is complete-with-explicit-handoff + a follow-up child card (fresh session from a banked checkpoint), not extending the sitting to the token cliff.
> - Executors bank receipts early (`kanban_comment` state after each step: done/file paths/decisions/next action) and declare scratch deliverables in `kanban_complete(artifacts=[...])`.

Full unified diffs (all 12 files): `~/.hermes/kanban/workspaces/t_f7c462b2/r6c-diffs.txt` (148 lines; each insert verified present — 10 `## Long-Card Session Discipline` + 2 `## Long-Card Session Budget` headers). Fresh sessions pick these up automatically; no gateway restart needed (config-only/SOUL change).

---

## 2. BASELINE — measured 2026-10-24T22:50:46Z (receipt 1 of 2)

Method/fidelity: per-profile `state.db` `sessions` table; sessions with `last_activity_at` in window and `input_tokens > 0`; statistic = per-session cumulative input tokens. Script: `scripts/measure_r6c_tokens.py` (in this repo; `--json` for machine-readable). The 72h window reproduces the original study method — architect avg 5.06M / n=101 today vs the study's 5.09M / n=97 (same-day measurement), validating method equivalence.

| profile | 72h n | 72h avg | 72h med | 72h p90 | 72h max | 7d n | 7d avg | 7d med | 7d max |
|---|---|---|---|---|---|---|---|---|---|
| kanban-board-architect | 101 | **5.06M** | 3.67M | 10.62M | 31.84M | 131 | **4.40M** | 2.81M | 31.84M |
| sw-architect | 9 | 1.88M | 1.43M | 2.62M | 5.05M | 9 | 1.88M | 1.43M | 5.05M |
| sw-dev-a | 64 | **3.95M** | 1.65M | 11.27M | 22.57M | 64 | **3.95M** | 1.65M | 22.57M |
| sw-dev-b | 55 | **4.05M** | 1.77M | 12.17M | 23.56M | 55 | **4.05M** | 1.77M | 23.56M |
| sw-devops | 5 | 1.29M | 479K | 4.29M | 4.29M | 5 | 1.29M | 479K | 4.29M |
| sw-docs | 21 | 2.04M | 1.94M | 4.12M | 5.04M | 21 | 2.04M | 1.94M | 5.04M |
| sw-pm | 102 | 925K | 474K | 2.42M | 6.07M | 102 | 925K | 474K | 6.07M |
| sw-qa | 2 | 3.34M | 588K | 6.09M | 6.09M | 2 | 3.34M | 588K | 6.09M |
| sw-reviewer | 9 | 4.24M | 3.81M | 6.39M | 6.45M | 9 | 4.24M | 3.81M | 6.45M |
| sw-ux | 5 | 2.58M | 1.68M | 7.20M | 7.20M | 5 | 2.58M | 1.68M | 7.20M |

**Comparison metric for the 1-week delta (fixed now, do not change):** the **7d window** rows above are the baseline; the recheck run re-runs the same script on 2026-10-31 and compares its 7d rows to these. Secondary tie-break: architect 72h avg (5.06M baseline).

---

## 3. Scheduled re-check (armed 2026-10-24)

- Card t_f7c462b2 is parked `status='scheduled'` with marker `SCHEDULED_UNTIL=2026-10-31T13:05:00-04:00`.
- Wake driver (wake-driver law — `SCHEDULED_UNTIL` is advisory): one-shot no-agent cron `r6c-1w-wake` on the **kanban-board-architect profile's** cron store (`schedule "5 13 31 10 *", --repeat 1, --script r6c-t_f7c462b2-wake.sh --no-agent`), which runs `hermes kanban --board default unblock t_f7c462b2 --reason …` (idempotent; no-op if already resumed).
- The woken run then: (1) re-runs `scripts/measure_r6c_tokens.py`; (2) compares 7d rows to §2 baseline; (3) posts the **1-week delta receipt** as a comment on t_f7c462b2 and appends the delta table here (§4 below); (4) completes the card. If the wake cron is missing at audit time, recreate it from this section (wake-driver mortality rule).
