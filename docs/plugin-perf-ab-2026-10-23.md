# Plugin Perf A/B — tool-slimmer vs toolaria vs skill-retrieval (2026-10-23)

**Task:** t_4ddfc8b8 (PLUGIN-PILOT, Scope B) · **Test profile:** `plugin-ab` (glm53, 20 tools, 54 skills, LiteLLM `orb.arch.jhu.edu`) · **Operator mandate:** measure vs baseline on an identical 3-task battery — tokens/turn (input side), TTFT, task success, tool-selection errors — with an explicit negative-result requirement.

**Verdict (fleet rollout): NO-GO for all three** on current fleet profile shapes. None showed a reproducible input-token reduction at 20 tools / 54 skills; tool-slimmer and toolaria consistently *added* tokens in their strongest test cells. No plugin degraded selection accuracy or TTFT — the negative results are about cost/benefit, not correctness. All artifacts: `~/.hermes/kanban/workspaces/t_4ddfc8b8/` (runner.py, results.json, final_summary.json).

## 1. Method

- Fresh CLI-over-tmux session per (arm × task) on `plugin-ab`; per-profile enable/disable between arms (hot-reloaded by the gateway, confirmed).
- Arms: `baseline` (no perf plugins) · `tool-slimmer 0.8.0 @1b90aa59` · `toolaria 3.1.1 @667df67` · `skill-retrieval 0.6.0 @79801c69`. Catalog-pinned SHAs byte-verified against pre-run source audits. All optional rerankers OFF (no `TYPESAFE_API_KEY` on the host); default local modes only.
- Battery: **file** (read 4 deterministic fact files, 3 verifiable answers), **web** (3 lookups + table), **kanban** (fix one-bug repo, run provided `run_tests.sh`, report diff) — v2 of the kanban task after v1 was invalidated (see §4).
- Metrics: per-session `input_tokens`, `api_call_count`, `tool_call_count` from `profiles/plugin-ab/state.db` (SQLite, read-only); wall time; TTFT by 0.4 s pane-polling (granularity-limited); task success by content grading of final assistant transcript message; tool-selection errors by transcript scan.
- n per cell: file n=4/arm, web n=1/arm, kanban-v2 n=2/arm (plus v1 remnants as anecdote). Single model, single host; treat deltas within ±10% as noise — LLM path stochasticity (how many tool calls a run takes) dominates.

## 2. Results (input tokens per task)

### file (single-turn, 2-API-call path unless noted)
| arm | runs (n=4) | input tokens | Δ vs baseline clean-path mean |
|---|---|---|---|
| baseline | 31,963 / 31,984 / 31,963 / 51,638* | clean-path mean **31,970** | — |
| tool-slimmer | 32,234 / 32,234 / 32,207 / 32,207 | mean **32,220** | **+0.8%** (consistent, its own 4 registered schemas outweigh the trim at 20 tools) |
| toolaria | 32,035 / 32,031 / 32,009 / 32,009 | mean **32,021** | **+0.2%** (no oversized results in this battery to rescue) |
| skill-retrieval | 30,687 / 24,417† / 36,966‡ / 36,844‡ | path-dependent | **no consistent reduction** (†1-tool-call path, ‡3-API-call path — path choice became erratic) |

*3-API-call outlier path; excluded from clean-path mean. All 13 file runs answered all 3 questions correctly.

### kanban-v2 (multi-API-call; the cell where compounding savings should show)
| arm | runs (n=2) | input tokens mean | Δ vs baseline mean |
|---|---|---|---|
| baseline | 79,839 / 66,313 | **73,076** (spread ±9%) | — |
| tool-slimmer | 67,186 / 67,048 | **67,117** | −8.2% — but inside baseline's own spread (its low sample 66,313 matches); not reproducible evidence |
| toolaria | 83,805 / 83,958 | **83,882** | **+14.8%** — both samples above *every* baseline sample; mechanism unclear (6 tool calls vs baseline 5) |
| skill-retrieval | 80,426 / 80,024 | **80,225** | **+9.8%** — contradicts the tainted v1 cell (−15%); not reproducible |

All kanban-v2 runs: 6/6 fixed the bug, tests green, correct one-line diffs.

### web (n=1/arm; web latency noise)
| arm | input tokens | wall | table present |
|---|---|---|---|
| baseline | 33,263 | 29.0 s | yes |
| tool-slimmer | 33,472 | 47.3 s | yes |
| toolaria | 33,748 | 28.6 s | yes |
| skill-retrieval | 33,849 | 29.0 s | yes |

