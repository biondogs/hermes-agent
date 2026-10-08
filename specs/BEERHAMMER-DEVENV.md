# BeerHammer Dev Environment (BEERHAMMER-DEVENV)

Owner: sw-devops · Card: t_b478aef3 · Verified live on ga01: 2026-10-08 (UTC)

## TL;DR

The dev environment for `/local/projects/beerhammer` (dev clone, upstream
fatpat81/BeerHammer — NEVER push, NEVER commit into it) is the stack that is
**already running** as `beerhammer-dev-*`. Inspection proved it bind-mounts
`/local/projects/beerhammer` directly (`com.docker.compose.project.working_dir
= /local/projects/beerhammer`, bind source = same path), so edits on the host
hot-reload into the running web/api. `/local/projects/beerhammer-qa` is NOT a
second code copy — it is an ops/evidence repo holding only the port-remap
override and runbook.

**Decision: REUSE the existing stack as the dev stack.** A second stack on
offset ports (13100/14100/…, audited free) would bind-mount the *same* source
dir and the *same* compose project (`forceorg-dev`) — compose forbids two
stacks sharing one project name/volume set without a fork, and the fork buys
nothing except divergence from what QA smokes. One stack, one truth.

**Shared-stack caveat (hotspot):** because this stack also answers
http://ga01:13000 for QA, any edit in the dev clone immediately changes what
QA sees. If a dev card needs isolation, see "Isolated dev stack (if ever
needed)" below — do not spin one up ad hoc.

## URLs & ports (all verified responding 2026-10-08)

| Service   | URL                          | Verified proof |
|-----------|------------------------------|----------------|
| Web (dev, hot reload) | http://ga01:13000 (host: localhost:13000) | HTTP 200, title `ForceOrg-40k — Warhammer 40K 11th Edition Army Builder` |
| API       | http://ga01:14000            | `GET /api/health` → `{"success":true,"data":{"status":"operational","version":"1.0.0"}}` |
| Postgres  | ga01:15432 (inside-net: `postgres:5432`) | `pg_isready` accepting; db `forceorg_dev`, 14 tables, seeded |
| S3 (SeaweedFS) | ga01:19000 (S3), ga01:19333 (UI/masters) | HTTP 200 on root |

DB query from host: `psql -h ga01 -p 15432 -U postgres -d forceorg_dev`
(or `docker exec beerhammer-dev-postgres psql -U postgres -d forceorg_dev -c ...`).

## Credentials location (never in this doc)

- Dev DB user/password: `docker-compose.dev.yml` in the beerhammer repo
  (committed dev-only defaults — that file is the location).
- Dev S3 keys: `api` service env in the same `docker-compose.dev.yml`.
- These are throwaway local-dev defaults from the upstream repo; no real
  secrets exist in this stack. Production credentials are elsewhere and this
  stack must never be pointed at them.

## Start / stop (exact commands, receipted)

Up (canonical, = beerhammer-qa RUNBOOK variant A; image `forceorg-dev:latest`
pre-built — add `--build` only if the image is missing):

```bash
export WEB_PORT=13000 API_PORT=14000
cd /local/projects/beerhammer
docker compose \
  -f docker-compose.dev.yml \
  -f /local/projects/beerhammer-qa/overrides/compose-ports.override.yml \
  --env-file /local/projects/beerhammer-qa/overrides/.env \
  up -d
```

Readiness (no blind sleeps): poll `curl -sf http://localhost:13000/`,
`curl -sf http://localhost:14000/api/health`,
`docker exec beerhammer-dev-postgres pg_isready -U postgres -d forceorg_dev`
— or run `bash /local/projects/beerhammer-qa/staging/verify-env.sh` (writes a
receipt JSON).

Stop (graceful — `down` sends SIGTERM first; kill -9 is forbidden unless
graceful demonstrably failed, receipted):

```bash
export WEB_PORT=13000 API_PORT=14000
cd /local/projects/beerhammer
docker compose \
  -f docker-compose.dev.yml \
  -f /local/projects/beerhammer-qa/overrides/compose-ports.override.yml \
  --env-file /local/projects/beerhammer-qa/overrides/.env \
  down
```

