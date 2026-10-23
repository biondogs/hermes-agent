# MPROV-MAINT-REPORT-2026-10 — October-2026 maintenance wave closeout

Author: sw-pm (kanban t_c93e0cbb), 2026-10-23. Live GitHub re-verification
done 2026-10-23 ~14:55Z via `gh` (all PR states, review requests, commit
messages, and PR bodies re-read from GitHub at audit time — several states
changed after the upstream cards completed; those rows below are LIVE, not
handoff snapshots).

> **VENUE ADDENDUM (operator ruling 2026-10-23, post-dating the filing
> cards):** the biondogs forks are **disused** as a work venue. The wave-2
> fork issue receipts in §1 are **superseded-intermediate**: the numbers
> stand as the audited filing record, but the final venue is the **mprov-ng
> repos + org project 9 "2026 Issue Sprint"**, relayed by live card
> **t_2beff046**, after which all 36 wave-2 fork issues are **deleted**.
> At this report's readback t_2beff046 was still RUNNING (not folded in as
> receipts — referenced as the live relay; see §8). PR venue is unchanged,
> so the standing-rule audit (§2–§3) applies exactly as planned to the four
> mprov-ng docs PRs.

## Headline

- **36/36 approved issues filed** verbatim (gate `t_0aa9dbb1` PASS, packs at
  `67f5109`), 36/36 read back byte-identical; 0 skipped, 0 failures.
  *(Venue superseded mid-wave: fork receipts are intermediate; final venue
  mprov-ng + project 9 via live relay t_2beff046 — see addendum above.)*
