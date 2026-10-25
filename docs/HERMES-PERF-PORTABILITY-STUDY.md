# HERMES-PERF-PORTABILITY-STUDY — measured study + ranked plan for operator Go

**Date:** 2026-10-24 · **Card:** t_cc6843d3 · **Author:** kanban-board-architect
**Method:** measure-first, read-only. No config edits, no restarts, no public writes were made for this study.
**Definitions (operator's):** PORTABILITY = whole system up on another machine (or ga01 rebuilt) with zero hand-fixing. PERFORMANCE = speed + stability of agent work; p99/tail latency outranks throughput.

All numbers below were produced by the measurement scripts in
`~/.hermes/kanban/workspaces/t_cc6843d3/` (measure_portability*.py, measure_perf*.py, measure_b9_skills.py, ttft_probe*.py, verify_recs.py, check_*.py) — every figure cites its source command or file.

---

## 1. Findings table

### A. PORTABILITY

| # | Area | Measurement | Source |
|---|------|-------------|--------|
| A1 | Skill duplication | Master tree: **846 files / 64.5 MB**, but **52.6 MB is `.hub/` index cache** (hermes-index.json alone 51.7 MB) + 4.5 MB curator backups → real skill content = **820 files / 7.0 MB**. 58 profile skill trees: **17,116 files / 265.9 MB**; content-only (state files & caches excluded) = **16,795 files / 176.6 MB = 25.3× duplication** of the master content. Largest trees: kanban-board-architect 47.6 MB, distiller 47.5 MB (both mostly `.hub` index cache copies); typical worker/research tree 5.9–6.0 MB / ~530 files (62–66% of master file count); sw-docs deliberately slim at 27 files. | `du`-equivalent os.walk + sha256 rel-path compare (measure_portability.py) |
| A1 | Skill drift | **97.1% of overlapping files byte-identical** to master. Real content drift is concentrated in exactly **2 files stale in ~49/48 profile copies** (`software-development/hermes-agent-skill-authoring/SKILL.md`, `autonomous-ai-agents/hermes-agent/references/troubleshooting.md`) — master is newer in every case; zero profile-newer cases. Remaining 1.7% drift is state files (.bundled_manifest/.curator_state/.usage.json/.hub locks). | sha256 per rel-path across 58 trees (measure_portability.py) |
| A1 | Sharing support | **`skills.external_dirs` is natively supported at our running version AND at upstream main** (agent/skill_utils.py: `get_external_skills_dirs()`, validated, `~`/`${VAR}`-expanded, HERMES_HOME-relative; tier precedence: trusted-project > local-profile > create_dir > external; same-name cross-tier = local wins with one-time shadow check; identical/symlinked copies judged "provably same skill"). Upstream main grep: 5 hits (stable API). | `sed`/`grep` of `agent/skill_utils.py` + `git show origin/main:agent/skill_utils.py` |
| A2 | Machine-specific literals (live config surfaces only) | Scanned 15,465 config/SOUL/skill/script/cron files total. Live surfaces (config.yaml/SOUL/scripts/cron/git-hooks): **hostnames 150 hits/45 files** (worst: g01-butler SOUL 24, g02-butler SOUL 23, g02-butler config 7, cron/jobs.json 6); **/home/arch 86/28** (gateway-graceful-bounce.sh 18, cron/jobs.json 16, estate-sync.sh 6); **/local 50/26**; **LiteLLM base_url `https://orb.arch.jhu.edu/v1` hardcoded in 61 config.yaml files** (root + most profiles); IP literals near-zero in live config (1 script); CA bundle appears only as `HERMES_CA_BUNDLE` env (71 .env files), 0 hardcodes in config. Docs/prose in skills add ~1,300 more hits (non-executing). | regex scans (measure_portability2.py) |
| A3 | Secrets sprawl | **167 real secret-store .env files** (root 1 + profiles 166; + 33 backups + 3 misc = 203 `.env`-named files total). **48 distinct keys; 43 keys duplicated across >1 file; 1,604 total assignments.** Top: KANBAN_STREAM_BOT_TOKEN/ALLOWED_USERS/OPS_CHAT_ID **115 files each**, LITELLM_API_KEY **110**, HERMES_CA_BUNDLE **71**, GH_CONFIG_DIR **61**, HINDSIGHT_BANK_ID **38**, GH_TOKEN/GITHUB_TOKEN **21** (two spellings!). The kanban-stream rollout physically edited **115 .env files** for one new fleet-wide secret — that is the measured cost of today's rotation procedure. | os.walk + key parse (measure_portability2.py) |
| A4 | Hotfix carry | **8 LOCAL HOTFIX commits on detached HEAD c6b760932c, 932 commits behind origin/main** (`git rev-list --count HEAD..origin/main`). t_7e91f1b9 triaged all 8: **ALL CARRY** — 0 upstream commits touch the kanban fence/notifier/stream files; upstream #143206 still OPEN, PR #143372 unmerged. Classification below in §4-R9. Branch `local/hotfixes-2026-10-24` + patch series `~/.hermes/patches/hotfix-stack-20261024/0001–0008` + estate refs `code/*` hold the stack. A 9th hotfix (dispatch-during-drain, t_a3384e1e) is in test now. | git log/ rev-list; t_7e91f1b9 comment thread |
| A5 | Bootstrap | Proven runbook exists (hermes-estate RESTORE.md, live drill 2026-10-24: clone → scratch HERMES_HOME → 22,750 files + 12 kanban DBs restored → `hermes config check`/`profile list`/`boards list` all exit 0, no second gateway). Today it is **~6 manual stages** (code via estate refs, rsync home, pigz snapshots, systemd units, crontab, launcher+start). **Gap list for one-command:** (1) dependency env never committed — bare machine needs `hermes pm repair` *and* `apt install build-essential libolm-dev` with `CC=gcc CXX=g++` (validated in drill; python-olm compiles from source); (2) code restore is a manual `git remote add`/fetch/checkout dance; (3) root+profile `state.db` family (756 MB root + 1.34 GB profiles) lives **only in the nightly mirror** — GitHub-only restore loses all chat history; (4) launcher recreation is manual; (5) Hindsight Postgres only partially covered (/local/compose/hindsight-backup); (6) adjacent serving infra (orb/LiteLLM + models on gaudi hosts, /local compose stack, CA bundle) is outside the estate — Hermes restores instantly but cannot answer until orb is reachable; (7) second-mirror target still not wired (operator decision pending). | hermes-estate/RESTORE.md + restore-proof/2026-10-24.txt |

### B. PERFORMANCE

| # | Area | Measurement | Source |
|---|------|-------------|--------|
| B6 | Prompt weight per lane (system prompt at session start, from `system_prompts` table, latest per profile) | **default 16.1 KB (~4.5 K tok)** — lightest; **sw-docs 21.9 KB (6.0 K)**; **g01-butler 37.6 KB (10.4 K)**; **kanban-board-architect 39.7 KB (11.0 K)**; **kanban-orchestrator 43.4 KB (12.0 K)**; **distiller 44.5 KB (12.3 K)**; **research 56.0 KB (15.5 K)**; **kanban-worker 63.8 KB (17.7 K)** — heaviest lane, and its SOUL is only 2 KB: the weight is the kanban protocol injection + 65-skill index (5.1 KB descriptions) + tool schemas (root CLI reference point: 76.9 KB / 45 tools in action-prompt-size.log). Cumulative per-session input (3d): **architect avg 5.09 M tok/session (n=97)**, sw-dev-a 3.77 M (n=67), sw-docs 2.04 M (n=21), distiller 584 K (n=70), butlers 64 K (n=14) — the architect/sw lanes are the heavyweight spenders. | profile state.db `system_prompts`/`sessions` (measure_perf4.py) |
| B6 | Plugin A/B (already done — folded in) | tool-slimmer **NO-GO** (+0.8% single-turn, trim outweighed by own schemas at 20 tools); toolaria **NO-GO** (+14.8% multi-call input); skill-retrieval **NO-GO/inconclusive** at 54 skills (erratic call paths, +9.8% multi-call). 25/25 task success, TTFT flat **1.12–1.13 s** through the full Hermes stack (glm53). ⟹ plugin helpers are not the lever; **content trimming is**. | t_4ddfc8b8 Scope B receipt; docs/plugin-perf-ab-2026-10-23.md (commit 8b47cb1) |
| B7 | Model-side latency (live probes through orb/LiteLLM, 2026-10-24 ~18:00 ET) | Tiny prompt (max_tokens 16, 5 samples/model): TTFT p50 0.05–0.10 s, max 0.47 s — all 5 lane models. Large prompt (~9.5 K tok input, 3 samples/model): TTFT p50 ≤0.10 s, total max 1.91 s (qwen38), 1.81 s (glm53), 1.47 s (qwen38-flash-fp8), 1.44 s (muse), 0.44 s (qwen36-fast). **Models are NOT the latency bottleneck**; ~1 s of through-stack overhead (session/prompt assembly + HTTP) sits on top. | ttft_probe.py / ttft_probe_big.py vs `https://orb.arch.jhu.edu/v1` |
| B7 | Tail-incident measurement | **2026-10-23: 55 compression calls >60 s, all on qwen38-flash-fp8, 49/74 InternalServerError (~66% fail, 90 s timeouts)**; every failure burned 90 s + retry. **2026-10-24: compression healthy on qwen36-fast — 104 ok / 1 err** (all 58 profiles pin `auxiliary.compression.model: qwen36-fast`; verified). Healthy compression still costs **12–24 s per event blocking the turn** (compression telemetry: aux_call 12–22 s, total 18–24 s; reclaimed 118–162 K tokens each time — worth it, but it IS the p99 visible to the operator). Root cause of the 10-23 storm is unexplained — either pre-pin config or a summary-model fallback path (`_summary_model_fallen_back`, metrics contract `aux_model_fallback`) routing to the main model. **FLAG (mismatch):** the fleet's main workhorse qwen38-flash-fp8 (orchestrator, butlers, research; 22/59 profiles) is fine at TTFT but catastrophically bad as a *compression* model; any fallback onto it re-creates 90 s stalls. | plugin-data/aux-ledger/calls.jsonl (250 rows); agent.log compression telemetry; check_aux_pin.py |
| B8 | Worker spawn cost | From task_events, 4 busy boards, last 7 days: **claim→spawn p50 ~0 s** (dispatcher instant); **spawn→worker_bound p50 3–4 s**; **spawn→first-heartbeat p50 4–7 s, p90 5–9 s** (default n=127, software-co n=323, gaudi n=96, garg02 n=257). Boot decomposition (CLI, representative): `hermes --help` 0.93 s, `config check` 2.43 s, `profile list` 5.79 s → spawn cost is **Python import + config/skill-catalog/session build, not model wait**, and it is ~7 s of a p50-627 s run (**~1%** — NOT worth optimizing now). Completed-run durations (default, 3d): p50 10.5 min, p90 25 min, max 47 min. | measure_perf3.py + `/usr/bin/time` CLI boots |
| B9 | Restart cost | **2026-10-24 verification bounce (receipts log): total operator-visible outage 13 m 18 s** (20:49:39Z→21:02:57Z) = drain **11 m 13 s** (6 in-flight cards finishing; SIGUSR1 deferred drain, ≤30 min cap) + board notices 28 s (~16 s/board) + PID swap/bot reconnect 19 s + **dispatcher boot +1 m 46 s** after gateway up. The 10-23 predecessor needed 3 attempts (refused with 4 live sessions → exit 1 → direct SIGUSR1) and, before the v1.1 ESTOP fix, burned retry budgets (8 cards gave_up → t_a3384e1e). Interim+root fixes already staged: gateway-graceful-bounce.sh v1.1 ESTOP pauses dispatch during drain; drain-gate hotfix rides the next update bounce. | logs/gateway-bounce-receipts.log; /local/.../gateway-bounce-fix2-2026-10-23.log |
| B10 | Kanban DB health | **All 7 boards healthy: WAL, freelist 0.0%, 0.13–7.58 MB, ready-scan 0.01–0.02 ms** (5-run avg). Row counts: default 114 tasks, gargantua02 332, gaudi 300, software-co 229, gargantua01 26, skipjack 50, skipjack-prototype 5; `_archived` boards ~0 MB. **No vacuum/archive action needed — kanban DBs are a non-issue.** The session stores are the real DB weight: root `state.db` **756 MB** (+35 MB WAL; 87 K messages, double FTS indexes: trigram + fts5), profiles **1.34 GB across 58** (architect 324 MB, g02-ops 131 MB, benchrunner 108 MB — 17% freelist); estate snapshots churn 654 MB gz nightly. | measure_perf2.py / measure_perf5.py (PRAGMA page/freelist, timed queries) |
| B11 | Config hygiene | Root config.yaml 518 lines; profile configs mean 122 lines (max kanban-worker 175, research 171, orchestrator 166; min 99). Universal keys: model/auxiliary/providers/plugins/timezone. **Divergences without a recorded reason:** `max_tokens: 65536` on every profile vs LiteLLM validation limits (the class that surfaced as agent-init invalid_params during the A/B harness); `context_length` pins 262 144 (52 profiles) vs 1 000 000 (glm53 lanes); `ssl_verify: false` on worker profiles (needed for internal CA — fine, but undocumented); compression tuning only in root (threshold 0.85, target_ratio 0.2) with **no per-profile record of why**; fallback_model set on only 8 profiles. `kanban.board` keys in the **5 butler configs are intentional** (local hotfix 602ea0a874 per-profile board pin — documented deviation, not a defect). Gateway start banner shows **4 duplicate platform-credential warnings** (default↔coding and default↔kworker-muse-probe sharing TELEGRAM/SLACK bot creds). | yaml parse of 59 configs (measure_perf5.py); 10-23 bounce banner |

---

## 2. What the numbers say (synthesis)

1. **The tail, not the mean, is where our pain lives — and it is config/routing, not hardware.** Model TTFT through orb is <1 s even at 10 K-token inputs; through-stack TTFT is ~1.1 s. Every measured p99 event had a *config* cause: compression falling onto qwen38-flash-fp8 (90 s ×retry), headless approval-gate stalls (the 345 s runner-hunt), and drain windows (11+ min).
2. **Skill duplication is 25×, and it is pure curatorial drag.** 97.1% of profile skill bytes are identical to master; live drift is 2 files. Hermes natively supports the fix (`skills.external_dirs`) at our version and upstream. This also shrinks the estate (280 MB → ~100 MB), the hourly sync, and every future rollout (the stream rollout touched 58 plugin copies + 115 .env files by hand).
3. **Portability is one runbook + 7 gaps away from one-command.** The estate mirror + RESTORE.md (both proven live today) removed the scary part. What remains is mechanics: deps bootstrap, code checkout, launcher, history DBs, adjacent infra (orb).
4. **The levers ranked by operator priorities (p99 > portability):** compression-fallback safety > shared skills > secrets manifest > per-host overlay > one-command bootstrap > prompt diet on the heavy lanes. Worker spawn (7 s, 1% of run) and kanban DB health are measured non-issues on purpose.

---

## 3. Quick wins (do these first — all reversible, none needs a gateway bounce)

| QW | Action | Measurement basis | Risk |
|----|--------|-------------------|------|
| QW1 | **Fix the 2 drifted skill files** — re-sync `hermes-agent-skill-authoring/SKILL.md` + `hermes-agent/references/troubleshooting.md` from master into the ~49 stale profile copies (curator one-shot or script). | A1: exactly 2 files, 49/48 copies, 0 profile-newer | ~zero (byte-identical to master) |
| QW2 | **Prune `.hub/` index caches** (51.7 MB hermes-index.json in master + ~47 MB copies in distiller/architect/…) out of profile trees — regenerable cache, not content; shrinks ~150 MB + estate sync size. | A1 | low (regenerates) |
| QW3 | **Add a compression-fallback guard**: after the t_a3384e1e lane lands, add one observability check (or a grep of aux-ledger in the daily summary) alerting on any `task=compression` call routed to qwen38-flash-fp8; investigate the `_summary_model_fallen_back` path once. | B7: 49×90 s failures all on 10-23, quiet since — needs a tripwire not a fix | ~zero |
| QW4 | **Unify GH token key spelling** (GH_TOKEN vs GITHUB_TOKEN, 21 files) + delete the 33 stale `backups/*/.env` copies. | A3 | low (check consumers first) |
| QW5 | **Record-why comments**: one line in each profile config (or a CONFIG-DIVERGENCES.md in software-co) noting why max_tokens=65536 / context_length is pinned / ssl_verify=false; clean the 4 duplicate-credential warnings by stripping creds from the two broken probe profiles (coding, kworker-muse-probe are already known-broken). | B11 | low |

---

## 4. Ranked recommendations (for operator Go — no changes made)

Ranked by operator priority order: tail-latency impact → portability → hygiene. Each item: impact / effort / risk / bounce? / rollback / lanes touched.

### R1 — Shared master skill tree via `skills.external_dirs` + slim per-profile allowlist
- **What:** keep one canonical tree at `~/.hermes/skills` (master); each profile config gets `skills: { external_dirs: ["~/skills"] }`; profile-local `skills/` shrinks to the true per-profile extras (today: ~200 files per profile, mostly identical copies). Verified native support at our commit AND upstream main; tier precedence keeps per-profile overrides winning; identical-copy resolution is explicit in the code.
- **Impact:** HIGH — deletes 176.6 MB of duplicated content and *the entire sync-drift class* (the curator's recurring stale-copy finding); cuts estate tree ~180 MB; every fleet rollout of a skill becomes 1 edit instead of 58 copies; portability bootstrap rsync shrinks proportionally.
- **Effort:** M (scripted cutover: compute per-profile delta set → keep extras → flip config → verify `skills_list` parity per profile on one throwaway session each; stage profile-by-profile, butlers last).
- **Risk:** L-M (shadowing semantics across tiers are explicit; must verify `.hub` cache per-profile behavior and skill_view paths; the pilot A/B showed skill loading quirks exist — so gate on a per-profile parity check).
- **Bounce:** NO (fresh worker sessions pick up config; butler/chat lanes on next session).
- **Rollback:** restore previous config.yaml lines (estate git has every config hourly) + re-rsync old trees from estate.
- **Lanes:** every profile; coordinate with curator lane.

### R2 — Secrets manifest + generator (`secrets.yaml` → 167 .env files)
- **What:** one YAML manifest in the estate repo listing every key, its value source (literal / file ref), and a profile selector (glob or per-profile section); a no-agent script generates all root+profile `.env` idempotently (umask 077); rotation = edit manifest + run script + verify. Keep Hermes' actual loading mechanism unchanged (.env per home) — this fixes the *proliferation*, not the loader.
- **Impact:** HIGH for portability + security hygiene — measured cost today: one fleet-wide secret = 115 file edits (kanban-stream); LITELLM_API_KEY rotation = 110 files; 43 duplicated keys incl. two spellings of the GitHub token.
- **Effort:** M (script + manifest ~1 day; dry-run mode with diff output; first run must be diff-verified against all 167 current files).
- **Risk:** M (secrets are involved; mitigate: dry-run + diff + estate snapshot is the rollback; never echo values — same discipline as the stream rollout).
- **Bounce:** NO.
- **Rollback:** files regenerate from previous manifest commit; estate hourly git holds the prior state.
- **Lanes:** all; security-sensitive — operator should name who may hold the manifest (it lands in the private estate repo, which already carries plaintext secrets per operator ruling 2026-10-24).

### R3 — Compression/p99 hardening pack (fallback tripwire + healthy-when-degraded path)
- **What:** (a) tripwire from QW3; (b) one-time root-cause read of the 10-23 storm (which sessions, which profiles, feasibility-fallback or pre-pin config); (c) document the degradation mode: if compression model errors, prefer raising the threshold + continuing over retry storms; (d) consider `compression.threshold` 0.85→0.9 on the very heavy lanes (architect/sw-*) so compression triggers slightly less often, trading slow tail events for slightly more tokens per turn.
- **Impact:** MEDIUM-HIGH on p99 — this is the single largest measured p99 event class after drain windows (90 s×N on 10-23; 12–24 s per event even when healthy, on lanes that hit 174–223 K tokens between compressions).
- **Effort:** S-M ((a) trivial, (b) one focused session reading state.db + ledger, (c)/(d) config-only).
- **Risk:** L ((d) uses slightly more context per session; reasoned tradeoff, reversible per-profile).
- **Bounce:** NO (config-only changes need no bounce; fresh sessions pick up).
- **Rollback:** config revert.
- **Lanes:** all; uses aux-ledger receipts.

### R4 — Per-host overlay for machine-specific literals
- **What:** (1) replace 61 hardcoded `providers.litellm.api: https://orb.arch.jhu.edu/v1` with a `${ORB_API}` env expansion (env expansion in config is proven — `api_key: ${LITELLM_API_KEY}` already resolves), define ORB_API per host in .env (one line per machine via R2's manifest); (2) scrub `/home/arch` and `/local` literals in `~/.hermes/scripts/*` + cron/jobs.json to `$HERMES_HOME`-relative or `/local` env-var form; (3) hostnames in butler SOULs stay (they are identity content, not config — but the SOUL template can take the hostname from one place).
- **Impact:** MEDIUM portability — a rebuilt ga01 or a second machine stops needing a find-and-replace pass; measured surface is small (150 hostname + 86 home_arch + 50 /local + 61 URL hits in live files).
- **Effort:** S-M (mostly mechanical; test each edited script).
- **Risk:** L-M (scripts are live ops tooling — estate-sync, bounce script; each edit needs a shadow-test; the bounce script is operator-law collateral: edit its own path handling carefully or not at all).
- **Bounce:** NO for config/env; scripts take effect next invocation.
- **Rollback:** per-file git revert (estate).
- **Lanes:** ops tooling; g02 rebuild scenario directly benefits.

### R5 — One-command bootstrap (`estate-restore.sh`) + close the 7 gaps
- **What:** wrap RESTORE.md §1–§5 into one script: `estate-restore.sh [--from github|/local|bundle] [HERMES_HOME]`, driving: apt pre-check (build-essential, libolm-dev, CC/CXX), code checkout at `code/running-commit`, rsync home, snapshot restore, systemd+crontab install, `hermes pm repair`, launcher, read-only verification (config check / profile list / boards list — the proven drill), explicit REFUSE-to-start guard unless `--i-own-this-host`.
- **Impact:** HIGH for the operator's stated definition of portability — bare machine → verified Hermes in one command; the runbook is already proven, this removes the human from the loop.
- **Effort:** M (script + one more isolated drill to prove it end-to-end; the drill harness already exists from t_a4dd80a6).
- **Risk:** M (restore-domain mistakes corrupt kanban DBs if a second gateway starts — keep the env-scrub + refusal guard hard-coded, as in the existing drill).
- **Bounce:** N/A (runs on the NEW machine, never on ga01).
- **Rollback:** N/A (scratch-destroyable; drill mode proves without touching live).
- **Lanes:** architect; also closes A5 gaps 1,2,4. Gaps 3 (state.db history via nightly mirror) and 6 (orb/adjacent infra) get documented as explicit preconditions, and gap 7 (second mirror) remains the pending operator decision tagged in t_a4dd80a6.

### R6 — Prompt diet on the heaviest lanes (kanban-worker, research, architect)
- **What:** measured weights: kanban-worker 63.8 KB sysprompt (17.7 K tok) with a 2 KB SOUL — the dominant parts are the kanban execution protocol + 65-skill index; architect 39.7 KB but 5.09 M cumulative input tokens/session. Actions: (a) give kanban-worker a curated skill subset (it needs ~10 skills, not 65) via the R1 allowlist; (b) tighten the kanban protocol boilerplate (it embeds the full lifecycle text in every session); (c) for architect/sw lanes, favor earlier `session_reset` discipline on long cards instead of letting sessions run to 174–223 K tokens between compressions.
- **Impact:** MEDIUM — token spend down on the highest-volume lanes (workers are the most-dispatched profile class; 17.7 K tok sysprompt ≈ 12 K more input tokens on *every* worker turn than a slim equivalent), fewer compression events (ties into R3), direct p99 improvement via shorter prompt-assembly.
- **Effort:** M ((a) is free after R1; (b) is careful editing of a doctrine document — needs orchestrator sign-off; (c) is operational habit/skill update).
- **Risk:** M (cutting worker skills can break real cards if the subset is wrong — do it per-board with a fallback "full set" profile during a trial week; (b) risks losing protocol guarantees — diff-review each change).
- **Bounce:** NO.
- **Rollback:** restore prior skill allowlist / SOUL from estate.
- **Lanes:** architect, workers, orchestrator (protocol text owner). NOTE: the plugin route (tool-slimmer/skill-retrieval) was already A/B-measured NO-GO — this is the content route, not a plugin.

### R7 — state.db retention & vacuum policy
- **What:** root state.db 756 MB (87 K messages, double FTS), profiles 1.34 GB total, gaudi-benchrunner 17% freelist. Define retention (e.g. archive sessions >60d to the nightly-mirror tier, keep hot store lean), schedule periodic `VACUUM` on the few fragmented DBs during idle windows, and consider dropping the trigram FTS index if unused by any consumer.
- **Impact:** LOW-MEDIUM — mostly estate-snapshot churn (654 MB gz/night), disk, and restore speed; negligible direct per-turn latency (queries are ms-class).
- **Effort:** S-M (policy + one-off vacuum; verify FTS consumers before dropping anything).
- **Risk:** L-M (retention must respect kanban recovery needs — worker sessions are evidence for receipts; archive-not-delete).
- **Bounce:** NO (DB maintenance with live SQLite needs brief write locks — do in low-traffic window; no gateway restart).
- **Rollback:** restore from estate snapshot.
- **Lanes:** ops.

### R8 — Restart-cost reduction (proposal only; root fix owned by t_a3384e1e)
- **What:** measured 10-24 bounce: 13 m 18 s total = 11 m drain + 28 s notices + 19 s swap + 1 m 46 s dispatcher boot. The staged drain-gate hotfix (t_a3384e1e) + v1.1 ESTOP already fix the *retry-budget* damage. Remaining safe shortenings: (a) schedule bounces in idle windows (dispatcher knows queue depth — a `--when-idle` pre-check in the bounce script), (b) optional drain SLA (e.g. after 5 min, cleanly requeue non-finished cards instead of waiting the full 30-min cap — needs the drain-gate hotfix loaded first), (c) pre-warm the dispatcher (~1 m 46 s of the total is post-boot dispatcher init; measure whether it can start in parallel with bot reconnect).
- **R8(c) BOOT-TIMING measurements (receipted per bounce; skill `hermes-gateway-graceful-bounce` v1.2):**
  - 2026-10-24 20:50Z verification bounce (t_8b461664): first_tg=+12s, last_tg≈+77s, dispatcher_lock≈+86s, first tick +91s → verdict: dispatcher init itself sub-2 s; ~95 % of the "boot" is waiting behind the serial ~13 s/bot telegram-reconnect chain. Overlap needs an in-product change (spawn the dispatcher watcher before the connect phase), NOT a script knob — upstream-able proposal, do not hotfix casually.
  - **2026-10-25 02:30Z update bounce (t_c0969a7f, v0.22.5+9.g3a931a6): first_tg=+12s, last_tg=+78s, dispatcher_lock=+87s** — second data point, consistent with the first (dispersion across boot conditions ≈ ±2 s on the lock). Confirms the measurement is stable, not a one-off.
  - **Knob-trial status:** the `--when-idle` / `--drain-sla` trial was NOT exercised on the update bounce (cards were running + dispatch paused at the code swap; the orchestrator ordered a short window) — **trial still pending, rides a future bounce**.
- **Impact:** MEDIUM for maintenance windows (13 min → ~3–5 min idle-window / ~7 min loaded).
- **Effort:** S-M (script flag + measurement; the SLA needs the hotfix + operator comfort).
- **Risk:** M if done before the drain-gate hotfix lands; L after.
- **Bounce:** is one (naturally — any trial rides the next sanctioned bounce).
- **Rollback:** script flags off.
- **Lanes:** bounce lane (t_d2f0a30f skill), t_a3384e1e, t_c0969a7f (update bounce). DO NOT duplicate t_a3384e1e's work — this only adds the script-level knobs.

### R9 — Hotfix carry reduction (fold into the update-prep lane)
- **What (A4 classification, from t_7e91f1b9's verified triage):**
  - **Upstream-able → file PRs, drop on merge:** `fe5e8bd91a` kanban_archive (PR #143372 already open — shepherd it), `c69ae0d911` chat -q source labels (a genuine upstream bugfix: canonical contract refuses non-surface labels), `6677747b17` cron suppressed-session rows.
  - **Upstream-able-as-feature (optional):** `37d4c9ed89` stream auto-subscribe WIDEN (F23) could ride the kanban-stream plugin instead of core.
  - **KEEP (estate doctrine, not upstreamable):** `602ea0a874` per-profile board pin + butler fence, `30a673f983`+`eabd25ae0a` F22 board-aware notifier, `c6b760932c` fence loud-reject, plus the incoming t_a3384e1e drain gate.
- **Impact:** MEDIUM — shrinks the carry rebase surface for the 932-commit update (t_7e91f1b9 proved zero-conflict today, but every dropped commit removes future drift), and upstreaming fixes upstream bugs for everyone.
- **Effort:** S-M per PR (the two bugfixes are small, tested, already isolated as patches; upstream PRs go through the operator-final-gate + distiller flow).
- **Risk:** L (patches already exist as a rebased stack; each PR is optional).
- **Bounce:** NO.
- **Rollback:** keep carrying until merged.
- **Lanes:** update-prep (t_7e91f1b9/t_c0969a7f), public-filing gates for the PRs.

### R10 — Config hygiene sweep (B11)
- **What:** unify GH token spelling (QW4), record-why file (QW5), strip creds from the two known-broken probe profiles to silence 4 gateway-start warnings, and — after R2 — collapse the 5 per-butler `kanban.board` blocks into the documented-deviation section of KANBAN-SYSTEM-AS-BUILT (they are correct, just underdocumented).
- **Impact:** LOW-MEDIUM hygiene; each warning at gateway start is a small boot-time stall + operator noise.
- **Effort:** S. **Risk:** L. **Bounce:** NO. **Rollback:** git. **Lanes:** architect.

**Explicit non-actions (measured not worth it):** worker-spawn optimization (7 s ≈ 1% of a p50-10.5-min run), kanban DB vacuum/archive (all boards 0% freelist, 0.01–0.02 ms queries), plugin-based prompt slimmers (all A/B NO-GO with numbers), model migration on TTFT grounds (all models <1 s at 10 K input).

---

## 5. Proposed card breakdown (NOT created — for the operator's Go)

| Card | Scope | Assignee | Depends on | Bounce |
|------|-------|----------|------------|--------|
| SKILLS-SHARE-PILOT | R1 staged cutover: 3 volunteer profiles (kanban-worker, research, distiller) → external_dirs + allowlist, parity receipts, then fleet wave | kanban-board-architect | — | no |
| SKILLS-SHARE-FLEET | R1 fleet wave (55 remaining profiles, butlers last) + QW1/QW2 drift/cache cleanup folded in | kanban-board-architect | SKILLS-SHARE-PILOT | no |
| SECRETS-MANIFEST | R2 manifest + generator + dry-run diff over all 167 files + rotation drill on one sacrificial key | kanban-board-architect | — | no |
| P99-TRIPWIRE + COMPRESSION-RCA | R3(a)(b)(c): aux-ledger tripwire in daily summary + one-session root-cause of the 10-23 storm | research | — | no |
| HOST-OVERLAY | R4: ${ORB_API} in 61 configs via env, scripts/cron path scrub, butler SOUL template note | sw-devops | SECRETS-MANIFEST (env plumbing) | no |
| BOOTSTRAP-ONECMD | R5: estate-restore.sh + isolated end-to-end drill, append RESTORE.md | kanban-board-architect | estate repo (done) | no |
| PROMPT-DIET-WORKER | R6(a): curated skill subset + protocol text tightening for kanban-worker, 1-week trial with fallback profile | kanban-board-orchestrator (protocol owner) + sw-docs | SKILLS-SHARE-PILOT | no |
| PROMPT-DIET-ARCH | R6(c): session-reset discipline for architect/sw lanes, update skill + measure 1 week of tokens/session | kanban-board-architect | — | no |
| STATEDB-RETENTION | R7 policy + vacuum; verify FSI consumers | sw-devops | — | no |
| BOUNCE-IDLE-KNOBS | R8 script flags (--when-idle, drain-SLA proposal doc) — coordination-only card vs t_a3384e1e/t_c0969a7f | kanban-board-architect | t_a3384e1e lands | NOT exercised on the t_c0969a7f update bounce (short window ordered); trial rides a future bounce |
| HOTFIX-UPSTREAM-PRs | R9: 3 upstreamable patches through distiller+operator gates | sw-dev-a | t_7e91f1b9 (rebased stack) | no |
| CONFIG-HYGIENE-SWEEP | R10 + QW4/QW5 | sw-docs | — | no |

Sequencing suggestion: Quick wins QW1–QW5 can start immediately; R1 pilot and R2 are the structural foundation (HOST-OVERLAY and PROMPT-DIET-WORKER both benefit from landing after them); everything else is parallelizable.

---

## 6. Receipt summary

- Deliverable: this file, `/local/projects/software-co/docs/HERMES-PERF-PORTABILITY-STUDY.md`, committed to the software-co (mprov) mgmt repo — internal repo, existing agent-level gates only (operator-final-gate scope exemption, ruling 2026-10-24).
- **Top 5 recommendations:** R1 shared skill tree (kills 25× duplication, native support verified) · R2 secrets manifest (115-file-edit rotations → 1) · R3 compression p99 hardening (largest measured tail class) · R5 one-command bootstrap (portability definition met) · R6 prompt diet on kanban-worker/architect lanes (17.7 K-token sysprompt + 5.09 M-token sessions).
- No public writes, no config edits, no restarts were performed for this study. All probes were read-only or read-only-inference (TTFT probes against orb; ~60 tiny completions total).