### TTFT, task success, tool-selection errors
- **TTFT:** 1.12–1.13 s in every one of the 25 runs (0.4 s poll granularity) — no plugin changed first-token latency.
- **Task success: 25/25** across all arms (file answers verified correct in all 13; kanban fixes verified by re-running the suite).
- **Tool-selection errors attributable to plugins: 0.** The only blocked calls in the whole battery were in the (invalidated) v1 kanban cell, caused by the environment, not a plugin — see §4.

## 3. Per-plugin verdicts

**tool-slimmer — NO-GO.** Its schema-trimming arithmetic doesn't pay at this fleet's tool count: +250 tokens of its own tool schemas on the single-turn cell (+0.8%), and a kanban delta (−8%) inside baseline noise. The plugin's own README targets "dozens of native and MCP tools … 15–20k tokens per request"; `plugin-ab`'s entire request preamble is ~32k of which tool schemas are a small fraction. Re-evaluate only for profiles with large MCP catalogs. (Note: its `jev` rerank mode phones home to api.typesafe.ai — requires TYPESAFE_API_KEY, absent on this host; default `keyword` mode is local-only, verified in source.)

**toolaria — NO-GO for fleet-wide install.** No observed benefit (its 12,000-char rescue threshold is never hit by this battery's tool results), +0.2% single-turn, and a consistent **+14.8%** input-token increase on the multi-call cell it should be neutral in. Zero correctness/latency harm. Possibly useful selectively on profiles that routinely pull oversized web/MCP payloads; that hypothesis was not tested here (out of battery scope) — do not install fleet-wide on this evidence.

**skill-retrieval — NO-GO / INCONCLUSIVE, leaning negative.** The one mechanism it has (names-only `<available_skills>`) could not be detected above path noise at 54 skills: single-turn paths became erratic (1–3 API calls vs baseline's uniform 2), and the multi-call cell came out +9.8%, contradicting the (tainted) v1 −15%. No correctness or latency harm. If re-tested, use n≥5 per cell and pin the skill library at ≥200 skills where its README claims the win lives.

## 4. Validity incidents and environment findings (all disclosed)

1. **v1 kanban cell invalidated & re-run.** The original battery failed to reset the fix-repo between arms: baseline fixed the bug; subsequent arms received an already-fixed repo. The v1 tool-slimmer run then spent 600 s hunting a test runner (command-discovery calls tripped the dangerous-command approval gate in a session with no human to answer: "BLOCKED: Command timed out without user response" ×2) and hit the runner cap. Root cause: **environment** (no pytest in the Hermes venv; headless approval gates), not the plugin — proven by a pure-baseline run afterwards doing the same hunt for 345.7 s / 159,178 tokens. The task was hardened (stdlib `run_tests.sh`, unittest-style tests) and all arms re-run from verified-pristine repos (`git checkout`+`clean` with dirty-state assert). v1 data is preserved in `results_invalid_kanban.json`.
2. **Headless approval-gate hazard (fleet-relevant, not plugin-caused):** interactive-CLI sessions whose prompts hit `which -a python*`-style "dangerous" classifications stall until timeout when no human is attached. Any future unattended CLI-harness battery should whitelist patterns or pre-provision runners.
3. **`hermes chat -q` one-shot broken host-wide (pre-existing):** `invalid_params` agent-init failure on all profiles while gateway-routed sessions work — surfaces from the runtime-store admission layer, NOT from any pilot plugin (reproduced on profiles with zero pilot plugins). Unresolved; worth a separate bug task. The A/B harness therefore ran through interactive CLI over tmux.
4. **plugin-ab auth fix:** the profile's `.env` was empty while its config referenced `${LITELLM_API_KEY}`, so the raw placeholder reached LiteLLM (HTTP 401, observed in gateway error log). Key added to the profile `.env` (correct secrets location; no transcript exposure).
5. Batteries ran strictly sequentially; no concurrent kanban traffic on `plugin-ab`.

## 5. What WOULD change these verdicts

- Profiles with 40+ tools or big MCP catalogs (tool-slimmer's actual design point).
- Profiles whose web/MCP tool results regularly exceed 12k chars (toolaria's rescue path — untested here).
- Skill libraries of hundreds of skills + n≥5 per cell (skill-retrieval's design point).

Otherwise: recommend against fleet rollout for all three; leave them disabled on `plugin-ab` (done); catalog entries remain available for targeted single-profile re-evaluation.

— kanban-board-architect, run 52 of t_4ddfc8b8, 2026-10-23 (America/New_York)
