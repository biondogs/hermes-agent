# BANK-MAP — Intended-state memory-bank map per profile family

**Purpose.** This is the authoritative intended-state map for every Hermes profile's
Hindsight memory bank on ga01, ratified by operator directive 2026-10-22
(board t_352debb7) plus the ORCH AMEND on t_fd8ca6f0 ("gaudi worker-lane bank
variety — Hermes q38 / hb-upstream-comm / hb-inference-bench — is deliberate
specialist separation; inference knowledge must NOT live in general board
knowledge; do NOT propose consolidation").

**Bank resolution rule (effective, verified in plugin source).** The primary
bank resolves as:

1. `HINDSIGHT_BANK_ID` in the profile's `$HERMES_HOME/.env` — **wins** when set
   (plugin issue #5171; `plugins/hindsight/__init__.py:1307`; README
   "Environment Variables": "when set, wins over `bank_id` in `config.json`").
   A `bank_id_template` would take precedence over the env var, but no profile
   uses one.
2. `$HERMES_HOME/hindsight/config.json` → `bank_id`.
3. Root-home `~/.hermes/hindsight/config.json` → `bank_id` (root/default
   profile only).
4. Default `hermes`.

There is no `~/.hindsight/config.json` on this host — that hop in the
client-side default chain is absent.

**Server**: `http://ga01:8888` (`mode: local_external`) — the aistack Hindsight
instance, 16 banks as of 2026-10-22.

---

## 1. Intended banks per profile family

### Host/root + default-board lanes → bank `hermes`
The shared general bank for host-level and cross-board agent work.
- `default` (root home `~/.hermes`) — root `hindsight/config.json`, bank `hermes`.
- `kanban-board-architect`, `kanban-orchestrator`, `kanban-worker`
- `research`
- `sampling-test` (test lane, hermes is acceptable; no isolation requirement)
- `distiller` (cross-board curator; hindsight tools surfaced manually
  (memory_enabled: false), bank `hermes` correct when used)

### Board worker/orchestrator lanes → per-FAMILY specialist banks (ratified, deliberate)
Specialist banks are **intentional** (operator 2026-10-22): the same family
serves every board fleet — bank membership follows the LANE ROLE, not the
board. Inference knowledge must not pollute general board knowledge.

| Lane role (per board fleet: g01- g02- gaudi- sj- sjp-) | Profiles per fleet | Intended bank |
|---|---|---|
| Orchestrator, planner, auditor, scribe, analyst, benchrunner | e.g. `g01-orchestrator`, `gaudi-analyst`, `sjp-scribe`, `gaudi-benchrunner`, `g02-auditor` | `Hermes q38` (q38-family dedicated bank; on gaudi also `gaudi-arch` uses synapse) |
| SDK/kernel/synapse engineering | `gaudi-arch`, `gaudi-perfeng`, `gaudi-synapse` | `hb-synapse-sdk` |
| Release/infra/deploy | `g01-ops`, `g02-ops`, `gaudi-deployer`, `sj-ops`, `sjp-ops` | `hb-infra-release` |
| Host ops / docker / sysadmin | `gaudi-dockerops`, `gaudi-sysadmin` | `hb-host-ops` |
| Upstream liaison | `gaudi-liaison` | `hb-upstream-comm` |
| Watcher (inference-bench observations) | `g01-watcher`, `g02-watcher`, `gaudi-watcher`, `sj-watcher`, `sjp-watcher` | `hb-inference-bench` |

### software-co fleet → bank `software-co`
- `sw-architect`, `sw-dev-a`, `sw-dev-b`, `sw-devops`, `sw-docs`, `sw-pm`,
  `sw-qa`, `sw-reviewer`, `sw-ux`
- Bank mission (as seeded): engineering-practice working-lore only — one-fix-
  one-approve-one-commit, review posture, commit/DCO hygiene, QA ladder, kanban
  handoff contract. Infra/Azure/GPU facts deliberately rejected.

### Per-board butler lanes (Topology-B) → dedicated `<board>-butler` banks
Per operator-approved policy (t_fd8ca6f0 items 4–5; missions set server-side):
butler memories stay isolated, never in shared banks. The `.env`
`HINDSIGHT_BANK_ID` pin must stay UNSET in butler profiles — env would win
over config.json (#5171) and re-route the butler into a shared bank.
- `g01-butler` → bank `g01-butler` (retrofix receipted on t_fd8ca6f0)
- `gaudi-butler` → bank `gaudi-butler` (receipted on t_fd8ca6f0)
- `g02-butler`, `swco-butler`, `sjproto-butler` → banks `g02-butler`,
  `swco-butler`, `sjproto-butler` (provisioned t_02de9dff BUTLERS-STAGE-3,
  2026-10-22; banks created server-side, canary retain/recall receipted;
  `config.json` and the `.env` `HINDSIGHT_BANK_ID` pin carry the SAME bank —
  the agreeing-pair form ratified for stage-3 per card body spec #3)
- future butlers (`sj-butler` for the production skipjack board if stood up):
  same pattern → `<slug>-butler`

### Per-board seeded summary banks (`gargantua01`, `gargantua02`, `gaudi`, `skipjack`, `skipjack-prototype`)
Created 2026-10-12 by the board-migration seeder (seed-banks2.py) as
board-summary stores. These are **server-side reference banks**, NOT the
intended effective bank of any standing profile: fleet profiles point at the
specialist banks above. Exception: none today.

### Living reference banks retained server-side (not assigned to any profile)
- `hermes-general` (5349 facts) — legacy pre-Hindsight-reorg general bank;
  historical, read-only value.
- The per-board summary banks above participate in this category.

### Live-state verification (2026-10-22 ~20:30Z, run of t_0fbb3c61 BANK-TRIAGE-MIRROR-2)
Server-side readback after the .env-pin fix and the butler SOUL cutover:
- **Butler banks all non-empty and accumulating** (live retain working,
  by-design butler-operational content only; no migration into them needed):
  `g01-butler` 37 · `swco-butler` 39 · `sjproto-butler` 28 · `gaudi-butler` 30
  · `g02-butler` 20 nodes.
- **Per-board summary banks frozen** since pass-1 (t_2e99dfb6), unchanged:
  `gaudi` 125 · `gargantua01` 18 · `gargantua02` 14 · `skipjack` 6 ·
  `skipjack-prototype` 6 (non-destructive ruling holds).
- **Post-cutover stray check on the main `hermes` bank** (window
  created_at ≥ 2026-10-22T14:07Z): 1,807 nodes / 287 originals, ALL from
  legitimate `hermes`-resident lanes (operator main session, kanban
  architect/orchestrator runs, builtin-memory deltas). **0 true strays** —
  no mirrors required on that pass.
- Subsequent OPERATOR RULING (same run, later): FRESH START on memory banks —
  legacy banks (incl. `hermes` main) go read-only-archive; ratified banks
  carry forward and repopulate naturally. Cutover plan:
  `docs/FRESH-BANK-CUTOVER.md` (t_0fbb3c61, operator GO pending; zero config
  changes executed by that run).

---

## 2. Defect class found by the 2026-10-22 audit (t_352debb7)

Every non-butler board-fleet profile (34 profiles across g01-/g02-/gaudi-/sj-/
sjp-) carries a 2026-10-12-era `.env` pin `HINDSIGHT_BANK_ID=<board>`, which
WINS over its ratified specialist bank in `hindsight/config.json`. Since
2026-10-12 the fleets have effectively been writing to the per-board banks
(e.g. `gaudi` bank: 125 facts incl. watcher bench findings; `hb-inference-bench`
starved of new watcher facts since the pin landed).

**Fix (applied 2026-10-22, backup-first):** comment out the `HINDSIGHT_BANK_ID`
line in each affected profile's `.env` (one receipt per profile below) so the
ratified `hindsight/config.json` bank governs again. No server-side changes;
no migration of the facts that landed in per-board banks during the override
window (content triage is a separate, operator-gated decision).

### Fix receipts — applied 2026-10-22 14:07Z (run of t_352debb7)
Backup (pre-fix `.env` + `hindsight/config.json` per profile):
`~/kanban-backups/bank-map-audit/env-pin-backups-20261022T140731Z.tar.gz`
Receipt manifest: `~/kanban-backups/bank-map-audit/receipts-20261022T140731Z.json`

Fix: comment-out of `HINDSIGHT_BANK_ID=<board>` in each `.env` with an in-file
marker `# BANK-MAP-AUDIT 20261022T140731Z: pin removed ...`. Post-fix
verification: 0 active pins anywhere in the fleet; effective bank ==
config.json bank for all 53 configured profiles; butler `.env` deliberate-unset
comments intact.

| Fleet | Profiles (receipts identical within group) | Removed pin | Bank restored |
|---|---|---|---|
| g01 | auditor, ops, orchestrator, planner, scribe, watcher (6) | `gargantua01` | Hermes q38 ×4, hb-infra-release, hb-inference-bench |
| g02 | auditor, ops, orchestrator, planner, scribe, watcher (6) | `gargantua02` | Hermes q38 ×4, hb-infra-release, hb-inference-bench |
| gaudi | analyst, arch, auditor, benchrunner, deployer, dockerops, liaison, orchestrator, perfeng, planner, scribe, synapse, sysadmin, watcher (14) | `gaudi` | Hermes q38 ×6, hb-synapse-sdk ×3, hb-infra-release, hb-host-ops ×2, hb-upstream-comm, hb-inference-bench |
| sj | auditor, ops, orchestrator, planner, scribe, watcher (6) | `skipjack` | Hermes q38 ×4, hb-infra-release, hb-inference-bench |
| sjp | auditor, ops, orchestrator, planner, scribe, watcher (6) | `skipjack-prototype` | Hermes q38 ×4, hb-infra-release, hb-inference-bench |

Reversible: restore any `.env` from the backup tarball, or uncomment the
`# removed: HINDSIGHT_BANK_ID=...` line.

**Escalation to operator (decision, no action taken):** facts retained into
per-board banks (`gargantua01` 18 / `gargantua02` 14 / `gaudi` 125 /
`skipjack` 6 / `skipjack-prototype` 6) during the 2026-10-12 → 2026-10-22
override window now sit outside their ratified specialist banks — do you want
a triage card to review/mirror them into the correct banks, or leave them as
board-summary lore?

---

## 3. Rules of the road going forward

1. **To set a profile's bank**: edit `hindsight/config.json` `bank_id` — and
   make sure the `.env` carries NO `HINDSIGHT_BANK_ID` unless you want the env
   pin to be the intended mechanism. Never leave the two disagreeing: the pair
   is a silent override waiting to happen.
2. **Butler profiles**: `.env` must keep `HINDSIGHT_BANK_ID` unset (or
   explicitly commented with the reason) — bank comes from config.json.
3. **Husks**: `coding`, `kworker-muse-probe` (husk dirs, no config.yaml) — no
   memory wiring; ignore until they are provisioned or removed.
4. This map is the source of truth; when adding a profile, pick the family
   bank from §1 and record it here.
