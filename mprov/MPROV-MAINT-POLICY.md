# MPROV-MAINT-POLICY — Standing rules for the mprov maintenance wave

Filed 2026-10-23 by sw-pm (kanban t_f46200db). Operator directive: we are
owners of the mprov stack; upstream maintainer is **uberlinuxguy**
(org: `mprov-ng`). These rules bind every card in this wave and any future
mprov work until the operator amends them.

## Amendments

- **2026-10-23 — Rule A standing line changed (operator amendment, kanban
  t_9e433953).** The required standing line on mprov commits/PRs is now
  exactly `Assisted by JoeBot`. The previous required line
  `Assisted by AI` is **retired**: an artifact carrying the old line is a
  **violation to be amended** (edit the commit message / PR description to
  carry the new line), not a valid variant co-existing with it. Everything
  else is unchanged: Rule A's bidirectional scope (ALL mprov repos only;
  NEVER any other repo), Rule B (`uberlinuxguy` reviewer), and Rule C
  (distillation standard).

## Scope — what "mprov repos" means

Exactly these four products (fork side and upstream side both in scope):

| Product | Fork (our working remote) | Upstream |
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