Teardown safety: containers carry `container_name: beerhammer-dev-*` AND label
`com.beerhammer.dev=1`; any teardown must select on BOTH. Volumes
(`forceorg-dev_dev_*`) survive `down` without `-v`; NEVER `down -v` or
`docker system prune` — the postgres volume holds the seeded dev DB.

Pre-flight before any up: `ss -tln | grep -Ew ':(13000|14000|15432|19000|19333)'`
must print nothing, and prod :8001 / aistack stack are OFF LIMITS.

## Dev workflow (from repo AGENTS/scripts — all in-container, no host Node needed)

```bash
cd /local/projects/beerhammer
export WEB_PORT=13000 API_PORT=14000
COMPOSE="docker compose -f docker-compose.dev.yml -f /local/projects/beerhammer-qa/overrides/compose-ports.override.yml --env-file /local/projects/beerhammer-qa/overrides/.env"
$COMPOSE up -d                    # stack
$COMPOSE run --rm toolchain bash /app/scripts/dev-container.sh verify   # lint+build+test gate
$COMPOSE run --rm toolchain npm test          # unit tests
$COMPOSE run --rm toolchain npm run lint      # lint
$COMPOSE exec postgres psql -U postgres -d forceorg_dev    # db shell
$COMPOSE logs -f web              # (note: plain `logs` needs the -f flags above)
```

`scripts/dev.sh` wrappers work only WITHOUT the QA override (they'd grab
default ports 3000/4000/5432/9000 — collision). On ga01 always use the
two-`-f` form above. Our code changes happen in software-co worktrees, never
in this clone; the bind-mount means the running stack is always HEAD-exact of
whatever the clone holds.

## Baseline test results (dev baseline — inherit state)

Run 2026-10-08 in the toolchain container against clone HEAD `36f00f2`
(fresh, `turbo run test --force`):

| Gate  | Result | Detail |
|-------|--------|--------|
| lint  | PASS (exit 0) | 11/11 tasks. 0 errors, 6 warnings (react-hooks/exhaustive-deps in changelog page ×3; `<img>` vs next/image ×3). |
| build | PASS (exit 0) | 7/7 tasks successful. |
| unit tests | PASS (exit 0) | 5/5 tasks; real suites: @forceorg/rules-engine-11e — 4 test files, **53 passed / 0 failed**. Other 4 workspaces define no tests (no-op). |

Baseline summary: **53 passed, 0 failed** (lint+build green). E2E (Playwright)
not run — needs one-time `dev-container.sh e2e-install`; treat as untested.

## Known env quirks

1. `forceorg-miniatures` S3 bucket does NOT exist after seed
   (`GET :19000/forceorg-miniatures/ → NoSuchBucket`). Photo/upload features
   will 404 until the bucket is created (api creates on first upload in some
   paths — file a dev card if upload flows matter).
2. DB tables are snake_case (`datasheets_11e`, `user_armies`, …), not the
   Prisma-model CamelCase a newcomer expects; seed data is starter-scale
   (datasheets=5, weapons=11, armies=0, profiles=0).
3. API dev log shows a Prisma UUID validation error
   (`Error creating UUID, invalid character … found '"'`) triggered by some
   request path — non-fatal, server stays operational; candidate dev-card.
4. Next.js dev prints cross-origin warnings when opened via `http://ga01:...`
   (needs `allowedDevOrigins` in a future Next major). Cosmetic today.
5. Restart policy on all five containers is `restart=no` — a ga01 reboot
   leaves the stack down until `up` is re-run (intentional per QA runbook).
6. Compose prints a benign warning about `dev_pw_browsers` volume being
   external-ish ("not created by Docker Compose"). Harmless.
7. Clone carries dirty local files (`.github/workflows/openwiki-update.yml`,
   `AGENTS.md` modified, untracked `CLAUDE.md`) — pre-existing, not ours; do
   not clean or commit them (repo law: never commit to the clone).
8. Host `node_modules/` and `.turbo/` in the clone are root-owned leftovers
   from an image build; the containers use volume-owned copies — ignore.

## Isolated dev stack (if ever needed — do NOT pre-build)

Ports 13100/14100/15532/19100/19433 audited free on 2026-10-08. Would require
a new override file (outside the repo) with renamed containers
(`beerhammer-isolated-*`), unique compose `name:`, distinct volume names, AND
a forked postgres volume copy — plus operator sign-off because two live
stacks then compete for the same clone via bind-mount. Cost > benefit today.
