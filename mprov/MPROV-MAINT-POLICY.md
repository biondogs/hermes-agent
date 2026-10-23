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
