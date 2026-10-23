# ADR-0003: Redevelopment stack — Python-first, harvest-forward, single-process web app

**Status:** Accepted (operator decision D1, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction) · sw-architect (formulation) · Card: METATRON-ARCH-1 (t_77ba5a4b)
**Supersedes:** none. **Series note:** ADR-0001 (project = directory) and ADR-0002 (revision-store semantics) remain canonical on the legacy repo's v2 branch (@b2c1a5b); the rewrite repo re-seeds them at P0 with lineage cited. This series continues their numbering to preserve cross-references.

## Context

The operator directed a full redevelopment from the foundational concept (greenfield codebase, name `metatron` retained). Three source lines were reviewed (R1 master@811e335, R2 v2@b2c1a5b, R3 feature/gui-editor@838f88c); none is a fork candidate, but each holds harvest assets. The durable assets are overwhelmingly **Python or protocol-level**: `message_normalize.py` (dual OpenAI/Anthropic shape validation), research clients, SQLite-only RAG (sqlite-vec), the citation stack shape, the v2 RevisionStore semantics (the only *tested* attribution-correct implementation), console UX — plus gui-editor's reusable artifacts, which are **protocol-level, not code** (gateway WS envelope protocol, suggestion-set model, edit-op vocabulary). METATRON-ARCH-BRIEF §4 sets out the full tradeoffs.

## Decision

**Option A: Python-first monorepo, single-process web app, harvest-forward.**

- Python 3.12+, `uv` packaging, distributed on PyPI under the reserved name `metatron`.
- One FastAPI process serving (a) the WS gateway (harvested gui-editor protocol: hello → replay-then-live, busy, 4401) and (b) the built SPA as static files — **one process, one port, one token, loopback by default**.
- Typer CLI for console parity, in-process against the same engine.
- Front end: pnpm workspace; BlockNote/React editor (versions locked per R3's green build: BlockNote 0.54.x / React 19 / TS 5.9 / vite 7; MPL-2.0 cleared by the permanent-OSS decision d096bbf/2f34532), run **non-collaboratively** — no Yjs, no Hocuspocus (ADR-0004).
- Repo private during redevelopment; MIT + permanently open source on any future public cut.

## Alternatives rejected

- **Option B — TypeScript clean-slate full-stack:** buys one language by discarding the proven Python harvest exactly on the hard parts (revisioning correctness, trust gate, RAG, citation machinery) and re-implementing them against thinner TS libraries with zero carried tests. Single-language is a benefit on the *easy* part (build system), paid on the *hard* part (correctness). Violates the evidence: the repo's durable asset is its Python component catalog.
- **Rebase/rework the existing repo (operator's "perhaps rebasing metatron" alternative):** every line carries structural defects — master has 4 overlapping orchestration paths (R1); v2 is 49 commits stale with a live tar CVE and an *introduced* `.env` S1; gui-editor never ran CI and its test suite cannot fail (R3). Harvesting beats rebasing on every axis the registers measured.

## Consequences

- Two languages in one repo → CI gate runs BOTH suites on every branch, and must be able to signal red (exit-0 masks are a P0-rejected defect class).
- Python packaging tests are a P1 exit criterion (GUI-016 class: runtime deps trapped in dev extras must be impossible).
- BlockNote is a 0.x moving target → version-pinning policy from day one; upgrades are deliberate cards.
- FastAPI/uvicorn are *runtime* dependencies, exercised by the packaging test.

## Revisit when (falsifier)

- Two consecutive harvest attempts in P1/P2 need >30% rework — that falsifies the portability premise of the harvest-forward stance.
- A Python-side blocker forces non-Python infrastructure for a core subsystem (not the front end, which is expected to be TS).
