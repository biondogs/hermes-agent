# FORK-ENDGAME Phase-0 receipts — 2026-10-23 (t_afc04040, sw-pm)

Operator ruling (option A): delete biondogs/{mprov_control_center,mprov_jobserver,mprov_scripts,mash}
after (1) four mprov-ng docs PRs resolve and (2) rescues below complete. Scope guard: NEVER biondogs/hermes-agent (#143372).

## Phase 0 — fork open-PR inventory (verified live 2026-10-23 ~14:56Z via `gh pr list --state open`)

| Fork PR | Fix | Verdict | Evidence |
|---|---|---|---|
| biondogs/mash#29 (base master; head rahul05ranjan/mash@fe8c8f3, branch fix/config-shapes-clean-error) | accept mapping-shaped configs, clean config errors | **LIVE → migrate** | `git apply --check` CLEAN on mprov-ng/mash master @ 36b6a5e; upstream `load_config` still iterates parsed YAML unconditionally (ValueError on mapping-shaped config) — verified at 36b6a5e. Related fork issue biondogs/mash#13 (MASH-013, adjudicated 2026-10-23); NO mprov-ng twin exists (mash upstream open issues are only #18/#19/#20). Original author Rahul Ranjan — preserve authorship on rebase. |
| biondogs/mash#30 (head rahul05ranjan/mash@f6a0374, branch fix/foreach-hash-items) | foreach stops dropping list items after a hash | **LIVE → migrate** | `git apply --check` CLEAN on 36b6a5e; upstream `do_foreach` path unchanged since Oct-15 pin. Adjudication hunk-check: covers none of MASH-101/102/103 — untracked upstream. |
| biondogs/mprov_control_center#2 (copilot/fix-7acece7a…, Feb 2026) | "security + code quality" hygiene | **DEAD / superseded — no PR** | Branch targets code that no longer exists upstream: systems/api/api.py + api2.py deleted, views_noath.py already renamed views_noauth upstream, settings.py already reads SECRET_KEY from env; net 12-file diff conflicts 12/12 files on upstream main @ 6afb414. Underlying themes tracked upstream via filed issues (e.g. CC-051/rootpw). Full net diff archived: rescue/cc2-net.diff in this card's workspace. |
| biondogs/mprov_control_center#3 (copilot/add-wysiwyg-text-editor) | WYSIWYG (CKEditor) feature | **DEAD — no PR** | Feature request, not a rescue fix: 1218 files / ~21k insertions, mostly vendored CKEditor statics, based Feb-2026 (upstream 301 commits ahead). If operator wants WYSIWYG, re-file as a clean upstream feature request — do not migrate this branch. |
| biondogs/mprov_jobserver | — | 0 open PRs (re-checked) | |
| biondogs/mprov_scripts | — | 0 open PRs (re-checked) | |

Rescue patches preserved byte-exact at this card's workspace: `rescue/fix29.patch`, `rescue/fix30.patch`, `rescue/cc2-net.diff`.
Migration PRs for the two LIVE mash fixes: card MPROV-M-RESCUE-MASH (sw-dev-a).

## Phase 1 — Oct-15 wave status (in progress this run)
- 120/120 Oct-15 fork issues enumerated (SETUP snapshot: CC #4–#43 = 40, JS #1–#31 = 31, SCR #1–#21 = 21, mash #1–#28 = 28). All exist ONLY on forks — vanish on deletion; survivors must be re-filed at mprov-ng.
- CC disposition complete (t_2eae052c attached `cc-oct15-dispositions.md`, at upstream pin d7c2094): 18 fixed-upstream w/ refs, 18 still-present, 4 partial (#5, #29, #35, #39), 0 regressions.
- JS/SCR/MASH disposition inputs: sweeps t_a43d97bb (JS: fork product tree identical to Oct-15 base), t_412f1a54 (SCR), t_1ee1e0e4 (MASH @ upstream pin 36b6a5e).
- Wave-2 upstream twins already filed at mprov-ng on 2026-10-23 (CC #309–#313, JSR2 twins incl. #141–#146/#155–#166, SCR #20–#27, MASH #18–#20); dedupe vs these is mandatory in the migration card.
- Bulk filing + 120/120 coverage receipt: card MPROV-M-OCT15-MIGRATE (survivor count >15 ⇒ dedicated card per ruling).

## Phase 2 — deletion gate: **NOT MET** (2026-10-23 14:59Z)
- mprov-ng/mprov_jobserver#153 MERGED 14:22Z ✓
- mprov-ng/mprov_control_center#307 MERGED 14:42Z ✓
- mprov-ng/mprov_scripts#19 OPEN ✗
- mprov-ng/mash#17 OPEN ✗
- Phase 0: receipts above complete; mash rescue PRs pending (card open).
- Phase 1: coverage receipt pending (card open).
Successor poll card created (+24h). Deletion requires operator explicit GO comment; never touches biondogs/hermes-agent.

## Ops note
`/local/projects/mprov-maint/*` shared clones were re-provisioned by a concurrent lane mid-run (2026-10-23 ~14:57Z, upstream remote refs wiped). Rescue artifacts therefore pinned to SHAs + saved patch files, not local branches.

## Phase 2 — deletion gate poll #2: **NOT MET** (2026-10-23 15:01Z, card t_9ae0e2b2)
- mprov-ng/mprov_jobserver#153 MERGED 2026-10-23T14:22:16Z ✓
- mprov-ng/mprov_control_center#307 MERGED 2026-10-23T14:42:23Z ✓
- mprov-ng/mprov_scripts#19 OPEN ✗
- mprov-ng/mash#17 OPEN ✗
- Docs-PR resolution: 2/4.
- Phase 0: card t_e5c9b3a3 (MPROV-M-RESCUE-MASH) still running (run 95) — mash rescue PRs not yet up ✗
- Phase 1: card t_74e17627 (MPROV-M-OCT15-MIGRATE) still running (run 96); mprov/maint-2026-10-23/OCT15-COVERAGE.md absent (grep-row check N/A) ✗
- Gate counters: PRs resolved 2/4 · Phase-0 cards done 0/1 · Phase-1 cards done 0/1 · coverage rows 0/120.
- Successor poll #3 created (+24h, SCHEDULED_UNTIL 2026-10-24T15:01Z). Scope guard unchanged: four mprov forks only; NEVER biondogs/hermes-agent; deletion ONLY on explicit operator GO comment.

## Phase 0 — mash rescue PRs UP (2026-10-23, card t_e5c9b3a3 / MPROV-M-RESCUE-MASH)
- Fix A (fork PR mash#29, fork issue #13 / MASH-013): **https://github.com/mprov-ng/mash/pull/21** — branch `fix/config-shapes-clean-error`, head 823062f (cherry-pick -x of fe8c8f3, Rahul Ranjan authorship preserved). One adaptation: test pins `shell.configfiles` (master's load_config now rescans the search list per merged #14). Local fresh-venv pytest 39/39 (base 33/33).
- Fix B (fork PR mash#30, fork issue #14 / MASH-014): **https://github.com/mprov-ng/mash/pull/22** — branch `fix/foreach-hash-items`, head 01bfcb8 (cherry-pick -x of f6a0374, authorship preserved, no changes vs fork). Local fresh-venv pytest 40/40.
- Gate compliance: both head-commit messages + both PR bodies carry exact line `Assisted by JoeBot`; uberlinuxguy requested as reviewer on both; Agent-Profile/Agent-Run hook trailers stripped pre-push per butler guidance; docs-sweep commit f9bb463 NOT carried (superseded by mash#17); base = mprov-ng/mash master @ 36b6a5e.
- CI: pytest (3.9/3.11/3.13) pass on both PRs. Rescue patches had been wiped from t_afc04040/rescue/ mid-run (sprint-sync lane); rebuilt via direct fetch from rahul05ranjan/mash (branch tips matched pinned SHAs fe8c8f3/f6a0374 exactly).

## Dated amendment 2026-10-23T17:41Z — mash rescue PRs #21/#22 CLOSED UNMERGED (operator policy)

Operator directive 2026-10-23: contributor PRs are not currently accepted on the main mprov-ng repos. Per directive, both rescue PRs were closed WITHOUT merging (neutral public comment posted on both; no internal detail disclosed).

| PR | State | Head SHA | Merged | Closed at |
|---|---|---|---|---|
| mprov-ng/mash#21 (config-shapes) | CLOSED | `823062fece1a2fc55908db6ec5fc2c9d5195044a` | no (`mergedAt: null`) | 2026-10-23T17:41:45Z |
| mprov-ng/mash#22 (foreach-hash) | CLOSED | `01bfcb84d5d6b6b94c0f90de619e0cd71f407787` | no (`mergedAt: null`) | 2026-10-23T17:41:47Z |

Read-back verified via `gh pr view --json state,number,mergedAt` (both `state: CLOSED`, `mergedAt: null`).

**Durable re-approach material:** closed PRs retain their full diffs permanently on mprov-ng — PR pages, commit history, and head SHAs above remain fetchable regardless of branch state. The re-approach (separate card) can always reconstruct each fix from `mprov-ng/mash` PR refs (`refs/pull/21/head`, `refs/pull/22/head`) or the cherry-picked upstream commits (originals: rahul05ranjan/mash fe8c8f3 / f6a0374, authorship preserved via `cherry-pick -x`). Nothing further needs to be preserved out-of-band.

Scope compliance: no branches deleted, no fork repos touched, mprov-ng/mprov_scripts#19 and mprov-ng/mash#17 (own docs PRs) untouched — unaffected by this policy. No re-open or re-submit performed here.

### Deletion-gate amendment (same date)
- mprov-ng/mash#21 and #22 are **resolved-as-CLOSED-UNMERGED** by operator policy (2026-10-23T17:41Z). They no longer await a merge and are removed from any gate expectation as pending-merge items; the rescue fixes they carried are preserved via the closed-PR diffs above for the separate re-approach card.
