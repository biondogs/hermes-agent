# Adjudication Report — MPROV-M maintenance wave (2026-10-23)

Adjudicator: sw-architect, kanban t_43e4e008. Gate deliverable for the MPROV-M wave.
Inputs: the four sweep registers + REVIEW-NOTES + dispositions from t_2eae052c (CC),
t_a43d97bb (JS), t_412f1a54 (SCR), t_1ee1e0e4 (MASH). Governing docs:
MPROV-MAINT-POLICY.md (Rule C distillation, Rule D issues-only, prior-art dedup,
"Assisted by JoeBot" Rule A — applies to commits/PRs, not issue filings),
REVIEW-CHARTER.md §2 severity scale. Precedent: Oct-15 adjudication (findings/ADJUDICATION.md).

Operator requirement honored (butler comment 2026-10-23): every verdict was checked
against OPEN PRs on both mprov-ng upstream and the biondogs forks — not just merged
commits and the Oct-15 issue index. This report is the semantic pass; the filing card
re-checks live state (freshness pass).

## 1. Verdict summary

| register | NEW findings | APPROVED (file fresh) | not filed (fixed upstream at head) | folded | severity amendments |
|---|---|---|---|---|---|
| control_center (CC-041..051) | 11 | 11 | 0 | 0 | CC-051 S2→S1 |
| jobserver (JSR2-01..18 + 19) | 18 | 14 | 4 (JSR2-04/05/06/10) | JSR2-19 → comment on fork #3 | 0 |
| scripts (SCR-022..029) | 8 | 8 | 0 | 0 | 0 (SCR-022 S2 held) |
| mash (MASH-101..103) | 3 | 3 | 0 | 0 | 0 (MASH-101 S2 held) |
| **total** | **40** | **36** | **4** | **1** | **1** |

