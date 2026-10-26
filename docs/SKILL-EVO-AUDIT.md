> Status: superseded by SKILL-EVO-RETIRE-NOTE.md + hermes-estate/docs/GOVERNANCE.md G-27 — audit led to retirement; receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# SKILL-EVO-AUDIT — the nightly GEPA skill-evolution system: keep / reshape / retire

**Date:** 2026-10-24 · **Card:** t_ba7a5ab9 · **Author:** kanban-board-architect
**Question (operator, Telegram):** *"What is the evo doing that is taking that long, make sure the Evo system we are using is even still best practice, should we be doing it at all is it still maintained? Has it done any thing beneficial for us"*
**Scope:** READ-ONLY audit. No cron, config, or public changes. All numbers below come from live logs, SQLite/Postgres queries, and real run receipts; commands/sources cited inline.

---

## TL;DR

| Question | Answer (evidence below) |
|---|---|
| What is it doing all night? | GEPA evolutionary prompt search: per skill ≈120 sequential LLM rollouts (20–39 s each) over a synthetically generated eval set, plus full-eval passes, reflections, and a holdout judge — ~2.5–3 h of sequential GPU serving for 3 skills. |
| Why so slow for `plan`? | 120 rollouts × ~30 s + 8 full evals + dataset gen + holdout > any per-skill cap that fits the 3 h cron window. `plan` needs ~4,200–5,200 s even at 8 iterations; the in-window ceiling is 3,735 s (proven by two real timed-out runs). |
| Still maintained? | **Effectively no.** Upstream `NousResearch/hermes-agent-self-evolution`: 8 commits ever, last 2026-06-17, **101 open PRs / 35 open issues unmerged** — including community fixes for the exact bugs we hit. Our two critical fixes are **local-only, unpushed**. Deps (DSPy) are maintained; the repo is not. |
| Still best practice? | **No.** Hermes upstream's own answer is usage-driven maintenance (built-in `agent/curator.py` + `agent/background_review.py`, active through 2026-10-07). GEPA is real, current research (ICLR'26 oral) — for *short prompt components with reliable metrics*, not 10–16 KB procedural skills scored by a noisy same-family LLM judge on 5 synthetic tasks. |
| Has it helped? | **Zero, in 97 nightly batches.** 280 candidate attempts failed; the only 10 runs that ever completed all returned `evolved_unchanged=true` (byte-identical to baseline); **0 promotions applied by GEPA or by the curator's evolution gate — ever.** No behavior change, no card-outcome evidence, no bloat (nothing was ever applied). Measured cost of the *working* era: 1,240 calls / ~11.0 M tokens / **$2.89 imputed** — GPU noise, but ~2.75 h of nightly sequential serving for no output. |
| **Recommendation** | **RETIRE the nightly GEPA evolution batch (cron 8feacb98cfb3). KEEP the nightly skill-curator cron (a4f3a5577b55) and lintlang guardrails — those have demonstrated value. The proposed dedicated off-peak slot for `plan`/`hermes-profile-management` is NOT warranted: it would buy more wall-clock for a pipeline whose every completed run keeps the incumbent.** Optional: fold GEPA into a periodic, human-in-the-loop *experiment* (weekly, ≤2 small skills ≤10 KB) only if the operator wants to keep the research thread alive. |

---

## 1. What it does, and where the time goes

### 1.1 Pipeline (per skill, per night)

Cron `8feacb98cfb3` ("nightly-skill-evolution", created 2026-07-20, `0 3 * * *`, script timeout 10,800 s, 99 completions to date) runs `~/.hermes/scripts/nightly_skill_evolution.py`:

