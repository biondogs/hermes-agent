---
type: Documentation Index
title: "Workflows"
description: "Files and subdirectories in Workflows."
---

# Files

- [Workflow: Roster Persistence & Offline Sync](roster-persistence-and-offline-sync.md) - End-to-end control flow for creating, editing and deleting a roster across browser localStorage, the best-effort API mirror, JWT ownership scoping and the user_armies table, including the guest path, the offline fallbacks and the identifier divergence that makes local rosters unreconcilable.
- [Workflow: Rules Compliance Audit](rules-audit-compliance-flow.md) - The audit round trip from the ComplianceDashboard modal through POST /api/rosters/:id/audit, JWT ownership scoping, a live datasheet batch fetch and validateRoster, how severity and category map into the UI buckets, the degraded client-side fallback, and why results are never persisted or writable from the modal.
- [Workflow: Rules Changelog & Sync Status Surfacing](rules-changelog-and-sync-status.md) - How GET /api/changelog composes its response from the ten newest sync_metadata rows plus a hardcoded seven-item MFM balance array, how /changelog renders that payload with a page-owned fallback dataset, and why the balance feed is curated static data rather than real ETL diffs.
