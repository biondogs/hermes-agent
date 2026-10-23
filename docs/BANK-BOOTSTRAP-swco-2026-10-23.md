# BANK-BOOTSTRAP-swco — October decision record ingested (2026-10-23)

**Card:** t_90d515dd (software-co board, sw-pm) · **Bank:** `software-co` (hindsight @ ga01:8888)
**Result:** 20 atomic retains queued and fully ingested; 0 pending, 0 failed operations.
No secrets retained (credential facts recorded as policy + sha256[:12] identities only).

## Stats before/after (`GET /v1/default/banks/software-co/stats`)

| Metric | Before (2026-10-23 19:31:12Z) | After (2026-10-23 19:33:53Z) | Δ |
|---|---|---|---|
| total_documents | 168 | 188 | **+20** (= 20 retains, 1:1) |
| total_nodes | 4,130 | 4,253 | +123 |
| total_links | 98,913 | 101,644 | +2,731 |
| observations | 1,459 | 1,514 | +55 |
| operations completed | 412 | 460 | +48 |
| pending / failed operations | 0 / 0 | 0 / 0 | clean |
| last_consolidated_at | 19:14:42Z | 19:32:32Z | — |

Recall spot-check PASS: querying the Scope B verdict returns the retained
NO-GO observation with numbers (tool-slimmer +0.8%, toolaria +14.8%,
skill-retrieval +9.8%, 25/25 success, TTFT 1.12–1.13 s).

## The 20 retains (tag → subject)

Decisions (11):
1. butler — butler-first routing doctrine LIVE 2026-10-22 (intake via butlers; default = meta + fail-safe stamp; skipjack prod has no butler)
2. butler — verified butler surface (34 PASS / 1 BLOCK-PASS) + two tool-layer gaps (no kanban_archive tool; no tool-layer board= fence)
3. plugin-pilot — Scope A PASS (6 plugins vetted at pinned SHAs; enabled on default only; custodian report-only enforced structurally)
4. plugin-pilot — Scope B fleet NO-GO with numbers (report = mgmt commit 8b47cb1)
5. banks — env-axis reorg: 7 per-env banks + 2 alias renames; 38 flips 0 errors; mixed pools detached, deletes are operator-GO proposals only
6. timezone — fleet TZ law America/New_York, 12 hosts, HPC/mgmt exclusion list; 60 profile pins; cron zone semantics
7. credentials — platform-creds canon: slack default-only + NO listener (explicit disable beats env auto-enable); telegram default+5 butlers, distinct tokens
8. dedup — dedup-close law: duplicates block 'duplicate of <id> — archive' and never execute; mid-run dedup-stop archive needs a coverage receipt naming in-flight artifacts
9. mprov — contributor allowlist (biondogs, uberlinuxguy, jhujasonw) + no-external-submissions: close unmerged, re-approach own-authorship, pre-push identity check
10. skills — skill-copy cleanup outcome: 1,851 lagging re-mirrored; 1,183/42 names deleted; 1 kept on curator allowlist; 13 parked
11. performance — (part of #4)

Protocols (6):
12. archive-gc — ARCHIVE-GC bridge: HOUSEKEEPING stamps → nightly sweeper, cancel honored, -butler/default-only authors, no running cards, cap 20, self-retiring
13. butler — escalation phrasing ('route this to the default orchestrator') + intake protocol (explicit board=, parents at create)
14. banks — config.json sole carrier (#5171 law) + sessions cache bank at startup → 24h deathwatch after flips
15. github — PR submit pattern GO→execute→readback (body sha byte-identical, drift = stop-and-block)
16. sprint — open-PR-overlap dedup join; covered issues stay open; missing Fixes-link = manual close at merge
17. skills — (see cleanup)

Pitfalls (4):
18. profiles — plugin enablement scope trap: workers load plugins from own profile home + secrets scrubbed → per-profile install+enable
19. approval-gate — headless CLI stalls on dangerous-classified commands; reset fix-repos between battery arms
20. ga01 — arch-owned /etc breaks timedated; symlink swap is the DAC-legal path; root:root ruling pending
21. commit-trailer — hook Agent-*/Co-Authored-By trailers leak into public PRs (one gate FAIL); strip pre-push, grep receipts
22. skills — bulk deletion: back up first, verify counts close; rmtree of a shared dir over-deleted 4 subskills (repaired, net zero)

## Sources mined
- docs/butler-routing-doctrine-2026-10-22.md · docs/BUTLER-VERIFY-2026-10-22.md (via doctrine)
- docs/BANK-ENV-CUTOVER-REPORT-2026-10-23.md · docs/BANK-MAP.md
- docs/plugin-perf-ab-2026-10-23.md · PLUGIN-PILOT t_4ddfc8b8 receipts (Scope A/B comments)
- docs/TZ-SYNC-2026-10-23.md · docs/PLATFORM-CREDS-2026-10-23.md
- mprov/maint-2026-10-23/REAPPROACH-RECEIPT.md · WORKLIST-2026-SPRINT.md · MPROV-MAINT-POLICY.md
- Board DB receipts: t_aabdf078, t_79c80a6b (1843-PUBLISH), t_588e76fe (dedup precedent), t_58393f2b, t_c5fa2e59, t_7531eb52 events

Already in bank, deliberately NOT re-retained: CHATQ-BUG root cause, 'Assisted by
JoeBot' standing line, kanban_archive upstream FR chain.

— sw-pm, card t_90d515dd, 2026-10-23 (America/New_York)