1. **Discover** all installed skills ≥800 chars (108 found on 10-24), skipping meta-skills.
2. **Query `~/.hermes/state.db`** for `skill_view`/`skill_manage` usage counts.
3. **LLM ranking** (1 call, `qwen38-flash-fp8`, ~24 s) picks the top 3 candidates.
4. For each picked skill, run `evolution.skills.evolve_skill` in the evo venv (DSPy 3.2.1, gepa 0.0.27), all models `openai/qwen38-flash-fp8` behind the orb/LiteLLM gateway:
   - **Synthetic eval dataset generated fresh each night** (`SyntheticDatasetBuilder`), 10 train / 5 val / 5 holdout (saved under `datasets/skills/<name>/`).
   - **`dspy.GEPA(max_full_evals=iterations)`** — "Running GEPA for approx **120 metric calls** … 8.00 full evals on the train+val set" (plan run log). Each rollout = the model produces a full task output conditioned on the (mutating) skill text, then an **LLM judge** (`skill_fitness_metric`/`LLMJudge`, same qwen38-flash-fp8) scores it. Rollouts are sequential: measured **19.7 → 36.8 s/rollout** as candidate skill texts grew longer (plan_evo8_3700.log).
   - **Reflection LM** call per iteration (temp 1.0, same model), candidate-pool promotions when subsample score beats incumbent.
   - **Post-GEPA holdout eval**: baseline + evolved scored on 5 holdout examples (2×5 more generate+judge pairs).
5. **lintlang guardrail** compares baseline vs evolved (verdict + herm score), rejects on FAIL/score-drop/no-improvement/`evolved_unchanged`.
6. Writes candidates + `metrics.json` to `output/<skill>/<ts>/`; **the nightly script applies nothing** — the curator cron (a4f3a5577b55, 5 AM) gates and applies (improvement > 0.05, constraints passed, ≤15 KB, semantic diff, backup first).

### 1.2 Where the time goes for `plan` (real receipts, t_ef0304ab)

From `~/.hermes/skill-backups/curator-go-2a-2026-10-24/plan_evo8_3700.log` + receipts:

| Event | Timing (real run, plan @ 8 iterations, cap 3700 s) |
|---|---|
| Start → first full-eval promotion | 195 s (Iter 1 promotion) |
| Promotions #1–#3 (cap-3300 run) | t ≈ 533 s / 1,029 s / 1,457 s; #4 mid-flight at kill |
| Rollout pace | 73/120 rollouts at 39:38 elapsed; **19.7 s/rollout early → 36.8 s/rollout late** (candidate texts grow ⇒ every later rollout is slower) |
| Result | **5 promotions, killed at 62 % of rollout budget, exit 124** |
| Extrapolated need | rollout-bound ≈ 4,200 s; promotion-cadence-bound ≈ 4,600–5,200 s — both > the 3,735 s ceiling that fits the 3-skill × 10,800 s window |

**Why `plan` and `hermes-profile-management` are uniquely expensive:**
- **`plan` (8,984 chars)**: its tasks demand *long* outputs (complete plans with code blocks), so each rollout's generation is slow and expensive; GEPA's evolved candidates add sections (the log shows new "Quality Checklist"/"Execution Handoff" sections being reflected in), inflating every subsequent rollout prompt. It has been picked 3 times and **timed out all 3 — never once completed**.
- **`hermes-profile-management` (16,085 chars)**: the largest candidate; every one of ~120 rollouts carries the whole skill body, and its outputs are similarly long. 6 attempts, 0 completions (2 timeouts, 4 crashes). Note: at 16,085 chars it **already exceeds the ≤15 KB gate** the curator enforces — even a winning evolved variant would be rejected as oversized. Same for mid-flight candidates that grow past 15 KB (`github-code-review` baseline is 14,594 — one reflection away from the gate).
- Every *completed* run of other skills measured 368–2,532 s (10 metrics.json files), i.e. the library's normal skills fit the cap; these two don't.

### 1.3 The 3-hour window math (why it "takes that long")

Worst-case night (happened 10-24): both 3,700 s overrides picked + one default skill timing out at 3,300 s + ~30 s overhead = **10,730 s vs the 10,800 s cron cap** — the window is structurally full, and the all-fail nights run the *entire* window producing nothing. That is the duration the operator is seeing.

---

## 2. Is it still maintained?

