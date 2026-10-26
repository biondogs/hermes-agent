> Status: superseded by hermes-estate/docs/PROFILES.md — sweep executed; receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# PROF-SWEEP-OPT — full-fleet profile optimization sweep receipts (2026-10-24)

Operator directive 2026-10-23/24. Card: `t_a386103a` (board: software-co, assignee: kanban-board-architect).
Method: read-only Phase-1 audit (`audit_phase1.py`, batch pattern per `references/profile-audit-batch-script.md`) → surgical guarded text-splice fixes (`fix_phase2.py`) → post-fix re-audit + per-profile `hermes -p <p> config check`.
Scope scanned: root config + 59 config-bearing profile dirs + 3 no-config dirs (coding, kworker-muse-probe, .deleted quarantine).
Backups: `~/.hermes/config-backups/prof-sweep-20261024T024500Z/` (58 pre-splice originals + 16 pre-later-edit states; earlier pre-dawn states in `aux-sync-*`/`comp-pin-*`; all changed values documented below for exact reversal).
Credentials: untouched (standing LAW). Banks: none deleted. No gateway restart performed; no aistack/container touches.

## Verdict per canon item

| # | Canon item | Verdict | Detail |
|---|---|---|---|
| 1 | Aux blocks byte-identical to root, compression qwen36-fast/litellm/none | **FIXED (59)** | All 59 aux blocks were dict-equal but text-divergent (the aux-sync used `yaml.dump(sort_keys=True)`, never the root's raw text). Spliced root's raw aux text into all 59 (guards: pre-splice dict equality, post-splice byte equality, parsed-identity, tmp+parse). Post-state: 59/59 byte-identical (the 6 append-not-splice files — 5 butlers + plugin-ab — carry the block at EOF; identical modulo file-terminating newline). compression canon verified 59/59 + root. |
| 2 | Butler `kanban.board` pins (hotfix 851d9e9231) | **GREEN (0 drift)** | g01→gargantua01, g02→gargantua02, gaudi→gaudi, sjproto→skipjack-prototype, swco→software-co — all 5 correct, non-board kanban keys: none anywhere. NO non-butler profile carries a kanban pin → nothing to flag. Checklist supersession recorded in skill + reference (see Skill updates). |
| 3 | Providers v46 dict / litellm pins / no custom_providers / no fallback_providers | **GREEN (0 drift)** | 59/59 profiles + root: `providers:` dict, no `custom_providers:` remnant, `providers.litellm` present; pin windows qwen36-fast 131072/32768 (probe-verified @e1f9993), qwen38-flash-fp8 262144, glm53 1000000. No `fallback_providers` anywhere. `fallback_model` live only on the 8 muse profiles (other hits are commented stock examples). |
| 4 | Credentials canon (read-only) | **GREEN (0 drift)** | Slack: root/default only, no listener anywhere. Telegram: default + 5 butlers, 6 distinct tokens (no duplicates). `TELEGRAM_FALLBACK_IPS` present in all 5 butler `.env`. Zero credential mutations performed. |
| 5 | Bank bindings per BANK-MAP @c09adec | **GREEN (0 drift, 1 map correction)** | All effective banks resolve correctly. The 3 gaudi bindings flagged in Phase 1 (dockerops/sysadmin→`gaudi-hpu-hostops`, liaison→`gaudi-hpu-upstream`) are the operator-ratified ALIAS ids — BANK-ENV-CUTOVER-REPORT-2026-10-23: "the alias names are canonical in configs". Audit map corrected; no config changes; no banks deleted. |
| 6 | Muse temp lane | **GREEN (0 drift)** | All 8 muse-default profiles (kanban-worker, g01/g02-scribe, sw-dev-a/b, sw-devops, sw-docs, sw-qa) wired per teardown manifest with live `fallback_model: qwen38-flash-fp8`; no stray muse defaults anywhere else. |
| 7 | General hygiene | **FIXED (16 file edits) + verified** | `hermes -p <p> config check`: 59/59 rc=0 post-fix ("Config version: 51 ✓"). context_length: 11 mis-pins fixed (see drift table) — now every profile's `model.context_length` matches its default model's real window. env-var references all resolve. SOUL titles match roles (3 Phase-1 hits were an audit-heuristic bug, no file changes). Timezone America/New_York where set. `_config_version`/`plugins` presence: ESCALATED, see below. |

## Drift table (before → after)

| Check | Before | Fix applied | After |
|---|---|---|---|
| aux text byte-identity (canon 1) | 59/59 drifted (dump-sorted key order vs root hand-order) | raw-text splice of root block | 0 drifted (59/59 identical) |
| `skills.always_load: []` dead key | 5 butlers | removed the two dead lines | 0 |
| `model.context_length` mis-pins | g01-ops, g01-watcher, g02-ops, g02-watcher, gaudi-watcher, sj-ops, sj-watcher, sjp-ops, sjp-watcher @ 1000000 on qwen38-flash-fp8 (served window 262144); sw-architect, sw-reviewer @ 262144 on glm53 (real window 1000000) | repinned to 262144 ×9 and 1000000 ×2 (guarded scalar splice) | 0 mis-pins (59/59 match real windows) |
| gaudi alias bank ids | 3 flagged (audit map bug) | map corrected per cutover receipt | 0 findings |
| SOUL title "mismatches" | 3 WARN | audit heuristic fixed; titles were correct all along | 0 |

Fix totals: **75 surgical edits across 59 profile config files** (59 aux splices + 5 always_load strips + 11 context repins). Every edit: per-file backup → guarded_write (parse + expectation checks → tmp write → parse → move). Post-fix parses: 59/59 clean; config checks 59/59 rc=0.

## Escalated — NOT touched (operator input needed)

1. **`_config_version` (59/59) + `plugins:` (59/59) presence — the item-7 "strip" canon is UNSAFE.** Source + logs prove both keys are per-home functional in this Hermes version (v51):
   - `plugins.enabled` is a per-home OPT-IN allow-list (`hermes_cli/plugins_discovery.py`); profiles do NOT inherit root's global list. Natural experiment: config-less husk `coding` logs "62 found, 57 enabled" — no root inheritance; g01-ops (`enabled: [hindsight, kanban-stream]`) logs "64 found, 58 enabled" with hindsight+kanban-stream mounted from its own plugin dirs. Stripping would disable hindsight + kanban-stream for every profile until an unpredictable grandfathering-migrate rewrote configs.
   - `_config_version` is a per-home migration stamp (`hermes_cli/config.py`: `current_ver = 0 if stamp is None`); deleting it makes the next migrate treat the home as unversioned and REWRITE config.yaml (comment loss).
   - Both left in place; skill checklist + batch-script reference amended from "strip" to "report only, NEVER strip blindly, pending operator ruling".
2. **plugin-ab** — `agent.description` MISSING (kanban-routing CRIT only if this lane ever routes; profile is the plugin A/B harness husk per BANK-MAP), and its plugins shape (`enabled: []`, `disabled: [skill-retrieval, tool-slimmer, toolaria]`) looks intentional. Needs ruling: provision properly (add description) or decommission.
3. **sampling-test** — plugins outlier: enabled list includes dashboard_auth, dashboard-sso, disk-cleanup, langfuse, etc. (deliberate test-lane config?). Verify intentional vs strip.
4. **sw-docs** — plugins enabled adds `degeneracy-guard` beyond the fleet-uniform `[hindsight, kanban-stream]`; likely degeneracy-harness residue. Ruling needed (currently also muse default + fallback wiring per canon 6, unaffected either way).
5. **Husks** — `coding` and `kworker-muse-probe` have NO config.yaml but carry SOUL.md/.env/state.db/fresh gateway.locks; cron ticker actively heartbeat-locks their cron dirs. Not provisioned, not deleted (no-deletion LAW). Ruling: decommission or provision. `.deleted/` is the sanctioned quarantine dir (tombstones for gaudi-reviewer, unsloth-litellm) — expected, no action.

## Needs-restart list for operator

None mandatory. All changes take effect at next per-profile session spawn (fresh config read). No gateway/aistack restart performed, per directive.

## Skill updates (in shared master `~/.hermes/skills/software-development/hermes-config-management/`)

- `SKILL.md` + `references/profile-audit-batch-script.md`: kanban checklist rule amended for the sanctioned butler `kanban.board` pin (hotfix 851d9e9231); stale pre-v46 `custom_providers` advice in the reference corrected to the v46 `providers:` dict canon; `plugins`/`_config_version` rules changed from "strip" to evidence-cited "report only".

## Restore map

- Aux splice: fully semantics-preserving (pre-splice dict equality was a hard guard); restore = reverse splice or copy from `prof-sweep-20261024T024500Z/`.
- always_load strip: re-add two lines `skills:` / `  always_load: []` (documented above).
- context repins: reverse per drift table (9× 262144→1000000 for qwen38-flash-fp8 seats; 2× 1000000→262144 for glm53 seats).

## Operator dispositions 2026-10-24 — executed by t_0eec511d (SWEEP-FOLLOWUP)

All five escalated clusters ruled by the operator via interactive prompt on 2026-10-24; verbatim rulings per item:

1. **`_config_version` + `plugins` keys — RATIFIED.** "Keep them; checklist stays WARN-only." No config action; the skill-checklist amendment above is canon as amended.
2. **Husks `coding` + `kworker-muse-probe` — DELETED.** "Delete both — probes over, backups exist." Full tars + sha256 manifest at `~/.hermes/backups/husk-deletion-20261024/` (sealed and hash-verified before deletion); reference sweep before rm: zero references across all 16 board DBs (every text column), every `cron/jobs.json`, dispatcher/global config, and live `ps` — clean; tombstones written to `.deleted/` (fleet convention); absent from `hermes profile list` post-delete. *Incident note:* a concurrent fleet census (t_3eed159c, as-built card) re-minted the three homes as empty husks seconds after the rmtree; caught on readback, guard-re-deleted (scripts refuse if `config.yaml` present), absent since.
3. **`sampling-test` — DELETED (profile + bank).** "Delete it, experiments are done." Same backup/reference precautions as item 2. Role bank `hb-sampling-test` deleted per the bank-deletion protocol: pre-delete readback snapshot saved (3 facts, all FBC22-CANARY cutover canaries from 2026-10-22 — zero load-bearing content); `DELETE /v1/default/banks/hb-sampling-test` → 200 (`deleted_count: 9`); 404 readbacks on `memories/list` + `stats`; listing recount **23 → 22**. BANK-MAP.md amended same commit (§1.3 → 9 role/specialist, §1.6 receipt row, §3 rule 3 husk list, header count).
4. **`sw-docs` muse de-scope — RESCINDED mid-execution, never applied.** Original ruling ("Sw-docs should be part of the software co board and have nothing to do with muse") was rescinded later the same day: **"Sw-docs can use muse."** No config change was ever made — `sw-docs` config verified unchanged by readback: `model.default: muse`, `model.fallback_model: qwen38-flash-fp8`. `docs/muse-wiring-v2/wired-profiles.md` annotated (lane stays **8 profiles**; sw-docs inclusion re-confirmed 2026-10-24); the sw-docs rollback manifest retains the original pre-muse state.
5. **`degeneracy-guard` (sw-docs pilot entry) — KEEP AS PILOT, verdict gate 2026-10-25.** "Degeneracy guard was supposed to be piloted and tested to see if it works then added to profiles if it was found valuable." Pilot entry intentionally kept (NOT stripped, NOT propagated fleet-wide); the 48h soak receipts land 2026-10-25 via the plugin-pilot-soak-collector cron → card t_4ddfc8b8, at which point the adopt/drop verdict goes to the operator. Captured in KANBAN-SYSTEM-AS-BUILT.md §9 (errata item 5) and as a comment on t_4ddfc8b8.

**Needs-restart list: still none.** Husk deletions (never-running profiles) and an un-applied/rescinded model change require no gateway restart; everything remains effective at next session spawn.
