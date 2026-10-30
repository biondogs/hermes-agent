---
name: upstream-hermes-filing
description: "Use when filing anything to github.com/NousResearch/hermes-agent (issue, PR, comment, review reply). Mechanical pre-filing checklist from the doctrine doc; every box checkable; uncheckable = block, don't file."
version: 1.0.0
author: sw-docs (card t_1a63e305)
license: MIT
metadata:
  hermes:
    tags: [github, upstream, hermes-agent, filing, compliance, gate]
    related_skills: [kanban-distiller-gate, butler-blocked-decision-prompt, strip-agent-trailers-public-commits]
---

# Upstream hermes-agent filing checklist

Executable enforcement copy. The rules, rationale, and citations live in the doctrine
doc of record — **do not restate or edit rules here**; only edit when a *check* changes:

- Doctrine (rules R1–R35 + R27b–f, D1–D10, citations): `/local/projects/software-co/docs/UPSTREAM-HERMES-FILING-2026-10-30.md`
- Ruling of record: **G-34** in `~/hermes-estate/docs/GOVERNANCE.md`
- Estate law that still gates every submission: **G-06** (distiller PASS + operator GO, byte-exact agent submit) and **G-07** (com persona, no internal specifics).

Upstream = `github.com/NousResearch/hermes-agent`, fork owner `biondogs`, base branch `main`.
Sources were captured 2026-10-30T15:45Z. **If the last capture is >30 days old, re-fetch**
`CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and the three issue-template YAMLs
(raw.githubusercontent `main`) and diff against the doctrine doc's §0 before checking any box.

## When to use

Any card whose output crosses to the hermes-agent upstream: new issue, issue edit, new PR,
PR body/title edit, PR/issue comment, review reply. Force-load in the filing card body
(`skills: [upstream-hermes-filing]`).

## Gate rule (last line is also the first)

**If any box below is uncheckable — evidence missing, field inapplicable-and-mandated,
capture stale, GO absent — `kanban_block(kind="needs_input")` with the box id and what's
missing. Never file past an uncheckable box. "N/A" is legal only where this checklist says
"(or N/A)" and requires a one-line reason on the card.**

## Section A — routing (doctrine R1–R9)

- [ ] **A1** Artifact type chosen by route table: security vuln in [SEC] §3.1 scope → GHSA private channel, NOT a public artifact (D1); bug → `[Bug]:` template; feature → `[Feature]:` template; install trouble → `[Setup]:`; design debate → Discussions/Discord, not an issue (R5).
- [ ] **A2** Out-of-scope security-adjacent item (heuristic bypass, prompt-injection-per-se, posture consequence, break-glass flag, third-party skill/plugin bug) is being filed as a *regular* issue/PR — checked against [SEC] §3.2 list (R1).
- [ ] **A3** Proposal is NOT a new memory provider, NOT a third-party-product plugin, NOT a niche bundled skill — those are standalone repo / catalog YAML / Skills Hub respectively (D2/R7). Evidence: `gh search prs --repo NousResearch/hermes-agent --state all <terms>` + open-and-merged duplicate search run, links pasted on the card (R8/D10).
- [ ] **A4** Source check done: capability not already in-tree (`search_files` on the hermes-agent checkout) — tracker lags code (R8).

## Section B — issue body (R10–R13)

- [ ] **B1** Every `required: true` field of the matching template filled (bug: Description / Steps to Reproduce / Expected / Actual / Affected Component / Debug Report / OS; feature: Problem / Proposed Solution / Feature Type). Screenshot or body paste proves it.
- [ ] **B2** Debug Report content is authored-and-scrubbed by a lane (no raw ga01 paste without distiller pass — R12); sanitized `--local` paste acceptable.
- [ ] **B3** Title prefix exact (`[Bug]:` / `[Feature]:` / `[Setup]:`); body mirrors template section order even if blank-filed (R13).
- [ ] **B4** Reproduction pins version + commit + OS + Python and confirms against latest (R31).

## Section C — PR body & commits (R14–R21)

- [ ] **C1** Body byte-follows `.github/PULL_REQUEST_TEMPLATE.md` headings in order (What / Related Issue / Type of Change / Changes Made / How to Test / Checklist / For New Skills / Screenshots). "For New Skills" deleted unless adding a skill.
- [ ] **C2** Type of Change: exactly one box.
- [ ] **C3** Every checklist box either ticked with evidence on the card or left unchecked with a one-line reason in the body — no unrun assertions (R15/D8).
- [ ] **C4** Title `type(scope): …` Conventional Commits (code PRs).
- [ ] **C5** Branch `fix/|feat/|docs/|test/|refactor/…` on biondogs fork, base `main` (R17).
- [ ] **C6** Issue link keyword correct: `Fixes #N` only on full closure; `Refs`/anchor wording otherwise (R20/D5).
- [ ] **C7** Diff is one logical change; `git log -p origin/main..HEAD` reviewed for unrelated hunks (R21/D4).
- [ ] **C8** Commit author/email maps to `contributors/emails/` or a `+login@users.noreply.github.com` form, else the mapping fix commit is in the PR (`scripts/audit_pr_attribution.py --fix`) (R19).
- [ ] **C9** No `Signed-off-by` (no DCO upstream), no AI-disclosure trailer, no `Agent-Profile`/`Agent-Run` trailers: `git log --format=%B origin/main..HEAD | grep -Ei 'signed-off|agent-profile|agent-run'` → empty (R19/D6; skill `strip-agent-trailers-public-commits` env-gate: commit with `env -u HERMES_KANBAN_TASK -u HERMES_SESSION_SOURCE -u HERMES_KANBAN_WORKSPACE`).

