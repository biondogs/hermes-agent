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
| mprov_control_center | 5 (#309–#313) | 6 | 0 | 6 | 5 |
| mprov_jobserver | 11 (#156–#166) | 3 | 0 | 3 | 11 |
| mprov_scripts | 8 (#20–#27) | 0 | 0 | 0 | 8 |
| mash | 3 (#18–#20) | 0 | 0 | 0 | 3 |
| **Total** | **27** | **9** | **0 — CAPABILITY WALL** | **9** | **27** |

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

## Project 9 — CAPABILITY FAILURE (blocks completion)

`gh project item-add 9 --owner mprov-ng --url <first-filed-url>` →
`error: your authentication token is missing required scopes [read:project]`
(token biondogs scopes: gist, read:org, repo, workflow; no GH_TOKEN in env;
`gh auth refresh` is browser-interactive → not possible headless).
`gh project field-list 9` fails identically, so the Todo option-name
verification never ran. **0 of 27 filed issues are in project 9.** Fix:
`gh auth refresh -s read:project,project`, then relay-resume adds all 27 +
completes the gated deletions below. Receipt:
`sprint-sync/project-denial-receipt.json`.

## Fork wave-2 cleanup

9 twin-covered fork issues DELETED after covering twins verified OPEN in the
same pass (`sprint-sync/twin-cleanup-receipt.json`): biondogs CC #48–#53,
JS #32–#34. 27 relayed-issue fork copies NOT yet deleted — per butler ruling
deletion is gated on the mprov-ng twin being live AND added to project 9;
project writes are wall-blocked. Pending deletions: biondogs CC #44–#47,
#54; JS #35–#45; SCR #22–#29; MASH #31–#33. Oct-15 wave fork issues:
untouched. Fork repos untouched. Fork branches with open PRs untouched.

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
