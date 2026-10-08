---
type: Documentation Index
title: "Data"
description: "Files and subdirectories in Data."
---

# Files

- [Static Catalog Data Pipeline (BSData → faction JSON → web public data)](catalog-data-pipeline.md) - How the pinned data/bsdata snapshot becomes the static catalog the web app actually renders. extract-factions.js dual-writes 27 canonical faction JSONs with detachments, DP costs, enhancements and leader links into data/factions (gitignored) and apps/web/public/data/factions (committed); build-combat-patrols.js emits the Combat Patrol lists; verify-data.js checks the schema (data:verify) but is not wired into CI. Includes the Docker/image policy and the known docs/DEPLOYMENT.md staleness about public/data.
- [Postgres Data Model, Prisma Migrations & Seed](data-model-and-migrations.md) - The canonical 11th Edition schema in packages/db-client: 13 tables split into public rules catalog, per-user tables and the sync_metadata ETL log; JSON payload columns with no DB validation; migrate-on-boot in both the pulled prod image and the source-build stack; the manual idempotent seed; and why rls-policies.sql is intent, not enforcement.