**Upstream `NousResearch/hermes-agent-self-evolution`** (checked live 2026-10-24):
- **8 commits total**; initial hermes-forge 2026-03-09; last commit **2026-06-17** (PR #122). 4+ months of silence.
- **101 open PRs, 35 open issues.** Issue #37 (2026-04-24): *"Project appears stalled — 19 PRs pending, no commits since March 9."* Still true, now 5× worse.
- The community has filed and PR'd fixes for the exact defects we hit, **none merged**: #171/#169 (constraint validation on bare body — patched locally), #173 (DSPy 3.3 GEPA compatibility), #196 ("fix GEPA wiring"), #38 (2026-04-24, *"Phase 1 SkillModule architecture prevents GEPA from mutating actual skill content"*), #172 (*"SkillModule couples skill_text as an input field — GEPA/MIPROv2 cannot write evolved skill text back to SKILL.md"*), #175 (*"evolution never writes back real skill changes"*).
- Popular (5.6 k stars — it is the flagship demo of GEPA-for-agents) but **popularity without maintenance**: phases 2–5 in the README are all still "Planned".

**Our local copy** (`~/.hermes/hermes-agent-self-evolution`, branch `main`, **ahead 2 of origin/main**): the two fixes that made the pipeline run at all are **local, unpushed commits by Sepp**:
- `4755417` 2026-10-18 — *repair GEPA call for DSPy 3.2.1 and unblock candidate production* (before this: ~90 consecutive nightly batches all-failed: 280 failed attempts, candidates "die at startup (exit 1 in ~2s)" — curator report of 2026-10-18; 87 runs/0 evolved at that point).
- `e7ba6a0` 2026-10-22 — *tolerate invalid JSON escapes in optimizer test-case output*.

So: **we are the maintainers now.** Every future DSPy/GEPA API change (DSPy moves fast — 3.2→3.3 already broke it community-wide) lands on us alone. A one-operator/agent-maintained private fork of a dormant research repo is a standing liability.

**Dependencies:** DSPy (stanfordnlp/dspy) is very much maintained — GEPA is a first-class `dspy.GEPA` optimizer (Agrawal et al., arXiv:2507.19457, ICLR 2026). The standalone `gepa-ai/gepa` package (0.0.27 in our venv) is not what we call — we use DSPy's port. LiteLLM 1.93.0 fine.

---

## 3. Is it still best practice?

**GEPA itself**: real, current, respected research for **evolving short prompt components of LM programs against a reliable metric** (SWE-bench-style programmatic scores). Not a fad.

**What we are doing with it is not that, and the mismatch is measurable:**
- **Fitness signal is noise.** Our metric is an **LLM judge (qwen38-flash-fp8) scoring synthetic tasks** — same model family as the optimizer, 5 holdout examples, observed score swings identical-run-to-identical-run of ±0.05 (e.g. `docker-compose-litellm-proxy`: "improvement" **+0.037 with `evolved_unchanged=true`** — the evolved text was byte-identical; the "improvement" is pure sampling noise). The curator's >0.05 threshold is inside the noise band, which is exactly why it has never fired in a real case.
- **The optimization target is unprecedented by design docs**: 10–16 KB procedural SKILL.md files with frontmatter, checklists, and tool-call recipes — not a 200-token instruction. Upstream's own issues (#38/#172/#175) document that the Phase-1 architecture cannot faithfully mutate such documents. GEPA "improvements" here manifest as appended generic sections (see plan log tail), which if ever applied would be bloat, not better skills.
- **The ecosystem's actual best practice for skill health is usage-driven**: Hermes upstream ships **`agent/curator.py`** (inactivity-triggered lifecycle transitions, archive-not-delete, LLM consolidation fork via `skill_manage`) and **`agent/curated … background_review.py`** ("background review can improve every skill", commit 2026-10-07) — actively developed at upstream main. Our own working version of this pattern is the **nightly curator cron**, which *has* delivered: frontmatter repairs, trigger-clause rewrites, oversize-skill split proposals (the 2026-10-18 "pre-split" batch), divergence detection, library health reports.
- Eval-gated prompt optimization *is* a recognized practice — but with **golden/held-out tasks and programmatic or multi-judge metrics**, run on demand, not a nightly cron over 100+ skills with synthetic-only evals.

**Verdict: nightly GEPA-over-SKILL.md is a niche experiment, not current best practice.** The novelty (self-improving agent docs) is real research value; the operational pattern (nightly, synthetic-eval, self-judge, auto-gate) is not where the field or upstream is going.

---

## 4. Has it helped? (all nightly runs to date)

Full-history numbers from `~/.hermes/logs/evolution.log` (97 batch summaries parsed), `output/*/*/metrics.json` (all 10 that exist), `.evolution-state.json`, curator outputs (`~/.hermes/cron/output/a4f3a5577b55/11 reports`), and LiteLLM spend logs (postgres `litellm_db`, `metadata->>'user_agent' LIKE 'DSPy%'` — the evo venv's clean fingerprint):

| Metric | Value |
|---|---|
| Nightly batches since 2026-07-20 | **97** (99 cron completions) |
| All-failed batches | **92 of 97** (2 loud BATCH_ALARM nights: 10-21, 10-24) |
| Candidate attempts | 289: **268 crashed + 12 timeouts + 9 completed-with-verdict** (+10 metrics incl. extras) |
| **Promotions applied per skill** | **0 — every skill, every night** (APPLIED total across all 97 batches: 0; REJECTED: 0 — the guard never even saw a changed candidate) |
| Completed runs | 10, **all 10 `evolved_unchanged=true`** (GEPA kept the incumbent every single time) |
| "Improvements" measured | +0.014 to +0.044 … on **byte-identical text** = judge noise; real max −0.046 |
| Kept vs reverted (curator gate) | 0 kept, 0 reverted — the curator's evolution gate has **never had a passing candidate** (highest improvement ever seen: +0.0445 < the required >0.05, and it was unchanged-text noise anyway) |
| Concrete behavior-changing diffs | **None.** Nothing was ever applied to a live skill by the evolution system. |
| Evidence of better card outcomes | **None possible** — no skill was ever changed by it. |
| Regressions / bloat caused | **None** — for the same reason. (Current oversize skill count in master: 1 (`devops/kanban-orchestrator`, 16,212 B) — caused by gateway-bounce-law propagation edits, not evo.) |
| Broken-era cost (7-20 → 10-17) | ~90 nights × (1 ranker call ≈ 4–6 K tokens + 3 near-instant crashes) ≈ **negligible**; the pipeline was dead every night |
| Working-era cost (measured, 10-23/10-24) | **1,240 LLM calls, 10.96 M tokens, $2.89 imputed** (avg 8,839 tok/call); nightly 3-timeout batch alone ≈ 384 calls / 3.4 M tokens / 2 h 45 min of sequential GPU wall-clock — **all output: zero artifacts** |

The only genuine product of the working era is *negative knowledge*: receipts that plan and profile-management don't fit the window, and the noise-band characterization of the judge (both already banked in t_ef0304ab and this audit). The parts of the "self-improvement stack" that **have** delivered are **not GEPA**: the curator cron, lintlang, skill backups, and the evo script's own alarm/bookkeeping plumbing (which caught the failures loudly and honestly).

---

## 5. Recommendation — with numbers

### RETIRE the nightly GEPA evolution batch

- **Yield basis:** 97 nights → 0 applied skills → 0 behavior changes. Even if the two oversized skills were given an off-peak slot and 5,200 s each, every completed run to date says the optimizer returns the incumbent; the only "active" runs are the ones that die — and their mid-flight "promotions" are subsample scores inside the ±0.05 judge noise band.
- **Maintenance basis:** dormant upstream (last commit 2026-06-17; 101 open PRs incl. fixes for our exact bugs), private 2-commit fork, DSPy 3.x API churn already bit once and will again.
- **Opportunity cost:** the tuning work alone has consumed multiple operator GOs and cards (3 timeout raises 2400→3300→3700, iteration overrides, window math) to keep a 0-yield pipeline inside its window.
- **What replaces it (already running):** the **nightly curator cron** (usage-driven, receipted, has applied real fixes) + **agent-authored skill patches** per the fleet's skill-evolution protocol (road-tested: every card that records a lesson edits a skill with a receipt) + upstream's built-in curator/background-review when we next rebase (present at upstream main; decision for the update-prep lane, not this card).

### Concretely (operator decision, nothing done by this card)

1. **Disable/pause cron `8feacb98cfb3`** (`hermes cron pause nightly-skill-evolution` or `enabled:false`). No other change needed; the script, venv, and receipts stay in place. Saves ~2.75 h of nightly sequential GPU serving + the recurring all-fail alarms.
2. **KEEP cron `a4f3a5577b55` (nightly-skill-curator) and lintlang** — its library-curation half is demonstrably productive; its evolution-candidate half will simply report "0 new candidates" (it already handles that with `skipped-noise` verdicts).
3. **The dedicated off-peak slot for `plan` and `hermes-profile-management` (t_ef0304ab open decision): NOT warranted.** It would buy wall-clock for a pipeline that has never converted wall-clock into a single applied skill. Instead, reduce `hermes-profile-management` below 15 KB (split) — both to satisfy the curator gate and because our own usage-driven edits improve it weekly with receipts.
4. **Optional research thread (operator's call):** if the self-improvement experiment is still interesting, reshape it as a **monthly, on-demand, human-in-the-loop** single-skill run — small skills (≤10 KB), golden eval set built from *real session transcripts* (the repo's `sessiondb` importer), a stronger/different-family judge, and ≥3-judge voting — and treat any output as a PR-style recommendation for the curator, never an auto-apply. Budget: ~$1/run equivalent, <1 h wall-clock.

### If Retire is declined: KEEP-but-reshape floor

Cap candidates at ≤10 KB skills (excludes plan/skill-authoring/profile-management entirely), 1 skill/night, rollout-budget cap (not iteration count), weekly cadence — cutting the window to <45 min and removing the timeout-tuning treadmill. But note: with every completed run to date returning `evolved_unchanged=true`, the expected yield of this configuration is still **zero**.

---

## Evidence appendix (how each number was obtained)

| Claim | Source (command / file) |
|---|---|
| 97 batches, 92 all-fail, 280 fails + 12 timeouts, 0 applied | parsed `~/.hermes/logs/evolution.log` (6,466 lines; all "Applied: N" batch lines summed) |
| 10 completed runs, all `evolved_unchanged=true`, sizes/scores | the only 10 `output/*/*/metrics.json` (listed via `find`), each read in full |
| plan timing (120 rollouts, 19.7→36.8 s, 5 promotions, 4200-5200 s extrapolation) | `~/.hermes/skill-backups/curator-go-2a-2026-10-24/{plan_evo8.log, plan_evo8_3700.log, plan_evo8_3700_timing.txt, RECEIPT.md}` + embedded window math (t_ef0304ab) |
| Nightly cron config, 99 completions, created 2026-07-20 | `~/.hermes/cron/jobs.json` (job `8feacb98cfb3`) + `last_error` stdout of the 10-24 all-fail night |
| Prompt/cadence facts | `~/.hermes/scripts/nightly_skill_evolution.py` (723 lines, in full), `nightly-skill-evolution.sh`, `evolution/skills/evolve_skill.py` (342 lines, in full) |
| DSPy 3.2.1 / gepa 0.0.27 / litellm 1.93.0 | `pip list` in the evo venv |
| Local-only fixes (ahead 2), upstream last commit 2026-06-17 | `git log`/`git status` in `~/.hermes/hermes-agent-self-evolution` + https://github.com/NousResearch/hermes-agent-self-evolution/commits/main (live) |
| Upstream issues #37/#38/#169/#171/#172/#173/#175, 35 open issues, 101 open PRs | https://github.com/NousResearch/hermes-agent-self-evolution/issues and /pulls (live) |
| Built-in curator + background review active upstream | `~/.hermes/hermes-agent/agent/curator.py` (1,212 lines), `agent/background_review.py` (1,349 lines), commit history through 2026-10-07 |
| Cost: 1,240 calls / 10.96 M tokens / $2.89 imputed; avg 8,839 tok/call; broken-era ≈ 4-6 K tokens/night | postgres in docker `litellm_db`: `SELECT … FROM "LiteLLM_SpendLogs" WHERE metadata->>'user_agent' LIKE 'DSPy%'` (+ per-window and per-day breakdowns; evo runs are the only DSPy-UA caller) |
| Curator never applied an evolution candidate | all 11 curator reports `~/.hermes/cron/output/a4f3a5577b55/*.md` ("0 applied", "skipped-noise", stub-alarm reports) |
| Oversize-skill count = 1 | `find ~/.hermes/skills -name SKILL.md -size +15k` (114 total) |
| `hermes-profile-management` 16,085 chars > 15 KB gate | 10-24 cron `last_error` stdout + curator gate criteria in cron prompt (job a4f3a5577b55) |

*Prepared as input to the operator's keep/reshape/retire decision. No changes made to crons, configs, skills, or public surfaces by this audit.*
