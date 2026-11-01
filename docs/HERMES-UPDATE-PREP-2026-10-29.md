# HERMES-UPDATE-PREP — 2026-10-29

**Card:** t_7c662188 (default board) · **Lane:** kanban-board-architect · **Operator request (verbatim):** "prepare our local hermes and fixes for an update."
**Scope:** inventory + plan only. No update was performed, no checkout mutated, no gateway touched. Everything below was re-verified live on 2026-10-29 (all commands read-only: git log/ls-remote/show, `gh api` reads, file reads).

---

## 0. Executive summary & GO/NO-GO

| Decision | Verdict | Why |
|---|---|---|
| **Version bump today** | **NO-GO** | Upstream's latest *release* is still **v0.22.5 (2026-10-23) — the exact base we already run**. There is no released version to update to. Updating would mean jumping ~1,137 unreleased upstream-main commits (flood-era churn) for zero release value. |
| **Update-readiness work NOW** (stack re-triage, script sync) | **GO** (small, mechanical, strongly recommended before anything else) | The sanctioned update path is currently **broken by drift**: the update script expects a 14-commit stack, its auto-picked carry branch holds 15, and the live install carries **21** — running it today would refuse at preflight (safe), and if force-reconciled naively would **silently drop 6 carried fixes** including the decomp-hold guard and the B2-4 kinds work. |
| **Real update when v0.22.6+ (stable) ships** | **GO, via the runbook in §6, under a fresh operator-GO'd card** | Sanctioned path (`hermes-update-with-hotfixes.sh`) already does pause → update → linear carry re-apply → carry test-net → rollback; it just needs the §5 drift fixes applied first. |

Bottom line: the estate is **not update-ready today** for mechanical reasons (documented drift in the carry machinery), and has nothing released to update to. Close the drift (§5, ~30 min of work), then wait for the next stable release.

---

## 1. Live state snapshot (verified 2026-10-29)

