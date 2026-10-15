# mProv Stack — Review Charter (SW-MPROV-0-CHARTER)

Status: BINDING for all mProv review, adjudication, and filing cards.
Product stage: GENERAL-RELEASE, entering CI/CD hardening. Reviews are
general-release product reviews, not skims.
Charter authored: 2026-10-15 (kanban t_a6e7e859, sw-pm).

Companion documents (all normative, same directory):
- CIRCUMSCRIPTION.md — the one-finding-one-issue rules every finding obeys.
- FILE-PLAN.md — the findings register schema and the mechanical checks the
  adjudication gate runs before anything reaches GitHub.

## 1. Product under review

The mProv provisioning stack (four repos). Work happens on operator forks
under github.com/biondogs/* (origin=biondogs, upstream=mprov-ng). Reviews are
READ-ONLY against these checkouts on ga01:

| Repo | Local path | Default branch | Role |
|---|---|---|---|
| mprov_control_center | /local/projects/mprov/mprov_control_center | main @98d4579 | Django web UI |
| mprov_jobserver | /local/projects/mprov/mprov_jobserver | main @4f73fc1 | background worker / provisioning orchestrator |
| mprov_scripts | /local/projects/mprov/mprov_scripts | master @55bdd51 | image-gen / post-boot scripts, run AS ROOT on fleet nodes |
| mash | /local/projects/mprov/mash | master @d8871d4 | CLI client (stalest repo — unchanged since 2023) |

Reviewers record the exact commit SHA they reviewed in the register header.

## 2. Severity scale (S1–S4)

Every finding and every filed issue carries exactly one severity. Severity is
assigned by IMPACT, never by how hard the fix is.

| Level | Label | Definition | Calibration test |
|---|---|---|---|
| S1 | s1-blocker | Security hole or data-loss path: auth/authz bypass, secret exposure, injection, destructive op able to hit the wrong target, credential leak. | You can name a concrete attack or loss scenario and the code path that enables it. No scenario nameable → not S1. |
| S2 | s2-functional | Functional bug: a documented/intended behavior is wrong in normal operation — job fails or misbehaves, wrong data shown/sent, CLI produces wrong result. | You can describe an ordinary-use sequence that produces the wrong outcome. |
| S3 | s3-robustness | Robustness/edge-case weakness: works in the happy path but degrades badly — missing error handling, unguarded edge inputs, missing protective features (dry-run, config validation, log rotation). | Happy path works; a named adverse condition (failure, partial state, bad input) makes it worse than it should be. |
| S4 | s4-hygiene | Hygiene: logging polish, dead code, confusing-but-harmless output, missing --help text, doc drift. No behavioral risk. | Worst case is developer/reviewer annoyance. |

Anti-inflation rules (adjudication enforces):
- S1 requires a NAMED concrete attack/data-loss scenario in blast_radius.
  "Potential security issue" with no scenario → downgrade or reject.
- Anything whose worst case is a confusing error message is S4, not S3.
- Missing protective features (dry-run, validation, rotation) are S3
  enhancements, never S2.

## 3. Issue taxonomy — labels on all four forks

Created 2026-10-15 on biondogs/mprov_control_center, biondogs/mprov_jobserver,
biondogs/mprov_scripts, biondogs/mash (receipts: LABELS-RECEIPTS.md).
`bug` and `enhancement` are GitHub defaults, reused as-is.

| Label | Meaning | Applied to |
|---|---|---|
| bug | Confirmed defect | every S1–S4 defect finding |
| enhancement | Obvious improvement request | every feature-request finding (see CIRCUMSCRIPTION.md §R11 obvious-bar) |
| s1-blocker | Severity S1 | per severity |
| s2-functional | Severity S2 | per severity |
| s3-robustness | Severity S3 | per severity |
| s4-hygiene | Severity S4 | per severity |
| review-found | Discovered by the 2026-10 comprehensive review, not by users | every issue filed from this program |

Every filed issue carries exactly three labels: one type (bug XOR enhancement)
+ one severity (s1..s4) + review-found.

## 4. Per-repo review scope

A comprehensive review of each repo covers AT MINIMUM the areas below. Full-tree
read; findings beyond these lists are welcome if they pass circumscription.

### 4.1 mprov_control_center (web / Django)
- Auth & authz: every view/URL mapped — who may reach it? Missing
  login/permission decorators, IDOR on object lookups, privilege checks only in
  templates (client-side theater).
- Secrets: settings.py vs env, secrets reachable from templates, tokens/keys in
  views or committed files, DEBUG exposure.
- ORM misuse: N+1 in request paths, missing select/prefetch on hot lists,
  unfiltered querysets on large tables, raw SQL / extra() parameterization.
- Migrations hygiene: hand-edited migrations, missing/unordered dependencies,
  data migrations without reversibility notes.
- Error handling: especially network-facing code — upstream commit 98d4579 is
  literally "better error reporting on network issues"; scrutinize that area
  and its siblings (swallowed exceptions, error text leaking internals).
- Forms/validation: unvalidated inputs reaching models or subprocesses.
- Dependency hygiene: unpinned requirements, known-vulnerable versions.

### 4.2 mprov_jobserver (daemon / orchestrator) — highest-stakes repo
- Job lifecycle traced end-to-end: queue → dispatch → provision → post-boot
  scripts. Every state edge: what happens on failure mid-edge?
- Subprocess/invoke handling: shell=True usage, string-interpolated commands,
  ssh/image-transfer quoting hazards, injection from DB/queue-sourced values.
- Destructive operations: image sync/overwrite — what stops a typo or stale
  record from wiping the wrong fleet? Guard analysis per destructive call site.
- Error propagation: bare/broad excepts that swallow, partial-provision states
  left behind, retries that mask permanent failures.
- Idempotency: re-running a job after crash — safe, or double-provisions?
- Concurrency: races on shared state (files, DB rows, image store), worker
  count assumptions.
- Logging: structured? rotation? credentials/keys in log lines?
- Fresh code: scripts/repack_image.py (upstream, added 2026-07) reviewed as
  new code, no benefit of the doubt.

### 4.3 mprov_scripts (root-on-node scripts)
Treat every script as PRIVILEGED CODE — they run as root on fleet nodes.
- Shell quoting/word-splitting: unquoted expansions, `$var` in destructive
  paths, eval usage, command substitution on external input.
- Destructive ops: rm -rf / dd / mkfs-class commands — argument-validation
  analysis: what is the worst value each variable could take at that line?
- cd-failure discipline: `cd` without `|| exit` before relative destructive
  paths.
- Network-fetch-piped-to-shell patterns (curl | sh).
- Portability: RHEL-version assumptions (7/8/9 divergence, sysv vs systemd,
  yum vs dnf, net-tools deprecation).
- Exit-code discipline: set -e/-u/-o pipefail presence and correctness;
  scripts that lie about success.
- Secrets in scripts: passwords/keys in argv (visible in ps), logs, or temp
  files — set_bmc_pw-class scripts get explicit scrutiny.
- Manifest drift: mpcc_scripts.yaml vs actual scripts (entries pointing at
  missing files, scripts not in manifest).

### 4.4 mash (CLI client)
- Credential/config handling: tokens in plaintext config, env fallbacks,
  world-readable config files, secrets echoed in errors.
- TLS verification defaults (verify=False class defaults are S1/S2 candidates).
- Arg validation: bad/missing args reaching API calls or destructive verbs.
- Output contracts: is stdout machine-parseable? are exit codes meaningful
  (0/nonzero discipline)? do errors pollute stdout?
- Config handling: unknown keys silently ignored, precedence (flags/env/file).
- API-surface drift (cross-repo): compare mash's endpoint calls against current
  control_center views/urls — renamed/added/removed endpoints mash misses.
  Drift findings are enhancements unless they break a current verb (then S2).
- Dependency currency: requirements vs current PyPI/Django-side reality.
- Feature mining is richest here — but only through the obvious-bar
  (CIRCUMSCRIPTION.md §R11): --json/machine output, dry-run on destructive
  verbs, config validation, help text.

## 5. Cross-repo dedupe policy

Same defect pattern at N sites (typical: identical quoting bug replicated
across mprov_scripts) = ONE issue enumerating all N sites with per-site
file:line, UNLESS severities genuinely differ (e.g. one site guards the
variable, three don't) — then split by severity class, evidence preserved.
Cross-repo findings file against the repo owning the PRIMARY evidence;
sites in other repos are enumerated inside the body.

## 6. Out of scope for the whole program

- No code changes, patches, or PRs anywhere (finding registers only until
  filing; filing creates issues only).
- No style nits a linter/formatter owns (shellcheck, flake8, black, isort,
  eslint, gofmt…): if a tool would flag it, the review output is "enable the
  linter in CI", at most ONE S4 enhancement per repo saying that — not N
  issues.
- No speculative findings: "this might race under load" without a traced
  call path producing the interleaving is not a finding.
- No rewrite proposals ("migrate to async", "replace Django with X").
  Propose the minimal fix IDEA inside the existing architecture.
- Upstream-vs-fork: reviews run against fork HEAD == upstream current;
  findings file on the fork. No issue may be a duplicate of an existing
  open issue (reviewers note existing-issue collisions in REVIEW-NOTES.md;
  adjudication dedupes against `gh issue list`).
