> Status: current. Canonical registry entry: hermes-estate/docs/GOVERNANCE.md G-34 (2026-10-30). This file is the doctrine text of record for all filings to github.com/NousResearch/hermes-agent.

# UPSTREAM-HERMES-FILING — filing rules for github.com/NousResearch/hermes-agent

**Card:** t_1a63e305 · **Lane:** sw-docs · **Date:** 2026-10-30
**Scope:** every outbound artifact to the hermes-agent upstream — issues, issue edits, PRs, PR body/comment edits, review replies. Applies to every filing lane (distiller, sw-dev-a/b, sw-docs, and anyone else with a GO to file).
**Companion:** skill `upstream-hermes-filing` (mechanical pre-filing checklist); estate law G-06 (operator GO on public filings) still gates every submission — nothing here releases a filing by itself.

---

## 0. Sources of record (captured 2026-10-30T15:45Z unless noted)

| Key | Path/URL | sha256 (first 12) |
|---|---|---|
| [C] | `CONTRIBUTING.md` @ `main` (57,145 B) — https://raw.githubusercontent.com/NousResearch/hermes-agent/main/CONTRIBUTING.md | captured in this card's workspace |
| [PRT] | `.github/PULL_REQUEST_TEMPLATE.md` @ `main` (3,447 B, blob `a2ef1740fbf8`) | |
| [BUG] | `.github/ISSUE_TEMPLATE/bug_report.yml` @ `main` (5,166 B, blob `67a3f64aa372`) | |
| [FEAT] | `.github/ISSUE_TEMPLATE/feature_request.yml` @ `main` (2,872 B, blob `720cc8f1f27c`) | |
| [SETUP] | `.github/ISSUE_TEMPLATE/setup_help.yml` @ `main` (3,752 B) | |
| [CFG] | `.github/ISSUE_TEMPLATE/config.yml` @ `main` (765 B, blob `109e98791be2`) | |
| [CI] | `.github/workflows/ci.yaml` @ `main` (25,744 B) + 56 sibling workflow files | |
| [LINT] | `.github/workflows/lint.yml` @ `main` (15,966 B) | |
| [ATTR] | `.github/workflows/contributor-check.yml` @ `main` (5,012 B, blob `d488090f1e1c`) — stable since commit `bf2f9570` (2026-10-14) | |
| [OWN] | `.github/CODEOWNERS` @ `main` (3,380 B, blob `9f049a39ffdf`) | |
| [SEC] | `SECURITY.md` @ `main` (15,752 B) | |
| [LIC] | `LICENSE` @ `main` — MIT, "Copyright (c) 2025 Nous Research" | |
| [LOG] | `git log` sample of `main` (shallow clone 2026-10-30T15:52Z) | |
| [DOCS] | https://hermes-agent.nousresearch.com/docs/developer-guide/contributing (fetched 2026-10-30T15:47Z; Docusaurus mirror of [C]) | |
| [AGT] | `AGENTS.md` @ `main` (11,952 B, blob `4c4ce5c04528`) — https://raw.githubusercontent.com/NousResearch/hermes-agent/main/AGENTS.md — \"For AI coding assistants and developers working on hermes-agent\" (fetched 2026-10-30T16:03Z) | |

