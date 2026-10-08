---
type: Documentation Index
title: "Operations"
description: "Files and subdirectories in Operations."
---

# Files

- [CI/CD Workflows](ci-cd-pipelines.md) - What the GitHub Actions workflows and the GitLab CI pipeline run on push, PR/MR, and cron; which checks gate a merge to main; and which container images get published where.
- [Configuration & Environment Variables](configuration-and-env-vars.md) - Single reference for every environment variable in the monorepo, which service reads it, how the S3_*/AWS_* aliases and S3_BUCKET/S3_BUCKET_NAME and CDN_BASE_URL/PUBLIC_CDN_BASE_URL pairs resolve, and the silent defaults (two different public JWT fallbacks, empty-by-default storage credentials, placeholder Supabase host, baked NEXT_PUBLIC_* values, the DIRECT_URL gap the API entrypoint closes) that change behavior without failing loudly.
- [Deployment, Docker Compose & Container Images](deployment-and-compose.md) - How the self-hosted ForceOrg-40k stack is built and started — the pull-based production composition and its placeholder-default credentials, the self-migrating API image, the published one-shot sync-worker image, the source-build and dev compositions, ports, and post-deploy checks.
- [Development Environment & Scripts](dev-environment.md) - The two supported local dev loops — host-native npm/Turbo and the shared Docker dev environment behind scripts/dev.sh — including the dev.sh command surface, the db-init migrate-and-seed one-shot, root npm scripts, and local port conflicts/overrides.
