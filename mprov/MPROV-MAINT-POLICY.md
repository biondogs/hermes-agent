# MPROV-MAINT-POLICY — Standing rules for the mprov maintenance wave

Filed 2026-10-23 by sw-pm (kanban t_f46200db). Operator directive: we are
owners of the mprov stack; upstream maintainer is **uberlinuxguy**
(org: `mprov-ng`). These rules bind every card in this wave and any future
mprov work until the operator amends them.

## Amendments

- **2026-10-23 — CONTRIBUTOR ALLOWLIST added (operator ruling, kanban
  t_508b58a2).** The only contributors to the main `mprov-ng` repos are
  `biondogs` and Jason Williams on either of his two accounts
  (`uberlinuxguy`, `jhujasonw`); everyone else is external. See the
  **Contributor allowlist** section below for logins, evidence, the
  consequence clause, and the new pre-publication identity check.

- **2026-10-23 — Filing venue changed: mprov-ng repos + project 9 (operator
  ruling, kanban t_2beff046).** ISSUE filings target the live
  **`mprov-ng/<repo>`** repositories — never the biondogs forks — and every
  filed issue is added to the org project **“2026 Issue Sprint”**
  (https://github.com/orgs/mprov-ng/projects/9) in its **Todo** column at
  filing time. PR venue is **unchanged**: fork topic branch → PR against
  `mprov-ng/<repo>`, `uberlinuxguy` requested as reviewer (Rule B), standing
  line `Assisted by JoeBot` (Rule A). Verbatim operator venue wording:
  *“biondogs forks are disused as work venue for issues, clones, and all
  maintenance going forward; PR head branches remain until the four open
  docs PRs resolve, after final fork disposition is operator-decided.”*
  Local maintenance clones are re-provisioned with
  `origin = https://github.com/mprov-ng/<repo>` (see `MPROV-MAINT-PINS.md`).
  Until the operator decides final fork disposition the four fork repos are
  **read-only legacy**: do not delete them, do not file there, do not touch
  the Oct-15 wave fork issues, and do not touch any fork branch carrying an
  open PR (deleting a fork kills its open PR).
- **2026-10-23 — PR TRACKING added (operator ruling, kanban t_3dde7503).**
  Every sprint fix PR must carry a plain exact `Fixes #N` line, its issue's
  project-9 item must sit **In Progress** while the PR is open, and the
  publication read-back must verify all four gates (PR open, reviewer,
  Fixes ref, issue-item column). PRs are tracked **through the issue**: do
  not create PR-level project-9 items. See the **PR tracking** section
  below for the full contract and the no-automation finding behind it.
  *(The no-PR-items clause was superseded same-day by the PR-ROWS
  amendment below; the Fixes-line and issue-item clauses stand.)*

- **2026-10-23 — PR-ROWS amendment: our fix PRs GET project-9 PR rows
  (operator ruling "match Jason's pattern", kanban t_5a84e78b).** This
  **supersedes** the "do not create PR-level project-9 items" clause of the
  entry above. At publication, the lane adds the PR itself as a **type
  PullRequest** project-9 item set to **In Progress**, and moves it to
  **Done** when the PR merges or closes resolved; the publication read-back
  grows from four gates to **five** (PR open + reviewer + Fixes ref +
  issue-item column + PR-row present). Column rationale: the operator's
  standing instruction is PR → In Progress; the maintainer's own open PR
  rows sit inconsistently (Todo / Testing Pending), so **In Progress** is
  our consistent, honest state. See the **PR tracking** section for the
  full contract.

- **2026-10-23 — Rule A standing line changed (operator amendment, kanban
  t_9e433953).** The required standing line on mprov commits/PRs is now
  exactly `Assisted by JoeBot`. The previous required line
  `Assisted by AI` is **retired**: an artifact carrying the old line is a
  **violation to be amended** (edit the commit message / PR description to
  carry the new line), not a valid variant co-existing with it. Everything
  else is unchanged: Rule A's bidirectional scope (ALL mprov repos only;
  NEVER any other repo), Rule B (`uberlinuxguy` reviewer), and Rule C
  (distillation standard).