- **4 docs PRs opened** (one per repo): **2 MERGED** (CC #307, JS #153 — both
  merged by `uberlinuxguy`), **2 OPEN awaiting `uberlinuxguy`** (SCR #19,
  mash #17; zero reviews submitted on either).
- **Standing-rule compliance: PASS 4/4 PRs, 6/6 commits.** Every commit
  message and PR body carries the exact line `Assisted by JoeBot` (Rule A,
  amended policy); every PR has `uberlinuxguy` requested as reviewer (Rule
  B). Zero artifacts of this wave carry the retired `Assisted by AI` line.
- **Confinement confirmed:** the attribution line appears on **nothing
  outside the four mprov repos** (local + GitHub-side scan, §6).
- **Zero old-line violations found anywhere**, including one FALSE-POSITIVE
  flag from the SCR lane that this audit disproved (§5).

## 1. Per-repo detail

Severity labels below are the filed issue labels (s1-blocker … s4-hygiene),
read from the filing receipts (`maint-2026-10-23/filing/RECEIPTS.md`,
`filing-receipts.json`, commit `8cb2030`).

### mprov_control_center
| | |
|---|---|
| Pin swept (upstream `mprov-ng/main`) | `d7c2094137b4b9b781d80760382445fcef6a6278` |
| Findings | 11 new → 11 filed |
| Severity (filed) | S1 ×1 (CC-051, amended S2→S1 at adjudication) · S3 ×8 · S4 ×2 |
| Issues filed *(superseded-intermediate fork venue)* | CC-041…CC-051 → fork **#44–#54** — https://github.com/biondogs/mprov_control_center/issues/44 … /54; final venue mprov-ng + project 9 via t_2beff046 |
| Dupes / not filed | 0 dupes; 0 not-filed; 4 upstream-twin pairs kept by design (CC-045/047/048/050 ↔ mprov-ng #268/#288/#290/#274) |
| Docs PR | https://github.com/mprov-ng/mprov_control_center/pull/307 — **MERGED** 2026-10-23T14:42:23Z by `uberlinuxguy`, merge commit `c44d5aa9` (head `9f3aad3`, 13 files +393 docs-only) |

### mprov_jobserver
| | |
|---|---|
| Pin swept (upstream `mprov-ng/main`) | `1fd4b123295a06831ac2b670c940bb5c17184eab` |
| Findings | 18 new → 14 filed, 4 not-filed (already fixed upstream, merge-verified: JSR2-04←PR#126, JSR2-05←PR#132, JSR2-06←PR#138, JSR2-10←PR#118), 1 folded (JSR2-19, S1 site → comment on fork #3, drafted, deferred to follow-up t_67a0ac84) |
| Severity (filed) | S2 ×3 (JSR2-01/02/03) · S3 ×7 (07/08/09/11/12/13/14) · S4 ×4 (15/16/17/18) |
| Issues filed *(superseded-intermediate fork venue)* | JSR2-01…18 → fork **#32–#45** — https://github.com/biondogs/mprov_jobserver/issues/32 … /45; final venue mprov-ng + project 9 via t_2beff046 |
| Dupes / not filed | 0 dupes; 4 upstream-fixed (above); 1 fold |
| Docs PR | https://github.com/mprov-ng/mprov_jobserver/pull/153 — **MERGED** 2026-10-23T14:22:16Z by `uberlinuxguy`, merge commit `c32dfa47` (head `5fbdffe`, 16 files +518/−1 docs-only) |

### mprov_scripts
| | |
|---|---|
| Pin swept (upstream `mprov-ng/master`) | `eb806171457b2c9494488e1fe44b01fa4247eb38` |
| Findings | 8 new → 8 filed |
| Severity (filed) | S2 ×1 (SCR-022) · S3 ×6 (023–028) · S4 ×1 (029) |
| Issues filed *(superseded-intermediate fork venue)* | SCR-022…029 → fork **#22–#29** — https://github.com/biondogs/mprov_scripts/issues/22 … /29; final venue mprov-ng + project 9 via t_2beff046 |
| Dupes / not filed | 0 dupes; 0 not-filed |
| Docs PR | https://github.com/mprov-ng/mprov_scripts/pull/19 — **OPEN**, awaiting `uberlinuxguy` (reviewRequests=[uberlinuxguy], zero reviews; head `5f48002`, 2 commits, 13 files +315/−1 docs-only) |

### mash
| | |
|---|---|
| Pin swept (upstream `mprov-ng/master`) | `36b6a5efc68fa620812b401a412a469bdb6dcf3f` |
| Findings | 3 new → 3 filed |
| Severity (filed) | S2 ×1 (MASH-101, S1-candidate held with recorded escalation condition) · S3 ×1 (102) · S4 ×1 (103) |
| Issues filed *(superseded-intermediate fork venue)* | MASH-101…103 → fork **#31–#33** — https://github.com/biondogs/mash/issues/31 … /33; final venue mprov-ng + project 9 via t_2beff046 |
| Dupes / not filed | 0 dupes; 0 not-filed (biondogs/mash#29 covers already-filed #13 only) |
| Docs PR | https://github.com/mprov-ng/mash/pull/17 — **OPEN**, awaiting `uberlinuxguy` (reviewRequests=[uberlinuxguy], zero reviews; head `4c4f5e3` per gate t_91714ba1, 8 files +313/−0 docs-only) |

### Wave totals
- Findings: **40 new → 36 filed** (S1 ×1, S2 ×5, S3 ×22, S4 ×8), 4
  upstream-fixed-not-filed, 1 folded.
- Prior-art dedup baseline: all **120** Oct-15 issues still OPEN; **0**
  duplicate filings; freshness pass at filing time: 0 skips
  (`filing/freshness-scan-summary.txt`).
- Existing-issue actions (pack §C/§D: CC 18 close + 4 narrow, JS #11/#21/#30
  + fold-comment, SCR #2/#5/#6, MASH 4 close + #13 pointer) are drafted in
  the packs and deferred to follow-up card **t_67a0ac84** — not executed by
  the issues-only filing card.

## 2. Rule A audit — `Assisted by JoeBot` (amended policy, 2026-10-23)

Audit target per butler comment 13:56 and `MPROV-MAINT-POLICY.md`
Amendments: exact line `Assisted by JoeBot` on every mprov commit message
and PR description; any artifact still carrying the retired `Assisted by
AI` = violation. Checked live at audit time by grepping the actual GitHub
bytes (`gh pr view --json commits/body`), not card claims.

| PR | commits | commit msg has exact line | PR body has exact line | old line present |
|---|---|---|---|---|
| mprov-ng/CC #307 | `9f3aad3` (1) | YES | YES | no |
| mprov-ng/JS #153 | `5fbdffe` (1) | YES | YES | no |
| mprov-ng/SCR #19 | `5ed577f`, `5f48002` (2) | YES ×2 | YES | no |
| mprov-ng/mash #17 | `4c4f5e3` (1) | YES | YES | no |

**Verdict: PASS — 6/6 commits, 4/4 PR bodies, zero old-line occurrences in
any artifact opened this wave.** (Note: PR titles are Rule-A-exempt per the
butler ruling on t_1d1f14ff.)

## 3. Rule B audit — reviewer `uberlinuxguy`

Live `reviewRequests` readback at audit time:

| PR | reviewer requested | outcome |
|---|---|---|
| CC #307 | YES | merged by `uberlinuxguy` himself (no formal review submitted) |
| JS #153 | YES | merged by `uberlinuxguy` himself (no formal review submitted) |
| SCR #19 | YES | pending — no review yet |
| mash #17 | YES | pending — no review yet |

**Verdict: PASS — 4/4 PRs requested `uberlinuxguy` at creation; zero
violations.**

## 4. Wiki PR states awaiting `uberlinuxguy`

Open docs PRs of this wave still awaiting his action (verified
`reviewDecision` empty, `reviews` empty on both):

1. **mprov-ng/mprov_scripts #19** — https://github.com/mprov-ng/mprov_scripts/pull/19
2. **mprov-ng/mash #17** — https://github.com/mprov-ng/mash/pull/17

Other open PRs on the orgs (not ours, no reviewer requested):
mprov-ng/CC #306 (netboot switch), mprov-ng/JS #154 (libgenders),
biondogs/CC #2/#3 (copilot), biondogs/mash #29/#30 (contributor
rahul05ranjan — #29 fixes already-filed fork #13; pointer comment queued in
t_67a0ac84).

## 5. Violations & corrections — none from this wave; one FALSE-POSITIVE disproved, edge case moot

- **No violations** of Rule A or Rule B on any artifact this card's wave
  opened (issues, commits, PRs).
- **False-positive corrected:** SCR lane (t_ea731719) flagged fork commit
  `aae84ee…` (biondogs/mprov_scripts master, Oct docs-lane) as carrying the
  retired `Assisted by AI`. Live audit: the commit's full message is exactly
  `docs: openwiki generation + documentation sweep (mprov CI/CD phase)` —
  **no attribution line of any kind**. A `grep 'Assisted by'` over the last
  100 commits of every fork master (all 4 repos) and every upstream head
  found the line only on our two merged wave commits (`9f3aad3`, `5fbdffe`)
  and the open wave branch heads. **Oct-15 fork-master retired-line edge
  case: MOOT-PENDING-FORK-DELETION, not amend-requiring** — per the
  operator venue ruling 2026-10-23 the biondogs forks are disused
  read-only legacy (wave-2 fork issues deleted; final fork disposition
  operator-decided after the two remaining docs PRs resolve), and the audit
  could not reproduce any retired line there anyway.
- **Related pin-file typo flagged (not patched here):**
  `MPROV-MAINT-PINS.md` records the scripts fork head as 39 hex chars
  (`aae84eec57c37205206f92ebe71b9a78d5bedb4`); real sha is
  `aae84eecc57c37205206f92ebe71b9a78d5bedb4` (API 422'd on the typo). Left
  for **t_2beff046** to correct as part of its mandated pins rewrite
  (clone re-provisioning rewrites that file — avoiding a concurrent edit).
- The Oct-15 docs-lane merge commits on all four fork masters predate Rule A
  (rule made law 2026-10-23) and carry **neither** line — no retroactive
  amendment needed.

## 6. Confinement — the line appears on NOTHING outside mprov repos

- **Local:** `git log --all --grep='Assisted by (JoeBot|AI)'` across all 27
  non-mprov repos under `/local/projects` (hermes-plugins, metatron, beerhammer,
  skipjack, vllm, …): all CLEAN. Management repo
  `/local/projects/software-co` commit messages: zero matches.
- **GitHub:** NousResearch/hermes-agent PR #143372 (opened by biondogs): 0
  occurrences in body and commits. `gh search` for both lines across
  `user:biondogs` and `org:mprov-ng` PRs/issues: no hits outside the four
  mprov repos' wave artifacts (repo-scoped body searches hit only our own 4
  docs PRs). All 36 filed issue bodies come from the Rule-C packs, which
  contain 0 occurrences (Rule A is N/A for issues anyway).
- **Expected definitional mentions (not attribution, not a violation):** the
  text of `MPROV-MAINT-POLICY.md` and `ADJUDICATION-2026-10-23.md` in this
  management repo quote the line to define the rule.

**Verdict: confinement CONFIRMED.**

## 7. Distiller gate ledger (per repo, for the record)

| Lane | Gate history |
|---|---|
| Filing packs | t_a5706d07 run 77 **FAIL** → amend `67f5109` → t_0aa9dbb1 **PASS** |
| CC docs PR | t_0487a4a8 **PASS** (bytes sha256 5989baaf…, sent unaltered) |
| JS docs PR | t_341d3a43 **PASS** (title/body verbatim; only GitHub trailing-newline delta) |
| SCR docs PR | t_1d1f14ff FAIL → t_3a48ac8e PASS → voluntary re-gate t_f8b38ac8 **PASS** on final tip |
| MASH docs PR | t_bedda913 FAIL (Agent-* trailers) → t_91714ba1 **PASS**; PR body sha256 6e7606cd byte-exact |
| Rule D note | The four docs PRs are operator-commissioned OpenWiki work (zero code); adjudicator gate flagged the literal "FILE ISSUES ONLY" tension — surfaced, treated as operator-authorized. |

## 8. Follow-ups owned elsewhere

- **t_2beff046 (live relay, RUNNING at this report's readback ~14:55Z)** —
  re-files wave-2 issues onto mprov-ng repos + org project 9 "2026 Issue
  Sprint" and deletes the 36 fork wave-2 issues after twin verification.
  Mid-run deviation notice (not yet final): live pass found SIX annotated
  CC twins (#268/#270/#273/#274/#288/#290, adding CC-046→#270, CC-049→#273
  to FILE's recorded four) plus three JS findings newly covered upstream
  (JSR2-01→#142, JSR2-02→#144, JSR2-03→#149) — working tally **27 filed
  upstream + 9 receipted skips** vs the butler's expected 32+4. Fold its
  completion receipts into the operator's sprint record when it lands; this
  report does not pre-endorse the in-flight tally.
- **t_67a0ac84** — pack §C/§D existing-issue actions + JSR2-19 fold-comment
  + MASH-013 pointer to biondogs/mash#29. NOTE: these actions target
  fork-side Oct-15 issues; venue scope should be re-checked against the
  disused-fork ruling (fork repos are read-only legacy; the mash#29 PR
  pointer is unaffected — PRs stay live).
- Awaiting `uberlinuxguy`: mprov-ng scripts #19, mash #17.
- Operator-side observation: both merged docs PRs were merged without a
  formal review submission (reviewer's prerogative; Rule B only requires the
  request).
