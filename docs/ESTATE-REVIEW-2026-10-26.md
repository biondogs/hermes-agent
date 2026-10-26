# ESTATE REVIEW A — deep review of the hermes-estate assembly (2026-10-26)

Card t_d325c0e0 · report-only (change NOTHING was executed; all findings read-only).
Operator request (verbatim): "do a deep review of our entire hermes-estate assembly and suggest real improvements, gaps, or feature adds, review any available official or community plugins as well to see if there are any that could benefit us."

Plugin survey is the sibling card (t_f5855ec3 → `PLUGIN-SURVEY-2026-10-26.md`, done); this document covers the ESTATE half. Synthesis card t_bf623554 merges both.

**Method.** Evidence gathered 2026-10-26 10:31–11:10 EDT from four parallel read-only probes (carry-stack git analysis; DR/backup/cron/log inventory; profile/config/board/gateway-log analysis; docs-of-record digest) plus direct verification of the two highest-stakes claims (restore runbook existence, secrets-vault git tracking). Every finding below names its evidence. Claims contradicted on verification are corrected inline (two subagent findings were wrong and are NOT reported: "no restore runbook" — `RESTORE.md` + `restore-proof/2026-10-24.txt` exist in `biondogs/hermes-estate`; "gateway-starts.log stale" — last start 2026-10-25 11:19 is consistent with live uptime).

**Canon respected.** Not re-proposed: Slack xoxb/listeners, Telegram mouse_tracking, Langfuse (fees), secret-redaction-on (deliberate), LITELLM-YAML LAW changes, skill-evo GEPA cron.

---

## 1. Current-state snapshot (verified live 2026-10-26)

| Area | State | Evidence |
|---|---|---|
| Core | hermes v0.22.5+11.g9f66ae8; carry branch `local/hotfixes-rebased-2026-10-25` @ 9f66ae8351; **784 commits behind origin/main**; merge base = v0.22.5 tag | `git rev-list --count origin/main ^local/hotfixes-rebased-2026-10-25` = 784 |
| Profiles | 59 dirs + root = **60** (AS-BUILT census says 58+root=59 — stale by 1); 28 glm53 / 23 qwen38-flash-fp8 / 9 muse; 5 butlers; 0 husks | `ls ~/.hermes/profiles`, `hermes profile list` |
| Boards | 7 boards + 8 archived remnants; default 3.1 MB, gaudi 8.3 MB (largest, wal 473 KB uncheckpointed) | sqlite ro-mode counts per kanban.db |
| Dispatcher | tick 15 s, stale 4 h, failure_limit 3, auto_decompose true (5/tick) — matches AS-BUILT canon | config.yaml:340–357 |
| Compression | RCA closure actions landed (fallback_model qwen38, degraded-models blacklist `[qwen38-flash-fp8]`, threshold 0.85); **0 compression errors in the 42 h log window** | config.yaml:69–70,122–144 vs COMPRESSION-RCA §7 |
| DR | Hourly git mirror → `biondogs/hermes-estate` (last sync 10-26 10:07 "sync OK") + nightly rsync → ga01; **restore proven 2026-10-24 to config-check boot, not to full gateway+dispatcher boot** | estate repo log, logs/estate-sync.log, RESTORE.md, restore-proof/ |
| Crons | 24 registry jobs, all "last run ok"; watchdog fleet healthy; **all alerting → single Telegram chat 8158007517** | `hermes cron list`, scripts grep |
| Churn | 11 gateway starts in 3 days; **236 zombie workers reaped in 42 h** (229 reap lines); spawned=311, crashed=13; reclaim=0 (no stale-claim reclaim fired despite 4–9-day-old cards) | gateway-starts.log (40 entries), gateway.log tail 400 KB window 10-24 17:01→10-26 10:41 |
| Cost | **No main-lane token/cost accounting anywhere**; aux-ledger covers auxiliary calls only; display.show_cost false | grep config.yaml (`usage|cost|billing` → 1 hit) |

---

## 2. CARRY STACK — the 11 local hotfixes (upstream triage)

Classification from direct git comparison against locally-fetched origin/main (no fetch performed):

