> Status: superseded by BANK-MAP.md + hermes-estate/docs/GOVERNANCE.md G-13 — receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# BANK-ENV-CUTOVER — Operator Review Report (2026-10-23)

**Card:** t_7d3062dc — BANK-ENV-AXIS-REVIEW · **Executor:** kanban-board-architect
**Authority:** Operator DM ruling 2026-10-23 (design-and-execute): "when the architect
is done ruling and reframing the memory bank arrangement, it is ok to fresh start
everything… clean bad mixed memory pools, and fix the name of the banks for increased
readability. Once everything is done create a report suggesting all the changes and
which banks can be deleted for user review."
**State:** EXECUTED and verified 2026-10-23 ~17:22–18:15 UTC. **No server-side deletes
performed** — every deletion below is a PROPOSAL awaiting your GO, per bank or in bulk.

---

## 1. What was wrong (measured, not assumed)

The 10-22 fresh start organized banks by LANE ROLE; the same role bank served all five
hardware estates. Classification of every fact in the shared pools (by writer
`agent_identity` + content keywords):

| Pool | Total | g01 | g02 | sj | sjp | gaudi | q38p-legacy* | unattributable |
|---|---|---|---|---|---|---|---|---|
| `hb-infra-release` | 3,027 | ~431 | ~1,073 | ~245 | ~2 | ~106 | ~202 | ~975 |
| `hb-inference-bench` | 2,038 | — | ~683 | — | ~2 | ~858 | ~33 | ~467 |
| `Hermes q38` | 6,092 | ~68 | ~665 | ~292 | — | ~1,156 | ~1,831 | ~2,196 |
| `hb-synapse-sdk` | 186 | — | — | — | — | 186 | — | — |

*`q38p-*` = pre-rename test-farm fleet (husk profiles, deleted); `Hermes q38` is a
test-farm-era name — its single biggest content class is that legacy fleet.

Concrete harm: a Gargantua02 watcher recalled Habana/HPU bench lore as if it applied
to Azure H100 VMs. Naming opacity confirmed by your own message: "hb" is
**hindsight-bank**, not Habana.

## 2. Taxonomy executed — hardware environment as the primary axis

