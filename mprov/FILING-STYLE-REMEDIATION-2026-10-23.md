# FILING STYLE REMEDIATION PROPOSAL — open filings (2026-10-23)

Proposed by sw-pm (kanban t_302a8bf1) per the operator directive to make our
filings look like Jason's. **PROPOSAL ONLY — no live filing was edited.**
Awaiting operator GO per tier before any bulk rewrite. Style basis:
`FILING-STYLE-PROFILE.md`; rules: `MPROV-MAINT-POLICY.md` § Filing style.

Census of biondogs-authored OPEN filings on mprov-ng (2026-10-23):
112 issues (CC 27 / JS 30 / scripts 28 / mash 27) + 24 PRs
(CC 8 / JS 6 / scripts 3 / mash 7).

## Tier T-A — Rule-A trailer gap (22 open PRs) — recommend GO first

This is NOT a style change: Rule A requires `Assisted by JoeBot` in every PR
description, and 22 of our 24 open PR bodies are missing it (a standing
violation, discovered while profiling — Jason's own posts show a first-person
AI-disclosure trailer is house-normal, he ships "🤖 Generated with [Claude
Code]").

- mprov_control_center: #336 #337 #339 #340 #341 #342 #343 #344
- mprov_jobserver: #193 #194 #195 #196 #197 #198
- mprov_scripts: #49 #50 #51
- mash: #49 #50 #51 #52 #53
(mash #47/#48 already carry it — no edit.)

Edit: append trailer line only; body otherwise byte-preserved. Read-back
must still grep `^Fixes #N$` and re-verify the five publication gates.

## Tier T-B — re-style 24 open PR bodies

Every open PR body uses our bold label-block shape (`**Symptom.** …
**Fix.** … **Test(s).**`) which Jason never uses; `Fixes #N` position drifts
(line 1 on some, last line on others). Restyle to `filing-templates/pr-body.md`:
`Fixes #N.` first line, content-named `##` sections (or none for ≤2-file
fixes), test evidence in his counts+base-compare sentence, trailer last.

Full list: CC #336 #337 #339 #340 #341 #342 #343 #344 · JS #193 #194 #195
#196 #197 #198 · scripts #49 #50 #51 · mash #47 #48 #49 #50 #51 #52 #53.
(If T-A is GO'd separately, T-B edits for the 22 must include the trailer —
do T-A+T-B in ONE PATCH per PR to avoid double churn.)

Note: #336/#337/#344 already have maintainer comments in-thread — body edit
only, never thread history; his comments stay legible against a re-styled body.

## Tier T-C — re-style 106 open sprint issues

106 open issues carry the `[Sx]` title prefix + five-label body block.
Restyle = title rewritten to his declarative form (severity token removed;
labels on the issue object UNTOUCHED pending conflict-2 adjudication) + body
rewritten to `filing-templates/issue.md` shape (same five contents, prose +
`**Fix:**`, ≤150w cap). Counts: CC 22 (#309–#313, #315–#318, #320–#332) ·
JS 29 (#156–#170, #172–#187) · scripts 28 (#20–#28, #30–#48) ·
mash 27 (#18–#20, #23–#29, #30–#46, minus #21/#22 numbering gaps as filed).
Excluded: the 6 operator-era legacy issues (CC #19 #45 #123 #124 #128,
JS #96) — already human-register; closed history — never rewritten.

Priority order proposed: issues WITHOUT an open fix PR first (next thing
Jason reads when triaging), then issues with a fix PR in flight, PR bodies
last of all only if operator wants uniformity before he merges them.

## What is NOT proposed

- No label/milestone changes anywhere (conflict 2 open; board tooling reads
  `sN-*`/`review-found`).
- No edits to closed issues/PRs, thread comments (ours or his), commit
  messages, or project-9 rows.
- No loosening: every rewritten body keeps its evidence (file:line pinned to
  the sha it was verified at), severity content, and word cap.

## Method when GO'd (per t_b3632e27 precedent, recorded in policy)

1. Stage full rewrite set in the lane workspace (before/after per filing,
   word counts, gate-checkable diffs of the five contents).
2. Distiller text gate per batch (≤10 filings), verdict on the card.
3. Apply via REST `PATCH /repos/mprov-ng/<repo>/issues/<n>` and
   `/pulls/<n>` — NEVER `gh pr edit --body-file` (silent no-op on this
   host's gh 2.45.0, memory-logged). One PATCH per filing, title+body in
   one payload where both change.
4. Read-back per filing: byte-compare title and body vs staged text; re-grep
   `^Fixes #N$` on PRs; re-run the five-gate publication check for any PR
   touched. A read-back mismatch = stop the batch, report, don't retry-blind.
5. Receipt: per-batch table (filing, PATCH status, read-back sha256 of final
   body) in the management repo + card comment.

Estimated blast radius: 22 body appends (T-A) / 24 body rewrites (T-B) /
106 title+body rewrites (T-C); fully reversible (before-text staged).
