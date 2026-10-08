---
type: Documentation Index
title: "Sync"
description: "Files and subdirectories in Sync."
---

# Files

- [Wahapedia ETL Sync Worker](wahapedia-etl-sync-worker.md) - The one-shot `apps/sync-worker` job that polls four placeholder Wahapedia endpoints with ETag conditional requests and SHA-256 content-hash delta detection, appends one SyncMetadata row per endpoint, and optionally posts a Discord/Slack summary alert. It writes only sync metadata — it never upserts datasheets, weapons, stratagems, or abilities into the rules tables.