| # | Hash | Carry | Class |
|---|---|---|---|
| 1 | 9f66ae83 | kanban protocol prompt diet (KANBAN_GUIDANCE 6,606→4,066 B) | LOCAL-ONLY (prompt budget) |
| 2 | fa69c0e5 | compression degradation mode: pinned fallback_model + storm-model guard + 300 s cooldown | **UPSTREAM-CANDIDATE** (generic-quality fix; no fork branch exists yet) |
| 3 | 3a931a63 | dispatcher drain-awareness, non-counting runtime_draining requeue (F27) | LOCAL-ONLY |
| 4 | 552f79aa | scoped kanban tools loud-reject explicit `board=` | LOCAL-ONLY |
| 5 | 76fafa64 | kanban stream WIDEN, auto-subscribe open cards, terminal-only events (F23) | LOCAL-ONLY |
| 6 | 57bf8461 | amend: delivery-time board-owner derivation (F22) | LOCAL-ONLY |
| 7 | fd18b2a1 | board-aware notifier wake-profile selection (F22) | LOCAL-ONLY |
| 8 | 3b560ce6 | per-profile board pin + tool-layer butler fence | LOCAL-ONLY |
| 9 | bfdea091 | end admission-committed session row on suppressed cron runs | **UPSTREAM-CANDIDATE** — PR branch ready: `fix/cron-suppressed-session-rows` @ 862e87c2 (NOT in origin/main) |
| 10 | 1ec1dce4 | one-shot `chat -q` died on inherited automation source labels | **UPSTREAM-CANDIDATE** — PR branch ready: `fix/chat-oneshot-source-labels` @ a6c85c32 (NOT in origin/main) |
| 11 | 7ee59473 | `kanban_archive` tool stopgap | **UPSTREAM-CANDIDATE** — blocked on upstream FR #143206 / PR #143372; branches ready |

**Retire candidates: 0** (nothing upstream already carries an equivalent). All 11 must keep carrying until upstreamed.

---

## 3. BUGS TO FIX

### BUG-1 · Triage auto-decompose duplication is a live, recurring risk
- **Evidence:** 2 prior duplication incidents (card scope note); 5 auto-decompose events in the 42 h window (10-24 t_de0f1aeb→4, 10-25 t_79f5df85→4, t_cda7bf7c→3, t_8347057e→4, t_fed212ba→5) — ~3/day with `auto_decompose: true`, `auto_decompose_per_tick: 5`.
- **Impact:** duplicated children waste worker sessions (the cost unit) and can double-execute side effects; twice already needed manual re-work.
- **Effort:** S–M. **Risk:** low.
- **Fix:** give the decomposer a per-card decompose marker + `idempotency_key` on spawned children (kernel already supports idempotency_key on `kanban_create`); near-term config mitigation: scope `auto_decompose` to boards where intake is operator-authored prose only, and require the marker before a re-decompose. Also an upstream RFE candidate.

### BUG-2 · Restart-kills-workers: zombie-worker flood, drain config mismatch
- **Evidence:** 236 zombie workers reaped in 42 h (229 reap lines, events every 30–90 min, latest 10-26 10:39); 11 gateway starts in 3 days; `agent.restart_drain_timeout: 0` (config.yaml:25) while the gateway-level drain cap is 1800 s and both 10-24/10-25 graceful bounces ran drain-then-restart ("5 active work units… 0 wedged").
- **Impact:** every restart orphans in-flight workers → cards lose run progress → dispatcher retry re-does the work from scratch; on this lane a lost run costs a 174–223 K-context session. This is the estate's largest recurring waste.
- **Effort:** M. **Risk:** medium (touches dispatcher/lifecycle).
- **Fix:** (a) set `restart_drain_timeout` > 0 (e.g. 300 s) so cards get their natural drain, matching the bounce script's ESTOP pause pattern; (b) shrink the retry-burn window on drain by keeping the F27 drain-gate hotfix armed at every restart, not just sanctioned bounces; (c) upstream RFE: worker checkpoint/resume on graceful drain (planning-with-files plugin from the sibling survey is the nearest stopgap until core lands it).

### BUG-3 · `hermes-update-with-hotfixes.sh` test-net and branch-guard gaps
- **Evidence:** HOTFIX_TEST_FILES (script lines 53–60) covers only 6 of the 11 carries' test files — carries 3a931a63 (drain gate), fa69c0e5 (compression degradation), 9f66ae83 (prompt diet) have **no post-cherry-pick regression check**; step 4 `checkout -qf -B local/hotfix-carried-$(date +%F)` force-overwrites on a second same-day run; a bare `hermes update` (updates.parked_branch_strategy: update_in_place) bypasses the script entirely with no dispatch pause; CARRY_BRANCH auto-pick is lexicographic on `local/hotfixes-repaired-*` (a stale `-2026-10-24` branch @ 64c59413 is excluded only by date sort); STACK_N is not sanity-checked against the documented 11; the carried stack is never written back to a fresh `local/hotfixes-rebased-<date>`, so every update re-cherry-picks the whole aging stack (784 commits of rebase debt and growing).
- **Impact:** a future update can silently land carries that compile-clean but break the drain gate, compression guard, or prompt budget — the three most incident-linked fixes in the estate.
- **Effort:** S. **Risk:** low (script-only).
- **Fix:** add the missing 5 test files to HOTFIX_TEST_FILES; add `STACK_N == 11` assert; date-unique the carried branch (`%F-%H%M`); append a post-checkout hook guard that refuses a bare `hermes update` while a carry branch is checked out; write the carried result back to a refreshed `local/hotfixes-rebased-<date>` per the script header's own re-triage note.

