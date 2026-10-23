# BANK-MAP — Intended-state memory-bank map per profile family

**Purpose.** This is the authoritative intended-state map for every Hermes profile's
Hindsight memory bank on ga01. Rewritten 2026-10-23 by the env-axis cutover
(BANK-ENV-AXIS-REVIEW, t_7d3062dc, operator ruling executed same day): the primary
organizing axis is now **HARDWARE ENVIRONMENT** (operator: "g02, g01, skipjack and
skipjack proto are all individual hardware environments… much different than anything
that has to do with ga01"), replacing the 2026-10-22 role-axis arrangement whose shared
role banks mixed facts from 4-5 distinct hardware estates.

**Naming convention.** `<environment-or-host>-<texture>`: `g01-infra`,
`g02-infra`, `skipjack-infra`, `skipjack-prototype-infra`, `gaudi-hpu*`. The
confusing `Hermes q38` name (test-farm-era) and the `hb-` (= *hindsight-bank*,
NOT Habana) prefix on mixed pools are retired from the active map; `hb-` survives
only on (a) detached archive pools awaiting an operator delete decision and
(b) kanban-core lane banks whose content is healthy (see §3).

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
instance, 33 banks as of 2026-10-23 (post env-axis cutover).

---

## 1. Intended banks per profile family

### Root/default lane → bank `hermes` (unchanged, operator-ratified 2026-10-22)
- `default` (root home `~/.hermes`) — root `hindsight/config.json`, bank `hermes`.
  `hermes` (~29.8k facts) is the root assistant's LIVE bank — ratified end state,
  not an archive.
- ⚠ **`hermes-general` is NOT read-only**: the default lane also writes it
  (observed 2026-10-23: 574 facts landed 10-22/10-23, identity `default`;
  mechanism unconfirmed). It is therefore NOT a deletion candidate until its
  writer is understood. Investigation item in the 2026-10-23 cutover report.

### Hardware-environment banks (fresh start, created 2026-10-23)
Fresh per operator ruling: deliberately empty at creation; repopulate from live
runs only. One bank per hardware estate; a worker recalls ONLY its own
environment's texture. Canary-verified 2026-10-23 (retain+recall per bank,
0 cross-env leaks).

| Bank | Environment | Bound profiles |
|---|---|---|
| `g01-infra` | Gargantua01 — prototype k8s | `g01-orchestrator`, `g01-planner`, `g01-auditor`, `g01-scribe`, `g01-ops`, `g01-watcher` |
| `g02-infra` | Gargantua02 — production k8s, Azure VMs 413-418 | `g02-orchestrator`, `g02-planner`, `g02-auditor`, `g02-scribe`, `g02-ops`, `g02-watcher` |
| `skipjack-infra` | Skipjack — HPC/AI hybrid cluster (mgmt02) | `sj-orchestrator`, `sj-planner`, `sj-auditor`, `sj-scribe`, `sj-ops`, `sj-watcher` |
| `skipjack-prototype-infra` | Skipjack Prototype — k8s on gh207+gh208 | `sjp-orchestrator`, `sjp-planner`, `sjp-auditor`, `sjp-scribe`, `sjp-ops`, `sjp-watcher` |
| `gaudi-hpu` | Gaudi host (ga01, Habana HPU) — general board/infra lane | `gaudi-orchestrator`, `gaudi-planner`, `gaudi-auditor`, `gaudi-scribe`, `gaudi-deployer` |
| `gaudi-hpu-perf` | Gaudi HPU — inference/bench lane | `gaudi-analyst`, `gaudi-benchrunner`, `gaudi-watcher` |
| `gaudi-hpu-sdk` | Gaudi HPU — SynapsePT/SDK/kernel lane | `gaudi-arch`, `gaudi-perfeng`, `gaudi-synapse` |

