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

### Open defect (FAIL above) — RESOLVED same day under operator ruling; see AMENDMENT 1 below

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
them. Status advances only when the covering PR merges. (Per AMENDMENT 1 below the `Fixes`
closing links are now in both bodies — GitHub `closingIssuesReferences` verified resolving
#47→#33 and #48→#34 — so merge auto-closes both issues; no manual close needed.)

## Boundary compliance

No merges, no PR body/reviewer/comment changes, no issue mutations performed by this card.
Management-repo write: this file only. *(Superseded in part by AMENDMENT 1 — PR-body writes
performed under explicit operator ruling; everything else still holds.)*

## AMENDMENT 1 (2026-10-23 ~19:54 UTC) — FAIL resolved under operator ruling (Option A)

**Authorization.** Operator ruling posted to card t_b3632e27 (comment by `swco-butler`,
2026-10-23 19:52 UTC): *"Option A — authorized to edit the PR bodies. Add the exact line
`Fixes #33` to mprov-ng/mash#47's body and `Fixes #34` to mash#48's body (keep everything else
byte-identical, including the 'Assisted by JoeBot' line and reviewer tag). Read-back verify
both bodies after the edit."* Task unblocked and re-dispatched on that ruling.

**Execution detail (mechanics).** `gh pr edit --body-file` FAILED WITHOUT EFFECT (exit 1,
aborted during its own read-back on the deprecated projects-classic `projectCards` GraphQL
field) — confirmed by live read-back showing bodies unchanged. Remediation used instead:
`gh api -X PATCH repos/mprov-ng/mash/pulls/{47,48} --input <jq -Rs '{body:.}' patch>` with the
original body bytes extracted via `gh pr view --json body` + `jq -r` and exactly one line
appended (`Fixes #33` / `Fixes #34`). API `updated_at`: 2026-10-23T19:53:56Z (#47),
19:53:57Z (#48).

**Post-edit verification (gh pr view + GraphQL, 2026-10-23 ~19:55 UTC):**

| Check | mash#47 | mash#48 |
|---|---|---|
| diff orig→live body | single added line `Fixes #33`; rest byte-identical ✅ | single added line `Fixes #34`; rest byte-identical ✅ |
| `Assisted by JoeBot` line intact | ✅ | ✅ |
| state / head sha unchanged | open / `9ca335462d269f40ce0e0cf4bf8f0503d692c717` ✅ | open / `8745a4822017282970965d560f0d938b9deaf110` ✅ |
| reviewer requested unchanged | uberlinuxguy ✅ | uberlinuxguy ✅ |
| CI after edit | pytest 3.9 / 3.11 / 3.13 all SUCCESS ✅ | pytest 3.9 / 3.11 / 3.13 all SUCCESS ✅ |
| GraphQL `closingIssuesReferences` | resolves → #33 `[S3] Common config file shapes…` (OPEN) ✅ | resolves → #34 `[S3] Foreach silently drops list items…` (OPEN) ✅ |

**Net state:** the original matrix's only FAIL is closed. Merging #47 auto-closes mash#33;
merging #48 auto-closes mash#34. No merges were performed by this card; reviewer request,
heads, titles, comments and both issues remain untouched apart from the two authorized
single-line body appends. Project-9 dedup authority (coverage note above) is unchanged until
merge.