### BUG-4 · Stale-card blindspot: reclaim=0 while 4–9-day-old cards idle
- **Evidence:** gargantua02 t_05987520 (hb 10-17, 9 days), t_6a6ca54c (hb 10-22, 4 days); gaudi t_91935e10 running 19.5 h with last_error "Iteration budget exhausted (200/200)"; software-co t_6e194773 blocked since 10-24, consecutive_failures=3; default t_e30677ab OPERATOR-REVIEW created 10-24 never started; default scheduled t_f7c462b2/t_4af2f705/t_a6fcf68e heartbeats 2 days stale. Dispatcher reclaim sum over the window = 0.
- **Impact:** stranded cards occupy "running"/"scheduled" visually while nothing will ever move them (no reclaim path for scheduled/no-hb states); the nightly board audit (10-26: HEALTHY) checks structure, not age, so it passes over all of these.
- **Effort:** S. **Risk:** low.
- **Fix:** add an age-based drift check to the nightly board-audit (flag running>24 h without heartbeat, blocked/scheduled >3 d idle); file the four named cards for an operator reopen-or-retire pass (same pattern as the documented t_5055661f decision).

### BUG-5 · Doc-of-record staleness (AS-BUILT + CONFIG-DIVERGENCES)
- **Evidence:** profile census 58+root documented vs 59+root live; cron table documents 15–18 jobs vs 24 live; session-gc row describes the retention_days=60 delete path that was disabled 2026-10-24 (STATEDB-RETENTION-POLICY §2); CONFIG-DIVERGENCES row 4 says `keep_first_n` where the live key is `protect_first_n` (config.yaml:130); AS-BUILT stamp figures (1.87 GB / 324 MB max state.db) stale within 2 days (live: 407 MB, snapshots tier 351 MB).
- **Impact:** the doc of record is the DR bootstrap's map; every stale row is restore-time confusion and audit toil.
- **Effort:** S. **Risk:** none.
- **Fix:** amend the five named rows (census, cron table, session-gc row, row-4 key name, stamped store sizes); adopt the AS-BUILT tail's own amendment list verbatim.

### BUG-6 · Config debris and unlabeled model usage
- **Evidence:** `_left_core_installed` still lists langfuse (disabled, migration marker, line 322/522); `model_overrides.anthropic.claude-sonnet-5.context_window: 1000000` in a custom:litellm-only tree (lines 525–528); gateway.log 10-24 22:30 names root orchestrator session model "claude-opus-5-5" while config default is qwen38-flash-fp8 — neither anthropic reference appears in CONFIG-DIVERGENCES; a compiled `secrets/__pycache__/secrets-gen.cpython-314.pyc` is committed to the estate repo.
- **Impact:** dead config misleads config-hygiene sweeps and restore; unexplained frontier-model usage on the root lane is a cost and doctrine gap.
- **Effort:** S. **Risk:** low.
- **Fix:** delete the marker/override/pyc (pyc via .gitignore `__pycache__/` — the secrets/.gitignore has the pattern but the file predates it); document or remove the claude model references; if claude-opus runs are real, add them to CONFIG-DIVERGENCES row set.

---

## 4. GAPS