- **2026-10-23 — FILING STYLE added (operator directive, kanban
  t_302a8bf1).** Our filings adopt the maintainer's look for STRUCTURE and
  FORMAT; content standards are untouched (operator carve-out verbatim:
  *"we don't need to loosen our standards"*). See the **Filing style**
  section below; normative templates in `filing-templates/`; the empirical
  profile and side-by-side delta in `FILING-STYLE-PROFILE.md`; the
  open-filing restyle PROPOSAL (awaiting operator GO — nothing live edited
  yet) in `FILING-STYLE-REMEDIATION-2026-10-23.md`.

## Contributor allowlist (2026-10-23, operator ruling)

The **only** contributors accepted on the main `mprov-ng` repos are:

| GitHub login | Principal | Flag | Evidence (read-only queries, 2026-10-23) |
|---|---|---|---|
| `biondogs` | Sepp / Joseph Biondo (operator) | **CONFIRMED** | Our filing identity; commits + merged PRs in all four repos (e.g. CC `c44d5aa`, mash `36ef120`). |
| `uberlinuxguy` | Jason Williams | **CONFIRMED** | GitHub profile `name: "Jason Williams"`, email `uberlinuxguy@gmail.com`; 113 merged PRs across the four repos since 2026-09-01; sole org-side committer on main. |
| `jhujasonw` | Jason Williams (second account) | **CONFIRMED** | GitHub profile `name: "Jason Williams"`; mprov-ng org member; commit-trail email `jasonw@jhu.edu` on ~30 authored commits incl. recent Sep-2026 merges; 19 merged CC PRs + 1 jobserver PR. |

Both Jason Williams accounts are CONFIRMED, not INFERRED: identical real
name on both GitHub profiles, both active as mprov-ng org members with
merged contribution history. If the operator ever disputes this mapping,
amend this section — do not silently reinterpret it.

### Consequence clause

PRs and issues authored by accounts **outside** this allowlist are not
accepted: they are closed unmerged without fix-phase work. Prior
application: `mprov-ng/mash#21` and `#22` closed unmerged 2026-10-23 per
the no-external-submissions directive (kanban t_395c5db2).

### Filing-lane identity check (added to the standing pre-publication checks)

Before ANY future commit, PR, or issue on an `mprov-ng` repo, the lane
MUST verify:

1. `gh api user --jq .login` returns an allowlisted login, AND
2. the commit author identity (name + email that will be published) maps
   to an allowlisted account.

If either check fails, do not publish — block the card instead.

### Reviewer rule — unchanged

Rule B stands as written: `uberlinuxguy` is requested as reviewer on
every mprov PR.

## Scope — what "mprov repos" means

Exactly these four products (fork side and upstream side both in scope).
**Venue note (2026-10-23 amendment below):** `mprov-ng` is the filing and
clone venue; the fork column is retained only because open-PR head branches
still live there.

| Product | Fork (legacy, read-only) | Upstream (filing venue) |
|---|---|---|
| control center | `biondogs/mprov_control_center` | `mprov-ng/mprov_control_center` |
| jobserver | `biondogs/mprov_jobserver` | `mprov-ng/mprov_jobserver` |
| scripts | `biondogs/mprov_scripts` | `mprov-ng/mprov_scripts` |
| mash CLI | `biondogs/mash` | `mprov-ng/mash` |

## Rule A — "Assisted by JoeBot" attribution line

EVERY commit message AND every PR description touching an mprov repo (fork
or upstream side) MUST include the exact line:

```
Assisted by JoeBot
```

Scope is bidirectional and absolute:
- **mprov repos ONLY.** The line is mandatory on these four repos.
- **NEVER on any other repo, anywhere.** Do not add the line to commits or
  PRs in hermes-agent, software-co, metatron, or any other repository under
  any circumstance. Copying it "for consistency" is a policy violation.

## Rule B — Reviewer

Every PR opened against an mprov repo (fork-side or `mprov-ng` side)
requests **`uberlinuxguy`** as reviewer at PR creation time.

## PR tracking (2026-10-23, operator ruling — kanban t_3dde7503; PR-row step + five-gate read-back added same day per "match Jason's pattern", kanban t_5a84e78b)

A fix PR is tracked on **two** board surfaces: through the issue it fixes
(issue-item column) **and** by its own PR row. Per the operator's
2026-10-23 ruling "match Jason's pattern", every sprint fix PR gets a
**type PullRequest** project-9 item at publication (the maintainer
hand-curates PR rows on this board; our lanes now do the same — the
earlier same-day "do not create PR-level project-9 items" clause is
superseded).