**Absence record (measured, not assumed):**
- `CODE_OF_CONDUCT.md`: **not specified upstream** — HTTP 404 on `main` (measured 2026-10-30T15:45Z). Community norms live in [C] §Community (Discord, GitHub Discussions) and the issue templates' tone. Conduct expectations for us: G-07 (persona, no internal specifics) is stricter than anything upstream states.
- **DCO / `Signed-off-by`: not specified upstream** — no DCO text in [C], no DCO/sign-off job in any of the 57 workflow files (grep measured 2026-10-30), and merged `main` history carries no `Signed-off-by` trailers ([LOG]). Do not add sign-off lines; they are noise upstream.
- **CLA: not specified upstream** — no CLA bot or text found.
- **AI-assisted / LLM-contribution disclosure/attribution policy: not specified upstream** — no disclosure or attribution policy in [C] or the templates: no template field asking "was this written by AI?", no `Signed-off-by`/DCO/CLA disclosure flow. Upstream DOES carry AI-assistant **working rules** in root `AGENTS.md` [AGT] ("For AI coding assistants and developers working on hermes-agent") plus per-area `AGENTS.md` files (routing table in [AGT] §Routing Table; docs block in [C] line 316 lists `AGENTS.md`; [PRT] docs block references it). The only adjacent attribution rule is [C] §Skill authoring standards HARDLINE #4: *"**`author` credits the human contributor first.** … 'Hermes Agent' is the secondary collaborator. If the contributor's commit shows 'Hermes Agent' as author because they used Hermes to draft the skill, replace it with their actual name — credit the human, not the tool."* Upstream's posture is therefore: **human-first attribution, no disclosure requirement, Hermes Agent allowed as named secondary collaborator in skill metadata, plus working-rules guidance for AI assistants in [AGT]**. Reconciliation with house law: our practice of stripping `Agent-Profile`/`Agent-Run` git trailers before public commits (skill `github/strip-agent-trailers-public-commits`, G-07) is *compatible* with and leans on the human-first side of upstream's posture — upstream asks nothing we don't already do, and asks nothing extra. Commit author stays `biondogs`; "Hermes Agent" may appear only as secondary collaborator where [C] itself prescribes it (skill `author:` fields).

---

## 1. Routing: issue vs PR vs other surface