### GAP-1 · DR is proven only half-way; second mirror still unwired
- **Evidence:** RESTORE.md + restore-proof (2026-10-24) prove clone→scratch-HERMES_HOME→`config check`/`profile list`/`boards list`; no drill has booted a gateway+dispatcher against restored state; upstream docs note orb/LiteLLM are outside the estate ("Hermes restores instantly but cannot answer until orb is reachable"); state.db chat history lives ONLY in the nightly ga01 mirror; the estate-nightly "pluggable second-mirror target" (garg02 / /local RAID / second GH namespace) remains "filed for operator pick" (PERF-PORT §1 A5 gaps 3/7, R5); mirrors are live mirrors — deletion/corruption propagates within a day, only git-history provides PIT rollback.
- **Impact:** host-loss recovery is credible for configs but unproven for the running system; a ga01+host simultaneous loss loses all chat/session history.
- **Effort:** M. **Risk:** low (it's additive).
- **Fix:** wire the second mirror (operator pick pending since 10-24); schedule a quarterly full-stack restore drill on a scratch machine through gateway boot + one-worker smoke card; add a canary/checksum verification step to estate-nightly so a silently-failing mirror alerts.

### GAP-2 · Single alert channel + no dead-man switch
- **Evidence:** 20 of 24 cron jobs alert only via Telegram chat 8158007517 (stdout-delivery, "empty stdout = silent"); no email/webhook/second-chat fallback found in any script; gateway heartbeat files are snapshotted hourly but nothing checks their age — a silently dead gateway produces zero alerts; prod-watchdog systemd units exist in the repo but are not confirmed running nor registry-monitored.
- **Impact:** one Telegram/gateway outage blinds the entire watchdog stack simultaneously — exactly the layers meant to catch outages.
- **Effort:** S. **Risk:** low.
- **Fix:** tiny no-agent cron: heartbeat-age check (alert if state/gateway.heartbeat older than N minutes while systemd says active) — the proven no-agent cron + alert-only pattern (memory: custodian-fleet-scan) fits; add one alternate sink (e.g. gh issue on a private repo, or a second chat) to the 5 most critical jobs only.

### GAP-3 · No log retention at all
- **Evidence:** logs/ = 55 MB and growing unbounded: tui_gateway_crash.log 23.6 MB, estate-sync.log 7.5 MB (entire history since 10-24), gateway.log 3.5 MB with no rotation sibling; no /etc/logrotate.d/hermes; per-card logs/t_*.log 2.7 MB since 10-17 unpruned; estate mirrors exclude `logs/` and `*.log` (rsync flags), so failure history is host-only.
- **Impact:** slow disk bleed now; after any incident, the primary forensic evidence is the thing not backed up.
- **Effort:** S. **Risk:** low.
- **Fix:** logrotate entry (weekly, rotate 8, compress) + include rotated logs in the nightly mirror; extend session-gc.sh or the card-log sweep with a >14 d prune (respecting GRAVEYARD conventions).

### GAP-4 · No main-lane cost/token observability
- **Evidence:** grep of config.yaml finds only `display.show_cost: false`; aux-ledger plugin covers auxiliary calls only (this is what COMPRESSION-RCA used); no per-profile token accounting exists despite this lane measuring 5.06–5.09 M cumulative input tokens/session (n≈100, PERF-PORT R6c).
- **Impact:** the estate's biggest cost driver (main-lane sessions) is unmeasured; every cost decision (prompt diets, model tiers, skill-tree dedup) is flying on one-off studies instead of a ledger.
- **Effort:** M. **Risk:** low (read-only telemetry).
- **Fix:** main-lane per-call ledger (jsonl like aux-ledger, keyed by profile/board/run), one nightly rollup cron; NOT Langfuse (canon: declined, fees) — local files only. Sibling survey's `session-lens` plugin is the trial candidate to compare against a homegrown 50-line ledger.

### GAP-5 · Retention policy structurally can't bound growth; its levers are propose-only
- **Evidence:** ARCHIVE-NOT-DELETE policy is followed mechanically (auto_prune false live, weekly vacuum engine receipted) but bounds only fragmentation: profile state.db up to 407 MB + architect state-snapshots 351 MB, already past the 10-24 stamped baselines; STATEDB-RETENTION-POLICY §4 P-A/P-B/P-C (optimize-storage ~40 MB reclaim, FTS5 merge on root's 247 MB trigram index) are "proposals for a follow-up card, not done"; trigram DROP is NO-GO (session_recovery requires it).
- **Impact:** hot-store growth is unbounded until the 60 d export window starts producing volume; the known levers sit unexecuted.
- **Effort:** M. **Risk:** medium (FTS work needs the documented pre-snapshots).
- **Fix:** action P-A/P-B as one card with the policy's own snapshot guardrails; revisit quarterly rather than on-disk-trigger.

---

## 5. FEATURE ADDS (estate-side; plugin adds live in the sibling survey)

### FEAT-1 · Upstream the 4 candidate carries → shrink the stack
fa69c0e5 (compression degradation mode) needs a PR branch authored; bfdea091 and 1ec1dce4 have ready branches (862e87c2, a6c85c32) awaiting the operator final gate; 7ee59473 rides upstream #143206/#143372. Landing all four cuts the carry stack 11→7, shrinks rebase-debt conflict surface (784 commits behind), and converts estate-specific maintenance into community-maintained code. Effort M total. This operationalizes PERF-PORT R9; every filing goes through the established distiller→operator-final-gate chain.

### FEAT-2 · Decompose idempotency + stale-card sweep (see BUG-1/BUG-4) — the two dispatcher-behavior fixes the sibling survey confirmed no plugin provides.

### FEAT-3 · Worker checkpoint-on-drain (upstream RFE): persist enough run state on graceful drain that the retry resumes instead of restarting. Would have saved a large fraction of the 236 reaped workers' work. Effort L upstream; nearest stopgap = planning-with-files (survey shortlist).

### FEAT-4 · Main-lane cost ledger (see GAP-4) + a weekly rollup line to the operator: makes the PERF-PORT prompt-diet and skill-tree decisions data-driven instead of study-driven.

### FEAT-5 · Execute PERF-PORT R1 shared skill tree (25.3× duplication, 16,795 files / 176.6 MB duplicated across profiles; cards proposed, never created). Largest single disk-and-drift hygiene win, and it multiplies every future skill edit from ~59 writes to 1. Effort M, risk medium (skills.external_dirs semantics), pilot-then-fleet per the study.

### FEAT-6 · Sixth butler for skipjack (documented deliberate gap, AS-BUILT §9 F3): intake still rides the default profile; stamp from the butler kit when skipjack traffic justifies it. Effort S. No action owed until traffic grows.

### FEAT-7 · Secrets vault encryption-at-rest: the R2 vault (62 real values, 0600) is deliberately committed to the private GitHub repo as the rollback copy (secrets/README §"Rollback"). That works, but it concentrates every fleet secret in one plaintext file on a third-party surface. Proposal: keep the one-edit-rotation generator, wrap the vault in `age` encryption before commit (generator gains one decrypt step; blueprints/manifest unchanged, value-free). Effort S–M, risk low. (Distinct from redaction canon — that governs chat/logs, not at-rest storage.)

---

## 6. RANKED TOP 10

| # | Finding | Class | Effort | Risk | One-line fix |
|---|---|---|---|---|---|
| 1 | Restart-kills-workers zombie flood (236/42 h; drain config mismatch) | BUG-2 | M | med | drain_timeout>0 + drain-gate at every restart + upstream checkpoint RFE |
| 2 | Auto-decompose duplication risk (2 incidents; 5 decomposes/42 h live) | BUG-1 | S–M | low | decompose marker + idempotency_key on children |
| 3 | Carry stack: 4 upstream candidates, 0 retires, 784-commits debt | FEAT-1 | M | low | file the 4 PRs; author branch for fa69c0e5 |
| 4 | Update-script test-net/branch gaps (3 carries unverified post-pick) | BUG-3 | S | low | add 5 test files + STACK_N assert + branch guards |
| 5 | DR: second mirror unwired, drill stops short of gateway boot | GAP-1 | M | low | operator picks mirror target; quarterly full drill |
| 6 | Single Telegram alert path + no heartbeat dead-man switch | GAP-2 | S | low | no-agent heartbeat-age cron + one alt sink |
| 7 | Zero log rotation (55 MB and unbounded; logs excluded from mirrors) | GAP-3 | S | low | logrotate + mirror rotated logs + card-log prune |
| 8 | Stale-card blindspot: reclaim=0, 4–9-day idle cards pass audit | BUG-4 | S | low | age-drift check in nightly audit + operator reopen/retire pass |
| 9 | No main-lane token/cost ledger (heaviest lane unmeasured) | GAP-4/FEAT-4 | M | low | per-call jsonl ledger + nightly rollup (local, not Langfuse) |
| 10 | R1 shared skill tree still unexecuted (176.6 MB, 25.3× dup) | FEAT-5 | M | med | pilot skills.external_dirs on 2 profiles, then fleet |

Quick wins also fixed above but below ranking cut: doc-of-record re-stamp (BUG-5), config debris cleanup (BUG-6), committed .pyc removal, CONFIG-DIVERGENCES row-4 key rename.

---

## 7. Explicit non-findings (checked, OK)

- Compression storm posture: RCA closures landed and holding — 0 compression errors in window; tripwire armed (last run 10-26 09:07 ok).
- Nightly board audit structural checks: 0 cycles / dangling parents / dead assignees / husks — verified accurate on structure (its age blindspot is BUG-4, not a false pass).
- Estate sync: hourly git mirror + nightly rsync both live and current (10-26 10:07 "sync OK"); 24/24 cron jobs "last run ok".
- Dispatcher config matches the documented canon exactly (one AS-BUILT section verified accurate).
- Hindsight banks healthy per BANK-MAP (hermes 30,164 facts; env banks repopulating per ruling); no action.
