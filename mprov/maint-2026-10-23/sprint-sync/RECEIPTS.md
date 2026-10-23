# SPRINT-SYNC RECEIPTS — wave-2 relay to mprov-ng + project 9 (kanban t_2beff046)

Executed 2026-10-23 by sw-pm. Venue ruling applied: issue filings target
live `mprov-ng/<repo>` repos + org project “2026 Issue Sprint”
(projects/9, Todo column). Forks disused for issues/clones; Oct-15 wave
issues untouched; fork REPOS untouched.

Pack source: `mprov/maint-2026-10-23/` @ `67f5109` (verified on-disk packs
byte-unchanged vs 67f5109 via `git diff 67f5109 HEAD -- APPROVED-FILING-*.md`
= empty before filing). FILE's fork-filing receipts: `filing/` @ `8cb2030`.

## Freshness pass (governing step-2 rule: newly-covered upstream → skip)

Method: live open-issue lists on each mprov-ng repo (Jaccard title scan AND
body-level evidence-site scan: each pack finding's `file:line`/function
references grepped against every open upstream issue body) + open-PR review
(CC #306 diff: zero bootdev/ipmitool touches; CC #308: Django-pin+migrations
only; JS #154: libgenders only; SCR #19 / MASH #17: docs-only). Two
orthogonal title scans (ours + FILE's) missed wording-divergent upstream
issues — the body-level scan is what caught the JS trio below.

Result: **9 skips** (deviation from the operator note's expected “4 twins” —
the packs annotate SIX CC twins; #142/#144/#149 were created upstream
2026-10-23T13:12–13:39Z by the plugin-test-suite pipeline, at/after FILE's
filing):

| ID | Repo | Action | Covering ref (all verified OPEN this pass) |
|---|---|---|---|
| CC-045 | mprov_control_center | SKIP-COVERED | mprov-ng CC #268 (pack-annotated twin) |
| CC-046 | mprov_control_center | SKIP-COVERED | mprov-ng CC #270 (pack-annotated twin) |
| CC-047 | mprov_control_center | SKIP-COVERED | mprov-ng CC #288 (pack-annotated twin) |
| CC-048 | mprov_control_center | SKIP-COVERED | mprov-ng CC #290 (pack-annotated twin) |
| CC-049 | mprov_control_center | SKIP-COVERED | mprov-ng CC #273 (pack-annotated twin; same site static/mprov_stateful.py:219-226) |
| CC-050 | mprov_control_center | SKIP-COVERED | mprov-ng CC #274 (pack-annotated twin) |
| JSR2-01 | mprov_jobserver | SKIP-COVERED | mprov-ng JS #142 (same site image_update.py:137-163, same fix) |
| JSR2-02 | mprov_jobserver | SKIP-COVERED | mprov-ng JS #144 (same site image_update.py:240-247+263) |
| JSR2-03 | mprov_jobserver | SKIP-COVERED | mprov-ng JS #149 (same site nads.py:209-214; #149 is a superset fix) |

## Per-repo counts

| Repo | filed-upstream | skipped-covered | added-to-project | fork-dupes-deleted | fork pending-delete (blocked) |
|---|---|---|---|---|---|
| mprov_control_center | 5 (#309–#313) | 6 | 5 | 11 | 0 |
| mprov_jobserver | 11 (#156–#166) | 3 | 11 | 14 | 0 |
| mprov_scripts | 8 (#20–#27) | 0 | 8 | 8 | 0 |
| mash | 3 (#18–#20) | 0 | 3 | 3 | 0 |
| **Total** | **27** | **9** | **27** | **36** | **0** |

(Final column/status per resume run 104 — see “Project 9 — RESOLVED” and
“Resume run 104” below. Attempt-1 snapshot recorded 0 added / 27 pending.)

Filed IDs→numbers: `sprint-sync/relay-receipts.json` (each entry: id, repo,
URL, labels, body sha256[:12], readback status, originating fork issue).
Readback: 27/27 title+labels byte-exact; bodies byte-exact modulo GitHub's
trailing-newline store normalization (documented artifact, content identical).
0 failures. 0 new issues beyond the 36 approved packs. Issues-only scope
guard honored (no code, no PRs).

## Label discrepancies (noted per card instruction)

Upstream repos had NO taxonomy labels (`s1-blocker/s2-functional/
s3-robustness/s4-hygiene/review-found`). Created on demand (additive,
trivially-safe; colors copied from the fork labels): CC +`review-found,
s1-blocker, s3-robustness`; JS +`review-found, s3-robustness, s4-hygiene`;
SCR +`review-found, s2-functional, s3-robustness, s4-hygiene`;
MASH + same four. `bug`/`enhancement` already existed everywhere.

## Project 9 — CAPABILITY FAILURE (attempt 1) → RESOLVED (resume run 104)

Attempt 1: `gh project item-add 9 --owner mprov-ng --url <first-filed-url>` →
`error: your authentication token is missing required scopes [read:project]`
(token biondogs scopes: gist, read:org, repo, workflow; no GH_TOKEN in env;
`gh auth refresh` is browser-interactive → not possible headless).
`gh project field-list 9` fails identically, so the Todo option-name
verification never ran. **0 of 27 filed issues were in project 9 at block
time.** Receipt: `sprint-sync/project-denial-receipt.json`.

Resolution 2026-10-23T15:21Z: operator ran `gh auth refresh`; token now
carries `project` scope (live-verified via `gh auth status`). All 27 filed
issues added to org project 9 “2026 Issue Sprint”; read-back `item-list`
shows **27/27 present, Status=Todo** (project items 120 → 147, exactly +27).
Todo option name verified via `field-list` first: Status field
`PVTSSF_lADOBiDZ0c4BoTUYzhm0DR4`, option `Todo` (`f75ad846`). Per-issue
receipts: `project9-adds.log` (add rc=0 ×27) +
`project9-additions.json` (url, item id, project_status=Todo).

## Fork wave-2 cleanup

9 twin-covered fork issues DELETED after covering twins verified OPEN in the
same pass (`sprint-sync/twin-cleanup-receipt.json`): biondogs CC #48–#53,
JS #32–#34. 27 relayed-issue fork copies were NOT deleted in attempt 1 (gated
on project-9 add per butler ruling); all 27 deleted in resume run 104 after
their mprov-ng twins were verified live-open immediately before each
deletion and confirmed added to project 9 — see “Resume run 104” below and
`sprint-sync/fork-deletions.log`. Total fork wave-2 cleanup: 36/36 deleted.
Oct-15 wave fork issues: untouched. Fork repos untouched. Fork branches with
open PRs untouched.

## Housekeeping comment count (butler note)

Swept all 4 fork repos + 4 upstream repos via raw
`/repos/<r>/issues/comments?since=2026-10-15` (and per-issue comment JSON):
**0** biondogs-authored housekeeping/FILE-run-86 comments exist anywhere.
Nothing to undo; count receipted as zero
(`sprint-sync/housekeeping-count.json`).

## Local clone re-provision (butler step c)

Old fork-oriented clones archived intact to
`/local/projects/mprov-maint/.archive-2026-10-23/` (NOT deleted). Archive
`mash` holds unique unpushed work preserved by this card: branches
`rescue/js29` (fe8c8f3), `rescue/js30` (f6a0374) + staged
`src/mash/app.py`/`tests/test_load_config.py` (fork #29/#30 fixes) — needs
its own card to land or retire. Fresh clones now at
`/local/projects/mprov-maint/<repo>` with origin=mprov-ng:
CC `6afb414`, JS `b07393d`, SCR `eb80617`, MASH `36b6a5e`.
`MPROV-MAINT-PINS.md` updated; `MPROV-MAINT-POLICY.md` amended with the
venue rule (verbatim operator wording included).

## Resume run 104 (2026-10-23T15:16–15:22Z, sw-pm) — final close-out

Context: attempt 2 (run 101) crashed on an owner-gateway disconnect ~3 min
in with outcome unknown; butler directive for the retry was reconcile-first,
not blind-replay.

1. **Reconciliation.** Token scopes re-verified live (`gh auth status`:
   `project` now present — operator `gh auth refresh` confirmed). Full
   `gh project item-list 9 --owner mprov-ng` snapshot (120 items at start):
   **0 of our 27 were present — run 101 landed zero project writes before
   dying.** Fork-side check: all 27 gated fork issues still existed.
   Nothing partial to dedupe.
2. **Project 9 adds.** Todo option verified first via `field-list`
   (Status = `PVTSSF_lADOBiDZ0c4BoTUYzhm0DR4`, option `Todo` = `f75ad846`).
   27/27 `item-add` rc=0 (`project9-adds.log`); read-back: 27/27 present
   with Status=Todo, project total 120 → 147 (`project9-additions.json`,
   `project9-after.tsv`).
3. **Gated fork deletions.** Pair list built from
   `relay-receipts.json` FILED entries; matched the butler ratification list
   exactly (CC #44–47,#54; JS #35–45; SCR #22–29; MASH #31–#33). Per pair:
   twin re-verified OPEN via REST immediately before delete; delete rc=0;
   post-check HTTP 410 “This issue was deleted”. 27/27 (`fork-deletions.log`,
   pairs in `delete-pairs.tsv`). Two guard passes executed zero writes first
   (gh CLI quirks: `issue view -q` needs `--json` in this build; REST
   `.state` is lowercase) — fail-safe skips, no unintended mutations; third
   pass ran the real loop. Fork wave-2 total now 36/36 deleted (9 attempt-1 +
   27 run-104).
4. **Scope guards held:** no re-filing, 9 skips untouched, Oct-15 wave
   untouched, no code, no PRs. Zero writes beyond the 27 project adds + 27
   gated deletions + this receipts commit.

Note (cross-card): the archived-clone `rescue/js29`/`rescue/js30` work above
has since landed as mprov-ng/mash PRs #21/#22 (t_e5c9b3a3, commit 2b2fc1c) —
that "needs its own card" line is historical.

Receipt file hashes (sha256): project9-adds.log
8bfecbd0ce0f79ad163e02448c48ddd791b3daff7df5d64f3c01042cced6960e;
fork-deletions.log 84c4d65721ec66474ca5ba57d60695a2bc8aab85b8082677be9523cbc1157192;
project9-after.tsv 482d6efe84e0ea7f3ab5d56d6dcc82aa567bd552911d0f4481031e2e4f55cc00.