Out-of-band verdicts on the ALREADY-FILED populations (guidance now baked into the
packs; not new filings): CC 18 closeable (fixed upstream), 4 narrowed, 21 still-present
no-op; JS #11 upstream-fixed comment, #21/#30 narrowed, #22 confirmed NOT closed by
92e619e; SCR #2 closeable, #5/#6 narrowed; MASH 4 closeable, 1 COVERED-BY-OPEN-PR
(#13), 24 still-live. Zero REJECTED-with-reason among NEW findings; zero regressions;
zero re-severitisations confirmed across all four sweeps.

## 2. Distillation pass (metric: human-review-cost)

Every approved NEW finding was re-rendered into the Rule C fixed structure —
symptom / evidence (file:line) / root cause / proposed fix / severity — target ≤150
words, no fillers, in the per-repo APPROVED-FILING-*.md packs. The JS register bodies
were already in this shape (validated) and carried over condensed; the CC/SCR/MASH
registers used the older wave-1 schema (evidence/repro/fix_idea/blast_radius/
regression_test) and were distilled by the adjudicator — repro mechanisms and executed
probes were compressed into symptom+evidence, regression_test content dropped
(harnesses don't exist yet; fix cards budget for them per Oct-15 open-question 2),
blast_radius folded into symptom/severity where it changed the reader's decision.
Mechanical word-count + structure check run over all 36 filed bodies: PASS (see §5).
Anaogue merges considered and rejected (with reasons) are in §6; the surviving
cross-referencing choices keep the maintainer's read at "one short read per issue".

## 3. Severity calibration decisions (to REVIEW-CHARTER §2)

1. **CC-051 S2 → S1 (the only amendment).** OSDistro API serializer returns the distro
   rootpw in cleartext to any holder of the shared API key. It is the open remainder
   of fork issue #5, which was filed S1 in the Oct-15 wave for the identical mechanism
   class (API credential exposure with a concrete path); the BMC-password half of #5
   was fixed upstream (ed147bf) and this half was not. Charter S1 test satisfied:
   concrete scenario (jobservers/nodes every API-key holder reads the fleet's install
   root password → fleet login) — nameable, coded path verified at source at d7c2094
   by the adjudicator. Held at S1, consistent with precedent rather than contesting it.
2. **MASH-101 held at S2 despite S1 candidacy.** SSTI with execution-verified payload
   reach. Held S2 because the precondition is deliberately running an
   attacker-supplied script file — the same trust boundary as a hostile .bashrc, and
   the .mash format's sharing story is the aggravating-but-not-sufficient factor.
   Recorded escalation condition (filed in the issue body): becomes S1 the day mash
   scripts are fetched or executed remotely. This mirrors the SCR-009 conditional
   recorded in the Oct-15 adjudication (open question 3) — established calibration
   pattern, no owner judgment required.
3. **SCR-022 held at S2 (reviewer's call confirmed).** Local-read credential exposure
   was calibrated S3 twice in Oct-15 (SCR-009 argv, SCR-014 staging file); SCR-022
   escalates one rung for materially larger scope (entire DB dump: all BMC passwords
   + media, persisted after the run, lost on reboot). S1 rejected: same
   local-read-only trust boundary as the S3 precedents.
4. **Boundary calls held at as-registered** (rationale recorded for the reviewer):
   CC-044 S3 not S2 — needs an edit inside a job's execution window (concurrency
   window precedent: JS #18 was filed S3 for the same class); CC-047 S3 not S2 —
   version-conditional credential corruption is an adverse condition, not normal
   operation; CC-045/CC-048 S4 — no shipped consumer breaks today / no data risk;
   JSR2-12 S3 not S2 — narrow documented extension point, garbage output only when
   consumed; JSR2-09 S3 not S1 — job params are mPCC-sourced; attacking through them
   presumes a compromised control plane.

## 4. Open-PR coverage matrix (operator requirement)

`gh pr list --state open` run 2026-10-23 on BOTH remotes of all four repos. Only
non-docs PRs were candidates; each was hunk-inspected against the NEW findings'
evidence sites:

| PR | verdict |
|---|---|
| mprov-ng/mprov_control_center#306 (System.provision netboot switch; +511/-81 across mprov_stateful.py, systems/{admin,models,views,views_noauth}.py, migrations, templates) | **Not covering.** Hunk-level inspection: adds a provision flag/gating and renames _doPowerCmd→_powerAction; leaves CC-041's bracket-wrap lines untouched (views_noauth hunks at 216/267 only), CC-043's unchecked ipmitool subprocess untouched (no returncode/bootdev changes anywhere in the diff), CC-049/050's fillpart/RAID loops untouched (single mprov_stateful.py hunk at line 16). Also re-verified it does NOT fix already-filed CC-040/#43 (hostname__contains filter and queryset[:10] truncation unchanged). |
| biondogs/mprov_control_center#2 (copilot "Fix critical security vulnerabilities…", Feb 2026) | **Not covering.** Full diff read: logging/except-narrowing/typo hygiene, dead-file removal; scriptType dereferences remain unguarded (CC-042 unfixed), no rootpw/serializer change (CC-051 unfixed), mprov_stateful.py hunks only touch exception_hook/main (CC-049/050 unfixed), views_noauth is a filename rename only. |
| biondogs/mprov_control_center#3 (WYSIWYG editor, 20k adds) | **Not covering.** Adds CKEditor statics + description fieldsets/migrations in scripts/{models,admin}.py; no null-scriptType guard (CC-042 unfixed). |
| mprov-ng/mprov_jobserver#152 (plugin/job tests, tests/ only) | **Not covering** — adds tests, changes no product code. |
| biondogs/mash#29 (accept mapping-shaped configs) | **COVERS an ALREADY-FILED item, not a NEW finding**: fixes MASH-013 (fork issue #13) — the PR's own test file cites MASH-013. Action changed from "still-live comment" to pointer-comment per the operator requirement. |
| biondogs/mash#30 (foreach dropping list items after hash) | **Not covering.** Single app.py hunk at do_foreach:362; zero hunks at renderString (MASH-101), query building (MASH-102), or plugin streams (MASH-103). |
| All OpenWiki docs PRs (mprov-ng CC#307, JS#153, SCR#19, mash#17) | Docs-only regenerations; no code. |

Also re-verified the four register-claimed upstream JS fixes are real MERGED PRs
(gh pr view 2026-10-23): #126 (merged 2026-10-21, JSR2-04), #132 (2026-10-23, JSR2-05),
#138 (2026-10-23, JSR2-06), #118 (2026-10-21, JSR2-10) — supporting the not-filed
verdicts in the JS pack §B.

## 5. Adjudicator verification (own-evidence standard, Oct-15 method)

100% source verification of every S1/S2 candidate at its pinned commit via
`git show <pin>:<path>` against the persistent clones in /local/projects/mprov-maint/
(S1/S2 after calibration: CC-051, JSR2-01, JSR2-02, JSR2-03, SCR-022, MASH-101):

| finding | check at pin | result |
|---|---|---|
| CC-051 | osmanagement/serializers.py:8-14 `fields='__all__'` + models.py:70 rootpw field @ d7c2094 | confirmed |
| JSR2-01 | image_update.py:130-170 @ 00d00bfd — peer-pull block writes image-versions without ever assigning imgVersions[image]=imageData['version']; no addjs patch | confirmed |
| JSR2-02 | image_update.py:238-268 @ 00d00bfd — .remove(image) inside iteration over self.imageList; :263 iterates self.imageList.items() on a list | confirmed |
| JSR2-03 | nads.py:205-278 @ 00d00bfd — "Error: Unable to detect…" then unconditional `return True`; lldpRes-true breaks the interface loop; downstream False check passed | confirmed |
| SCR-022 | tools/backup-mprov.sh:1-35 @ eb80617 — dumps incl. systems (BMC passwords) + media into /tmp, tarball to /tmp, no perms handling | confirmed |
| MASH-101 | src/mash/app.py:460-480 @ 36b6a5e — plain Environment(BaseLoader, autoescape=False), from_string().render() | confirmed |

S3/S4 items were accepted on the sweeps' validated registers (validator PASS with
verbatim excerpts at pins in all four sweeps) plus the merge-status checks above and
the open-PR hunk inspections, which incidentally re-exposed several S3 sites
(CC-041's commented wrap, CC-043's unchecked subprocess). The CC reviewer's coverage
claim (62/790 files but "full-sweep by module") is accepted per its REVIEW-NOTES
method statement; the Oct-15 adjudication had already source-verified the full CC
surface and the incumbent 21 still-present findings at the older pin.

Mechanical distillation check (this session): scripted parse of all 36 filed bodies —
each has exactly the five Rule C section labels in order, every body ≤150 words
(max observed: 149). One label typo found and fixed (MASH-102 "review-found").

## 6. Merge/dedupe decisions (human-review-cost pass)

- **CC-049/CC-050 vs mprov_scripts #8/#4 (SCR-008/SCR-004)**: DECLINED cross-repo
  dedupe — parallel implementations of the same pattern in different repos
  (static/mprov_stateful.py vs post-boot/localTempDisk.py); the fix must land in both
  repos, so both filings stand, with bodies cross-referenced. The Oct-15 "5 cross-repo
  dedupes" removed true duplicates routed to the wrong repo; these are not duplicates.
- **SCR-022 vs SCR-014/#14**: DECLINED merge — different script, different root cause
  (umask+volatile destination vs staging stream); bodies cross-reference.
- **JSR2-02 vs fork #7**: distinct defects on the same input path — both stand (per
  register's own marker).
- **JSR2-04/05/06/10**: removed from filing entirely — fixed at upstream head
  (merge-verified); filing them on a 28-commits-behind fork would generate four
  issues closable the day the fork syncs.
- **JSR2-19**: folded into fork issue #3 as a supplementary-site comment (register's
  own recommendation, adjudication concurs).
- **CC-047/CC-048**: considered merging (both in install_scripts/init_mpcc.sh) —
  DECLINED: distinct defects (credential capture vs signal handling) with distinct
  fixes; merging would obscure both.
- **Upstream twins cited in bodies** where they exist (mprov-ng#268/270/273/274/288/290)
  to ease later upstreaming, per the CC sweep's filing guidance — one line, no
  expansion.

## 7. Revisit conditions (falsification)

- CC-051 S1 stands unless the rootpw field is removed from the API shape (serializer
  exclusion/write-only) — revisit if upstream declares detail-response exposure
  deliberate policy for distro credentials (they did so for BMC ?detail).
- MASH-101 S2 stands only while mash scripts are locally-run, user-selected files;
  any remote fetch/auto-execution feature (marketplace, server-push) falsifies it →
  re-file S1.
- The 4 not-filed JS findings' verdicts are falsified if the fork diverges its jobserver
  product tree instead of fast-forwarding — then re-adjudicate before sync.
- The open-PR clearance is a point-in-time semantic pass; the filing card's freshness
  re-check remains mandatory and overrides any verdict here.

## 8. Handoff to the gate and filing lane

- Packs (this wave's filing input): APPROVED-FILING-{CC,JS,SCR,MASH}.md — 36 issues
  to file, 1 fold-comment, 4 upstream-fixed no-files, plus existing-issue
  comment/close guidance per repo.
- **Distiller gate card** (assignee: distiller) created to check the packs against
  Rule C (≤150 words, five-section fixed structure, no redundancy, titles carry
  severity prefix). PASS verdict required before the filing card (t_31448dcb) runs;
  the gate card is linked as an additional parent of the filing card.
- Scope guard carried: issues only, no commits/PRs (Rule D); Rule A attribution is
  N/A for issue filings but binding on any future mprov PR.
