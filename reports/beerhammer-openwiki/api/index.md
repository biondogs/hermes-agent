---
type: Documentation Index
title: "Api"
description: "Files and subdirectories in Api."
---

# Files

- [Express API Server, Middleware Chain & Error Contract](api-server-and-middleware.md) - Bootstrap of the Express API in apps/api, the security and rate-limit middleware chain in mount order, public catalog read endpoints, the per-module PrismaClient/try/catch convention, and the uniform success/error envelope ending in a 500 INTERNAL_ERROR handler, checked against the docs/API.md transport rules, error-code table, and JWT `sub` provisioning requirements.
- [JWT Auth, Token Minting & Ownership Scoping](authentication-and-ownership.md) - How write protection actually works on the ForceOrg API — HS256 bearer verification in requireAuth, the documented UUID sub claim that must match a provisioned user_profiles row, the per-query findFirst({ id, userId }) ownership invariant that answers 404 instead of 403, and why the Supabase-style RLS policies in rls-policies.sql are not the enforcement layer.
- [Miniature Photo Upload: Sharp Pipeline & S3 Storage](media-upload-and-object-storage.md) - End-to-end path for custom miniature photos: multer multipart ingest, dual WebP derivatives produced by Sharp, deterministic S3/R2 storage-key layout, the user_unit_media upsert record, and storage-then-database delete semantics.
