# Adjudication Report — mProv Findings Registers

Adjudicator: sw-architect, 2026-10-15. Scope: SW-MPROV-REV (charter + CIRCUMSCRIPTION
governing; this file is the gate deliverable for the review lane).

Adjudicated registers and pinned commits (unchanged from review):

| register | commit | findings | S1 | S2 | S3 | S4 | types |
|---|---|---|---|---|---|---|---|
| control_center | 98d4579b4c11441561daca092879cc78466cfe69 | 40 (was 39) | 8 | 13 | 18 | 1 | 37 bug / 3 enh |
| jobserver | 4f73fc1b2ca17c24a7639057249d04168008e121 | 30 | 5 | 10 | 13 | 2 | 28 bug / 2 enh |
| scripts | 55bdd511e4c6912b0a6d44aefb22fc6e791e60d5 | 21 | 0 | 4 | 13 | 4 | 18 bug / 3 enh |
| mash | d8871d44c7c754198d825b32984fbc99fbd3d1f7 | 28 | 0 | 6 | 16 | 6 | 23 bug / 5 enh |

Total: 119 findings (118 reviewed + 1 adjudication-added). All four registers pass
scripts/validate_register.py at the pinned commits (re-run post-amendment).

## Verdict summary

Every register finding is APPROVED for filing as written, with two amendments,
both in the control_center register:

1. CC-004 severity recalibrated S2 -> S1 (R14 correction, applied in-register
   with a provenance comment). Rationale: README-documented admin:admin default
   credentials remain a nameable full-compromise path on the control plane;
   the charter's S1 definition (credential leading to full compromise) applies
   regardless of documentation. Original S2 reasoning (documented quick-start
   default) is defensible but the documented-default mitigation is a README
   sentence, not a mechanism: no force-change, no install-time prompt.
2. CC-040 added (S1, bug). Cross-repo routing item from the mash review
   (findings/mash/REVIEW-NOTES.md): the CC power endpoint filters
   systems/views.py:816-822 by hostname__contains and silently truncates to 10
   BMCs, so a targeted power command against compute001 can power off
   compute0010..compute0019. Charter section 5 files it against control_center
   (primary evidence); R14 lets adjudication re-apply it. Independently
   verified at source by the adjudicator at 98d4579; not a duplicate of
   CC-035 (same view, different defect). This was the only routing item lost
   between lanes - the other three routed items (script_runner return-code
   discard, entity.json world-readable secrets, image_update rootpw argv) are
   already filed as JS-010, JS-003, JS-002 respectively.

No findings were rejected, downgraded, merged, or re-titled. No excerpts were
found to be cherry-picked: in every checked case the mechanism manifests in the
wider context window, not just the cited lines.

## Verification methodology and accounting

Method: S1/S2 -> 100% independent source verification via wide-context dumps
(git show at the pinned commit, window [start-30, end+15]); S3/S4 -> 25%
minimum random-ish sample per register by the same method, plus mechanical
greps/od/comm where the claim was checkable without judgment. Reviewer
execution claims (mash probes, scripts fixtures) were treated as corroboration,
never as the adjudicator's own evidence.

| register | S1/S2 verified | S3/S4 sampled (quota >=25%) |
|---|---|---|
| control_center | 21/21 (100%): CC-001..006, 010..021, 038, 004, 040 | 5/19 = 26%: CC-022, CC-024, CC-026, CC-033, CC-037 (CC-039 additionally seen incidentally inside CC-002's window) |
| jobserver | 15/15 (100%): JS-001..015 | 5/15 = 33%: JS-016, JS-021, JS-026, JS-029, JS-030 |
| scripts | 4/4 (100%): SCR-001..004 | 7/17 = 41%: SCR-007, SCR-009, SCR-011, SCR-015 (re-run mechanically: 12 unlisted files match exactly), SCR-016 (grep), SCR-017, SCR-018 (od: `#/bin/bash` confirmed) |
| mash | 6/6 (100%): MASH-001..006 | 7/22 = 32%: MASH-007, MASH-014 (shlex comments-param semantics confirmed), MASH-017, MASH-019 (grep), MASH-021 (grep), MASH-022 (grep), MASH-023 |

All sampled and 100%-verified findings confirmed: mechanism real at source,
severity consistent with the charter scheme, excerpts verbatim and
representative. Zero disconfirmations.

## Mechanical validation

scripts/validate_register.py PASS on all four registers at the pinned commits,
before and after amendment. The earlier mash "R3 failures" were a validator
invocation path typo (mprov_mash vs mash), not evidence fabrication - all
files exist at d8871d4 per git ls-tree, and the corrected invocation passes.

## R13 collision re-check (adjudication duty)

- biondogs/mprov_control_center, biondogs/mprov_jobserver,
  biondogs/mprov_scripts, biondogs/mash: ALL FOUR FORKS HAVE ISSUES DISABLED
  (gh issue list re-run 2026-10-15). Filing (t_290a32eb) is blocked for every
  register until issues are enabled on the forks or the program re-targets.
- mprov-ng/mash open issues: #8 ("odd issues creating systems via mash"),
  #7 ("if mash.yaml doesn't exist, look for jobserver.yaml"). Neither
  duplicates a register finding (the load_config->jobserver.yaml fallback of #7
  already exists in the fork's copy; #8 is an unresolved troubleshooting report
  matching no filed mechanism). No action.
- Upstream mprov-ng/mprov_control_center and mprov-ng/mprov_jobserver were
  scanned by their reviewers (no collisions; R1/R2 notes), re-confirmed as
  adjudication accepts their scans: no register finding is an upstream
  duplicate. JS-022 vs upstream #94 kept distinct (mechanism differs:
  restart-trigger vs un-reaped mid-job death - the filing lane may merge if
  upstream maintainers disagree).

