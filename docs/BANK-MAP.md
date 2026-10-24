# BANK-MAP — Intended-state memory-bank map per profile family

**Purpose.** This is the authoritative intended-state map for every Hermes profile's
Hindsight memory bank on ga01. Rewritten 2026-10-23 by the env-axis cutover
(BANK-ENV-AXIS-REVIEW, t_7d3062dc, operator ruling executed same day): the primary
organizing axis is now **HARDWARE ENVIRONMENT** (operator: "g02, g01, skipjack and
skipjack proto are all individual hardware environments… much different than anything
that has to do with ga01"), replacing the 2026-10-22 role-axis arrangement whose shared
role banks mixed facts from 4-5 distinct hardware estates. Amended later the same day
by a second operator ruling (this update, t_05966941): gaudi's `*-perf`/`*-sdk` banks
are ROLE banks not environment banks, `hermes-general` is identified as the
operator-laptop bank (`laptop`), and the 2026-10-23 deletion GO was executed —
server held exactly **24 banks**. A third ruling the same evening
(t_7601b273): the `unsloth-litellm` profile was declared **obsolete** —
profile deleted and its lane bank `hb-unsloth-studio` deleted — so the
server held exactly **23 banks**. A fourth ruling (2026-10-24, t_0eec511d):
the `sampling-test` experiment profile was retired ("Delete it, experiments
are done") and its throwaway lane bank `hb-sampling-test` was deleted — so the
server now holds exactly **22 banks**.

**Naming convention.** `<environment-or-host>-<texture>`: `g01-infra`,
`g02-infra`, `skipjack-infra`, `skipjack-prototype-infra`, `gaudi-hpu*`. The
confusing `Hermes q38` name (test-farm-era) and the `hb-` (= *hindsight-bank*,
NOT Habana) prefix on mixed pools are retired from the active map; `hb-` survives
today only as immutable bank_ids on retained role/specialist banks — kanban-core
lanes plus the two gaudi specialist pools under readable aliases (see §1). Every
historical `hb-` mixed pool and every frozen legacy name was deleted 2026-10-23
(receipt in §1.6).

**Bank resolution rule (effective, verified in plugin source).** The primary
bank resolves as:

1. `HINDSIGHT_BANK_ID` in the profile's `$HERMES_HOME/.env` — **wins** when set
   (plugin issue #5171; `plugins/hindsight/__init__.py`; README
   "Environment Variables": "when set, wins over `bank_id` in `config.json`").
   Not used as an active pin anywhere in the fleet (all pins removed 2026-10-22;
   butler profiles keep explicit deliberate-unset comments).
2. `$HERMES_HOME/hindsight/config.json` → `bank_id` (+ `banks{}` carrier entry).
3. Root-home `~/.hermes/hindsight/config.json` → `bank_id` (root/default
   profile only).
4. Default `hermes`.

There is no `~/.hindsight/config.json` on this host — that hop in the
client-side default chain is absent.

**Server**: `http://ga01:8888` (`mode: local_external`) — the aistack Hindsight
instance, **exactly 22 banks as of 2026-10-24** (live recount via
`GET /v1/default/banks`, post `hb-sampling-test` retirement, t_0eec511d).

**Ratified canon (operator, 2026-10-23; amended 2026-10-24): 3 general + 5 butler + 5 environment +
9 role/specialist = 22** (24 until the unsloth lane was retired the same
evening; 23 until the sampling-test lane was retired 2026-10-24). Every bank on the server falls into exactly one of
these groups; the group counts below are live-verified.

---

## 1. Intended banks per profile family

### General banks (3) — shared/operator-owned, never deletion candidates

| Bank (server id) | Display name | Facts (live) | Role |
|---|---|---|---|
| `hermes` | `hermes` | 30,164 | Root/default lane: root `hindsight/config.json` (root home `~/.hermes`). Root assistant's LIVE bank — ratified end state 2026-10-22, not an archive. |
| `hermes-general` | **`laptop`** | 6,053 | **Operator-owned.** The operator's laptop Hermes instance's LIVE bank — an *external client* writing to ga01 (bank_id immutable; display name PATCHed to `laptop` 2026-10-23). |
| `software-co` | `software-co` | 4,306 | software-co fleet bank (see §1.5). |

**`laptop` resolves the "unbound writer" mystery (2026-10-23).** The prior map
flagged `hermes-general` as "NOT read-only — default lane writes observed
(574 facts landed 10-22/10-23, identity `default`, mechanism unconfirmed)".
Identified per operator ruling: those writes came from the operator's laptop
Hermes instance, not the ga01 default lane. The bank is therefore LIVE,
operator-owned, and **must NEVER be proposed for deletion**.

### 1.2 Hardware-environment banks (5) — fresh start 2026-10-23
Fresh per operator ruling: deliberately empty at creation; repopulate from live
runs only. **One bank per hardware estate** — a worker recalls ONLY its own
environment's texture. Canary-verified 2026-10-23 (retain+recall per bank,
0 cross-env leaks).

| Bank | Environment | Bound profiles | Facts (live) |
|---|---|---|---|
| `g01-infra` | Gargantua01 — prototype k8s | `g01-orchestrator`, `g01-planner`, `g01-auditor`, `g01-scribe`, `g01-ops`, `g01-watcher` | 141 |
| `g02-infra` | Gargantua02 — production k8s, Azure VMs 413-418 | `g02-orchestrator`, `g02-planner`, `g02-auditor`, `g02-scribe`, `g02-ops`, `g02-watcher` | 244 |
| `skipjack-infra` | Skipjack — HPC/AI hybrid cluster (mgmt02) | `sj-orchestrator`, `sj-planner`, `sj-auditor`, `sj-scribe`, `sj-ops`, `sj-watcher` | 178 |
| `skipjack-prototype-infra` | Skipjack Prototype — k8s on gh207+gh208 | `sjp-orchestrator`, `sjp-planner`, `sjp-auditor`, `sjp-scribe`, `sjp-ops`, `sjp-watcher` | 103 |
| `gaudi-hpu` | Gaudi host (ga01, Habana HPU) — the estate's one env bank | `gaudi-orchestrator`, `gaudi-planner`, `gaudi-auditor`, `gaudi-scribe`, `gaudi-deployer` | 191 |

**REGROUP (operator 2026-10-23):** `gaudi-hpu-perf` and `gaudi-hpu-sdk` were
listed here as environment banks in the morning cutover — they are **ROLE
banks, not environment banks** (operator: "they shouldn't be in the environment
grouping"). Moved to §1.3. One system = one env bank: gaudi's environment group
is `gaudi-hpu` alone. Display names already PATCHed server-side to
`gaudi-perf [role]` / `gaudi-sdk [role]`; **bank_ids immutable and unchanged**.

### 1.3 Role / specialist banks (9)
Lane-role separation *within* an estate, plus dedicated kanban/research lanes.
The gaudi role banks preserve the 2026-10-22 ORCH AMEND doctrine ("inference
knowledge must NOT live in general board knowledge; do NOT propose
consolidation") under the env-axis taxonomy: a gaudi fact still cannot be
recalled by a g02 worker — the env axis handles that — and within the gaudi
estate the amend's specialist separation lives on as these role banks.
Non-gaudi estates are single-bank: their fact volumes (~200-1,000/mo each,
mostly ops+watcher) do not justify a second bank; revisit if watcher noise
pollutes ops recall.

| Bank (server id) | Display name | Lane | Bound profiles | Facts (live) |
|---|---|---|---|---|
| `gaudi-hpu-perf` | `gaudi-perf [role]` | Gaudi inference/bench | `gaudi-analyst`, `gaudi-benchrunner`, `gaudi-watcher` | 187 |
| `gaudi-hpu-sdk` | `gaudi-sdk [role]` | Gaudi SynapsePT/SDK/kernel | `gaudi-arch`, `gaudi-perfeng`, `gaudi-synapse` | 133 |
| `hb-host-ops` | `gaudi-hpu-hostops` (alias) | Gaudi host ops | `gaudi-dockerops`, `gaudi-sysadmin` | 139 |
| `hb-upstream-comm` | `gaudi-hpu-upstream` (alias) | Gaudi upstream/liaison | `gaudi-liaison` | 421 |
| `hb-orchestrator` | `hb-orchestrator` | kanban-orchestrator lane | `kanban-orchestrator` | 96 |
| `hb-architect` | `hb-architect` | kanban-board-architect lane | `kanban-board-architect` | 384 |
| `hb-kanban-worker` | `hb-kanban-worker` | kanban-worker lane | `kanban-worker` | 67 |
| `hb-research` | `hb-research` | research lane | `research` | 3 |
| `hb-distiller` | `hb-distiller` | distiller lane | `distiller` | 810 |

*`hb-sampling-test` (throwaway test lane, 3 facts) was removed from this table
2026-10-24: the `sampling-test` profile was retired by operator ruling
("Delete it, experiments are done") and its bank deleted per the §1.6 protocol
(DELETE → 200 `deleted_count: 9`; 404 readbacks; listing recount 23 → 22).*

The two `hb-host-ops` / `hb-upstream-comm` pools were gaudi-pure (no
cross-env mixing), so the fresh-start ruling did not require cold-starting
them; the alias gives the readable name with identical two-way reachability
(verified: canary facts appear under both ids; Hindsight server API supports
aliases natively — "another id to answer to", 409 on collisions, zero data
movement).

### 1.4 Per-board butler banks (5) — Topology-B, isolated (unchanged)
Per operator-approved policy (t_fd8ca6f0): butler memories stay isolated, never
in shared banks. The `.env` `HINDSIGHT_BANK_ID` pin stays UNSET in every butler
profile (env would win over config.json — #5171). Future butlers
(`sj-butler` for the production skipjack board if stood up): same pattern →
`<slug>-butler`.

| Bank | Board front-end | Facts (live) |
|---|---|---|
| `g01-butler` | gargantua01 | 37 |
| `g02-butler` | gargantua02 | 120 |
| `gaudi-butler` | gaudi | 116 |
| `sjproto-butler` | skipjack-prototype | 28 |
| `swco-butler` | software-co | 899 |

### 1.5 software-co fleet → bank `software-co` (unchanged; kept in production per operator)
- `sw-architect`, `sw-dev-a`, `sw-dev-b`, `sw-devops`, `sw-docs`, `sw-pm`,
  `sw-qa`, `sw-reviewer`, `sw-ux`.
- Bank mission (as seeded): engineering-practice working-lore only — one-fix-
  one-approve-one-commit, review posture, commit/DCO hygiene, QA ladder, kanban
  handoff contract. Infra/Azure/GPU facts deliberately rejected.
- `software-co` is the third member of the general canon group (§1).

### 1.6 Deletion receipt — 2026-10-23/24, operator GOs executed
Deleted from the server with 404 + listing readback verification:

| Bank | Facts (at delete) | Class |
|---|---|---|
| `Hermes q38` | 6,092 | detached mixed pool (lane workers from all 5 estates + q38p test-farm legacy ≈1,831) |
| `hb-infra-release` | 3,027 | detached mixed pool (ops texture from g01/g02/sj/sjp/gaudi + q38p-deployer) |
| `hb-inference-bench` | 2,038 | detached mixed pool (watcher/bench observations from g02/gaudi +q38p) |
| `hb-synapse-sdk` | 186 | gaudi SDK pool, superseded by fresh-start `gaudi-hpu-sdk` |
| `gaudi` | 125 | frozen legacy per-board summary bank (board-migration seeder, 2026-10-12) |
| `hb-unsloth-studio` | 4 | lane bank retired same-day: operator ruled the `unsloth-litellm` profile OBSOLETE (t_7601b273, 2026-10-23 evening); contents were canary facts from the tuning verification only — DELETE `/v1/default/banks/hb-unsloth-studio` → 200 (`deleted_count: 15`), listing recount 24 → 23 |
| `hb-sampling-test` | 3 | throwaway test lane retired with its profile (operator ruling 2026-10-24, t_0eec511d: "Delete it, experiments are done"); all 3 facts were FBC22-CANARY cutover canaries from 2026-10-22, zero load-bearing content — DELETE `/v1/default/banks/hb-sampling-test` → 200 (`deleted_count: 9`), 404 readback on `memories/list` + `stats`, listing recount 23 → 22 |

The then-live 24-bank listing (pre-unsloth-lane-retirement; see header — server
recount is 23 as of the same evening) additionally confirms the other four frozen legacy
per-board summary banks are gone in the same wave (the card receipt names only
the five above; the server listing is source of truth):
`gargantua01` (18) · `gargantua02` (14) · `skipjack` (6) ·
`skipjack-prototype` (6). Net: **33 → 24 banks**.

Pre-delete readback snapshots (per-bank fact dumps, writer-identity
classification, deathwatch logs) live in the 2026-10-23 cutover report and the
rollback bundle (§3 footer). **NOT deleted** — and never to be proposed:
`hermes-general`/`laptop` (operator-owned, §1).

---

## 2. Defect class retired by the 2026-10-23 env-axis cutover

The 2026-10-22 fresh start organized banks by LANE ROLE with shared membership
across all five hardware fleets. Measured contamination of the three big shared
pools (classification by writer identity + content keywords, 2026-10-23; the
prior §2 env-pin defect fixed 2026-10-22 remains fixed):

| Pool | Total | g01 | g02 | sj | sjp | gaudi | q38p-legacy | unattributable |
|---|---|---|---|---|---|---|---|---|
| hb-infra-release | 3,027 | ~431 | ~1,073 | ~245 | ~2 | ~106 | ~202 | ~975 |
| hb-inference-bench | 2,038 | — | ~683 | — | ~2 | ~858 | ~33 | ~467 |
| Hermes q38 | 6,092 | ~68 | ~665 | ~292 | — | ~1,156 | ~1,831 | ~2,196 |

A watcher on Gargantua02 could recall Habana/HPU bench lore as if it applied to
Azure H100 VMs — and vice versa. The env-axis taxonomy removes this class by
construction.

Recall-quality cost of the cold start (accepted by the operator ruling
"fresh start everything"): every fleet worker loses recall of its 2026-09/10
history in the mixed pools until its env bank repopulates organically. Largest
losses by writer: g02-ops (901 facts in hb-infra-release), gaudi-watcher (704),
g02-watcher (522), gaudi benchrunner/auditor (375/216 in Hermes q38). Those
pools have since been **deleted under the 2026-10-23 operator GO** (§1.6) —
the acceptance of that loss is what made the delete GO possible.

## 3. Rules of the road going forward

1. **To set a profile's bank**: edit `hindsight/config.json` `bank_id` (and the
   `banks{}` carrier to match) — and keep the `.env` free of
   `HINDSIGHT_BANK_ID` unless the env pin is the intended mechanism. Never
   leave the pair disagreeing: the pair is a silent override waiting to happen.
2. **Butler profiles**: `.env` keeps `HINDSIGHT_BANK_ID` unset (or explicitly
   commented with the reason) — bank comes from config.json.
3. **Husks** (no hindsight wiring): `plugin-ab`, `.deleted` — ignore until
   provisioned or removed. (`coding` and `kworker-muse-probe` were husks here
   until 2026-10-24, when operator ruling "Delete both — probes over, backups
   exist" retired them: dirs deleted, tombstones in `profiles/.deleted/`,
   full tars at `~/.hermes/backups/husk-deletion-20261024/`.)
4. **New hardware environment?** One fresh `<env>-infra` bank + fleet flip,
   following the 2026-10-23 cutover receipts as the recipe. One system = one
   env bank; role sub-banks within an estate are allowed per §1.3 but are
   ROLE banks, never counted as environment banks.
5. **Running sessions cache their bank at startup** — bank flips take effect on
   the next fresh process (dispatcher-spawned workers: next claim; served
   sessions: next reload). Deathwatch any detached bank for 24h after a
   cutover to catch missed reloads.
6. **Operator-owned banks are never deletion candidates** — `hermes`,
   `laptop` (hermes-general), `software-co`. Deletion GOs for anything else
   come from the operator only, and every deletion lands as a receipt in §1.6.
7. This map is the source of truth; when adding a profile, pick the env bank of
   its estate (or the role bank of its lane) and record it here.

**Rollback for the 2026-10-23 cutover**:
`~/kanban-backups/env-bank-cutover-20261023T172208Z/` — pre-cutover
`hindsight/config.json` + `.env` for every profile (tar: `pre-cutover-profile-configs.tar.gz`),
pre/post bank snapshots, flip receipts, canary log. Restore = untar + copy the
profile's two files back; aliases removable via
`DELETE /v1/default/banks/{bank}/aliases/{alias}`. Deleted banks (§1.6) are not
recoverable from this bundle — it predates the delete GO; their pre-delete
readback dumps (if preserved in the cutover report) are the only record.
