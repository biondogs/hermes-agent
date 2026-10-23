# Metatron — Intake Inventory (METATRON-0-INTAKE, kanban t_cef0727b)

Compiled 2026-10-23 by sw-pm. All facts verified live via git/gh on
`/local/projects/metatron` (origin = https://github.com/biondogs/metatron,
private fork, sole plausible "metatron" repo: `gh repo list biondogs` and
`gh search repos metatron --owner biondogs` return exactly one hit; no other
metatron dir under /local/projects apart from `metagpt*` which is unrelated;
zero references in software-co management repo before this intake).

## 1. Repo facts

- Single remote: `origin → github.com/biondogs/metatron` (HTTPS w/ token, private).
- Default branch: `master`. **No tags exist** — v0.x "versions" live only in
  `pyproject.toml` / CHANGELOG.
- Size: 4.0 MB `.git` (1.56 MiB pack). Master: 251 `.py` files ≈ 1.5 MB,
  36 `.md`, 126 test files, CI (.github/workflows/ci.yml: ruff/mypy/pytest
  unit+e2e/coverage gate/Docker, Python 3.11–3.13), Dockerfile + compose,
  MIT license, hatchling build, published-name `metatron` on PyPI (Publish
  job exists, currently skipped).
- History: root commit `effc861` "feat: initial scaffold for Metatron — AI
  agent harness for academic writing" 2026-06-05; master 160 commits, latest
  2026-09-21 (v0.4.0). PRs merged up to #82. 19 issues open (filed 2026-07-11
  by an automated review; several since fixed on master), 7 PRs open (#69 =
  the v2 merge proposal; rest dependabot).