## Stale-dependency history verification (task-deliverable check)

Task note asked for a git-history review of control_center requirements.txt
"post-commit 73b4381 (expected ~7/9 major-version bumps, none of the 5
pinned)". The sha 73b4381 does not resolve in ANY of the four repos and the
string appears nowhere in the findings tree - the note's reference is stale;
the "CC-005" label also mismatches (CC-005 is the unauthenticated register
endpoint; the dependency finding is CC-028). The substantive claim was
verified with the real history instead:

- f90d476 (2022-04-18): requirements.txt debuts with 2 pinned lines
  (django greater-or-equal 3.2 and less than 3.3; dataclasses).
- 23bb591 (2022-05-04): down to 1 pin (the django lock).
- 6c029c4 (2024-12-11) "Remove the version lock on django": the django pin
  is deleted; zero constraints from here on.
- 47434f6 (2025-11-03) to the reviewed commit 98d4579: all 21 dependency
  lines carry no version operator whatsoever.

So CC-028's mechanism ("fully unpinned, README still documents Django 3.2
while a fresh install resolves 4.x") is confirmed at source and by history:
constraint removal was deliberate (the unpin commit is self-describing) and
the README contradiction is real (README line 16). CC-028 stands as filed
(S3, enhancement). For the record: the repos have never carried a lock file.

## Open questions (for the filing lane / operators, not blockers)

1. Filing targets are blocked (issues disabled on all four forks). This is a
   program-owner action item, not a register defect.
2. No repo has a runnable test suite today (CC: all tests.py empty; mash CI is
   release-trigger only; scripts repo has no harness). Every regression_test
   field names a test that cannot run until the fix lane bootstraps harnesses;
   fix cards must budget for that.
3. Severity conditionals flagged by reviewers that will move if deployment
   assumptions change: SCR-009 (BMC pw in argv) becomes S1-shaped the day
   post-boot scripts can re-run on live multi-user nodes; CC-004's default
   credentials are internet-reachable-deployment S1 (now filed S1
   unconditionally); tools/set_bmc_pw shipping a changeme default is an
   operator habit risk outside any register.
4. CC REVIEW-NOTES.md still says "39 findings" - reviewer artifacts are
   immutable by design; this report and the register provenance comments are
   the authoritative delta record (CC-004 severity, CC-040 added).
5. Upstream policy question for the operators: several fixes (notably the S1
   cluster CC-001/CC-002/CC-004) deserve upstream mprov-ng PRs rather than
   fork-only issues; the charter routes filing to the forks, so PRs are out of
   this review's scope but should be surveyed when issues are enabled.
6. The task note's stale-deps reference (commit 73b4381) could not be located
   in any repo; if it was meant to point at a specific historical review or
   fork state, the program owner should re-supply it. The verification above
   used the actual requirements.txt history instead.

## QC journal (no-fabrication controls)

- Every quoted line came from `git show <commit>:<path>` executed this session
  at the pinned commits; no excerpt was trusted from the register alone (the
  validator independently re-checks R3/R8 verbatim-ness mechanically).
- The only initially-failing checks were traced to their root cause with
  direct commands (mash validator path typo; SCR-015 "missing file" was a
  duplicate manifest entry, not a dangling reference; CC-040 first title was
  83 chars -> R2 violation -> shortened and re-validated).
- Sampling lists above are the complete set of judgment checks performed;
  nothing sampled was discarded as inconvenient. Tools/scripts used are in the
  task workspace: extract.py, listf.py, ctx.py, ctx/*.txt dumps.
- Amendment edits to control_center.issues.yaml carry in-file provenance
  comments naming the adjudicator, date, charter sections, and non-duplicate
  rationale.