## Section D — CI/quality claims (R22–R27f)

- [ ] **D1x** `scripts/run_tests.sh` green locally (relevant subset ok, full-suite baseline noted) — never bare `pytest` (R27c); host-specific tests use `@pytest.mark.platforms(...)`, never faked `sys.platform`
- [ ] **D1y** Red-first invariant tests: 1–2 tests per fix that are proven red on the base and green with the fix; PR rebased onto `main` before filing (R27b)
- [ ] **D2x** `python scripts/check` green (blocking lint + code-health ratchet; new-code caps: cc≤20, fn≤300, nest≤6, file≤2000 & never grows).
- [ ] **D3x** `scripts/check-windows-footguns.py` clean on the diff; platform tested named in body (R32).
- [ ] **D4x** New PyPI deps carry `<next_major` (pre-1.0: `<0.minor+2`); git deps SHA-pinned; actions SHA-pinned+commented; no raw pip/uv into PM envs (D3).
- [ ] **D5x** Generated artifacts regenerated (icons, lockfiles) in-PR (R27).
- [ ] **D6x** Diff touches no CODEOWNERS path (`.github/`, `scripts/ci/`, `scripts/check`, `scripts/code_health/`, prompt-surface fixtures, eslint/prettier, `optional-mcps/`, `setup.py`/`*.pth`, manifests/lockfiles, Dockerfiles, `.npmrc`, installers, `SECURITY.md`) — or the review tax is pre-flagged in the body (R25).
- [ ] **D7x** Contribution not in rejected-even-when-well-built set (hooks w/o consumer, new `HERMES_*` env var for non-secret config, new core tool where terminal+file/skill suffices, `offset`/`limit` pagination on instructional tools, "fixes" that destroy the feature they secure, outbound telemetry w/o opt-in gate, change-detector tests, plugin touching core, third-party product in core tree; full set at [AGT] §Contribution rubric — check all of it, not just these) (R27d)
- [ ] **D8x** Area `AGENTS.md` read for every area the diff touches (routing table [AGT]); `AGENTS.md` chain ≤30k chars respected (R27e)
- [ ] **D9x** Security-sensitive PR: `shlex.quote`/`realpath`/no-secret-logs/broad-exception-guard applied (R27f) AND PR description notes security impact explicitly (*\"If your PR affects security, note it explicitly in the description\"* — [C] 909–917) — or N/A with one-line reason (not security-sensitive)

## Section E — disclosure & hygiene (G-06/G-07 + D6–D9)

- [ ] **E1** No internal specifics anywhere in the artifact: no card ids, board/lane/gate names, fleet vocabulary, host names. Grep the exact final bytes: `grep -Ei 'kanban|t_[0-9a-f]{8}|butler|distiller|ga01|sw-dev|software-co' draft.md` → clean (G-07).
- [ ] **E2** Upstream-internal vocabulary stays upstream's own (issue numbers of *their* repo are fine; ours never appear).
- [ ] **E3** Distiller `VERDICT: PASS` recorded on the card against the sha256 of the final bytes: `sha256sum` of the exact submit payload, matched to the PASS sha (G-06).
- [ ] **E4** `OPERATOR GO` comment present on the submit card AND its bytes sha-match E3's payload. External public surface → gate applies; do not confuse with internal-repo flow (G-06).
- [ ] **E5** Submit is executed by an AGENT byte-exact (never hand the command to the operator), and the filed artifact is read back live (`gh issue/pr view`) and byte-compared to the approved payload before the card completes.

## Section F — after filing

- [ ] **F1** CI aggregate `CI` observed on the head SHA (fork PRs park at `action_required` until a maintainer approves runs — that is NOT our failure; record the state, don't re-push).
- [ ] **F2** Watch armed: no ping before 14 days (R35); a watch cron/card created, not a reminder in prose.

## Terminal rule

Any uncheckable box → `kanban_block(kind="needs_input", reason="upstream-hermes-filing box <ID> uncheckable: <what/why>")`. The block comment carries the box id and the missing artifact; unblock only when the artifact exists. Filing past an uncheckable box is a doctrine violation on the same plane as filing without GO.