Every sprint fix PR must satisfy, **at publication time**:

1. **Exact Fixes line.** The PR body carries a plain, machine-checkable
   line `Fixes #N` on its own line (N = the `mprov-ng` issue being fixed).
   Plain text only — no bold/decoration wrapping the keyword. Check:
   `gh pr view <PR> --repo mprov-ng/<repo> --json body -q .body |
   grep -qm1 -E '^Fixes #[0-9]+$'`.
   If a body edit is needed after creation, use a REST
   `PATCH /repos/<owner>/<repo>/pulls/<n>` — `gh pr edit --body-file`
   silently no-ops on the gh version installed on this host (2.45.0).
2. **Issue-item column.** The fixed issue's project-9 item is moved to
   **In Progress** the moment the PR is published (column model: filed →
   **Todo**; fix PR open → **In Progress**; merged or closed-with-issue-
   resolved → **Done**; no open PR → back to **Todo**). The lane publishing
   the PR performs this move itself — see the no-automation finding below;
   never assume the board moves on its own. When the merge is confirmed,
   the lane moves the item to **Done** and re-reads it — do not rely on
   issue auto-close to move the board item (no board automation has ever
   been observed firing unattended).
3. **PR row.** The lane adds the PR itself as a **type PullRequest**
   project-9 item set to **In Progress** at publication (GraphQL
   `addProjectV2ItemById` + `updateProjectV2ItemFieldValue` — or
   `gh project item-add` + `item-edit`). When the PR merges, or closes
   with its issue resolved, the lane moves the row to **Done** and
   re-reads it. The row is the PR's own status surface, independent of
   the issue-item column in gate 2. **Read-back pitfall (t_5a84e78b
   receipt):** a freshly added row can be absent from every list view
   (`gh project item-list` AND the raw GraphQL `items` connection) while
   `node(id:)` already resolves it — a GitHub-side index lag. Poll by
   `node(id:)`; if still invisible after ~5 minutes, delete and re-add
   the row (proven remedy; `addProjectV2ItemById` is content-idempotent,
   so re-adding an already-indexed PR cannot create a duplicate).
4. **Publication read-back (all five gates, by live re-fetch after the PR
   is opened):** (i) PR state is open, (ii) `uberlinuxguy` reviewer is
   attached, (iii) the live body still carries the exact `Fixes #N` line,
   (iv) the issue's project-9 item reads **In Progress** (e.g.
   `gh project item-list 9 --owner mprov-ng --limit 500 --format json`,
   match the issue URL and re-read its Status), and (v) the PR's own
   project-9 row (type PullRequest) is present and reads **In Progress**.
   A publication is not complete until all five read green.

