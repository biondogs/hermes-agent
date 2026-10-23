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
