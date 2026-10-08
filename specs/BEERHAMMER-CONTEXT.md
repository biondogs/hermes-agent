# BEERHAMMER-CONTEXT — Spin-up Context Pass

- Card: BH-CTX (t_c170c3d8) · Author: sw-pm · Date: 2026-10-08
- Upstream: https://github.com/fatpat81/BeerHammer (owner `fatpat81`; top contributor `biondogs`)
- Local clone: `/local/projects/beerhammer` @ `36f00f2` == `origin/main` (tree clean; remote is fatpat's — **never push**)
- Inputs read: README.md, AGENTS.md, docs/{DEV_NOTES,DEV_ENVIRONMENT,DEPLOYMENT,API}.md, git log -40, live `gh issue/pr list` + `gh api` (READ ONLY), `/local/projects/beerhammer-qa/{SMOKE-REPORT.md,ARCHITECTURE.md}` (QA repo @ `c83fe3f`).

---

## 1. What the product is + architecture one-pager

**ForceOrg-40k / BeerHammer** — tournament-grade Warhammer 40,000 **11th Edition**
force builder + tabletop battle console. Self-hosted by design: one Docker host runs
everything; no managed cloud dependency (Supabase is a dead legacy stub).

**Monorepo** (Turborepo + npm workspaces, Node 20 pin, `npm@10.8.0`):

| Component | Path | Stack |
|---|---|---|
| Web | `apps/web` | Next.js 14 App Router; pages `/`, `/catalog`, `/changelog`, `/login`, `/army/[id](/edit)` |
| API | `apps/api` | Express 4, helmet/CORS/rate-limit 300·15min⁻¹·IP⁻¹; routes: datasheets, rosters, media, audit, changelog; `:4000` |
| Sync worker | `apps/sync-worker` | Wahapedia ETL one-shot (cron via GH Action); behind compose `profiles: ['tools']`, non-hermetic |
| Rules engine | `packages/rules-engine-11e` | 11e AST wargear compiler + compliance auditor; **only package with unit tests** (vitest) |
| DB client | `packages/db-client` | Prisma schema (13 models), migration, seed |
| Shared | `packages/types`, `packages/ui-theme` | TS types; faction CSS system |

**Auth model:** guest-first (any callsign, localStorage persistence per callsign, transparent
fallback when API offline) + JWT HS256 (`JWT_SECRET`) for API writes; reads public.

**Data:** pinned BSData/wh40k-11e snapshot in `data/bsdata/` (~47 MB) → `scripts/extract-factions.js`
→ per-faction JSONs served by web; PostgreSQL 16 + SeaweedFS S3 (miniature photos); sync-worker
scrapes wahapedia.ru advisory cross-reference (BSData is primary authority per `1ac8ffe`).

**Three compose shapes:** `docker-compose.dev.yml` (hot-reload workbench, project `forceorg-dev`,
`${WEB_PORT}/${API_PORT}` overridable), `docker-compose.yml` (source build), `docker-compose.prod.yml`
(GHCR pull-based, placeholder test creds). `scripts/dev.sh` is the sanctioned one-command harness.

**CI (GitHub, push to main):** Production Deployment Pipeline (lint+coverage+build → GHCR images),
Playwright E2E (5-test guest suite, **no API/DB in the job** — proves localStorage fallback),
daily Wahapedia ETL cron, OpenWiki wiki refresh. `.gitlab-ci.yml` mirrors tests (secondary).

## 2. Roadmap: as stated vs as-practiced

**As stated:** there is **no roadmap/plan file in the repo** (no ROADMAP.md, no backlog docs;
grep over docs/*.md found none). The stated direction lives in README/DEPLOYMENT: complete
self-hosted story, API as the only integration surface, pinned-snapshot dev/test vs live-source
release policy, guest-first usability. AGENTS.md is OpenWiki boilerplate only (just-in-time wiki
use, source/tests authoritative, no hand-editing generated pages).

**As-practiced (last 40 commits, reconciled):** a clear sprint arc, Oct 5→7, 2026:
1. **Self-hosted migration COMPLETE** (PR #1 merged `6142c86`): Supabase fully removed from
   compose/env/docs, guest local-persistence auth, deployment docs rewritten.
2. **Containerization COMPLETE**: dev workbench (`c130c0a`), self-migrating API image,
   sync-worker image + compose service, prod pull-based path, CI unbroken.
3. **Data layer COMPLETE**: full 11e datasheets/weapons/rules/stratagems for all factions,
   BSData-as-primary policy + schema verification, all 27 canonical factions + subfaction
   inheritance + Combat Patrol (`67aa392`, `1ac8ffe`, `0bf583f`).
4. **Battle Mode ACTIVE surface** (newest, still moving): distinct edit vs battle mode,
   phase-adaptive datacards, CP generator (`333ced1`), detachment switcher + DP banner
   (`581910f`), E2E updated for battle mode + detachment DP costs (`36f00f2`, HEAD).

**Reconciliation verdict:** practice has run *ahead of* the docs — README/docs match the
self-hosted architecture but do not mention Battle Mode depth or the faction rollout; there is
no written plan to be stale, and no open upstream issues capturing future intent. Near-term
gravity is unambiguously Battle Mode + catalog correctness.

## 3. Open upstream issues table

**Verified via gh (2026-10-08): zero open issues.** `gh issue list --state all --limit 100`
returns nothing; `gh api repos/fatpat81/BeerHammer` → `open_issues_count: 0`, `has_issues: true`
(issues are enabled, just empty). PRs: only #1 (merged, the self-hosted epic).

| # | Title | Labels | Our read |
|---|-------|--------|----------|
| — | *(none open — the repo tracks no known defects; our punch-list §4 is currently the only defect inventory)* | — | — |

Implication: our findings have **no upstream home yet**. Publishing them (issues/PRs on
fatpat's repo) requires operator GO per this card's constraint; until then they are
report-draft territory + local fixes.

## 4. Our punch-list status (QA @ first run 36f00f2 → rerun verdicts)

QA history: first smoke run red on leg 3 (API dead-in-container), fixed via BH-ENVFIX
(workspace build inside toolchain), rerun green. **Cumulative: 6 PASS / 1 N/A / 0 FAIL**
(QA repo commit `c83fe3f`; env left standing at ga01:13000/14000).

Original 5-item list (first run), status after rerun:

| # | Item | Status after rerun |
|---|------|--------------------|
| 1 | **P0** fresh-clone wall: `dev.sh up` boots API that crashes `MODULE_NOT_FOUND @forceorg/db-client/dist` until workspace packages are built once (dev compose assumes prior build; `npm ci` links, doesn't build) | **Environmentally fixed on our box** (workspace build in toolchain, turbo 7/7). **Upstream defect stands** — fresh clone still hits it. Upstream-report candidate #1. |
| 2 | **P1** false-green health: no HTTP healthcheck for api/web in dev compose; `docker ps` Up + port-poll PASS while app dead (docker-proxy listens regardless) | **Open, upstream-report candidate #2.** qa-side mitigation exists (poller HTTP check correctly FAILed). |
| 3 | **P2** `/favicon.ico` 404 on web | **Open (cosmetic).** Upstream-report candidate #3; trivial fix. |
| 4 | **P3** suspected data-nulling on `PUT /api/rosters/:id` (unguarded `detachmentSecondary`/`factionThemeOverride`) | **REFUTED as suspected** (rerun: omitted fields arrive `undefined`, Prisma skips them → preserved). **Refined finding stands:** explicit-`null` PUT clears only the two unguarded nullable fields; PATCH/PUT semantics asymmetry at rosters.ts L109-114 = low-priority consistency wart. Upstream-report candidate #4a. |
| 5 | **P4** non-fatal inherited: @supabase/* EBADENGINE warns (legacy stub), multer/deprecation warnings, `seaweedfs:latest` unpinned in dev compose (prod pins 3.80) | **Open, low.** Hygiene; report-annex material. |

New from rerun (add to inventory):

| # | Item | Status |
|---|------|--------|
| 6 | **P2-new** malformed (non-UUID) roster id → 500 `DB_ERROR` not 400 (no route-level id validation; P2023 reaches client class) | **Open.** Upstream-report candidate #4b. Good first code-fix. |
| 7 | Status-code flattening: any Prisma error on roster routes → 500; no input-fault vs server-fault split | **Open (info).** Companion to #6. |

**Consolidated upstream-report candidates = the 4 items in SMOKE-REPORT's final section**
(fresh-clone wall / healthcheck gap / favicon / PUT asymmetry + id-validation gap). We do NOT
patch their repo without operator GO.

## 5. Dev-readiness checklist

- [x] **Local clone**: `/local/projects/beerhammer` @ `36f00f2` == `origin/main`, clean. Remote = fatpat's; **never push.**
- [x] **Live env already up** (operator decides teardown): UI `http://ga01:13000`, API `:14000/api/health` green, S3 `:19000/19333`. QA stack bring-up uses overrides OUTSIDE the repo: `-f docker-compose.dev.yml -f /local/projects/beerhammer-qa/overrides/compose-ports.override.yml --env-file overrides/.env` with `WEB_PORT=13000 API_PORT=14000` (host ports 3000/4000 collide with obsidian/litellm on ga01).
- [x] **Harness**: `./scripts/dev.sh up|down|verify|test|e2e-install|e2e|logs <svc>|shell|psql` — the sanctioned entry point (docs/DEV_ENVIRONMENT.md). `verify` = lint + build + unit tests in-container. **Remember P0:** after a fresh volume, run the workspace build once (`dev.sh shell` → `npm run build`, or the verify gate) before expecting the API to boot.
- [x] **Test commands** (repo root unless noted; from docs/DEV_NOTES §3 — AGENTS.md itself carries only OpenWiki conventions):
  - `npm run lint` (ESLint + tsc --noEmit, 11 workspaces) · `npm run build` (turbo 7/7) · `npm test` (vitest, 53 tests, rules-engine only)
  - E2E: `./scripts/dev.sh e2e-install` once, then `./scripts/dev.sh e2e` (5 guest tests, internal port 3456) — browsers live in a docker volume, never install onto host.
- [x] **JWT for write legs**: dev compose sets no `JWT_SECRET` → fallback `dev-secret-change-in-production` (auth.ts L8); mint in-container with jsonwebtoken. Prod default `please-change-me`.
- [x] **Data refresh**: `npm run data:extract` / `data:verify` for the pinned BSData snapshot; never hand-edit generated `apps/web/public/data/` output without extracting.
- [ ] **CI notes / watch items**: Production pipeline + E2E green @ `36f00f2`; **OpenWiki Update workflow failing** (2 consecutive: `581910f`, `36f00f2`) — upstream-owned, don't hand-edit `openwiki/`; **Wahapedia ETL flaky** (failed 10-07, succeeded 10-08) — flakiness is itself report-relevant.
- [ ] **Open owner-decision items upstream** (from DEV_NOTES §7, no LICENSE file; GitHub Pages serves raw repo root and can't run the SSR app; admin-only fixes).
- [ ] **Constraint reminders**: gh is READ-ONLY on fatpat's repo without operator GO; rate limit 300 req/15 min/IP; avoid host `npm install` (postinstall prisma fetch) — work in-container.

## 6. Recommended near-term development lanes

Ranked for sw-dev-a / sw-dev-b (final work-package scoping is BH-ARCH's job, t_67618ae2 —
lanes here are directional; every code lane is **fork-local branches only**, PRs gated on
operator GO):

1. **LANE-A — API robustness (ours-to-fix, smallest reviewable PRs).** Route-level UUID
   validation → 400 on `/api/rosters/:id` (kills P2-new), split Prisma error mapping so
   input faults aren't flattened to 500 (P7), optional: unify PUT semantics in rosters.ts
   L109-114 (P3-refined). Files: `apps/api/src/routes/rosters.ts`, shared validation helper,
   vitest/HTTP tests. Low risk, high report credibility.
2. **LANE-B — Dev-environment hardening (ours-to-fix upstream candidate #1/#2).** Make
   `dev.sh up` self-sufficient: build workspace packages before first api boot (or gate docs
   on `verify`), add HTTP healthchecks for api/web in docker-compose.dev.yml. Files:
   `scripts/dev*.sh`, `docker-compose.dev.yml`. Acceptance: fresh `down -v` + `up` →
   `/api/health` green with zero manual steps; `docker ps` never shows Up-while-dead.
3. **LANE-C — Upstream report pack (PM/architect + QA, no code).** Draft the 4-candidate
   report (each: repro command, expected vs actual, suggested fix) for operator review; on GO,
   file as upstream issues. Zero repo-write risk; unblocks fatpat fixing what we can't push.
4. **LANE-D — Catalog/data verification pass (support, feeds Battle Mode work).** Run
   `data:verify` across all 27 faction JSONs + Combat Patrol extractions, reconcile any
   weapon-characteristic gaps (cf. `caadd66` lineage); cheap, hermetic, catches regressions
   the daily-ETL flakiness could mask.
5. **Not lanes now:** favicon (fold into any web PR), sync-worker behavior changes
   (non-hermetic, out of hermetic-test scope), LICENSE/Pages (owner decisions, not ours).

---
*Handoff facts: `open_issue_count = 0`; punch-list = 5 original (1 env-fixed-open-upstream, 1 refuted→refined, 3 open-low) + 2 rerun findings; CI watch: OpenWiki failing, ETL flaky.*
