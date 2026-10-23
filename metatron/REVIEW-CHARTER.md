# Metatron — Review & Redevelopment Intake Charter (METATRON-0)

Status: BINDING for all metatron review, adjudication, and architect cards.
Product stage: PRE-REDEVELOPMENT. The operator directive (2026-10-23) is a
FULL REDEVELOPMENT from the foundational concept; the review phase exists to
harvest what the existing lines know, not to polish them.
Charter authored: 2026-10-23 (kanban t_cef0727b, sw-pm).

Companion documents (same directory):
- INVENTORY.md — branch inventory, per-branch health table, foundational
  concept with source citations. Read first.
- OPERATOR-DIRECTION.md — locked operator decisions from intake Q&A
  (2026-10-23). Binding; supersedes any charter caveat it closes.

## 1. Product under review

Single repo: **biondogs/metatron** (private), local clone `/local/projects/metatron`
(remote origin = https://github.com/biondogs/metatron). Python 3.11+, ~1.5 MB
across 251 `.py` files on master, MIT. No git tags exist anywhere; versions
live only in `pyproject.toml` (master @ 0.4.0).

Work happens ONLY on the operator fork (biondogs/metatron; no upstream).
Reviews are READ-ONLY against the local clone.

Branches under review (pinned SHAs — record these in every register header):

| Branch | Head SHA | Identity |
|---|---|---|
| master | 811e335 | The "v1" line. v0.4.0, CI-green, richest line (160 commits). |
| v2 | b2c1a5b | The "v2" line, 12 unique commits off merge-base b4a55f2. PR #69 open, never merged. |
| feature/gui-editor | 838f88c | GUI Phase 2 web editor (newest activity in repo, 2026-09-22). No PR. |
| feature/gui-dev | 5cce9c8 | GUI test-env line; ancestor of gui-editor. No PR. |

Reviewers record the exact commit SHA they reviewed in the register header.
Use `git show <ref>:<path>` / dedicated throwaway worktrees OUTSIDE the clone;
do NOT create worktrees inside `/local/projects/metatron` (nested, as the
existing `.worktrees/` are) and do NOT disturb the operator's main checkout —
it is parked on `dependabot/pip/production-8a961bab16` with untracked operator
files.

## 2. Severity scale (S1–S4)

Every finding carries exactly one severity. Severity is assigned by IMPACT,
never by how hard the fix is. (Identical scale as mprov precedent,
../mprov/REVIEW-CHARTER.md §2.)

| Level | Label | Definition | Calibration test |
|---|---|---|---|
| S1 | s1-blocker | Security hole or data-loss path: auth/authz bypass, secret exposure, injection, destructive op able to hit the wrong target, credential leak. | You can name a concrete attack or loss scenario and the code path that enables it. No scenario nameable → not S1. |
| S2 | s2-functional | Functional bug: a documented/intended behavior is wrong in normal operation. | You can describe an ordinary-use sequence that produces the wrong outcome. |
| S3 | s3-robustness | Robustness/edge-case weakness: happy path works but degrades badly under a named adverse condition. | Happy path works; a named adverse condition makes it worse than it should be. |
| S4 | s4-hygiene | Hygiene: logging polish, dead code, doc drift. No behavioral risk. | Worst case is developer/reviewer annoyance. |

Anti-inflation rules (adjudication enforces):
- S1 requires a NAMED concrete attack/data-loss scenario in blast_radius.
- Anything whose worst case is a confusing error message is S4, not S3.
- Missing protective features are S3 enhancements, never S2.

## 3. Issue taxonomy

Label taxonomy (mirrors mprov): one type (`bug` XOR `enhancement`) + one
severity (`s1-blocker`, `s2-functional`, `s3-robustness`, `s4-hygiene`) +
`review-found`. **OPERATOR DECISION Q7=c (2026-10-23, OPERATOR-DIRECTION.md
§2.8): there is NO filing phase — findings registers feed the rewrite backlog
directly.** GitHub labels on biondogs/metatron are never created and never
used; taxonomy is enforced at register-schema level only (every finding
carries its type + severity fields in the YAML register).

## 4. Per-branch review scope

### 4.1 master (v1 line) — harvest + health
- Core pipeline & agents (`src/metatron/pipeline/`, `agents/` — 18 files):
  stage model rigidity (fixed-order, no back-edges — see INVENTORY §3 audit
  answers), metadata bleed between stages (existing issue #57 — record a
  still-open/fixed verdict vs current HEAD; no re-filing, Q7=c).
- RAG subsystem (`rag/` — 11 files): vector-store resource leaks (#44),
  SQL injection via collection_name (#33), non-deterministic embeddings
  (#49), silent zero-vector fallbacks (#45).
- Security layer & REST server (`security*`, `server/`): unauthenticated
  API (#42), sanitizer not wired into server (#51), safe-tar (fixed in
  6aac261 — confirm).
- Citation integrity (`citation/`): verifier checks existence only, not
  claim support (audit answer #2 in
  `docs/feature-requests/interactive-paper-development.md` on v2);
  BibTeX/LaTeX escaping areas (fixed on master — verify).
- Console/GUI Phase 0–1 (`console.py`, `workflow.py`, `events.py`,
  `webridge.py`): event-bus contract vs `docs/dev/EVENT-BUS.md`.
- Existing-issue reconciliation: 19 issues open since 2026-07-11; several
  are already fixed on master (#54/#74, #55/#56, #58, #28, #72, #70). A
  REQUIRED output of this review is a per-issue verdict: still-open /
  fixed-on-master / fixed-on-v2 / unverified.

### 4.2 v2 branch — design-intent harvest (primary concept source)
- ADRs `docs/adr/0001,0002` + plans `docs/plans/2026-07-13-ux-replan-full-lifecycle.md`,
  `2026-07-14-project-workspaces-*`: are the ADRs internally consistent,
  do the 12 v2 commits actually implement what ADR-0001/0002 decide?
- `docs/feature-requests/research-lifecycle-v2.md`: treat the ✅/🔶/⬜
  annotations as claims to spot-check against code, not as ground truth.
- The 2056-insertion v2 src delta: workspace/revisioning code quality; it is
  a candidate seed for the rewrite — grade accordingly.

### 4.3 feature/gui-editor (+ gui-dev) — GUI direction harvest
- Gateway protocol + agent-participation + suggestion-set model (commit
  c45d322 docs): architecture soundness, coupling to AgentEvent bus.
- Hocuspocus/BlockNote/pytest stack (Phase 2 scaffold 6944702): licensing
  already decided open-source in 2f34532/d096bbf on master — verify no
  new licensing exposure.
- No CI runs exist on these branches (CI triggers only on main/master + PRs).

### 4.4 Stale branches (fix/e2e-ansi-color-codes, fix/mypy-numpy2-pep695,
feature/llm-sdk-enhancements, feature/parallel-agent-execution, dependabot/*)
— inventory only. Health table entries; no deep review unless they contain
the sole copy of a fix (check `git cherry` before assuming merged-in-spirit).

## 5. Cross-branch dedupe policy

Same defect at N branch-sites = ONE finding enumerating sites with
branch:file:line, UNLESS severities genuinely differ. A defect fixed on one
branch but live on another is recorded as fixed-on-<branch>, not re-counted.
Findings file against the branch owning the PRIMARY evidence.

## 6. Out of scope for the review phase

- NO code commits anywhere — including `/local/projects/metatron` itself and
  any new worktrees' branches. Findings registers only.
- NO upstream writes: no issues, PRs, label creation, branch deletion, tag
  creation on biondogs/metatron. (Management-repo commits like this charter
  are not upstream writes.)
- No style nits a linter owns; at most ONE S4 per branch saying "enable X".
- No speculative findings without a traced call path.
- No rewrite proposals — the redevelopment IS the rewrite; the review's job
  is to harvest concepts, decisions, and defects, not to re-litigate
  architecture. Minimal-fix ideas are recorded only where the v-line will
  keep running during the review.
- Do not run test suites or install anything into the operator's `.venv`;
  static reading + CI status are the evidence base.