**Why gaudi keeps three role banks** (reconciled with the 2026-10-22 ORCH AMEND
"inference knowledge must NOT live in general board knowledge; do NOT propose
consolidation"): the env axis already eliminates the cross-estate pollution the
amend guarded against — a gaudi fact can no longer be recalled by a g02 worker.
Within the gaudi estate the amend's specialist separation is preserved as
role-secondary sub-banks (`gaudi-hpu` / `-perf` / `-sdk`). Non-gaudi estates are
single-bank: their fact volumes (~200-1,000/mo each, mostly ops+watcher) do not
justify a second bank; revisit if watcher noise pollutes ops recall.

### Gaudi specialist banks retained LIVE under readable aliases (content preserved, zero churn)
| Alias (config carrier) | Underlying bank (server id) | Bound profiles | Facts |
|---|---|---|---|
| `gaudi-hpu-hostops` | `hb-host-ops` | `gaudi-dockerops`, `gaudi-sysadmin` | 139 |
| `gaudi-hpu-upstream` | `hb-upstream-comm` | `gaudi-liaison` | 421 |

These two pools were gaudi-pure (no cross-env mixing), so the fresh-start ruling
did not require cold-starting them; the alias gives the readable name with
identical two-way reachability (verified: canary facts appear under both ids;
Hindsight server API supports aliases natively — "another id to answer to",
409 on collisions, zero data movement).

### Kanban core / specialist lanes → unchanged from 2026-10-22 fresh start
- `kanban-orchestrator` → `hb-orchestrator`
- `kanban-board-architect` → `hb-architect`
- `kanban-worker` → `hb-kanban-worker`
- `research` → `hb-research`
- `distiller` → `hb-distiller`
- `sampling-test` → `hb-sampling-test` (throwaway test lane)
- `unsloth-litellm` → `hb-unsloth-studio` (added 2026-10-23, t_7601b273)

### software-co fleet → bank `software-co` (unchanged; kept in production per operator)
- `sw-architect`, `sw-dev-a`, `sw-dev-b`, `sw-devops`, `sw-docs`, `sw-pm`,
  `sw-qa`, `sw-reviewer`, `sw-ux`.
- Bank mission (as seeded): engineering-practice working-lore only — one-fix-
  one-approve-one-commit, review posture, commit/DCO hygiene, QA ladder, kanban
  handoff contract. Infra/Azure/GPU facts deliberately rejected.

### Per-board butler lanes (Topology-B) → dedicated `<board>-butler` banks (unchanged, isolated)
Per operator-approved policy (t_fd8ca6f0): butler memories stay isolated, never
in shared banks. The `.env` `HINDSIGHT_BANK_ID` pin stays UNSET in every butler
profile (env would win over config.json — #5171).
- `g01-butler` → `g01-butler` · `g02-butler` → `g02-butler` ·
  `gaudi-butler` → `gaudi-butler` · `sjproto-butler` → `sjproto-butler` ·
  `swco-butler` → `swco-butler`.
- Future butlers (`sj-butler` for the production skipjack board if stood up):
  same pattern → `<slug>-butler`.

### Detached mixed pools (read-only archives; deletion is a future operator GO — see cutover report)
Old role-axis banks that mixed multiple hardware estates. No profile binds to
them anymore (verified 2026-10-23, 63 profile dirs scanned, 0 violations); zero
post-flip writes (deathwatch snapshot in the report). **Detached, NOT deleted.**
- `Hermes q38` (6,092) — lane workers from all 5 estates + q38p test-farm legacy (≈1,831).
- `hb-infra-release` (3,027) — ops texture from g01/g02/sj/sjp/gaudi + q38p-deployer.
- `hb-inference-bench` (2,038) — watcher/bench observations from g02/gaudi (+q38p).
- `hb-synapse-sdk` (186) — gaudi SDK facts (gaudi-pure, but slated for fresh
  start by the 2026-10-23 operator ruling; superseded by `gaudi-hpu-sdk`).

### Frozen legacy per-board summary banks (created 2026-10-12 by board-migration seeder)
Not bound to any standing profile; unchanged by this cutover; deletion folds
into the same operator review: `gargantua01` (18) · `gargantua02` (14) ·
`skipjack` (6) · `skipjack-prototype` (6) · `gaudi` (125).

### hermes-general (6,011)
Previously classified "detached read-only legacy"; **live `default`-lane writes
observed 2026-10-23** (see root-lane warning above). Not a delete candidate yet.

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
g02-watcher (522), gaudi benchrunner/auditor (375/216 in Hermes q38). The pools
remain server-side as read-only archives, so nothing is destroyed before an
explicit delete GO.

## 3. Rules of the road going forward

1. **To set a profile's bank**: edit `hindsight/config.json` `bank_id` (and the
   `banks{}` carrier to match) — and keep the `.env` free of
   `HINDSIGHT_BANK_ID` unless the env pin is the intended mechanism. Never
   leave the pair disagreeing: the pair is a silent override waiting to happen.
2. **Butler profiles**: `.env` keeps `HINDSIGHT_BANK_ID` unset (or explicitly
   commented with the reason) — bank comes from config.json.
3. **Husks** (no hindsight wiring): `coding`, `kworker-muse-probe`,
   `plugin-ab`, `.deleted` — ignore until provisioned or removed.
4. **New hardware environment?** One fresh `<env>-infra` bank + fleet flip,
   following the 2026-10-23 cutover receipts as the recipe.
5. **Running sessions cache their bank at startup** — bank flips take effect on
   the next fresh process (dispatcher-spawned workers: next claim; served
   sessions: next reload). Deathwatch any detached bank for 24h after a cutover
   to catch missed reloads.
6. This map is the source of truth; when adding a profile, pick the env bank of
   its estate and record it here.

**Rollback for the 2026-10-23 cutover**:
`~/kanban-backups/env-bank-cutover-20261023T172208Z/` — pre-cutover
`hindsight/config.json` + `.env` for every profile (tar: `pre-cutover-profile-configs.tar.gz`),
pre/post bank snapshots, flip receipts, canary log. Restore = untar + copy the
profile's two files back; aliases removable via
`DELETE /v1/default/banks/{bank}/aliases/{alias}`; the 7 new banks are harmless
if left orphaned (or removable by operator GO later).
