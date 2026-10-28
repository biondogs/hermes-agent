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

- **2026-10-24 — SEVERITY MODEL added: `[SEC]` tier; S tiers reserved for
  crisis/break only (operator standing rule, kanban t_5e7399b2).** Operator
  rule verbatim: *"You need to tag all filings that are security
  enhancements as security in the repo and recategorize them, s1 should be
  reserved for crisis or break/bug fix security should be considered future
  nice to have."* See the **Severity model** section below; applied
  retroactively across the four repos (30 items labeled, 8 `[SEC]`
  retitled, 0 verification failures) — receipts on kanban card t_5e7399b2.

- **2026-10-24 — OPERATOR COMMENTS ruled: biondogs-login notes are FULL
  maintainer engagement (operator ruling, kanban t_038a3543).** Operator
  ruling verbatim: *"The lanes should respond to my comments as biondogs
  exactly as it would to any other maintainer. If I post a comment you
  should address it even if that makes it appear I am replying to myself."*
  New rule **COM-OPS** in the **Comms & engagement** section below:
  operator notes posted under the `biondogs` login (Giuseppe's in-thread
  review notes, e.g. SCR#50 *"if this is accurate how is working in the
  production system"*, SCR#51 backup-intent question) bind the owning/
  watching lane to respond IN-THREAD under `biondogs` with the standard
  response process — identical register to answering any other reviewer;
  the appearance of self-reply is accepted house policy. Body-editing
  skip rules TRIGGER on operator notes (see COM-OPS). This codifies the
  FILING-WATCH duty wording already live on card t_b2d3c1c0 (comments
  706/710 — 710 supersedes 706's surface-and-wait clause); this section
  and that wording share one intent.

- **2026-10-24 — FILING IMPACT section added: every new filing gains an
  `Impact:` block (operator directive, kanban t_b0c9922b).** Operator
  directive verbatim: *"Adjust the mprov repo posting guidance, all filings
  should include an additional section describing the impact of the issue or
  fix, things like what it touches and how it differs from the way it works
  in production. Aswell as what files are touched"* New rule **FS9** below;
  distiller gate check **5b**; mirrored in `filing-templates/issue.md` and
  `filing-templates/pr-body.md`. Body word cap raised 150 → **175** to make
  room — receipt: a tight 2–4-line Impact block measures 30–31 words, and
  live open biondogs PR bodies sit at median 131 / p90 147 words (issue
  p90 121), so 150 could not absorb the section without cutting Rule-C
  content; +25 is the minimal fit and the cap stays a cap. Forward-looking
  only: open filings are **not** retrofitted — impact text needs per-filing
  code analysis, not mechanical restyle (operator scope ruling on-card).
  *(This forward-looking-only clause was superseded **same-day** by the
  FILING IMPACT RETROFIT directive entry below; the per-filing code-analysis
  requirement stands and is satisfied by drafted-then-gated analysis, not by
  skipping open filings.)*

- **2026-10-24 — FILING IMPACT RETROFIT directive: FS9 scope extended to
  open filings (operator directive, kanban t_6a9550f5, butler intake).**
  Operator directive verbatim: *"Operator directive 2026-10-24: retrofit ALL
  existing open biondogs filings with the new Impact section"* — relayed via
  butler intake and recorded in the opening line of card t_6a9550f5's body
  ("RETROFIT PROGRAM — lane mprov_control_center. …", on-card receipt).
  This **supersedes** the "forward-looking only / open filings are not
  retrofitted" scope clause of the entry above and of FS9 below. Program
  shape mirrors the operator-GO'd style-retrofit precedent (t_b19bbdd2):
  per-filing code analysis → drafts (live body byte-identical + FS9 Impact
  block at template position, nothing else) → distiller text gate → REST
  PATCH → GET read-back byte-compare → receipts. Engagement law is honored,
  not overridden: maintainer- or operator-note-engaged filings are
  skipped-with-receipt (FS8/COM-OPS), non-biondogs-authored items are
  untouched, and operator-era legacy issues stay excluded per the t_b19bbdd2
  precedent — so the retrofitted population is open **unengaged biondogs**
  filings. Running across all four lanes (mprov_control_center /
  mprov_jobserver / mprov_scripts / mash); draft packs under
  `filing-drafts/impact-retrofit-2026-10-24/`, gate cards to distiller
  per lane.

- **2026-10-25 — DEPLOYMENT THREAT MODEL added: security filings must state
  harm under the controlled-deployment premise (maintainer ruling on
  mcc#318, kanban t_2450bd52).** Maintainer direction verbatim (mcc#318
  comment 6393012139): *"This system is in a tightly controlled setting
  where an admin would have cabled a system in a deliberate way to use the
  port match function in NADS.  Systems not cabled deliberately, would fall
  into the auto detection section of the UI and require manual intervention
  by an admin.  Unless I am missing something, the code functions as
  intended."* and *"I would suggest you restructure your security model
  around this and reassess all your open security issues and PRs."* All 30
  open security-classified filings reassessed under it (verdict table +
  receipts under `maint-2026-10-25/sec-remodel/`); mcc#318 closed
  working-as-intended on the ruling; PR cc#336 stays open as the opt-in
  hardening the maintainer shaped. Distiller gate check **5c**;
  `filing-templates/` mirrored. See the **Deployment threat model** section
  below.

- **2026-10-28 — JOEBOT SIG COMMENTS: signature law extended to ALL
  public output including comments (operator ruling, kanban t_f208c170).**
  Operator ruling verbatim (butler channel): *\"It seems you've been
  missing your signatures for the mprov repos, you should be signing off
  on all of your comment's, prs, issues, filings with your 'Assisted by
  JoeBot' signature.\"* **Scope expansion:** the Rule-A standing line
  `Assisted by JoeBot` (exact standalone line) now covers **ALL** public
  JoeBot output on `mprov-ng` repos: commits, PR title/body per existing
  rules, **issue bodies**, AND **thread comments** — comments were
  previously ungated and are now gated. Every queued public comment MUST
  carry the exact standalone line `Assisted by JoeBot` as its own
  trailing paragraph (blank line before it, nothing else on the line);
  the distiller gate (check 2) REJECTs any comment lacking it. Policy
  Rule A, the distiller gate, and `filing-templates/maintainer-reply.md`
  are amended accordingly; a 30-day retro sweep of `biondogs`-authored
  comments was performed on-card (receipt: counts + amended ids). Out of
  scope: `metatron-rewrite` (mprov-only rule), upstream `hermes-agent`
  (different venue convention).

- **2026-10-28 — JOEBOT VOICE: public replies must be plain-language and
  self-contained (operator relay, kanban t_c9cbdae6).** Operator relay
  verbatim: *"joebot might need to be less terse and more verbose...
  'Corrected the description: null projection from the levels a real payload
  carries no Ansible keys on, plus the whole-array select — not the
  escaping.' What?"* New rule **FS10** below; distiller gate check **7a**
  (cold-reader test); `filing-templates/maintainer-reply.md` mirrored. Scope:
  JoeBot's public output on `mprov-ng` repos (comments, issue bodies, PR
  replies) ONLY — internal board traffic unaffected. See the **JoeBot voice**
  section below.

- **2026-10-28 — PR342-PATTERN: canonical five-part PR-body skeleton
  (operator relay of Jason's ruling, kanban t_7a324945).** Operator relay
  verbatim: *"Jason has asked that you make sure all of your initial PR
  filings from now on are structured similarly to MPCC #342."* Exemplar
  verified live this run: [`mprov-ng/mprov_control_center#342`](https://github.com/mprov-ng/mprov_control_center/pull/342)
  (open at `781ac6f`-era pin; body 165 words). New rule **FS11** below;
  distiller gate check **5d**; `filing-templates/pr-body.md` replaced with
  the canonical skeleton. All initial PR filings from this date forward MUST
  match the five-part skeleton in order — Fixes line, problem paragraph,
  The fix, Impact, Testing, trailer — no badges, checklists, or meta
  sections. See the **PR body — canonical skeleton (FS11)** section below.

- **2026-10-28 — NO-SELF-GATE law: gate cards carry a mandatory independent
  assignee (operator directive, kanban t_84b852b9; incident t_fecde306).**
  An author lane created its own "DISTILLER GATE" card, assigned it to itself,
  PASSed its own bytes in ~90 s, and relaxed the check set mid-gate. New law
  **R6 (NO-SELF-GATE)** in software-co
  `docs/gate-wait-pattern-2026-10-28.md`: a gate card is assigned ONLY to an
  independent gate profile (`distiller` for text gates, `sw-reviewer` for code
  review) — never the creating lane or the bytes' author; a gate may not weaken
  its own check set; a self-issued PASS is void (stop the apply leg, annotate,
  re-gate independently). `filing-templates/gate-card.md` added as the
  canonical gate-card skeleton with the mandatory `Assignee: distiller` line;
  all future mprov text-gate cards MUST be filed from it.

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

EVERY commit message, every PR/issue description, AND every thread
comment touching an mprov repo (fork or upstream side) MUST include the
exact standalone line:

```
Assisted by JoeBot
```

For commits and PR/issue bodies: the line is the exact last line (or
standalone final paragraph) per existing rules. For **comments**: the
line is a standalone trailing paragraph — blank line before it, nothing
else on the line, no decoration/bold/prefix. The distiller gate
(check 2) REJECTs any queued public comment lacking it.

Scope is bidirectional and absolute:
- **mprov repos ONLY.** The line is mandatory on these four repos —
  commits, PR bodies, issue bodies, AND comments.
- **NEVER on any other repo, anywhere.** Do not add the line to commits,
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

- Target **≤175 words** (150 before 2026-10-24; the raise exists solely to
  make room for the FS9 Impact section — see Filing style).
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
`file:line` at the verified sha; test counts + base comparison); ≤175-word
cap on our filing bodies (raised from 150 on 2026-10-24 solely to make room
for the FS9 Impact section — a CAP, not a target; prefer his brevity: his
issue median is 41 words); lanes never merge.

### The style rules (FS)

- **FS1 — issue titles.** Declarative failure sentences for defects ("X
  never reboots: Y unmounts /proc before Z"), imperative for enhancement
  asks ("Let job servers claim a job atomically"). ≤14 words. NO `[Sx]` or
  any tag prefix, no trailing period — sole exception: the `[SEC]` prefix on
  security-enhancement filings per the Severity model section (2026-10-24).
  The `fact: mechanism` colon form is
  encouraged where it reads naturally.
- **FS2 — issue bodies.** Prose paragraphs only: no `## ` headings, and
  NEVER the visible five-label block (`Symptom:` / `Evidence:` / `Root
  cause:` / `Proposed fix:` / `Severity:` as labels). The five contents must
  still all be present and findable. At most two bold mini-labels from his
  vocabulary — `**Fix:**` (his workhorse, use it), `**Likely cause:**`,
  `**To decide:**`, `**Coordinate with:**`, `**Check first:**`,
  `**Needs verification:**`. House addition kept by carve-out: a final
  `Severity: S<N> — <one-clause impact>` line (he weaves impact into prose;
  our severity must stay explicit — flagged conflict #3 below), with the
  FS9 `Impact:` block sitting directly above it (house addition, 2026-10-24).
  Close with his provenance/footer line ("Found while … for #N. Related: #N."); a real
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
- **FS5 — PR bodies (superseded in form by FS11; invariants here still
  bind).** `Fixes #N` as a plain standalone line at the TOP (position
  adopted from his `Closes #N.` first line; our line carries no period
  because the gate greps `^Fixes #N$` — the one visible deviation,
  deliberate). The canonical skeleton is now **FS11** (PR342-PATTERN); this
  rule's invariants — plain Fixes line, ≤175-word cap, Impact mandatory,
  deployment-threat-model framing, `Assisted by JoeBot` last line, no
  badges/checklists/meta sections — remain in force and are restated there
  in skeleton order. Where this section and FS11 disagree on section
  names or order, FS11 wins.
- **FS6 — thread comments.** One paragraph, stance/verdict first, first
  person, mirror the counterpart's length; receipts inline (backticked
  sha/file/test names, `#N` refs, one or two numbers) instead of bulleted
  receipt lists; bullets only for ≥3 true list items; asks worded as
  preferences ("I would prefer … because …"). Same evidence law as filings:
  tested verdicts only. Verify your own comment landed via API read-back.
- **FS7 — labels/milestones.** Issue-object labels stay the filing lane's
  (`bug|enhancement` + `review-found` + `sN-*`) — tooling metadata under
  operator adjudication (conflict #2); severity appears NOWHERE ELSE but
  the body's Severity line. Exception (2026-10-24): the `security` label is
  mandatory on every security-classified filing per the Severity model
  section. Milestones: none (matches his current practice).
- **FS8 — corpus boundaries.** Closed issues/PRs, all historical comments
  (ours and his), commits, and project-9 rows are never restyled. Restyle
  applies to NEW filings immediately and to OPEN filings only per the
  operator-GO'd tiers in `FILING-STYLE-REMEDIATION-2026-10-23.md`, and
  never on a filing with live maintainer or operator-note engagement —
  operator notes under the `biondogs` login count as engagement per
  COM-OPS (Comms & engagement section, 2026-10-24).
- **FS9 — Impact section (operator directive 2026-10-24, kanban
  t_b0c9922b).** Every new biondogs filing — issues AND PRs — carries ONE
  short Impact block covering exactly three things in 2–4 lines/bullets
  max: (1) what the issue/fix touches, subsystem/feature in plain words;
  (2) current production behavior vs expected (PRs: behavior before vs
  after the fix); (3) files touched as repo-relative paths — for issues,
  suspected files or best-known location, marked `suspected`. Form follows
  the medium: issues use a plain `Impact:` label block directly above the
  `Severity:` line (house addition under the same carve-out as the Severity
  line — not one of FS2's two bold mini-labels, no `##` heading); PRs use
  a content-named `## Impact` section (FS5 idiom). No other headings and no
  template bloat: an Impact block missing any of the three things, or
  naming no file, fails the gate (check 5b). Applies to new filings AND —
  per the operator's 2026-10-24 retrofit directive same-day, superseding the
  original new-filings-only scope ruling — to open unengaged biondogs
  filings via the impact-retrofit program (dated entry in Amendments above;
  the original ruling stands on record there, never silently dropped).

- **FS10 — JoeBot voice: public replies must be plain-language and
  self-contained (operator relay 2026-10-28, kanban t_c9cbdae6).** Every
  PUBLIC JoeBot message on `mprov-ng` repos — issue bodies, PR replies,
  thread comments — must be understandable on first read by someone who has
  NOT followed the internal thread. This is a CLARITY rule, not a length
  target: being terse is never an excuse to be unintelligible. Required
  shape (all three, in order):
  1. **Context clause:** name the artifact or behavior being discussed
     (e.g. \"This PR changes how the cron template renders labels\" / \"In
     my previous comment I said the fix was X\").
  2. **Finding/claim in complete sentences:** subject-verb-object, no
     telegraphic noun-chain fragments. Each technical claim gets its own
     sentence with the actor and mechanism spelled out.
  3. **Consequence:** what this means for the reader — what changes, what
     they should do, or what the fix addresses.
  Minimum **3 full sentences** (a sentence = subject + finite verb +
  terminal punctuation). Corrections have an extra requirement: restate
  BOTH the original (wrong) claim and the corrected finding in full — never
  \"corrected above\" or a fragment that assumes the reader remembers the
  prior wording. No unexpanded shorthand: every abbreviation, internal
  term, or file/field nickname is defined or linked on first use. Scope is
  PUBLIC `mprov-ng` output ONLY; internal board traffic, kanban comments,
  and worker handoffs are unaffected and may stay terse. FS6's
  \"mirror the counterpart's length\" still applies, but it is bounded
  below by this rule: a one-line question still gets at least 3 sentences,
  because a cold reader cannot reconstruct context from a two-word reply.

  BAD (real incident that prompted this rule): \"Corrected the description:
  null projection from the levels a real payload carries no Ansible keys on,
  plus the whole-array select — not the escaping.\" — a single noun-chain
  fragment with no context clause, no stated prior claim, and no
  consequence.

  GOOD (same content, passing): \"Correction to my previous comment: I
  originally said the failure came from shell escaping of the payload. That
  was wrong. The real causes are (1) the projection returns null because the
  levels our real payload carries contain no Ansible keys at all, and (2) the
  whole-array select grabs entries it shouldn't. Escaping is not involved;
  the fix addresses (1) and (2).\" — context (what is being corrected),
  both claims stated, consequence (what the fix covers), ≥3 sentences,
  plain English.

- **FS11 — PR body — canonical five-part skeleton (CC#342 exemplar,
  operator ruling 2026-10-28, kanban t_7a324945).** Every initial PR filing
  MUST match [`mprov-ng/mprov_control_center#342`](https://github.com/mprov-ng/mprov_control_center/pull/342) (verified live
  2026-10-28: `Fixes #316`, 165 words, open) in order, with no badges,
  checklists, or meta sections. Skeleton:

  1. **Line 1:** `Fixes #NNN` standalone — plain `^Fixes #[0-9]+$`, own line.
  2. **Problem paragraph:** what's broken, reproduction against a named sha,
     why current code does it. Complete sentences, no boilerplate.
  3. **`## The fix`** — mechanism of change + consumer-compatibility
     analysis (who reads the changed surface, why they're unaffected /
     affected; e.g. `setupBMC.py`'s `?system=ID&detail` query, jobserver
     `dns.py` reads).
  4. **`## Impact`** — FS9 block: `Touches X. Before: ... After: ... Files:
     <repo-relative paths>.` Covers touched subsystem, prod before/after,
     and at least one repo-relative path.
  5. **`## Testing`** — named tests with RED-on-base / GREEN-on-fix
     comparison + full-suite count (e.g. `test_bulk_detail_omits_password`
     RED on `781ac6f`, GREEN on fix; full suite 164 OK).
  6. **Last line:** `Assisted by JoeBot` standalone (Rule A).

  Target **150–175 words** total (exemplar 165). FS5's former flexible
  section names (`## Change`, `## Merge notes`, etc.) and optional-section
  rule are retired for this skeleton — the three `##` headings above are
  required, in that order, with exactly those names. Normative body text is
  in `filing-templates/pr-body.md`.

### Distiller text-gate ruleset for mprov (amends the t_03720d69 conventions)

Provenance note: card t_03720d69 no longer resolves in any board DB
(pruned); its conventions are restated from gate precedent and extended
here. Every future mprov text-gate card MUST carry as inputs: this section,
`filing-templates/` (all four files, gate filed from the `gate-card.md`
skeleton), and the draft under review. Gate cards are assigned ONLY to
`distiller` — NO-SELF-GATE law R6, software-co
`docs/gate-wait-pattern-2026-10-28.md`: no self-gating, no mid-gate weakening
of this check set, self-issued PASSes are void. The gate checks,
in order:

1. Leak-scan + sanitizer (unchanged): no `t_` ids, board/gate vocabulary,
   agent/persona tells, internal hostnames, cross-board detail.
2. Rule A: exact `Assisted by JoeBot` line present and LAST in PR
   bodies (and in commits); **thread comments MUST also carry the exact
   standalone line `Assisted by JoeBot` as their trailing paragraph
   (blank line before it, nothing else on that line) — REJECT any
   queued public comment lacking it**; Rule B reviewer requested.
3. `Fixes #N` present as first-line plain standalone match `^Fixes #N$`.
4. Rule C contents: all five (symptom / evidence / root cause / proposed
   fix / severity) semantically present — as prose under FS2, NOT as labels.
5. Style (FS rules): no `[Sx]`/tag title prefix (sole exception `[SEC]` per
   the Severity model); no visible five-label
   block; no generic `##` headings; section names content-shaped or absent;
   ≤2 bold mini-labels, allowed vocabulary only; body ≤175 words.
5a. Severity classification at the gate (operator rule 2026-10-24): a
   security ENHANCEMENT (hardening/scoping with no active breakage) must
   carry `[SEC]` title prefix + `security` label and NO S tier — REJECT an
   `s1-blocker` (or `[S1]`) on such a filing unless the body evidences an
   ongoing crisis or breakage of default deployments; crisis-tier security
   keeps its S tier and must also carry the `security` label.
5b. Impact section (FS9, operator directive 2026-10-24): present — issues
   carry an `Impact:` block above the Severity line, PRs a `## Impact`
   section — AND it states what the issue/fix touches, the production-
   behavior delta (current vs expected; PRs: before vs after), and
   at least one repo-relative file path (issues may mark paths `suspected`).
   REJECT a filing with no Impact section, one that names no file, or one
   missing the prod/expected contrast; also REJECT Impact blocks over
   4 lines/bullets (bloat guard).
5c. Deployment threat model (maintainer ruling 2026-10-25): a security-framed
   draft must state its harm under the controlled-deployment premise (see
   the Deployment threat model section) — a concrete defect, leak, or
   misbehavior that survives with NO untrusted network actor. REJECT framing
   whose only harm is an attacker on the deployment L2 / untrusted network
   ("an unauthenticated network caller can …", "a host on the same L2 …"):
   under the premise that is working-as-intended, not a defect.
5d. PR-body skeleton (FS11, CC#342 exemplar, operator ruling 2026-10-28):
   every PR body MUST match the five-part skeleton in order — (1) `Fixes #N`
   standalone first line (`^Fixes #[0-9]+$`), (2) problem paragraph (what's
   broken + reproduction sha + why current code does it, complete sentences),
   (3) `## The fix` with mechanism + consumer-compatibility analysis,
   (4) `## Impact` FS9 block (`Touches … Before: … After: … Files: …` with
   at least one repo-relative path), (5) `## Testing` with named RED-on-base
   / GREEN-on-fix tests + full-suite count, (6) last line `Assisted by
   JoeBot` standalone — REJECT a PR body missing any heading, with headings
   out of order or misnamed, with no Fixes line first, no problem paragraph,
   no compatibility note, no Impact files, no RED/GREEN + suite count, or
   with badges / checklists / meta sections. Target 150–175 words; exemplar
   is [`mprov-ng/mprov_control_center#342`](https://github.com/mprov-ng/mprov_control_center/pull/342) (165 words).
6. Evidence: defect-site `file:line`/permalink present; error output quoted
   verbatim where the claim is observational; test evidence has counts AND
   a base comparison.
7. Tone/voice: single human first-person voice, stance-first,
   length-mirroring (FS6 for comments).
7a. Cold-reader test for public replies (FS10, operator relay 2026-10-28):
   every PUBLIC JoeBot comment/issue/PR reply on `mprov-ng` must pass the
   cold-reader test — no unexpanded shorthand; ≥3 full sentences
   (subject-verb-object with terminal punctuation); corrections restate
   BOTH the original (wrong) claim and the corrected finding in full;
   required shape: context clause → finding in complete sentences →
   consequence. Scope is `mprov-ng` public output ONLY — internal board
   traffic is exempt. REJECT a public reply that is a telegraphic
   noun-chain fragment, has fewer than 3 sentences, or corrects without
   restating both claims.
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
   our PRs will read marginally terser than his own — deliberate. *(Raised
   to **175** 2026-10-24 solely for the FS9 Impact section — receipt in the
   Amendments entry; relative to his Impact-free median 157 the cap still
   binds, so the terser-reading outcome stands.)*
5. Profile-side sync of this ruleset into the `distiller` profile's SOUL
   checklist is profile meta-work: routed to a `kanban-board-architect`
   card (PM lacks that authority); until then, gate cards carry this
   section as an input per the ruleset above — the distiller reads repo
   etiquette files FRESH by design, so the policy file is canonical.


## Severity model — S tiers reserved; the `[SEC]` security tier (2026-10-24, operator standing rule, kanban t_5e7399b2)

Operator rule verbatim: *"You need to tag all filings that are security
enhancements as security in the repo and recategorize them, s1 should be
reserved for crisis or break/bug fix security should be considered future
nice to have."*

- **S1–S4 are for crisis or break/bug fixes only** — things broken today.
  An item keeps or receives `s1-blocker` ONLY if it is an ongoing crisis or
  breaks default deployments (e.g. credential exposure actively live,
  unauthenticated destructive endpoint open by default, root code execution
  on the shipped install path).
- **Security enhancement** — hardening, permission scoping, authn/authz
  improvement, secret-handling hygiene, injection/traversal prevention with
  no active breakage — files as the nice-to-have tier: title prefix
  `[SEC]`, repo label `security`, NO S tier. The `[SEC]` prefix is the one
  tag-title exception to FS1.
- **Crisis-tier security keeps its S tier** (it must not demote below the
  break it represents) and ALSO gets the `security` label — no `[SEC]`
  prefix. `[SEC]` means nice-to-have; crisis items stay in the S taxonomy.
- **Classification tie-break:** unsure whether crisis? keep the S tier and
  still add the `security` label. Never retitle an item a maintainer has
  already commented on — label only, and receipt the skipped retitle
  ("commented on" includes operator notes under the `biondogs` login per
  COM-OPS, Comms & engagement section).
- **Label:** `security` exists in all four repos. `mprov_control_center` /
  `mprov_jobserver` carried it since before this wave (FF0000, no
  description); `mprov_scripts` / `mash` got it 2026-10-24 (color 5319e7,
  description "Security enhancement / hardening").
- **Retitled items keep their legacy `sN-*` labels** untouched (removal was
  not in the operator directive's scope); the `[SEC]` title prefix is the
  authoritative tier for them. New `[SEC]` filings get no `sN-*` label.
- Project 9: recategorized items stay in their current column — the tier
  change is not a state transition.

## Deployment threat model — controlled setting (maintainer ruling 2026-10-25, kanban t_2450bd52)

Maintainer direction verbatim (uberlinuxguy, mcc#318 comment 6393012139,
2026-10-25T03:35:02Z): *"Your context for implementation is flawed.  This
system is in a tightly controlled setting where an admin would have cabled a
system in a deliberate way to use the port match function in NADS.  Systems
not cabled deliberately, would fall into the auto detection section of the UI
and require manual intervention by an admin.  Unless I am missing something,
the code functions as intended.  I would suggest you restructure your
security model around this and reassess all your open security issues and
PRs."* This is the standing threat model for every mprov security-framed
filing:

- **The premise.** mPCC deployments are tightly controlled: admins cable
  systems deliberately (port-match enrollment), and unexpected systems land
  in auto-detection until an admin assigns them. There is NO assumed
  untrusted actor on the deployment L2/network — the network and the
  machines reachable on it are operated by the same admin running mPCC.
  House precedent (mcc#318, closed working-as-intended on this ruling):
  maintainer platform-design intent wins over stricter-security defaults;
  comply, do not counter-propose.
- **Harms that still stand on their own** (reportable per the Severity
  model): secret material leaking into API output or world-readable /
  volatile files; silent data-integrity or association destruction;
  break-on-misconfig and break-on-malformed-input; destructive tools aimed
  by unvalidated operator input; executing fetched bytes without
  verification; shipped default credentials; local exposure on shared
  multi-user nodes (Slurm compute nodes are multi-user by design).
- **Filing rule (gate check 5c).** Every security-framed filing MUST state
  its harm under THIS premise — what breaks, leaks, or misbehaves assuming
  no untrusted network actor. Framing whose only harm is
  "an (unauthenticated) network attacker can …" is GATE-REJECTED going
  forward. If the harm vanishes entirely under the premise, the item closes
  as working-as-intended with a courteous comment citing the ruling; if the
  harm survives but was security-escalated, it is restruck per the Severity
  model — retitle away the attacker framing (unless maintainer-engaged:
  never retitle a quoted item, receipt the skip), drop the security
  classification, restate severity under the premise.
- **2026-10-25 reassessment** (kanban t_2450bd52): all 30 open
  security-classified filings across the four repos verdicted
  KEEP-UNCHANGED / RESTRIKE / CLOSE-INTENDED against this premise; verdict
  table and receipts under `maint-2026-10-25/sec-remodel/` and on the kanban
  card. ADR-0001 v2 territory (identity layer: cc#331, cc PRs #341/#344, the
  accepted cc#315 exposure) was cross-checked for consistency and left
  untouched — the ADR already encodes his rulings.

## Comms & engagement (2026-10-24, operator ruling — kanban t_038a3543)

### COM-OPS — operator comments are FULL maintainer engagement

Operator ruling verbatim (2026-10-24): *"The lanes should respond to my
comments as biondogs exactly as it would to any other maintainer. If I
post a comment you should address it even if that makes it appear I am
replying to myself."*

The operator posts review notes and questions directly on `mprov-ng`
filings **under the `biondogs` login** — the same identity our lanes
publish under — so these notes were historically treated as "ours" and
ignored. That is over:

- **An operator note is engagement, not noise.** The owning/watching lane
  MUST address it IN-THREAD under `biondogs` with the standard response
  process — distiller-gated text (FS6 register), ≤150 words,
  evidence-backed, publication verified by API read-back — identical to
  answering any comment from Jason. Surface-and-wait is not compliant
  (superseded per FILING-WATCH card t_b2d3c1c0 comment 710).
- **Self-reply appearance is accepted house policy.** A thread showing
  `biondogs` answering `biondogs` is the intended look. No hedging,
  disclaimers, or meta-commentary about the note's authorship may appear
  in public text; the reply reads exactly like an answer to any reviewer.
- **Fix-lane exception.** If the answer requires fix-lane code analysis
  beyond existing verified evidence, the analysis is filed via the owning
  lane's card (pattern: t_0e040611) — but the thread still gets addressed
  (acknowledge + state what is being verified). Never go silent while the
  analysis runs.
- **Receipts.** Every operator-note reply (comment id) is receipted on
  FILING-WATCH (t_b2d3c1c0).

**Operator-note signature** (scan rule, same wording intent as FILING-WATCH
comments 706/710): a `biondogs`-authored comment that is addressed to
`@biondogs`/`@uberlinuxguy`, uses reviewer-style phrasing, or asks a direct
question on a biondogs filing — EXCLUDING known worker-receipt shapes
(distiller verdicts, read-back receipts, FILING-WATCH's own posts).

**Engagement semantics (body-editing programs).** The
"maintainer-engaged" skip rules used by retrofits, restyles, and reclass
programs (FS8; the Severity model's never-retitle-a-commented-on clause)
TRIGGER on operator notes: while a note is live on a filing, the body
stays hands-off. The same note simultaneously triggers the duty-to-respond
above. Expected order: **answer first; re-consider body edits only after
the thread settles.**

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