**Shape chosen: per-env banks (your option "per-env banks… + role as secondary where
needed"), not an env×role grid.** Rationale: (1) it matches your stated intuition;
(2) a full grid would create ~15 extra near-empty banks for lanes that write
200-1,000 facts/month; (3) the only role separation with a standing operator
amendment is gaudi's (ORCH AMEND t_fd8ca6f0: "inference knowledge must NOT live in
general board knowledge") — preserved as gaudi role sub-banks.

### New banks created (fresh, empty, missions set server-side)
| Bank | Environment / lane |
|---|---|
| `g01-infra` | Gargantua01 — prototype k8s |
| `g02-infra` | Gargantua02 — production k8s, Azure VMs 413-418 |
| `skipjack-infra` | Skipjack — HPC/AI hybrid cluster (mgmt02) |
| `skipjack-prototype-infra` | Skipjack Prototype — k8s on gh207+gh208 |
| `gaudi-hpu` | Gaudi host (ga01, Habana HPU) — general board/infra lane |
| `gaudi-hpu-perf` | Gaudi — inference/bench lane (ORCH AMEND preserved) |
| `gaudi-hpu-sdk` | Gaudi — SynapsePT/SDK/kernel lane |

### Renames via server-side bank aliases (content preserved, zero churn)
Hindsight natively supports bank aliases ("another id to answer to" — verified; 409 on
collisions; zero data movement). Two banks were gaudi-PURE (unmixed), so instead of
cold-starting them they got readable aliases and the two bound profiles now address
them by the new name:

| Alias (new name) | Underlying server id | Facts preserved |
|---|---|---|
| `gaudi-hpu-hostops` | `hb-host-ops` | 139 |
| `gaudi-hpu-upstream` | `hb-upstream-comm` | 421 |

### Per-profile binding flips — 38 profiles, hindsight/config.json carrier only
| Fleet (profiles) | Old banks | New bank |
|---|---|---|
| g01: orchestrator, planner, auditor, scribe, ops, watcher | Hermes q38 / hb-infra-release / hb-inference-bench | `g01-infra` |
| g02: same 6 roles | same three | `g02-infra` |
| sj: same 6 roles | same three | `skipjack-infra` |
| sjp: same 6 roles | same three | `skipjack-prototype-infra` |
| gaudi: orchestrator, planner, auditor, scribe, deployer | Hermes q38 / hb-infra-release | `gaudi-hpu` |
| gaudi: analyst, benchrunner, watcher | Hermes q38 / hb-inference-bench | `gaudi-hpu-perf` |
| gaudi: arch, perfeng, synapse | `hb-synapse-sdk` | `gaudi-hpu-sdk` |
| gaudi: dockerops, sysadmin | `hb-host-ops` | `gaudi-hpu-hostops` (alias) |
| gaudi: liaison | `hb-upstream-comm` | `gaudi-hpu-upstream` (alias) |

**Unchanged by design:** software-co fleet → `software-co` (kept in production);
all 5 butler banks (isolation preserved, names already readable); kanban-core lanes
(`hb-orchestrator`, `hb-architect`, `hb-kanban-worker`, `hb-research`, `hb-distiller`,
`hb-sampling-test`, `hb-unsloth-studio` — fresh 10-22 banks, healthy, single-profile);
root default → `hermes` (live, operator-ratified 10-22).

## 3. Verification receipts (all PASS)

1. **Backup first:** `~/kanban-backups/env-bank-cutover-20261023T172208Z/` —
   pre-cutover `hindsight/config.json` + `.env` for every profile (tar), pre/post
   server snapshots, flip receipts, canary log.
2. **38 flips, 0 errors**, each with on-disk readback assertion
   (`flip-receipts.json`).
3. **Fleet conformance sweep:** all 63 profile dirs scanned — 0 active
   `HINDSIGHT_BANK_ID` pins anywhere (#5171 law holds; config.json carrier governs),
   0 profiles still bound to a mixed pool
   (`post-flip-binding-table.json`).
4. **Canary retain+recall, one fresh one-shot session per new/aliased bank (9/9 OK):**
   unique markers EBX23* retained from fresh sessions → found in the correct bank;
   **0 cross-env leaks** (every marker queried in every other new bank = 0 hits);
   alias banks verified under BOTH ids (marker counts identical via alias and
   underlying id).
5. **Clean detach:** mixed pools show zero writes after the flip —
   `hb-infra-release` 3,027 (last write 03:45Z), `hb-inference-bench` 2,038
   (17:04Z), `Hermes q38` 6,092 (17:04Z), `hb-synapse-sdk` 186 (10-14) — all
   timestamps pre-flip.
6. **Bank inventory:** 33 banks (26 before), exactly the 7 planned additions.

Known caveat (verified on 10-22, applies here): long-lived sessions cache their bank
at startup. Dispatcher-spawned workers are fresh processes (next claim picks up the
new binding); if any served/gateway session predates the flip it may still write to a
mixed pool until reloaded — recommend a 24h deathwatch recheck of the four pools
(tomorrow's nightly audit can carry it).

## 4. Recall-quality cost of the cold start (what workers lost)

Per your fresh-start ruling, no history was reingested. Each fleet worker recalls an
empty bank until it repopulates from live runs. Largest per-writer losses (= their own
facts now archived in mixed pools): g02-ops 901 · gaudi-watcher 704 · q38p-deployer 145
(legacy) · g02-watcher 522 · gaudi-benchrunner 375 · g02-auditor 259 · gaudi-auditor
216 · sj-ops 175 · g01-ops 328 … plus ~5,300 facts with no writer metadata. Workers did
NOT lose: butler memory, software-co lore, kanban-core lanes, hostops/upstream gaudi
banks (preserved via aliases). Mitigation: the archived pools stay queryable
server-side until the delete decision, so any critical fact is recoverable by targeted
recall during a hand-over if needed.

## 5. DELETE CANDIDATES — for your review (no deletion performed)

| # | Bank | Facts | Detached? | Why deletion is safe / caveats |
|---|---|---|---|---|
| 1 | `Hermes q38` | 6,092 | Yes — 0 bindings, 0 post-flip writes | Old test-farm-era mixed pool; content ~30% pre-rename q38p legacy; ~36% gaudi; ~11% g02; no lane needs it; new env banks hold the living texture. Biggest single win for readability. |
| 2 | `hb-infra-release` | 3,027 | Yes | Mixed ops pool across 5 estates (majority g02-ops). Superseded by per-env infra banks. |
| 3 | `hb-inference-bench` | 2,038 | Yes | Mixed watcher/bench pool (gaudi + g02 dominant). Superseded by `gaudi-hpu-perf` + per-env banks. |
| 4 | `hb-synapse-sdk` | 186 | Yes | Gaudi-pure but slated for fresh start by your ruling; superseded by `gaudi-hpu-sdk`. Smallest loss. |
| 5 | `gargantua01` | 18 | Yes — frozen since 10-12 | Board-migration seeder summary; superseded by `g01-infra`. |
| 6 | `gargantua02` | 14 | Yes — frozen | Same; superseded by `g02-infra`. |
| 7 | `skipjack` | 6 | Yes — frozen | Same; superseded by `skipjack-infra`. |
| 8 | `skipjack-prototype` | 6 | Yes — frozen | Same; superseded by `skipjack-prototype-infra`. |
| 9 | `gaudi` (board bank) | 125 | Yes — frozen | Seeder summary + override-window strays (mostly gaudi-watcher); superseded by `gaudi-hpu`/`gaudi-hpu-perf`. |
| 10 | `hermes-general` | 6,011 | **NO — still live** | ⚠ NOT safe to delete yet: the default lane wrote 574 facts on 10-22/10-23 (identity `default`; mechanism unconfirmed — the root config binds `hermes`). Recommend investigating the writer first (candidate for a follow-up card). |

Not candidates: `hermes` (root assistant's live bank, ratified 10-22), `software-co`
(production per your instruction), butler banks (live, isolated), kanban-core `hb-*`
lanes + `hb-unsloth-studio` (live), the 7 new env banks + 2 alias underlyings
(`hb-host-ops`, `hb-upstream-comm` — live; the alias names are canonical in configs,
underlying ids can never be deleted while aliased).

**Deletion mechanics when you GO:** server-side `DELETE /v1/default/banks/{bank_id}`
(per bank, or name them in a bulk GO); I would snapshot each bank's export
(`GET …/export`) into `~/kanban-backups/` immediately before deleting, so even a GO is
reversible for as long as you keep the backup.

## 6. Proposed follow-ups (cards, not urgent)

1. **Deathwatch:** recheck the 4 mixed pools for late writes in tomorrow's nightly
   audit (catches any session that cached an old bank binding).
2. **`hermes-general` writer investigation** — prerequisite before it can ever become
   delete candidate #10.
3. Optional: alias-renames for the kanban-core `hb-*` lane banks for full `hb-`-free
   readability (low value; they are healthy and single-tenant).

**Rollback (if you want to undo any of this):** restore per-profile
`hindsight/config.json` from the backup tar; delete the two aliases
(`DELETE …/banks/hb-host-ops/aliases/gaudi-hpu-hostops`, same for upstream); new banks
can be left orphaned or deleted by GO. Full details in `docs/BANK-MAP.md` §Rollback.