| Item | Value |
|---|---|
| Checkout | `~/.hermes/hermes-agent` (git install; the gateway runs this tree directly — launcher `~/.local/bin/hermes` → `.hermes/bin/hermes` in the checkout; running gateway code = on-disk HEAD) |
| Branch / HEAD | `local/hotfix-carried-2026-10-28` @ **165b2a5af3** |
| `git describe` | `v0.22.5+canary.20261027T070237Z-28-g165b2a5af3` |
| Base version | upstream release **v0.22.5** (= latest stable; tag `56b6a31fed`, legacy base `bf0203a794`) + upstream main through merge-base **fa59cb998a** (2026-10-18) |
| Carry stack | **21 commits over upstream** (20 `LOCAL HOTFIX` + 1 upstream-PR commit `0522a7bbb4`, PR #145581) — full table §3 |
| Working tree | clean (no uncommitted local changes) |
| Remotes | `origin` = NousResearch/hermes-agent (blob:none partial) · `fork` = biondogs/hermes-agent · `estate` = biondogs/hermes-estate |
| Update config | `updates.pre_update_backup: quick`, `backup_keep: 5`, `parked_branch_strategy: update_in_place` — mitigated by the sanctioned script's explicit sequence |
| Sanctioned update path | `~/.hermes/scripts/hermes-update-with-hotfixes.sh` (G-26; bare `hermes update` is refused by the launcher shim while carries exist) |
| Upstream PR situation | 5 PRs by biondogs open, **none merged** (§4); upstream repo under severe spam flood (~51.9k open issues; PR creation blocked for non-collaborators — operator HOLD on the held filing t_ed6f85c9) |

---

## 2. Version delta (local ⇄ upstream)

```
local base ── fa59cb998a (2026-10-18, merge-base)
                 ├── +0 upstream   [we ride v0.22.5 release tag lineage + main to fa59cb998a]
                 └── local carry stack: 21 commits → live HEAD 165b2a5af3

upstream main:
  last-fetched origin/main  e5ea5fd9cc (fetched 2026-10-28 11:48 EDT)  = fa59cb998a + 44
  live main (ls-remote)     088f657ecf (2026-10-29)                     = e5ea5fd9cc + 1,093
                                                          TOTAL delta    = fa59cb998a + 1,137
```

- **Latest upstream release: v0.22.5, published 2026-10-23** (verified via GitHub API; nothing newer released as of 2026-10-29). Canary tags ship daily (`v0.22.5+canary.2026102*T*Z`, latest fetched locally: `20261028T064834Z`).
- The 44 fetched commits (`fa59cb998a..e5ea5fd9cc`) are concentrated in **worker/session ownership**: `gateway/session_managed_worker.py`, `gateway/session_worker_reservation.py` + tests, including a Revert of "the worker reservation always binds the owner's OS subject". **Zero overlap with any hotfix root-cause file** in that window (diff of 88 files, intersected with the carry footprint = empty).
- The further **+1,093 commits are NOT fetched locally** (this task was read-only on the checkout). Per-file churn in the full window was probed via GitHub API instead (§5 risk table). Repo-wide themes visible from public history: flood-era plugin-catalog churn, webapp/desktop fixes, deps bumps, deadline/poll_until refactors, kanban worker-turn attribution changes (already in base).
- No CHANGELOG-based breaking-change list is publishable from here; the practical breaking surface for *us* is the per-file churn table below plus whatever a post-fetch diff shows at update time.

---

## 3. Inventory — the 21-commit carry stack (oldest → newest on `local/hotfix-carried-2026-10-28`)

Numbering follows the update script's hotfix ledger (#1–#14); #15+ are landed since 2026-10-27 and are **undocumented in the script** (see §5).

| # | Commit | What it fixes | Root-cause files | Upstream PR | PR status | Needed after bump? |
|---|---|---|---|---|---|---|
| 1 | `0a259687d3` | R6(b) kanban protocol prompt diet — KANBAN_GUIDANCE 6,606→4,066 rendered bytes | `agent/prompt_builder.py`, `tests/agent/test_kanban_guidance_diet.py` | none | — | YES (perf, estate-specific) |
| 2 | `6360647bfa` | Compression degradation mode — pinned fallback_model, storm-model guard, 300 s fallback-arm cooldown | `agent/context_compressor.py` + 2 tests | **#145277** | **OPEN** | YES until merged |
| 3 | `a6eb24b781` | Dispatcher drain-awareness — no dispatch while gateway drains + non-counting `runtime_draining` requeue (F27) | `gateway/kanban_watchers.py`, `hermes_cli/kanban_db_dispatch.py`, `hermes_cli/kanban_worker_client.py` + 3 tests | none | — | YES (protects card budgets at every bounce) |
| 4 | `189f07a469` | Scoped kanban tools loud-reject fenced explicit `board=` (was silent wrong-board create) | `tools/kanban_tools.py` + test | none | — | YES (fleet safety) |
| 5 | `dbff6f626c` | Kanban stream WIDEN — auto-subscribe every open card, terminal events only (F23) | `gateway/kanban_watchers*.py`, `hermes_cli/config_defaults.py`, `kanban_db_notify.py` + test | none | — | YES |
| 6 | `f915aca057` | AMEND: delivery-time board-owner derivation (F22 scope-2) | `gateway/kanban_watchers_notifier.py` + test | none | — | YES |
| 7 | `9f7d3420b1` | Board-aware notifier wake-profile selection (F22 — no more cross-board butler wakes) | `gateway/kanban_watchers_notifier.py`, `hermes_cli/kanban_db.py` + test | none | — | YES |
| 8 | `494df3ec0b` | Per-profile kanban board pin + tool-layer butler fence | `hermes_cli/config_defaults.py`, `kanban_db.py`, `tools/kanban_tools*.py`, `toolsets.py` + test | none | — | YES (the incident-class fence) |
| 9 | `8ac12b0734` | End admission-committed session row on suppressed cron runs | `cron/scheduler.py` + test | **#144221** | **OPEN** | YES until merged |
| 10 | `0e9d141eff` | One-shot `chat -q` died host-wide on inherited automation source labels | `hermes_cli/gateway_session_store.py` + test | **#145254** (fork branch `fix/chat-oneshot-source-labels` also on fork) | **OPEN** | YES until merged |
| 11 | `fc54bb7e37` | Model-callable `kanban_archive` tool — stopgap until upstream lands one | `tools/kanban_tools*.py`, `toolsets.py` + test | **#143372** (anchor issue **#143206**) | **OPEN / issue OPEN** | YES until merged (7 competing PR variants on the anchor issue ⇒ merge may take a while, or never ours specifically) |
| 12 | `de0318877a` | Decompose child idempotency — `decompose:<root>:<idx>` keys + reuse backstop (ER-2) | `evals/kanban_graph_identity.py`, `hermes_cli/kanban_db_graph.py` + test | none | — | YES |
| 13 | `2b0bfe743e` | G-29 long-job detach rule (hjob launcher, no worker bg/tmux) in KANBAN_GUIDANCE | `agent/prompt_builder.py` + test | none | — | YES (governance carrier) |
| 14 | `4abea8b1ed` | **boards list COUNTS pin-free read-only resolution** (the `kanban boards list` fenced-counts fix; root cause `kanban_db.py:_board_path` env-pin class) | `hermes_cli/kanban_boards.py` + test | **HELD — t_ed6f85c9**: fork branch `biondogs:fix/kanban-boards-counts-fenced` @ `25509d0ba3` pushed, PR creation externally blocked (upstream interaction-limits amid spam flood); **operator HOLD 2026-10-29: "Hold the filing till further notice." Do not touch, retry, or drop.** | not filed | YES regardless of PR status |
| 15 | `0522a7bbb4` | PR #145581 rev-2 head: per-subscription event-kind allowlist for notify subs (B2-4) — carried intentionally so the live branch exactly matches the filed PR | `hermes_cli/kanban*.py` (5 files) + test | **#145581** | **OPEN** | CARRY while open (once merged upstream, drop from stack — it becomes identical content) |
| 16 | `020c250cb4` | AMEND: stream auto-subscribe stamps `kinds` (`kanban.stream_notify_kinds`) — builds on #15 | `gateway/kanban_watchers_notifier.py`, `hermes_cli/kanban_db_notify.py` + test | none (local extension of #15) | — | YES (depends on #15) |
| 17 | `435d990334` | Kanban dashboard drops stale cross-board `/board` responses (activeBoardRef guard) | `plugins/kanban/dashboard/dist/index.js` **only — built dist bundle, no regression test** | none | — | YES (re-derivation expected: dist bundles get rebuilt upstream) |
| 18 | `ea9a914d46` | CLI `--board` fence-divergence loud refusal (was silent current-board fallback; AS-BUILT F24/F8 closure) | `hermes_cli/kanban.py`, `tests/hermes_cli/test_kanban_cli_board_flag_fence.py` | none | — | YES |
| 19 | `0b5e1895c4` | **Hotfix #16**: auto-subscribed notify+wake rows are born with the config's kinds allowlist (B2-4 kinds-gap closure) | `gateway/slash_commands.py`, `hermes_cli/kanban_db.py`, `kanban_db_notify.py` + 3 test files (incl. `test_kanban_notify.py`, `test_kanban_tools.py`) | none | — | YES |
| 20 | `31ec07d34c` | Carry lint: PIE807 useless-lambda fixes in carried hotfix test files | 2 test files only | none | — | YES (rides the stack) |
| 21 | `165b2a5af3` | **Suppress auto-decomposer/specifier on operator-held cards** (`OPERATOR HOLD` marker → hold_markers match; DECOMP-HOLD GUARD, t_7fd1c800) | `hermes_cli/config_defaults.py`, `kanban_db.py`, `kanban_db_graph.py`, `kanban_decompose.py`, `kanban_diagnostics.py` + `test_kanban_hold_guard.py` | none | — | YES (live guard, activated 2026-10-29 hotfix 165b2a5af3) |

**Regression-test net documented in the update script (`HOTFIX_TEST_FILES`, 14 unique files) covers #1–#14 only.** Missing from it: `tests/hermes_cli/test_kanban_cli_board_flag_fence.py` (#18), `tests/hermes_cli/test_kanban_notify.py` + `tests/tools/test_kanban_tools.py` (#16/#19), `tests/hermes_cli/test_kanban_hold_guard.py` (#21); #17 (dist bundle) has no test file at all — must be documented as such in the script comment.

---

## 4. Upstream filing ledger (all statuses verified live 2026-10-29 via GitHub API)

| Artifact | What | Status | Carried-future linkage |
|---|---|---|---|
| PR **#145581** | feat(kanban): per-subscription event-kind allowlist (B2-4) | **OPEN**, not merged, head `0522a7bbb4` == carried commit #15 | when merged → drop #15 from the stack |
| PR **#145277** | feat(compression): degradation mode | **OPEN** | #2 |
| PR **#145254** | fix(cli): bound classic client's session.create source | **OPEN** | #10 |
| PR **#144221** | fix(cron): end admission-committed session row on gate-suppressed runs | **OPEN** | #9 |
| PR **#143372** | feat(kanban): model-callable kanban_archive | **OPEN** | #11 |
| Issue **#143206** | anchor issue for kanban_archive (7 PR variants) | **OPEN** | #11 |
| **Held filing — t_ed6f85c9** | boards-list-counts PR kit (frozen bytes sha256-matched, fork branch pushed @ `25509d0ba3`) | **BLOCKED externally / OPERATOR HOLD** — upstream repo is under a spam flood (~51,871 open issues) with interaction-limits refusing PR creation for non-collaborators; operator 2026-10-29: "Hold the filing till further notice." | #14 stays carried locally regardless |
| Staged, not filed | `~/.hermes/patches/upstream-fr-kanban-self-gate/` (issue draft, 2026-10-28) | draft only; no public write | n/a |
| Staged, not filed | `~/.hermes/patches/er3-upstream-prs/` (chat-oneshot, compression-degradation, kanban-archive issue-comment kits) | older staging dirs for the filed PRs above | — |

**Net: nothing is redundant today. Every one of the 21 carried commits stays needed.**

⚠ Observation (no action taken, per the hold): held card t_ed6f85c9 sits in `scheduled` status with a banked wake protocol for 2026-10-30 15:00 EDT, while the operator's later HOLD says "no further automated retries / stays parked". That wake (wake-driver or one-shot cron, whichever was armed — the earlier 1 h retry cron 3f691558ce3c per card comments) should be stood down when the hold is next serviced — flag for the operator, done from that card's own lane, not from this prep.

---

## 5. Risk assessment per carried fix (straight-bump impact)

Upstream churn measured via GitHub commits-API per path, window 2026-10-17 → 2026-10-29 (≈ the full delta; a handful of counted commits are ≤ merge-base, so counts slightly overstate — directionally reliable). Verdict legend: **(a)** applies clean / silently keeps working · **(b)** reverts or needs re-derivation · **(c)** conflict, manual rebase expected (cherry-pick conflict = script auto-rollback, then re-triage).

| Fix | Upstream churn on its files | Verdict | Notes |
|---|---|---|---|
| #2 degradation mode | `context_compressor.py` **19** | **(c) HIGH** | hottest of the logic files; expect textual conflicts |
| #10 one-shot chat -q | `gateway_session_store.py` **27** | **(c) HIGH** | small fix in a heavily churned file |
| #9 cron session row | `cron/scheduler.py` **13** | **(c) HIGH** | |
| #3 drain-awareness | `kanban_db_dispatch.py` **14**, `kanban_worker_client.py` **11**, `kanban_watchers.py` 0 | **(c) HIGH** | |
| #1 diet / #13 G-29 guidance | `prompt_builder.py` **9** | **(c) MED** | guidance-text insertions into churned builder |
| #8 pin+fence / #4 loud-reject | `config_defaults.py` **37**, `kanban_db.py` **9**, `toolsets.py` **6**, `tools/kanban_tools.py` **0** | **(c) MED-HIGH** | config_defaults is the most-churned shared file; the tools-side half should apply clean |
| #19 born-allowlist | `slash_commands.py` **8**, `kanban_db.py` 9, `kanban_db_notify.py` 0 | **(c) MED** | |
| #21 decomp-hold guard | `config_defaults.py` 37, `kanban_db.py` 9; `kanban_db_graph/decompose/specify/diagnostics` **0** | **(c) MED** | config_defaults overlaps only |
| #11 kanban_archive | `tools/kanban_tools.py` 0, `toolsets.py` 6, `kanban_tools_schemas.py` 1 | **(a/c) borderline** | mostly clean; watch toolsets.py |
| #15 PR#145581 content | `kanban.py` 0, `kanban_db.py` 9, parser/connect low | **(a/c) MED** | PR will itself need rebasing on the fork when main moves |
| #17 dashboard dist guard | dist bundle path **0** in window, but dist is a rebuild artifact | **(b)** assume re-derivation | re-apply source-side change & rebuild, or re-derive guard in the new bundle |
| #5/#6/#7 stream+notifier, #16 kinds stamp | `kanban_watchers*.py` 0, `kanban_db_notify.py` 0 | **(a)** clean | |
| #12 decompose idempotency | `kanban_db_graph.py` 0 | **(a)** clean | |
| #14 boards list counts | `kanban_boards.py` 0 | **(a)** clean | |
| #18 CLI fence refusal | `kanban.py` 0 | **(a)** clean | (already survives in the 15-commit rebased branch) |
| #20 carry-lint | test files | **(a)** trivial | may even merge as no-op |

Important caveat: the +1,093 unfetched commits mean this table's churn includes the real window; the **exact** conflict set is only knowable after a fetch at update time. The script's cherry-pick with auto-rollback makes (c)-verdicts safe-but-blocking, not dangerous.

### 5.1 Drift findings that BLOCK a safe update today (must close first)

1. **Script stack-count drift:** `EXPECTED_STACK_N=14` vs auto-picked carry branch `local/hotfixes-rebased-2026-10-25` = **15 commits** → preflight refuses (safe, but the sanctioned path is dead until synced).
2. **Silent-carry-loss hazard (the important one):** the auto-picked rebased branch is **missing 6 of the 21 live-stack commits** — #15 (`0522a7bbb4` PR content), #16 (`020c250cb4`), #17 (`435d990334`), #19 (`0b5e1895c4`), #20 (`31ec07d34c`), #21 (`165b2a5af3`). If someone "fixed" only the count and ran the script as-is, the update would land **without the kinds-gap closure, dashboard guard, and the OPERATOR-HOLD decomposer guard**, silently. 
3. **Test-net drift:** `HOTFIX_TEST_FILES` lacks the new carries' regression files (see §3 note); #17 has no regression test (document the exemption).
4. **No off-host backup of carry refs:** the fork holds only the held PR branch; all `local/hotfix-carried-*` / `local/hotfixes-rebased-*` branches and `local-hotfix-stack-*` tags exist only on ga01. The estate tar-backup covers `~/.hermes` bulk, but the update runbook below adds an explicit git-bundle snapshot.

**Fix for 1–3 (the Phase-0 stack sync, runbook §6):** anchor a fresh `local/hotfixes-rebased-2026-10-29` at the live carried tip (identical shas — a branch copy, no cherry-pick), bump `EXPECTED_STACK_N` to **21**, extend `HOTFIX_TEST_FILES` with the four missing test files (#17 documented as test-less), update the script's CARRY LIST header comment. One edit, per ER-4 law.

---

## 6. Safe-update runbook (execute ONLY under an operator-GO'd card; not this one)

### Phase 0 — Stack sync (do NOW; independent of any release; one small card)
1. `cd ~/.hermes/hermes-agent && git branch local/hotfixes-rebased-2026-10-29 local/hotfix-carried-2026-10-28` — makes the auto-picked newest rebased branch == the live 21-commit stack (date-unique name per carry-stack law).
2. One edit to `~/.hermes/scripts/hermes-update-with-hotfixes.sh`: `EXPECTED_STACK_N` 14→**21**; append to `HOTFIX_TEST_FILES`:
   `tests/hermes_cli/test_kanban_cli_board_flag_fence.py` (#18), `tests/hermes_cli/test_kanban_notify.py` + `tests/tools/test_kanban_tools.py` (#16/#19), `tests/hermes_cli/test_kanban_hold_guard.py` (#21); comment `#17 dashboard dist — no regression test (dist bundle, t_80c84a9a exemption)`. Refresh the CARRY LIST header (#15 = PR #145581 content; #16–#21 as in §3).
3. Dry-verify the preflight invariants WITHOUT updating: `git rev-list --count origin/main..local/hotfixes-rebased-2026-10-29` == 21; every listed test file exists at the carried tip; `bash -n` the script.
4. Re-verify hotfix-#14's five upstream PR statuses (§4) — drop-from-stack opportunities appear only on merge.

### Phase 1 — Decide the target & get the GO
5. Check what's released: `gh api repos/NousResearch/hermes-agent/releases/latest`. Default policy: **update only onto a stable release tag** (v0.22.6+ when it ships). Updating to unreleased main is an explicit operator choice with a stated reason.
6. Operator GO on a dedicated update card (reference this doc). Confirm a quiet-ish window (the script engages the global ESTOP `hermes pause` itself).

### Phase 2 — Snapshot (insurance before any mutation)
7. `git -C ~/.hermes/hermes-agent tag local-hotfix-stack-20261029 165b2a5af3`
8. `git -C ~/.hermes/hermes-agent bundle create ~/.hermes/backups/hermes-agent-pre-update-20261029.bundle --all` (all carry branches + tags in one off-tree file; verify with `git bundle verify`).
9. Board DBs: rely on `kanban-dr-backup` (daily 02:17) but run a manual pass: snapshot all 7 board DBs + `~/.hermes/state.db` into `~/.hermes/backups/pre-update-20261029/`. Code-only updates don't touch DBs, but the cheap belt is cheap.
10. Record `PRE_HEAD=$(git -C ~/.hermes/hermes-agent rev-parse HEAD)` and `PRE_BRANCH=local/hotfix-carried-2026-10-28` on the card.

### Phase 3 — Execute the sanctioned path
11. `bash ~/.hermes/scripts/hermes-update-with-hotfixes.sh` (add `--skip-tests` only if the operator explicitly waives the net — don't). The script: preflight (clean tree, STACK_N==EXPECTED, test-net present) → carry-test baseline (FAILED-set snapshot) → `hermes pause` → `git checkout -B main origin/main` (ff) → `hermes update --yes --no-gateway-restart` (fetch happens here — this is when the real conflict surface materializes) → detached-HEAD cherry-pick of `CARRY_BASE..CARRY_TIP` → carry test re-run gated on **zero new FAILED** vs baseline → writes back `local/hotfix-carried-<stamp>` + `local/hotfixes-rebased-<stamp>`.
    - **On cherry-pick conflict:** the script auto-rolls-back (checkout restored, dispatch RESUMED, old gateway keeps serving) and exits with the re-triage pointer. Re-triage per §5 verdicts (expect conflicts on #2, #9, #10, #3, #8/#21 per the churn table), re-run. #17 (dist bundle) likely needs re-derivation rather than a clean pick.
    - **Do not** run a bare `hermes update` — the launcher shim refuses it for good reason; do not bypass with `HOTFIX_UPDATE_SANCTIONED=1` outside the script.

### Phase 4 — Activate & verify (this lane owns the bounce)
12. Only after Phase-3 success + operator line: restart via the canonical skill `bash ~/.hermes/scripts/gateway-graceful-bounce.sh --reason "Hermes update <newhead> + hotfix carry"` (never `hermes gateway restart`, never hand-rolled).
13. Post-bounce addendum-B triage on all 7 boards (per the bounce law).
14. Verification suite (evidence into the card):
    - **Carry net, clean-clone authoritative receipt:** `git clone --branch local/hotfix-carried-<stamp> ~/.hermes/hermes-agent /tmp/<name> && cd /tmp/<name> && uv sync --group dev && ./scripts/run_tests.sh <FULL updated HOTFIX_TEST_FILES list>` — all green (in-place host runs are acceptable for the kanban/gateway subset only; see skill `hermes-agent-local-testing`). **(Amended 2026-11-01, CI-CONTAINERS-1/2 live:** preferred path is now inside the standing containers — clean-clone rebuild via `software-co ci/hermes-upstream/run-branch.sh <clone>` on `hermes-upstream:fresh`, estate-shaped probes (profile list, config check, fix-class probes) via `ci/hermes-estate-twin/scripts/twin-shell`/`twin-test` in the estate twin; pin the image tag + sha (or twin STATUS stamp) as the receipt — see `docs/CI-CONTAINERS-GUIDANCE.md`.)
    - `hermes -p <profile> config check` on root + butler + architect profiles.
    - Live probes per fix-class: `hermes kanban boards list` inside an env-pinned worker context shows correct per-board counts (#14); an `OPERATOR HOLD`-marked blocked card is not decomposed (#21); new auto-subscribed stream rows carry the kinds allowlist (#16/#19); CLI `--board <foreign>` under a pinned profile refuses loudly (#18); `kanban_archive` tool resolves (#11); stream auto-subscribe + terminal-only delivery (#5); `hermes doctor`.
    - If `verify_pins.py` (AS-BUILT F14 tooling) is present/relevant, run the 5/5 pin check.

### Phase 5 — Rollback
15. **Before activation (Phase-3 failure):** nothing to do — the script restored PRE_HEAD and RESUMED dispatch; triage the conflicts and retry, or stand down and report.
16. **After activation (new gateway misbehaving):** `git -C ~/.hermes/hermes-agent checkout -qf local/hotfix-carried-2026-10-28` (restore the pre-update carried branch exactly — never a bare sha while main carries the rebase), then a second canonical bounce; verify HEAD == `165b2a5af3`… (or whichever PRE_HEAD was recorded in step 10 if a post-#21 hotfix landed in the meantime — use the recorded value, not this doc's). Rollback is code-only: no DB or config restore needed. Receipt/comment everything; block the update card for the operator if the rollback itself fails.

### Housekeeping after a successful update
17. Update AS-BUILT §HERMES record + GOVERNANCE G-26 references with the new carried branch/stamp; drop any carry whose upstream PR merged in the run-up (#15 first candidate); notify the operator.

---

## 7. Recommendation to the operator

1. **Bless Phase 0 (stack sync) now** — it's the only real prep gap: EXPECTED_STACK_N 14→21, test-net + 4 files, fresh `local/hotfixes-rebased-2026-10-29` anchor. ~30 min, no version change, closes the silent-carry-loss hazard.
2. **Hold the version bump until upstream ships a stable release newer than v0.22.5** (or explicitly rule to track main/canary). Take it via §6 under a fresh GO card.
3. **Leave t_ed6f85c9 held** exactly per your standing order; when that lane is next touched, stand down the leftover 2026-10-30 15:00 wake noted in §4.
4. Optional insurance: push the carry branches/tags to the private `biondogs/hermes-estate` mirror (or accept the daily estate bulk backup) so the hotfix stack survives ga01 disk loss — operator's call.

*Prepared by kanban-board-architect, card t_7c662188. Read-only session: no checkout mutations, no gateway actions, no upstream writes.*
