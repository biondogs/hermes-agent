# Curator's notes — what was changed in this copy

Source: OpenWiki code-mode output (`openwiki code --update --print`) on a working-tree
clone of `fatpat81/BeerHammer` at commit `36f00f2` (2026-10-07), generated 2026-10-08.
Everything below was edited **in this copy only**; the upstream repo was not committed to.

## Inaccuracies fixed (verified against source before editing)

1. `quickstart.md` — "monorepo of **four** apps and four packages" → "**three** apps and
   four packages". `apps/` contains exactly `web`, `api`, `sync-worker`
   (`ls apps/` at 36f00f2); the four packages (`types`, `ui-theme`,
   `rules-engine-11e`, `db-client`) were already correct.

## Link rewrites (presentation, not content)

- 341 repo-relative links pointing outside the wiki (`../README.md`, `../../docs/…`,
  `../../apps/…`) were rewritten to GitHub permalinks pinned at
  `36f00f242ab6d5fe73ee567f7aa43069b2ec0fab` so the copy is self-contained under
  `software-co/reports/`. Intra-wiki links (124) stay relative.
- `testing/testing-strategy.md` — the `src/__tests__/` **directory** link (unresolvable
  as a file permalink) was pointed at the GitHub tree permalink; the claim "53 `it`
  cases" was verified correct (`grep` counts 53 across the four suites).
- Removed three `<!-- openwiki: broken internal link … -->` lint markers that the
  generator left in `operations/dev-environment.md` (×2) and
  `testing/testing-strategy.md` (×1). The first two flagged line-range anchors
  (`docs/DEV_NOTES.md#L46-L55`) that GitHub doesn't treat as heading anchors; the
  permalinks themselves resolve.

## Claims spot-checked and found correct (not edited)

- Ports/origins: web :3000, API :4000 (`PORT || 4000`), SeaweedFS S3 :9000,
  Playwright server :3456 with `reuseExistingServer: false`, no auto-build.
- Rate limit: `windowMs 15min`, `limit 300`, envelope-shaped 429 `RATE_LIMIT_EXCEEDED`.
- JWT fallback secret `dev-secret-change-in-production` (`apps/api/src/middleware/auth.ts`).
- prod compose placeholders `JWT_SECRET=please-change-me`,
  `postgres/postgrespassword`; sync-worker in `profiles: ['tools']`; GHCR images
  `ghcr.io/fatpat81/beerhammer/forceorg-{api,web,sync-worker}`.
- Guest session keys `forceorg_local_user` / `forceorg_rosters_<userId>`.
- Node 20 (`.nvmrc`), `.npmrc include=dev`, turbo `dev` task `cache:false, persistent:true`.
- `CompositeUnitCard`/`StratagemPanel`/`PhotoUploadModal` orphan claim: no route imports
  them (PhotoUploadModal is imported only by the orphaned CompositeUnitCard).
- CI: 4 GitHub workflows + a `.gitlab-ci.yml` targeting a different registry, as documented.
- Sync worker metadata-only limitation, cron `0 2 * * *`, Playwright suite = 5 tests.
