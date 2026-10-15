# mProv Review Program — Circumscription Rules (BINDING)

Normative for every reviewer, the adjudication gate, and the filing lane.
Operator demand: "everything well circumscribed." Each rule is numbered R-n
and each has a MECHANICAL CHECK column: how adjudication verifies it without
judgment calls where avoidable. A finding failing any hard rule is REJECTED
or sent back to the review card — it never reaches GitHub softened.

## The rules

| # | Rule | Mechanical check |
|---|---|---|
| R1 | ONE finding = ONE issue. Never bundle two defects because they are adjacent or "related". Exception: §5 charter dedupe — one replicated pattern at N sites is ONE issue enumerating N sites (that is one finding, pattern-shaped). | Register: 1 YAML entry = 1 issue; adjudication merges entries sharing identical defect + differing only in site. |
| R2 | Title: `[Sx] <short imperative>` — severity prefix, ≤80 chars, no trailing period, no repo name (the repo is the issue location). | Regex: `^\[S[1-4]\] [A-Z].{2,78}$` (prefix applied at file-plan stage; register stores title WITHOUT prefix + severity field). |
| R3 | Every finding carries file:line evidence at the reviewed commit: repo-relative path + line or range + VERBATIM excerpt copied from those lines. | Adjudication: `git show <commit>:<path>` contains the excerpt (whitespace-normalized) within [line_start, line_end] ±2. Failure → reject, no mercy. |
| R4 | Every finding carries a minimal repro OR a code excerpt with a prose explanation of what goes wrong and why. "Bad practice" is not a repro. | Field `repro` present, ≥1 concrete sequence or scenario. |
| R5 | Proposed fix is an IDEA in prose — the approach, the guard, the validation — NEVER code, never a diff, never a patch file. Implementation is the fix lane's job. | Field `fix_idea` present; no fenced code block, no unified-diff markers, no full statements ending in `;`/`:` code syntax. |
| R6 | Every finding carries blast_radius: what breaks, for whom, how often, worst case. S1 additionally must NAME its attack/loss scenario (charter §2). | Field present; S1 entries: adjudication checks a named scenario sentence exists. |
| R7 | Every finding carries a regression-test DESCRIPTION (test name + what it does + fail-before/pass-after assertion). Description, not code. | Field present, has test-name + assertion sentence. |
| R8 | NO file:line evidence → NO issue. Full stop. Findings you cannot pin to a line stay in REVIEW-NOTES.md narrative ("observations"), never in the register. | Register entries without complete `evidence[]` are invalid YAML-schema → auto-reject. |
| R9 | No speculative style nits. Anything a linter/formatter would own (shellcheck, flake8, black, isort, eslint) is NOT a finding — max ONE S4 "enable <linter> in CI" enhancement per repo, from the reviewer who notices first. | Adjudication rejects lint-class findings beyond the one-per-repo allowance. |
| R10 | No speculation, no "might". Claims of races/injection/crashes require the traced path that produces them, cited line by line. If you could not trace it, it is an observation in REVIEW-NOTES.md, not a finding. | Adjudication: causal-path sentences in repro reference concrete call sites. |
| R11 | Feature requests pass the OBVIOUS bar: the improvement is (a) in the obvious class — missing --help/help text, no dry-run on a destructive op, no config validation, no log rotation, no machine-readable (--json) output on a CLI that scripts pipe — AND (b) expressible as ONE SENTENCE of user value that a skeptical operator nods at without debate. Anything needing a paragraph of justification is a redesign proposal, not a feature request: REVIEW-NOTES.md only. | Field `user_value` present, single sentence. Adjudication confirms obvious-class membership explicitly per enhancement. |
| R12 | Severity by IMPACT per charter §2 calibration tests; enhancements are S3 (missing protective feature) or S4 (ergonomics). Adjudication may downgrade; inflation is rejected, not relitigated. | Severity field ∈ {S1..S4}; adjudication records calibration changes in APPROVED-FILING.md. |
| R13 | No duplicate of an existing open issue. Reviewers check `gh issue list -R <fork> --state open` for collisions and note them in REVIEW-NOTES.md; adjudication re-checks and drops collisions, keeping the note. | Adjudication: title/pattern fuzzy-match against live open-issue list at adjudication time. |
| R14 | Registers are immutable drafts: reviewers never edit a register after completing their card; corrections happen by reviewer comment on their card, adjudication reapplies. Filing lane copies APPROVED-FILING.md rows VERBATIM — no rewording at file time, formatting fixes only. | Filing receipt: filed title/labels equal APPROVED-FILING row; bodies differ only by whitespace. |

## Consequences of a failed check

- Missing/soft evidence (R3/R8) → REJECT; list in send-back comment on the
  review card with the rule number. Reviewer may resubmit with real evidence.
- Fix delivered as code (R5) → adjudication rewrites to a one-line prose IDEA
  or rejects if no prose IDEA can be stated (fix-unknown usually means
  not-a-finding).
- Severity inflation (R12) → downgrade, verdict logged.
- Enhancement failing the obvious-bar (R11) → demoted to REVIEW-NOTES.md
  observation, verdict logged.

## Register → issue mapping (what a compliant entry becomes)

- Title: `[S<severity>] <title>`
- Labels: `<type>, s<severity>-<name>, review-found` (charter §3)
- Body sections, in order, from register fields:
  **Summary** (title + one-line context) · **Evidence** (per-site file:line +
  excerpt block) · **Repro / mechanism** · **Blast radius** · **Proposed fix
  idea** (prose) · **Regression test (description)** · **Found by** ("2026-10
  comprehensive review, <register id>").

Full field schema and the register format: FILE-PLAN.md.
