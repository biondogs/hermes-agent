# mProv Review Program — FILE-PLAN: findings register schema & filing queue

The register format every review card writes, the schema the adjudication gate
machine-checks (scripts/validate_register.py enforces the structural rules;
adjudication adds the judgment checks from CIRCUMSCRIPTION.md), and the exact
mapping to GitHub issues for the filing lane.

## 1. Register files & layout

```
/local/projects/software-co/mprov/
  findings/
    control_center.issues.yaml     # R1 register (id prefix CC)
    jobserver.issues.yaml          # R2 register (id prefix JS)
    scripts.issues.yaml            # R3 register (id prefix SCR)
    mash.issues.yaml               # R4 register (id prefix MASH)
    control_center/REVIEW-NOTES.md # narrative + observations (non-findings)
    jobserver/REVIEW-NOTES.md
    scripts/REVIEW-NOTES.md
    mash/REVIEW-NOTES.md
```

One YAML document per repo. Registers are immutable after card completion
(CIRCUMSCRIPTION.md R14). IDs are `<PREFIX>-<NNN>`, zero-padded, unique,
never reused even if a finding is later dropped.

## 2. Schema

```yaml
# ---- register header (required) ----
review:
  repo: mprov_control_center        # exact fork slug under biondogs/
  branch: main                      # branch reviewed
  commit: 98d4579abcdef...          # FULL sha reviewed (evidence verified against it)
  reviewed_at: "2026-10-16"         # ISO date
  reviewer: sw-reviewer
  coverage:
    files_reviewed: 120             # int
    files_total: 123                # int
    method: full-tree               # full-tree | targeted (targeted needs note in REVIEW-NOTES)

# ---- findings (list; empty list allowed and means "clean repo") ----
findings:
  - id: CC-001                      # ^[A-Z]{2,4}-\d{3}$, unique in file
    type: bug                       # bug | enhancement
    severity: S2                    # S1|S2|S3|S4 (impact-based, charter §2)
    title: "Crash on malformed JSON body in node status callback"   # no [Sx] here
    user_value: null                # required single sentence iff type=enhancement (R11); null for bugs
    evidence:                       # >=1 site; every site real at review.commit (R3)
      - path: app/views.py          # repo-relative, exists at commit
        lines: 42-47                # int or int-int, within file length
        excerpt: |                  # VERBATIM source lines (whitespace-normalized compare)
          data = json.loads(request.body)
          node = Node.objects.get(pk=data["node_id"])
    repro: >                        # minimal repro OR mechanism prose (R4)
      POST /api/node-status with body '{"node_id": "x"}' returns 500.
    fix_idea: >                     # PROSE ONLY, no code/diff (R5)
      Parse defensively and return 400 with an error envelope when the
      payload is malformed or the id is not numeric.
    blast_radius: >                 # what/whom/how-often/worst case (R6; S1 names scenario)
      Any malformed callback kills the worker thread; fleet status UI
      stalls for all users until restart.
    regression_test: >              # name + steps + fail-before/pass-after (R7)
      test_malformed_node_status_returns_400: post non-numeric node_id,
      assert 400; fails today with 500, passes after guard.
```

Field rules: all keys required (null allowed only for `user_value` on bugs
and nothing else); strings non-empty otherwise; extra keys are a schema
error (typos must not silently pass); severity label mapping per charter §3.

## 3. Mechanical checks (adjudication gate)

Structural — run `python3 scripts/validate_register.py <register> --repo-path <local clone>`
(requires PyYAML — `pip install --user pyyaml`; verified working 2026-10-15: passes
examples/register-example.yaml, rejects fabricated evidence, code-in-fix_idea, and bad YAML):
| Check | Rule |
|---|---|
| YAML parses; header keys present; coverage ints | schema |
| id format/unique/prefix-correct | R1 hygiene |
| type/severity enums valid; user_value required iff enhancement | R11/R12 |
| title regex `^[A-Z].{2,78}$`, no `[S` prefix, no trailing `.` | R2 |
| every evidence site: path exists at `git show commit:path`; excerpt (whitespace-normalized) found within [start-2, end+2] window | R3/R8 |
| fix_idea/repro/blast_radius/regression_test non-empty | R4-R7 |
| fix_idea contains no ``` fences, no `--- `/`+++ ` diff markers, no lines ending in code punctuation stacks (`{`, `;`) | R5 |

Judgment (human/LLM adjudication, logged per finding in APPROVED-FILING.md):
- S1 scenario named (R6), causal path traced (R10), lint-class filter (R9),
  obvious-bar per enhancement (R11), cross-repo dedupe (charter §5),
  open-issue collision re-check (R13), severity calibration (R12).
- Source-reading spot-check: ≥25% of S3/S4 per repo, 100% of all S1/S2.

## 4. Approved queue → GitHub issue mapping (filing lane)

Adjudication emits APPROVED-FILING.md as per-repo ordered queue rows; each row
is filed with:
- `gh issue create -R biondogs/<repo> --title "[S<sev>] <title>" --label <type>,s<sev>-<name>,review-found --body-file <row body>`
- Body template (section order fixed):
  ```
  ## Summary
  ## Evidence            <- per site: `<path>:<lines>` + fenced excerpt
  ## Repro / mechanism
  ## Blast radius
  ## Proposed fix idea   <- prose only
  ## Regression test (description)
  ## Found by            <- "2026-10 comprehensive review, <id>"
  ```
- One queue row = one `gh issue create` = one line in FILED-ISSUES.md
  (repo, issue#, title, severity, url). Bodies verbatim (R14).

## 5. Verdicts & counters

Adjudication must report: findings_in / approved / rejected (by rule) /
merged (dedupe) / downgraded / demoted-to-observation, per repo and total.
Reviewers complete their cards with counts by severity; these must match
`len(findings)` in their register — validator prints the tally.