- **R1 — Security vulnerabilities never go to a public issue or PR.** Report privately via GitHub Security Advisories or `security@nousresearch.com`. [SEC] §1: *"Do not open public issues for security vulnerabilities."* [CFG] routes the security link ahead of everything: *"Report vulnerabilities privately — never in a public issue. Read SECURITY.md for scope first."* Before filing anything security-flavored, run it against [SEC] §3.1 (in scope) vs §3.2 (out of scope: heuristic bypasses, prompt-injection-per-se, posture consequences, break-glass flags, third-party skills/plugins). A §3.2 item files as a *regular* issue/PR, not via the private channel ([SEC] §3.2: *"they are still welcome as regular issues or pull requests"*).
- **R2 — Bug report → 🐛 Bug Report template** (title prefix `[Bug]:`, label `bug`). [BUG] `title: "[Bug]: "`.
- **R3 — Feature request → ✨ Feature Request template** (title prefix `[Feature]:`, label `enhancement`). [FEAT] `title: "[Feature]: "`.
- **R4 — Install/config trouble → 🔧 Setup Help template** (title prefix `[Setup]:`, label `setup`). [SETUP].
- **R5 — Design proposals / architecture discussion → GitHub Discussions or Discord, not an issue.** [C] §Community: *"GitHub Discussions: For design proposals and architecture discussions"*.
- **R6 — New memory provider or third-party product integration → standalone plugin repo, never a core PR.** [C] §Memory Providers: *"We are no longer accepting new memory providers into this repo… PRs that add a new directory under `plugins/memory/` will be closed with a pointer."* [C] §Third-Party Product Integrations: *"**These do not land in this repo.** … A well-built third-party-product plugin can clear automated review and still be closed for this reason."* Reaching users = a catalog PR adding one `plugin-catalog/<name>.yaml` pinned at an exact commit ([C] §Submitting a Plugin to the Catalog).
- **R7 — Specialized/niche skill → Skills Hub, not bundled.** [C] §Should the Skill be bundled?: bundled = *"broadly useful to most users"*; official-but-not-universal → `optional-skills/`; niche → registry + Discord `#plugins-skills-and-skins`.
- **R8 — Search before filing anything.** [C] §Before You Start: *"Search both open *and* merged PRs and issues for your topic or error symptom"* (`gh search issues/prs --repo NousResearch/hermes-agent …`), plus *"The issue tracker can lag the code… also search the source."* If an open PR already addresses it: *"consider reviewing or improving that one instead of opening a competing duplicate."* For larger work, comment on the issue first to claim it. No unverified-premise bug filings: repro on `main` + name the exact line where the bug manifests (check intent with `git log -p -S "<symbol>"`) [AGT].
- **R9 — PR without a prior issue is allowed but discouraged for non-trivial work.** [PRT] Related Issue: *"Link the issue this PR addresses. If no issue exists, consider creating one first."* House practice (from our #143206/#143372 pair): feature PRs anchor to an issue that frames the design decision; the PR references it with `Refs #N` (or `Closes #N` when it fully settles it — see R20).

## 2. Issue conformance (byte-level fields)

- **R10 — Bug issues must fill every `required: true` [BUG] field.** Required: Bug Description, Steps to Reproduce, Expected Behavior, Actual Behavior, Affected Component (dropdown, multiple), **Debug Report** (`hermes debug share` links — required:true; fallback `hermes debug share --local` output), Operating System. Optional-but-expected: Python Version, Hermes Version, Additional Logs, Root Cause Analysis, Proposed Fix, "willing to submit a PR" checkbox. Pre-submit checklist embedded in the template: search existing issues, `hermes update` and confirm still broken.
- **R11 — Feature issues must fill every `required: true` [FEAT] field.** Required: Problem or Use Case, Proposed Solution, Feature Type (dropdown). Optional: Alternatives Considered, Scope (Small <50 LOC / Medium <300 / Large), Contribution checkbox, Debug Report. The template's own pre-flight: *"Is this a new skill? Most capabilities should be skills, not tools."*
- **R12 — Debug Report integrity.** Any `paste.rs`/debug link we file must be content we authored and scrubbed (G-07: no internal specifics in anything public). Before `hermes debug share` on a production host, assume it uploads config + logs; prefer `--local` + hand-pasted, sanitized output for estate hosts. **House rule (stricter than upstream):** debug artifacts from ga01 are public filings — they route through the distiller gate + operator GO like any other outbound text (G-06).
- **R13 — Free-text issue bodies mirror the template sections** even when filed as a blank issue (`blank_issues_enabled: true` in [CFG]) — same headings, same order, so triage labels (`comp/*`, `type/*`, `P*`, `area/*` observed live on our #143206) apply cleanly.

## 3. PR conformance (byte-level fields)

- **R14 — PR body = the [PRT] skeleton, unfilled placeholders are filing failures.** Sections in order: `## What does this PR do?` · `## Related Issue` (`Fixes #` line) · `## Type of Change` (exactly one of 🐛/✨/🔒/📝/✅/♻️/🎯) · `## Changes Made` (*"Include file paths for code changes"*) · `## How to Test` (numbered; bugs: repro steps + proof the fix works) · `## Checklist` (Code + Documentation & Housekeeping sub-blocks, all boxes ticked or N/A'd) · `## For New Skills` (only when adding a skill; *"Delete this section otherwise"*) · `## Screenshots / Logs`.
- **R15 — Checklist boxes are assertions, not decoration.** [PRT] Code block requires: read [C]; Conventional Commits; duplicate search done; **only** related changes in the PR; `pytest tests/ -q` green; `python scripts/check` green; tests added (*"required for bug fixes, strongly encouraged for features"*); platform tested (name it, e.g. `Ubuntu 24.04`). Docs block: docs updated / `cli-config.yaml.example` / `CONTRIBUTING.md`+`AGENTS.md` / cross-platform impact / tool descriptions — each ticked or N/A. A lane may only tick a box it ran; unrunnable boxes go unchecked with a one-line explanation in the body (house law: truthful receipts).
- **R16 — Title style.** Code PRs: Conventional Commits — `<type>(<scope>): <description>` with types `fix|feat|docs|test|refactor|chore` and scopes like `cli, gateway, tools, skills, agent, install, whatsapp, security` ([C] §Commit messages; [PRT] checklist confirms titles/commits follow it). Issue-titled work keeps the template prefix (`[Bug]:`, `[Feature]:`, `[Setup]:`).

## 4. Branches, commits, workflow

- **R17 — Fork + feature branch from `biondogs/hermes-agent`, PR into `NousResearch/hermes-agent:main`.** Branch prefixes [C] §Branch naming: `fix/…`, `feat/…`, `docs/…`, `test/…`, `refactor/…`. (Live example: our PR #143372 rides `feat/kanban-archive-tool` → `main`.)
- **R18 — Commit messages: Conventional Commits** (`fix(scope): …`) per [C] §Commit messages. Body explains *why* + evidence (the live `main` history is one-line imperative subject + dense why/body — [LOG]); trailer line `Refs: <issue URL>` in the body is upstream-visible practice in our own merged-style commits and acceptable; upstream does not require it.
- **R19 — No DCO/sign-off (see §0 absence record); no AI-disclosure trailer.** Strip `Agent-Profile`/`Agent-Run` trailers before any public commit (existing house law `strip-agent-trailers-public-commits`). Contributor emails must map: the [ATTR] CI job fails a PR whose new author emails lack a `contributors/emails/<email>` file — fix with `python3 scripts/audit_pr_attribution.py --fix` on the PR branch (bot/noreply emails auto-exempt). First filing from a fresh git identity will trip this; budget one extra push.
- **R20 — Issue-linking keywords:** `Fixes #N` closes on merge — use only when the PR fully settles the issue. `Refs #N` (or "Linked issue: #N") for partial/anchor relationships, e.g. where the design decision is the maintainers' call. House law (REFS-vs-FIXES amendment, mprov maint directive mirrored): feature PRs against an anchor issue default to `Refs`.
- **R21 — One logical change per PR.** [C] §Before submitting #5: *"Keep PRs focused: One logical change per PR. Don't mix a bug fix with a refactor with a new feature."* [PRT] checklist: *"My PR contains **only** changes related to this fix/feature."*

## 5. Tests, CI, and what must be green

- **R22 — Run locally with CI's own runners** before filing: `scripts/run_tests.sh` ([C]: *"use `scripts/run_tests.sh` for the same environment and per-file isolation as CI"*) and `python scripts/check` (*"runs every blocking lint check CI runs, with the same pinned tools"* — [LINT] header). Manual smoke: *"Run `hermes` and exercise the code path you changed"*. Cross-platform diff: `scripts/check-windows-footguns.py` ([C] §Cross-Platform: *"CI runs it on every PR too"*).
- **R23 — Effective CI = the `CI` orchestrator (`ci.yaml`)**. It classifies the diff (`detect-changes`) and calls lane sub-workflows (tests, tests-os, lint, supply-chain, e2e…); *"A final `all-checks-pass` gate job aggregates results so branch protection only needs to require a single check"* ([CI]). Practical rule: **the `CI` aggregate must be green on the PR head**; lane skips by the classifier are normal, lane *failures* block. E2E lanes never run on PRs ([CI] gate-lanes forces e2e off for `pull_request`) — don't claim E2E results as PR gates.
- **R24 — Blocking lint = `ruff check .` (enforced ruleset, currently `PLW1514`) + the code-health ratchet** ([LINT]): new functions ≤ cyclomatic complexity 20, ≤ 300 lines, nesting ≤ 6; files ≤ 2,000 lines and already-over files may only shrink; pattern rules (blind `except Exception`, missing timeouts, hardcoded `~/.hermes`, new `HERMES_*` env vars) block *new* instances ([C] §Code style "Code health ratchet").
- **R25 — CODEOWNERS review is a hard gate, not a CI job.** [OWN]: paths needing `@NousResearch/hermes-agent-core` approval include `.github/`, `scripts/ci/`, `scripts/check`, `scripts/code_health/`, prompt-surface fixtures, eslint configs, `optional-mcps/`, `setup.py`/`sitecustomize.py`/`*.pth`, `pyproject.toml`, `package.json`, lockfiles, `*Dockerfile`, `.npmrc`, `pm/lock.json`, the installers, and `SECURITY.md`. *"Require review from Code Owners"* is ruleset-enforced. Rule: if your diff touches any of these, expect maintainer review latency and pre-flag it in the PR body.
- **R26 — Dependency rules are review-blocking.** Every new PyPI dep: `>=floor,<next_major` ceiling (*"PRs adding unbounded `>=X.Y.Z` specs will be rejected"*); pre-1.0 packages: `<0.(minor+2)` window. Git URLs pinned to full SHA; GitHub Actions pinned to SHA + version comment; `supply-chain-audit.yml` flags manifest changes for manual review ([C] §Dependency pinning policy).
- **R27 — Generated artifacts must be regenerated in-PR:** icons (`node scripts/generate-icons.mjs`) — *"Generated outputs are committed and CI fails if they are stale"*; lockfiles via PM/uv (never raw pip/uv into a PM env, [C] §Manual development).
- **R27b — Rebase + red-first invariant tests.** [AGT] §Commits and PRs: *"rebase onto `main` before merging"* ("a squash from a stale branch silently reverts newer fixes") and *"1–2 invariant tests per fix, proven red on the base"* (fetched 2026-10-30T16:03Z). Every fix PR rebases onto `main` at submit time; every bug fix carries 1–2 tests that fail on the base and pass with the fix.
- **R27c — Test runner is `scripts/run_tests.sh`, not bare `pytest`.** [AGT] §Tests: *"always `scripts/run_tests.sh`, never bare `pytest`"*; host-specific behaviour uses `@pytest.mark.platforms(...)` (*"never by faking `sys.platform`"*); *"tests never write to `~/.hermes/`"* (fetched 2026-10-30T16:03Z). Behaviour-contract tests, never change-detector or source-reading tests ([AGT] §Tests; `tests/AGENTS.md` for full placement rules).
- **R27d — Contribution rubric: rejected-even-when-well-built (9 items).** [AGT] §Contribution rubric: *"Rejected even when well-built: hooks with no concrete consumer; new `HERMES_*` env vars for non-secret config (`.env` is secrets only, behaviour goes in `config.yaml`); a new core tool when terminal + file or a skill already does the job; `offset`/`limit` pagination on instructional tools; "fixes" that destroy the feature they secure; outbound telemetry without an opt-in gate; change-detector tests; plugins that touch core files; third-party products in the core tree (ship a standalone plugin repo)".* (fetched 2026-10-30T16:03Z; long form in `website/docs/developer-guide/contributing.md` §Contribution rubric). Do not file these; a PR in these categories will be closed regardless of quality.
- **R27e — Area AGENTS.md routing.** [AGT] §Routing Table — *"working in X → read X/AGENTS.md"*: each area's `AGENTS.md` loads automatically when you work in that directory; read it before editing there (fetched 2026-10-30T16:03Z). If the diff touches `agent/`, `hermes_cli/`, `gateway/`, `tools/`, `plugins/`, `skills/`, `tests/`, `pm/`, etc., read that area's `AGENTS.md` first.
- **R27f — Security-sensitive code: note in PR description + four coding rules.** [C] §When contributing security-sensitive code (~lines 909–917): *"If your PR affects security, note it explicitly in the description."* plus the four coding rules: always `shlex.quote()` when interpolating user input into shell commands; resolve symlinks with `os.path.realpath()` before path-based access-control checks; never log secrets (API keys, tokens, passwords); catch broad exceptions around tool execution so a single failure doesn't crash the agent loop (fetched 2026-10-30T16:03Z).

## 6. Scope & size expectations

- **R28 — Contribution priority order** ([C] §Contribution Priorities): 1 bug fixes (always top), 2 cross-platform, 3 security hardening, 4 performance/robustness, 5 new broadly-useful skills, 6 new tools (*"rarely needed. Most capabilities should be skills"*), 7 docs. A tool PR without a skill-not-tool argument is out of priority order and will feel it at review.
- **R29 — Skill-size targets** ([C] §HARDLINE #5): ~200 lines complex / ~100 simple; description ≤ 60 chars one sentence ending in a period; body section order `When to Use / Prerequisites / How to Run / Quick Reference / Procedure / Pitfalls / Verification`; tests at `tests/skills/test_<skill>_skill.py`, stdlib+pytest only, no live network; scripts/references/templates in their dirs; `.env.example` edits isolated to a delimited block.
- **R30 — Feature-request scope honesty:** the [FEAT] Scope dropdown (Small <50 / Medium <300 / Large) is our own sizing vocabulary too — put the diffstat in the PR body early (our #143372 pattern: `4 files changed, 319 insertions(+), 1 deletion(-)` with the test/impl split called out).

## 7. Repro/requirements for bug reports (beyond R10)

- **R31 — Repro is minimal and dated to a commit.** [SEC] §1 pattern generalizes: *"A reproduction against `main` or the latest release"* + `hermes --version` + commit SHA + OS + Python. [BUG] template additionally demands confirmation on latest (`hermes update`).
- **R32 — Cross-platform hazard claims name the platform matrix tested** ([C] §Cross-Platform 15 rules are the reviewer checklist — `os.kill(pid,0)`, `shutil.which`, encoding, signals, path separators, OneDrive paths, CRLF, …). A "works everywhere" claim without a matrix is a FAIL box.

## 8. Conduct, tone, persona

- **R33 — No conduct document upstream; house law governs conduct:** G-07 Comms Law (operator persona, no internal specifics, human brevity) and G-06 (distiller PASS + operator GO on the exact bytes before any agent submits). Upstream tone is informal-engineer ([C] opens *"A quick search before you build saves your time"*); match it — dense, factual, no ceremony.
- **R34 — Community escalation:** quick questions/feature evangelism → Discord `discord.gg/NousResearch` [C] §Community; issues stay for reproducible reports and scoped requests.

## 9. The hard DON'Ts

- **D1** — Never file a public issue/PR for a security vulnerability ([SEC] §1); never file a §3.2 out-of-scope item through the private channel either ([SEC] §3.2).
- **D2** — Never add a memory provider or third-party-product plugin to the core tree ([C] ×2; PR auto-closed with a pointer).
- **D3** — Never file an unbounded dependency (`>=X` with no ceiling) ([C] §Dependency pinning: *"will be rejected"*).
- **D4** — Never mix unrelated changes in one PR ([C], [PRT]).
- **D5** — Never leave `Fixes #` dangling on a PR that doesn't close its anchor, and never `Closes` an anchor issue whose decision belongs to maintainers (R20).
- **D6** — Never submit `Agent-Profile`/`Agent-Run` trailers, agent identifiers, card ids, board names, or fleet vocabulary into any upstream surface (G-07; upstream asks for nothing that would leak this).
- **D7** — Never let an agent submit without G-06: distiller `VERDICT: PASS` + operator GO on byte-matched sha256, submitted byte-exact by an agent, read back live.
- **D8** — Never mark a checklist box a lane did not run; never cite E2E/CI results not observed on the actual head SHA.
- **D9** — Never touch `SECURITY.md`, CODEOWNERS paths, or `.github/` casually (R25 — each is a core-owner review tax).
- **D10** — Never file duplicates, and never compete with an open PR without engaging it first ([C] §Before You Start).

## 10. Review SLA norms

- **R35 — No published SLA upstream — not specified upstream** (measured: no SLA text in [C], workflows, or docs site). Observed from our live pair: issue #143206 (2026-10-22) and PR #143372 sat ~8 days to 2026-10-30 with labels applied (`comp/*`, `P2`) but no maintainer comment. Norm we operate to: label-driven triage is the signal; no ping before **14 days**; at 14d+ a single polite comment max; competing-PR pressure is worse than waiting (R8/D10). Silence ≠ rejection: 7 sibling PRs sit open on the same feature.

---

*Every rule above is traceable to §0. Where a category is "not specified upstream," the rule is either a measurement of absence (DCO, CoC, AI policy, SLA) or house law cited by its G-nn key. Refresh discipline: re-fetch [C]/[PRT]/templates whenever a filing is drafted and the last capture is >30 days old; a changed template invalidates the skill's checklist verbatim.*
