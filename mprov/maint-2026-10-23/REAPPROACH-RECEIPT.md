# REAPPROACH-RECEIPT — mprov-ng/mash #47 / #48 (re-approach of closed #21 / #22)

Date: 2026-10-23 (EDT) · Card: kanban software-co t_b3632e27 · Prior card: t_7531eb52 (archived mid-run under dedup-stop rule) · Per earlier receipt: t_395c5db2 (#21/#22 closed unmerged per no-external-submissions policy)

## Handoff

t_7531eb52 (mash re-approach lane) was archived mid-run under the dedup-stop rule, leaving its
two own-authorship PRs open and unwatched. This card closes that loop: verification below, this
receipt as the durable marker, and the project-9 coverage note so batch 2 never re-files
duplicates.

Both PRs are the re-approach of the closed external submissions (#21 → #47, #22 → #48), now
filed under our own allowlisted account **biondogs** with the house trailer discipline.

## PR verification (verified live 2026-10-23 via gh api; READ-ONLY — no merges, no PR changes)

| Check | mprov-ng/mash#47 | mprov-ng/mash#48 |
|---|---|---|
| Purpose | config-shapes fix (covers issue mash#33) | foreach-hash fix (covers issue mash#34) |
| state | open ✅ | open ✅ |
| head sha (full) | `9ca335462d269f40ce0e0cf4bf8f0503d692c717` | `8745a4822017282970965d560f0d938b9deaf110` |
| branch | fix/accept-mapping-configs | fix/foreach-split-comments |
| author | biondogs ✅ | biondogs ✅ |
| commits | single, msg ends exact line `Assisted by JoeBot` ✅ | single, msg ends exact line `Assisted by JoeBot` ✅ |
| hook trailers (Agent-\*/Co-Authored-By) in commits | zero ✅ | zero ✅ |
| reviewer requested | uberlinuxguy ✅ | uberlinuxguy ✅ |
| reviews so far | none (unreviewed) | none (unreviewed) |
| CI (checks) | pytest 3.9 / 3.11 / 3.13 all `success`; no required status contexts (combined `pending` = no contexts) ✅ | pytest 3.9 / 3.11 / 3.13 all `success`; same ✅ |
| body contains `Fixes #33` / `Fixes #34` | **FAIL — no Fixes/closes keyword or issue link anywhere in body** ❌ | **FAIL — no Fixes/closes keyword or issue link anywhere in body** ❌ |
| duplicate open PRs on repo | none — #47/#48 are the only open PRs on mprov-ng/mash | none |

### Open defect (FAIL above)

Neither PR body carries a `Fixes #33` / `Fixes #34` closing link. Consequence: merging either PR
will **not** auto-close its issue. This card's boundary is READ/verify + management-repo write
only ("no GitHub changes on the PRs themselves"), so the fix is NOT applied here. Remediation
(one line each, requires operator go-ahead or an explicitly PR-write-scoped card):

```
gh pr edit 47 --repo mprov-ng/mash --body-file <body + trailing "Fixes #33">
gh pr edit 48 --repo mprov-ng/mash --body-file <body + trailing "Fixes #34">
```

Alternatively, whoever merges simply closes mash#33 / mash#34 manually with a reference. Until
then, the coverage note below is the dedup authority.

## Project-9 coverage note (batch-2 dedup authority)

- mprov-ng/mash#33 `[S3] Common config file shapes crash connect with raw tracebacks` —
  **open**, project-9 Status **Todo** (verified via GraphQL), **covered-by-PR: mprov-ng/mash#47**
  (head `9ca335462d`).
- mprov-ng/mash#34 `[S3] Foreach silently drops list items containing a hash character` —
  **open**, project-9 Status **Todo** (verified via GraphQL), **covered-by-PR: mprov-ng/mash#48**
  (head `8745a48220`).

Both issues STAY open in project-9 Todo. Batch 2 (and any future fan-out) must **not** file
duplicates or spawn fix cards for #33/#34: the open-PR-overlap join plus this receipt exclude
them. Status advances only when the covering PR merges (then close the issue manually if the
Fixes link is still absent).

## Boundary compliance

No merges, no PR body/reviewer/comment changes, no issue mutations performed by this card.
Management-repo write: this file only.