- Working-copy caution: main checkout is parked on
  `dependabot/pip/production-8a961bab16` (open PR #29) with untracked
  operator files (`docs/metatron-board-templates.md`,
  `openwiki/operations/board-orchestration.md`, `.github/workflows/openwiki-update.yml`,
  `scripts/`); 2 stashes on old master; 6 worktrees incl. `.worktrees/`
  nested inside the clone (anti-pattern — charter §1 forbids adding more).
  During intake one index-only no-op (`git checkout origin/master -- .`)
  touched the main checkout's index; it was fully reverted with
  `git restore --stage --worktree -- .` (verified: no tracked modifications
  remain; pre-existing untracked files intact).

## 2. Branch inventory + health table

| Branch | Head | Last commit | Divergence vs master | CI (head) | Health verdict |
|---|---|---|---|---|---|
| master | 811e335 | 2026-09-21 | — | all green (lint/mypy/py3.11–3.13/e2e/docker) | VITAL — richest line, v0.4.0, active through Sept |
| v2 | b2c1a5b | 2026-07-23 | merge-base b4a55f2 (2026-07-11, dependabot #32): master +49, v2 +12; shared root effc861 | all green | STALE-BUT-LOAD-BEARING — 12 commits of design (ADRs, workspaces, revisioning) + PR #69 open unmerged 3 months |
| feature/gui-editor | 838f88c | 2026-09-22 | +11 ahead of master | none (no PR; CI only on master/PRs) | ACTIVE-LAST — newest commit in repo; GUI Phase 2 (Hocuspocus+BlockNote+gateway). Unmerged, no PR |
| feature/gui-dev | 5cce9c8 | 2026-09-21 | +4 (contained in gui-editor) | none | SUPERSEDED by gui-editor |
| fix/mypy-numpy2-pep695 | (local+remote) | 2026-08-12 | pre-merge-base fork, ~3 weeks stale | — | STALE |
| fix/e2e-ansi-color-codes | (remote) | 2026-07-23 | fixed-on-master via b2c1a5b-line/#70 | — | LIKELY OBSOLETE |
| feature/llm-sdk-enhancements | (remote) | 2026-07-10 | pre-merge-base | — | STALE |
| feature/parallel-agent-execution | (remote) | 2026-07-11 | pre-merge-base, long merged-in-spirit per ROADMAP | — | OBSOLETE |
| dependabot/* (5 open PR branches) | — | Jul | — | mixed | PR #29 open since 2026-07-11 (12 prod bumps) — dep debt |

**Operator's "v1 and v2":** they are BRANCHES in the one repo, not tags or
repos. "v1" is not a branch name — `master` is the only v1 candidate (v0.4.0);
operator confirmed this reading via Q1 answers (see OPERATOR-DIRECTION.md).
`v2` is a real branch with its own design docs and an open PR #69 (kept as
source material, not merged). The *newest* work (GUI Phase 2) lives on neither
— it is on `feature/gui-editor`, operator-confirmed IN scope (Q1).

## 3. Foundational concept (with sources)

**What Metatron is meant to be** — `README.md` (master), line 3 + §intro:
> "Multi-agent AI harness for academic research and writing. … end-to-end
> support for the academic writing workflow — from literature research to
> final evaluation — through a configurable pipeline of 12 specialized AI
> agents."

`pyproject.toml` description: "AI agent harness for academic writing —
multi-agent pipeline for research, drafting, review, and citation."

**v1 concept (master line)** — `docs/ARCHITECTURE.md`: pipeline-of-agents
harness: CLI(Typer)/TUI → security layer (PII redaction, injection detect) →
profile system → orchestrator → 11–12 agents (Researcher, Drafter, Reviewer,
Citer, LiteratureAnalyst, Synthesizer, Evaluator, RAGAgent, Orchestrator,
Outline, Finalize) over research APIs (ArXiv/Crossref/S2/PubMed/Scholar),
RAG backends (in-memory/SQLite/Chroma/Qdrant), exporters (PDF/DOCX/MD/LaTeX),
REST API, plugin/skill systems. v0.4.0 added the workflow-driven Console TUI
(9-phase state machine INIT→…→DONE, checkpoints, `metatron serve` browser
mode, typed AgentEvent bus) — `CHANGELOG.md` v0.4.0, `docs/dev/EVENT-BUS.md`,
`docs/plans/2026-09-21-ui-redesign.md`.

**v2 concept (the rethinking)** — `docs/feature-requests/research-lifecycle-v2.md`
(v2 branch, "How Humans Actually Conduct Research and Write Academically"):
the v1 fixed-order pipeline is the wrong shape for research — research is
recursive; v1 has "no back-edge support, no decision log, and no cyclic state
machine" (§0.1.1), and citation verification is existence-checking, not
claim-support checking (§0.1.2). Companion: `docs/research-lifecycle-report.md`,
`docs/plans/2026-07-13-ux-replan-full-lifecycle.md`, writing-voice-profile spec.
**ADRs** (v2 branch): `docs/adr/0001` — a project is a DIRECTORY
(`~/.metatron/projects/<name>/`), outline+sections are plain Markdown files,
per-project library/RAG/sessions/decision-log; `docs/adr/0002` — git-backed
revision store for drafts (history/diff/rollback/checkpoints without git
knowledge). Implemented partially in the 12 v2 commits (`dbb542f feat: project
workspaces with git-backed draft revisioning`).

**GUI direction (post-v0.4.0)** — `docs/research/2026-09-21-gui-canvas-editor-research.md`
+ commits 2f34532/d096bbf (permanently open source; BlockNote XL cleared):
single-user product / multi-user substrate (Yjs+Hocuspocus day one).
`feature/gui-editor` implements Phase 2: FastAPI WS gateway speaking the
AgentEvent contract, agents as document authors with presence/streaming
edits/suggestion-sets, BlockNote editor UI.

**Seed defects that motivated v2** (open since 2026-07-11, still open unless
noted): #57 stage metadata bleed, #42 unauthenticated REST API, #51 sanitizer
not wired to server, #33 SQL-injection in SQLiteVectorStore, #44 vector-store
resource leaks, #38 subagent stub, #49 non-deterministic embeddings. Fixed on
master since: BibTeX/LaTeX escaping (#74/#56 equivalents), safe-tar (#28 via
6aac261), CLI provider settings (#72), delegation contract (#58).

## 4. Review-phase receipts index

- Charter: `metatron/REVIEW-CHARTER.md` (this dir), commit sha in card handoff.
- Operator direction: `metatron/OPERATOR-DIRECTION.md` (this dir) — locked
  Q1–Q8 decisions, 2026-10-23.
- "v1 and v2" RESOLVED by operator (Q1–Q3): master = v1 line, `v2` branch =
  v2 line, `feature/gui-editor` IN scope as third source; all three are
  down-selection material for a greenfield rewrite (name `metatron` kept).
- Reviewer label set: never to be created — Q7=c closed the filing gate as
  moot; registers feed the rewrite backlog directly.
