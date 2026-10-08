---
type: Documentation Index
title: "Architecture"
description: "Files and subdirectories in Architecture."
---

# Files

- [Shared Contracts: Types, Envelope, Ruleset Versions](shared-contracts.md) - The cross-package vocabulary every layer of ForceOrg-40k depends on: the @forceorg/types shape catalog, the success/data/error/meta API response envelope, the duplicated Prisma-vs-TypeScript enums, the ruleset version id convention, and the unvalidated RosterPayload JSON contract.
- [System Topology & Monorepo Layout](system-topology.md) - How the ForceOrg-40k monorepo is partitioned into apps/web, apps/api, apps/sync-worker and four shared packages, which process owns what at runtime, and how web (:3000), Express API (:4000), Postgres 16 (:5432) and S3-compatible SeaweedFS (:9000) connect on a single self-hosted Docker host.
