# HERMES-STATEDB-RETENTION-POLICY — session-store retention & vacuum (R7) — ARCHIVE-NOT-DELETE

- **Status:** ACTIVE (operator GO 2026-10-24 on HERMES-PERF-PORTABILITY-STUDY.md item R7, commit 757b729)
- **Owner:** kanban-board-architect · **Engine:** `~/.hermes/scripts/statedb-maintenance.py` (weekly, root crontab Sun 04:17, flock'd)
- **Receipts:** `~/.hermes/logs/statedb-maintenance.log` (JSONL) · first execution 2026-10-24 23:2x–23:3x UTC

## 0. Baseline (measured 2026-10-24, 59 session stores)

| Metric | Value |
|---|---|
| Root `state.db` | 756 MB (87.3 K messages; 382 sessions; trigram FTS `messages_fts_trigram_data` 247 MB + base `messages_fts_data` 53 MB) |
| Profile `state.db`s | 1.34 GB across 58 profiles (largest: kanban-board-architect 324 MB, g02-ops 131 MB, gaudi-benchrunner 108 MB) |
| Total estate | **2.10 GB** logical |
| Fragmented (≥2% freelist) | 35/59 DBs; worst sw-ux 76.7%, g01-orchestrator 76.0%, gaudi-orchestrator 74.0% |
| Sessions idle >60d | 2 (root, ended TUI sessions) — estate is young; the mechanism compounds as it ages |
| FTS layouts | 57/59 DBs compact v23 external-content; **kanban-board-architect + research still carry legacy inline `_content` FTS** (optimize-storage candidates, see §4) |
| Nightly byte tier | estate-snapshot-dbs.py `--big` (.backup API + pigz, ≤12 h) → /local nightly dated sets, 14-set retention — includes ALL state.dbs (root gz 243 MB verified 2026-10-24 17:50) |

## 1. Tiers

| Tier | Location | Holds | Write path |
|---|---|---|---|
| **hot** | `state.db` per home | sessions idle <60 d — fully live, searchable, resumable | gateway |
| **archive-exports** | `/local/backups/hermes-estate/session-archive/exports/YYYYMMDD/<home>.jsonl` | full-fidelity JSONL of every ended session idle ≥60 d (ALL sources, incl. cron/kanban worker sessions — receipt evidence) | weekly engine; `ledger.tsv` makes exports a per-session delta (idempotent) |
| **byte-mirror** | `/local/backups/hermes-estate/nightly-*` + `session-archive/db-snapshots/<date>/*.state.db.gz` | whole-DB consistent snapshots (sqlite `.backup` API) | estate-sync 12 h + pre-vacuum per-DB snapshot (keep last 4) |

## 2. Policy statements

1. **ARCHIVE-NOT-DELETE.** No `hermes sessions prune`/`delete` is ever run by the retention engine, and `sessions.auto_prune` is **false** on the root config (was `true` with `retention_days: 60` — a live delete path found and disabled 2026-10-24; config-only change, no bounce needed). Rows never leave state.db as a side effect of aging.
2. **60-day export window.** A session (ended, freshest-of `last_activity_at`/latest-message/`started_at` — exact upstream selector, incl. the `startup_orphan_reap` ages-from-sweep caveat) is exported to the /local tier the first weekly run after it goes 60 d idle. Exports are unredacted, 0600, sha256 in the receipt log; the operator's private /local tier already carries the unredacted nightly mirror, so fidelity > redaction for recovery evidence.
3. **Soft-archive stamp, worker-exempt.** After export, non-worker sessions idle ≥60 d are stamped `archived=1, auto_archived=0` (exactly `set_session_archived` lineage semantics: compression lineages stamped together, tips-only selection). Soft-hide only — reversible, messages intact. **Never stamped:** pinned, hidden, open (never-ended), and all worker-linked sessions (`worker_executions` row or source ∈ {cron, kanban, child, compute, tool, oneshot}) — worker sessions stay fully visible as receipt evidence; they are only *exported*, never hidden.
4. **Open sessions stay hot.** Ended-only selector (upstream guard): never-ended sessions are never exported/stamped by the engine.
5. **VACUUM only the fragmented, only when quiet.** Candidate rule: (`freelist ≥ 5%` AND reclaim ≥ 2 MB) OR reclaim ≥ 10 MB. Per-DB gates: db+`-wal` mtime idle ≥120 s (one 60 s retry), pre-`quick_check` must be ok, `busy_timeout` 30 s, ≤3 locked-retries, post-`PRAGMA integrity_check` must be ok, PASSIVE (never TRUNCATE) WAL fold-back. Skips (hot writer, lock) are receipted and retried next week. Root `state.db` is in scope only when it crosses the threshold — today it is 1.37% fragmented and the busiest writer, so it is correctly excluded.
6. **Pre-vacuum snapshot mandatory.** Every VACUUM candidate gets a consistent `.backup` + pigz snapshot in the archive tier first; restore is proven (2026-10-24: `db-snapshots/20261024-1933/profiles/sj-orchestrator/state.db.gz` → decompress → `integrity_check: ok`, 10 sessions/278 messages intact).

## 3. Documented exceptions (pre-existing, bounded)

- **`session-gc.sh`** (hermes cron, daily): reaps *never-active* cron session rows older than 6 h and *ended* cron sessions older than 7 d — the operator-approved 2026-10-23 fix for the gpu418 monitor litter leak (~240 rows/day, upstream cron-runner leak). Receipt *evidence* (worker_receipts tables, kanban boards, kanban.db) is untouched by it — it only removes session-transcript rows. **Proposal (not actioned):** gate it to never-active-only, or add an export-before-prune step, if the operator wants cron transcripts >7 d preserved too.
- **`sessions.auto_archive`** (built-in soft-hide) stays OFF: it has no worker-source exemption, so it would hide cron/kanban evidence from listings. The weekly engine implements the R7 semantics instead. If upstream adds a worker exemption, the built-in can replace the engine's stamp step.

## 4. Trigram FTS inventory → DROP IS NO-GO (as suspected in R7; propose-only, nothing dropped)

`messages_fts_trigram` (FTS5, tokenizer=trigram) consumers found in source:

| Consumer | File | What breaks if dropped |
|---|---|---|
| Search routing | `hermes_state_search.py` | CJK/substring fallback route (per-token ≥3-char gate `_trigram_route_ok`); `_ensure_v23_fts_tables()` would recreate the table on next maintenance — a drop cannot stick |
| **Session recovery (hard)** | `hermes_cli/session_recovery.py` (line ~1002) | fresh-destination verification **errors**: "fresh destination is missing required FTS tables" unless BOTH `messages_fts` and `messages_fts_trigram` exist |
| Lost & found salvage | `hermes_cli/session_lost_and_found.py` | rebuilds trigram from salvaged rows |
| Doctor | `hermes_cli/doctor_state.py` | FTS tables are a health surface (`fts_tables` stats, repair paths) |
| Index maintenance | `hermes_state_search.py` (insert/delete triggers), `config_defaults.py` v23 schema | excluded-source set `FTS_TRIGRAM_EXCLUDED_SOURCES=(cron, subagent)` — cron rows and subagent runs are already kept out of the trigram index |

**Recommendation: DO NOT DROP.** The v23 schema structurally requires the table; recovery refuses to run without it; maintenance recreates it; removing it saves nothing durable and risks breaking recovery. Size levers that ARE sanctioned (proposals for a follow-up card, not done here):

- **P-A (biggest win):** `hermes sessions optimize-storage` on the two legacy-inline DBs — `kanban-board-architect` (has `messages_fts_content` + `messages_fts_trigram_content` ≈ 38 MB content copies to drop by external-content demote) and `research`. Estimated reclaim ~40 MB plus FTS merge; runs chunked, duty-cycled against live writers. Do it on the architect lane in a quiet window (its own gateway is live, so not from inside a run).
- **P-B:** `hermes sessions optimize` (FTS5 segment merge + VACUUM, "no data change") on root after a few more weekly cycles — merges the 247 MB trigram segment chain if it fragments.
- **P-C:** upstream RFE — trigram indexing for interactive sources only (worker sources are already excluded via FTS_TRIGRAM_EXCLUDED_SOURCES), or a documented `sessions.auto_archive` worker exemption so the built-in can own the stamp step.

## 5. First-execution receipt (2026-10-24)

| Item | Result |
|---|---|
| Archive exports | 2 root sessions → `exports/20261024/root.jsonl` (512,822 B, sha256 `4ff215d1d887dbf69e45dd1812f380c9ad9bc8ccf71806e48f6b04ce397471ac`); both stamped `archived=1` (verified: root now has exactly 2 archived rows, messages intact 21/35) |
| VACUUM | **27/28 candidates vacuumed**; `gaudi-benchrunner` skipped — live writer (12.75% freelist, retried Nov cycle) |
| Space | candidates 804.2 MB → 421.9 MB (**382 MB freed**); estate 2.10 → **1.87 GB** logical |
| Integrity | **all 59 DBs `integrity_check` ok** (post-pass sweep) |
| Pre-vacuum snapshots | 27/27 in `db-snapshots/20261024-1933/` (209 MB); one restore proven (§2.6) |
| Still ≥2% freelist | 4 sub-threshold DBs (reclaim <2 MB — below action threshold by policy) + gaudi-benchrunner (hot-writer skip) |
| Config | root `sessions.auto_prune: true → false` (delete path off) — config-only, no bounce |
| Schedule | root crontab `17 4 * * 0` (flock `/.statedb-maintenance.lock`) — installed, verified |

## 6. Rollback

Any vacuumed DB: restore from `db-snapshots/<date>/` (pigz -dc → replace, with that home's gateway stopped or via `hermes sessions recover`). Stamps: `UPDATE sessions SET archived=0` (or leave — soft-hide only). Config: `hermes config set sessions.auto_prune true` (NOT recommended — it is the delete path this policy exists to prevent). Engine removal: delete the crontab line; the archive tier is append-only.

## 7. Review cadence

Weekly receipts are self-auditing (successes log `vacuum.ok`/`archive.exported`; skips log reasons). Escalate to the operator if: any `INTEGRITY-FAIL`, any `archive.export.FAILED` twice for the same session, or the archive tier grows past ~50 GB (retention decision needed).