**No-automation finding (2026-10-23 audit, t_3dde7503):** project #9 has no
automation that puts PRs on the board. All 23 PR-type items on it were
created by hand by `uberlinuxguy` on 2026-10-23 (GraphQL `creator` is his
human account; several created seconds before he clicked merge, e.g.
mprov_jobserver#192 at 20:38:04Z, merged 20:38:16Z), while our 25 open
sprint PRs with valid `Fixes` refs produced zero board items on their own.
GitHub's native merge automation (close-the-issue via Fixes) does fire —
mprov_jobserver#171 auto-closed 2s after merge — but no board movement has
ever been observed without the maintainer at the keyboard. Therefore the
fix-lane publication checklist itself owns gates 2, 3 and 5 (move it
yourself, read it back); this section exists because that contract step was
missing when mprov_jobserver#192 opened untracked. **State update
(t_5a84e78b, same day):** the 23 hand-curated PR rows counted above were
subsequently deleted from the board by the intervening "no PR items" sync
sweep (the board briefly carried zero PR rows, including the maintainer's
own JS#191/JS#192 Done rows); the 25-row PR backfill for our open sprint
fix PRs re-established PR-type tracking — restoring the maintainer's own
deleted rows, if wanted, is an operator/butler decision, not lane work.

## Rule C — Issue-filing distillation standard

A human must understand the issue AND the potential solution with minimum
reading. Hard requirements for every new issue body:

- Target **≤150 words**.
- Fixed structure, in this order: **symptom / evidence (`file:line`) /
  root cause / proposed fix / severity**.
- No filler: no preamble, no restating the title, no boilerplate sections
  beyond the five above.

**2026-10-23 amendment (kanban t_302a8bf1):** the five Rule-C items are now
a CONTENT checklist every body must satisfy, not visible labels. Their
EXPRESSING FORM is governed by the **Filing style** section below — Rule C
wording survives for content; where this section and Rule C read as
requiring the old visible-label layout, this section wins on form only.

## Filing style (2026-10-23, operator directive — kanban t_302a8bf1)

Operator directive: *"Feedback from Jason is that he doesn't like the
formatting of many of our issue and PR comments … make our filings look more
like his."* Carve-out: *"we don't need to loosen our standards."* Norm =
`uberlinuxguy`'s current (Oct-2026) filing pattern, measured across all four
mprov-ng repos (`FILING-STYLE-PROFILE.md`). This section governs STRUCTURE
and FORMAT; it never licenses dropping content.

### Invariants (style never touches these)

Rule A trailer (`Assisted by JoeBot`, exact, last line of PR bodies and in
every commit); Rule B reviewer; contributor allowlist + pre-publication
identity check; PR tracking with the five-gate publication read-back; the
`Fixes #N` machine check (`^Fixes #N$`, plain, own line); distiller
pre-publication text gate + leak-scan law; evidence quality (defect-site
`file:line` at the verified sha; test counts + base comparison); ≤150-word
cap on our filing bodies (a CAP, not a target — prefer his brevity: his
issue median is 41 words); lanes never merge.

### The style rules (FS)

- **FS1 — issue titles.** Declarative failure sentences for defects ("X
  never reboots: Y unmounts /proc before Z"), imperative for enhancement
  asks ("Let job servers claim a job atomically"). ≤14 words. NO `[Sx]` or
  any tag prefix, no trailing period. The `fact: mechanism` colon form is
  encouraged where it reads naturally.
- **FS2 — issue bodies.** Prose paragraphs only: no `## ` headings, and
  NEVER the visible five-label block (`Symptom:` / `Evidence:` / `Root
  cause:` / `Proposed fix:` / `Severity:` as labels). The five contents must
  still all be present and findable. At most two bold mini-labels from his
  vocabulary — `**Fix:**` (his workhorse, use it), `**Likely cause:**`,
  `**To decide:**`, `**Coordinate with:**`, `**Check first:**`,
  `**Needs verification:**`. House addition kept by carve-out: a final
  `Severity: S<N> — <one-clause impact>` line (he weaves impact into prose;
  our severity must stay explicit — flagged conflict #3 below). Close with
  his provenance/footer line ("Found while … for #N. Related: #N."); a real
  "Migrated from …" provenance may live in that sentence.
- **FS3 — evidence.** Defect-site evidence as a commit-pinned permalink
  (`https://github.com/mprov-ng/<repo>/blob/<sha>/<path>#L<n>`) preferred,
  backticked `file:line` at minimum; verbatim error/diff output in a fenced
  block whenever the claim is about observed output. Never paraphrase an
  error, never invent a receipt.
- **FS4 — references.** Same-repo `#N`; cross-repo `mprov-ng/<repo>#N`;
  coordination phrasing from his set: `Related:`, `Blocked by … That has to
  reach … before this merges.`, `Depends on #N. Merge that first.`,
  `Unblocks …`. No internal ids/vocabulary anywhere (leak-scan unchanged).
- **FS5 — PR bodies.** `Fixes #N` as a plain standalone line at the TOP
  (position adopted from his `Closes #N.` first line; our line carries no
  period because the gate greps `^Fixes #N$` — the one visible deviation,
  deliberate). Then narrative prose (what was true before / what changes /
  why safe). Sections are content-named (`## Change`, `## Testing`,
  `## Merge notes`, `## API clients`, `## The bug` / `## The fix`) or absent
  entirely for small fixes — never `## Summary`/`## Description` filler,
  never bold-label blocks. Test evidence in his sentence shape: "Full
  suite: N passed, N xfailed, in the image built from this branch. Against
  main's code, N of the new tests fail." A before/after table is his idiom
  for behavior matrices. Last line `Assisted by JoeBot`.
- **FS6 — thread comments.** One paragraph, stance/verdict first, first
  person, mirror the counterpart's length; receipts inline (backticked
  sha/file/test names, `#N` refs, one or two numbers) instead of bulleted
  receipt lists; bullets only for ≥3 true list items; asks worded as
  preferences ("I would prefer … because …"). Same evidence law as filings:
  tested verdicts only. Verify your own comment landed via API read-back.
- **FS7 — labels/milestones.** Issue-object labels stay the filing lane's
  (`bug|enhancement` + `review-found` + `sN-*`) — tooling metadata under
  operator adjudication (conflict #2); severity appears NOWHERE ELSE but
  the body's Severity line. Milestones: none (matches his current practice).
- **FS8 — corpus boundaries.** Closed issues/PRs, all historical comments
  (ours and his), commits, and project-9 rows are never restyled. Restyle
  applies to NEW filings immediately and to OPEN filings only per the
  operator-GO'd tiers in `FILING-STYLE-REMEDIATION-2026-10-23.md`.

### Distiller text-gate ruleset for mprov (amends the t_03720d69 conventions)

Provenance note: card t_03720d69 no longer resolves in any board DB
(pruned); its conventions are restated from gate precedent and extended
here. Every future mprov text-gate card MUST carry as inputs: this section,
`filing-templates/` (all three), and the draft under review. The gate checks,
in order:

1. Leak-scan + sanitizer (unchanged): no `t_` ids, board/gate vocabulary,
   agent/persona tells, internal hostnames, cross-board detail.
2. Rule A: exact `Assisted by JoeBot` line present and LAST in PR bodies
   (and in commits); Rule B reviewer requested.
3. `Fixes #N` present as first-line plain standalone match `^Fixes #N$`.
4. Rule C contents: all five (symptom / evidence / root cause / proposed
   fix / severity) semantically present — as prose under FS2, NOT as labels.
5. Style (FS rules): no `[Sx]`/tag title prefix; no visible five-label
   block; no generic `##` headings; section names content-shaped or absent;
   ≤2 bold mini-labels, allowed vocabulary only; body ≤150 words.
6. Evidence: defect-site `file:line`/permalink present; error output quoted
   verbatim where the claim is observational; test evidence has counts AND
   a base comparison.
7. Tone/voice: single human first-person voice, stance-first,
   length-mirroring (FS6 for comments).
8. Verdict mechanics unchanged: PASS, or REJECT with numbered, verifiable
   findings; one edit + re-gate, second failure stops the lane.

### Flagged conflicts (kept on record — operator adjudicates; nothing silently dropped)

1. **Rule C's mandated visible structure vs his label-free prose.** Kept
   both: contents mandatory (Rule C), form his (FS2). Gate enforces presence
   of contents, not labels.
2. **Severity taxonomy (`[Sx]` + `sN-*` + `review-found` labels) vs his
   label-free recent issues (0 labels, 76 filings).** Title token dropped
   (pure look). Object labels KEPT by default — board/worklist tooling joins
   on them; if the operator rules they're also off-style, removal is one
   batch of label PATCHes.
3. **Explicit `Severity: S<N>` body line vs his prose-impact weaving.**
   Kept as a house addition under the carve-out (severity must be
   checkable); placed as his footer-style sentence so the look stays his.
4. **≤150-word cap vs his PR median 157 words.** Cap kept per carve-out;
   our PRs will read marginally terser than his own — deliberate.
5. Profile-side sync of this ruleset into the `distiller` profile's SOUL
   checklist is profile meta-work: routed to a `kanban-board-architect`
   card (PM lacks that authority); until then, gate cards carry this
   section as an input per the ruleset above — the distiller reads repo
   etiquette files FRESH by design, so the policy file is canonical.


## Rule D — Review-phase scope (this wave)

**FILE ISSUES ONLY.** No code commits, no PRs to mprov repos this wave.
Any card that needs a code change is out of scope until the operator
releases the fix phase.

## Prior-art dedup (context for Rule C filings)

The 2026-10-15 wave filed 120 issues to the forks (index:
`MPROV-PRODUCT-REPORT.md`, authoritative register: `FILED-ISSUES.md`).
State snapshot 2026-10-23: **120/120 still OPEN** (CC #4–#43: 40 open; JS
#1–#31: 31 open; scripts #1–#21: 21 open; mash #1–#28: 28 open). Per-issue
snapshot: `maint-2026-10-23/issue-state-2026-10-23.json`. The sweep MUST
dedupe against these before filing anything new. Note upstream `mprov-ng`
has active commits since our fork pins (see `MPROV-MAINT-PINS.md`) — check
upstream history for already-applied fixes before filing.
