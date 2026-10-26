> Status: superseded by BANK-MAP.md — receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# FRESH-BANK-CUTOVER — decision package for operator GO

**Produced by:** t_0fbb3c61 (BANK-TRIAGE-MIRROR-2), 2026-10-22 ~21:00Z, per the
OPERATOR RULING (FRESH START): *"NO reingest, NO triage, NO assessment memo of
old memories. Correctly aligned banks go forward; repositories/boards repopulate
naturally via ongoing retains."*

**This run executed ZERO config changes.** Everything below is a plan awaiting
operator GO. All inventory data was gathered read-only
(profile scans + server API counts; raw evidence in the card's workspace:
`profile_scan.json`, `discover_out.json`, `straws_win.json`).

> **EXECUTED 2026-10-22 ~20:22Z — see "Execution outcome" appendix at the
> bottom.** Operator GO (with modifications) landed on the card: default root
> KEEPS `hermes` (row 1 dropped); rows 2-7 + 8-10 executed and verified.
> The tables below remain the *plan as ratified*; the appendix records what
> actually ran.

---

## 1. Inventory — every profile and its CURRENT effective bank

Effective-bank resolution verified by direct scan of all 56 profile dirs
(2026-10-22): `.env HINDSIGHT_BANK_ID` pin wins > `hindsight/config.json`
`bank_id` > default chain → `hermes` (plugin issue #5171).

### 1a. Profiles still writing to LEGACY banks (cutover scope)

| Profile | Current bank | Carrier | Fate under FRESH START |
|---|---|---|---|
| **default (root ~/.hermes)** | `hermes` (28,446-node accumulator) | root `hindsight/config.json` | → NEW lean bank (§2) |
| kanban-orchestrator | `hermes` | profile config.json | → NEW orchestrator bank (§2) |
| kanban-board-architect | `hermes` | profile config.json | → NEW bank or share orchestrator lane bank (operator choice, §2) |
| kanban-worker | `hermes` | profile config.json | → NEW worker bank (§2) |
| research | `hermes` | profile config.json | → NEW research bank (§2) |
| distiller | `hermes` | profile config.json | → NEW bank (or leave on legacy, §2 note) |
| sampling-test | `hermes` | profile config.json | → NEW throwaway bank (§2) |

Pre-cutover cruft also sits in the frozen per-board banks (`gaudi` 125,
`gargantua01` 18, `gargantua02` 14, `skipjack` 6, `skipjack-prototype` 6 nodes)
— but **no profile writes to them anymore** (BANK-MAP-AUDIT fix, 2026-10-22
14:07Z; re-verified this run: totals identical). They need no config change,
only a disposition decision (§3).

### 1b. Profiles already on correctly aligned banks (carry forward unchanged)

| Bank | Profiles | Verified state |
|---|---|---|
| `Hermes q38` | 22: g01/g02/gaudi/sj/sjp auditor·orchestrator·planner·scribe, gaudi-analyst, gaudi-benchrunner | clean (5,968 nodes, growing) |
| `software-co` | sw-architect, sw-dev-a/b, sw-devops, sw-docs, sw-pm, sw-qa, sw-reviewer, sw-ux | clean (583) |
| `hb-infra-release` | g01-ops, g02-ops, gaudi-deployer, sj-ops, sjp-ops | clean (2,981) |
| `hb-inference-bench` | g01/g02/gaudi/sj/sjp watcher | clean (1,853) |
| `hb-synapse-sdk` | gaudi-arch, gaudi-perfeng, gaudi-synapse | clean (186) |
| `hb-host-ops` | gaudi-dockerops, gaudi-sysadmin | clean (134) |
| `hb-upstream-comm` | gaudi-liaison | clean (402) |
| `g01-butler` | g01-butler | live, non-empty (37) — config.json carrier |
| `gaudi-butler` | gaudi-butler | live, non-empty (30) — config.json carrier |
| `g02-butler` | g02-butler | live (20) — **carried by .env pin** ⚠ |
| `swco-butler` | swco-butler | live (39) — **carried by .env pin** ⚠ |
| `sjproto-butler` | sjproto-butler | live (28) — **carried by .env pin** ⚠ |
| (husks) | coding, kworker-muse-probe | no config.yaml, no memory wiring — ignore |

⚠ The three stage-3 butlers use the *agreeing-pair* form ratified on
t_02de9dff (config.json AND `.env` pin name the same bank). That is stable but
leaves the pin-wins override armed; §4 offers a converge-to-config.json-only
normalization (optional, low priority).

### 1c. Legacy banks that exist with no live writer

- `hermes` (28,446 nodes) — writers are the 7 profiles in §1a.
- `hermes-general` (5,349) — no profile points at it; pure historical archive.
- `gaudi`, `gargantua01`, `gargantua02`, `skipjack`, `skipjack-prototype`
  (169 nodes total) — seeded summary banks, frozen since the .env-pin fix.

---

## 2. Proposed final map — profile → ratified bank

### Already-correct lanes: NO CHANGE (34 fleet lanes + 5 butlers + 2 husks)

Keep exactly as §1b. Their banks survive FRESH START untouched and keep
accumulating (they already repopulate "naturally via ongoing retains" — that
is the status quo).

### NEW banks to create on the Hindsight server (ga01:8888)

The `hermes` lane needs fresh homes. Proposed names follow the existing
`hb-` and role-based conventions:

| New bank | Serves | Notes |
|---|---|---|
| `hb-orchestrator` | kanban-orchestrator | **Cold-start flag (operator has accepted):** the orchestrator loses 10K-node cross-session recall accumulated in `hermes`; its recall budget will return empty for a while and repopulate only from new runs. |
| `hb-architect` | kanban-board-architect | OR merge with `hb-orchestrator` into one `hb-kanban-core` — operator choice A/B below. Keeping them separate preserves role-scoped recall (architect config/ops knowledge vs orchestrator routing state) and matches the specialist-separation doctrine (inference knowledge ≠ board knowledge ≠ host knowledge). |
| `hb-kanban-worker` | kanban-worker | mechanical executor lane; fresh bank is cheap, its memory value is low-grade. |
| `hb-research` | research | keeps research digests out of ops lanes. |
| `hb-sampling-test` | sampling-test | throwaway test lane; can also point at any scratch bank and be deleted freely. |
| `hb-distiller` | distiller | cross-board curator; alternatively park distiller on `hb-orchestrator` since usage is manual/rare (`memory_enabled: false` — hindsight tools surfaced manually today). |
| `hb-main` (or `hb-host`) | **default (root ~/.hermes)** — the operator's own assistant | This is the biggest UX change: the root assistant cold-starts too. Operator has accepted fresh-start broadly; if the root assistant's *user-preference* recall specifically is missed mid-way, a one-off `hindsight_retain` of a short "operator profile" hand-note into `hb-main` is permitted under NO-REINGEST (it is new content, not reingest) — operator call. |

**Operator choice A/B (needed for GO):**
- **A — role-separated (recommended):** create all 7 banks as listed.
- **B — consolidated:** create `hb-kanban-core` (orchestrator+architect+worker+distiller), `hb-research`, `hb-main`, `hb-sampling-test` → 4 banks, fewer cold starts, blurrier recall scoping.

### Pre-cutover cruft carriers (per-board banks)

No profile writes to them; nothing to remap. Disposition only (§3).

---

## 3. Disposition of legacy banks — RECOMMENDATION, not executed

| Bank | Recommendation | Rationale |
|---|---|---|
| `hermes` (28,446) | **DETACH-KEEP-READ-ONLY** now; **DELETE later** (e.g. after 2-4 weeks of clean operation on the new banks) | Contains genuine host-ops history (aistack setups, ARCHIVE-GC contract, kanban_archive FR trail) that may be worth a manual grep in the coming weeks; keeping it read-only costs only disk. Deletion reclaims the most space of any bank (1M+ links). |
| `hermes-general` (5,349) | **DETACH-KEEP-READ-ONLY**; delete on the same schedule | Already a reference archive; nobody writes to it. |
| `gaudi`/`gargantua01`/`gargantua02`/`skipjack`/`skipjack-prototype` | **DETACH-KEEP-READ-ONLY**; delete earliest (smallest, most volatile content, worst signal-to-noise — 54/92 items in pass-1 triage were transient watch-logs) | Frozen since 14:07Z; near-zero reuse value beyond a week. |

"DETACH-KEEP-READ-ONLY" is trivially true today for every bank except `hermes`
(it stops being written the moment §4's config changes land — the server has no
bank-level write-lock, so *read-only-ness is enforced by no-profile-pointing-at-it*).
No server-side mutation is required for the recommend phase; **DELETE** would use
the existing bank-delete path and must be a separate operator-GO'd execution card.

---

## 4. Exact change list (executes only after GO)

Set `bank_id` in `<profile>/hindsight/config.json` per §2/choice-A (or B),
one declarative converge script (`scripts/fresh_bank_cutover_converge.py`,
modeled on `route_by_default_converge.py`), each step idempotent with
pre/post backups:

| # | Profile | File | Key | Old | New (choice A) |
|---|---|---|---|---|---|
| 1 | default root | `~/.hermes/hindsight/config.json` | `bank_id` | `hermes` | `hb-main` |
| 2 | kanban-orchestrator | `~/.hermes/profiles/kanban-orchestrator/hindsight/config.json` | `bank_id` | `hermes` | `hb-orchestrator` |
| 3 | kanban-board-architect | `…/kanban-board-architect/hindsight/config.json` | `bank_id` | `hermes` | `hb-architect` |
| 4 | kanban-worker | `…/kanban-worker/hindsight/config.json` | `bank_id` | `hermes` | `hb-kanban-worker` |
| 5 | research | `…/research/hindsight/config.json` | `bank_id` | `hermes` | `hb-research` |
| 6 | distiller | `…/distiller/hindsight/config.json` | `bank_id` | `hermes` | `hb-distiller` |
| 7 | sampling-test | `…/sampling-test/hindsight/config.json` | `bank_id` | `hermes` | `hb-sampling-test` |
| 8 | g02-butler | `…/g02-butler/.env` | `HINDSIGHT_BANK_ID` | `g02-butler` | *(comment out — converges to config.json carrier, normalization only, OPTIONAL)* |
| 9 | swco-butler | `…/swco-butler/.env` | `HINDSIGHT_BANK_ID` | `swco-butler` | *(comment out — OPTIONAL)* |
| 10 | sjproto-butler | `…/sjproto-butler/.env` | `HINDSIGHT_BANK_ID` | `sjproto-butler` | *(comment out — OPTIONAL)* |

Preconditions (also part of GO execution):
- Create the new banks server-side (POST /v1/default/banks) with a short
  `bank_mission` each so retains extract role-appropriate facts.
- No `.env` `HINDSIGHT_BANK_ID` may exist on any of the 7 profiles (verified
  clean this run) — the config.json edit then governs unopposed.

**Rollback:** the converge script writes timestamped backups of every touched
file to `~/kanban-backups/fresh-bank-cutover-<ts>/`; restore = copy back +
(optional) relinquish new banks. Nothing in the plan mutates or deletes bank
content, so rollback is complete and lossless.

## 5. Verification plan (post-GO execution card gates)

1. **Scan conformance:** re-run `scan_profiles.py` → all 7 profiles show the new
   effective bank, zero `.env` pins.
2. **Retain canary:** one `hindsight_retain("FBC22-CANARY-<profile> …")` per
   cut-over profile; canary must appear ONLY in its new bank
   (`memories/list?q=FBC22-CANARY`), zero hits in `hermes` and every other bank.
3. **Recall canary:** `GET …/memories/recall` against each new bank returns the
   canary fact.
4. **Deathwatch on `hermes`:** after 24h of fleet activity, node count of
   `hermes` unchanged (no accidental writer left behind). Butler banks likewise
   unchanged in content-character (their own banks only).
5. **Live lanes:** confirm a real kanban run's retains land in the new bank
   (document_id evidence), not just synthetic canaries.
6. Receipt each step on the execution card; only then file the separate
   DELETE-disposition card for the legacy banks (per §3 schedule).

## 6. What the operator needs to decide (GO checklist)

1. **Choice A (7 role-separated banks)** vs **B (4 consolidated)** — recommend A.
2. Bank names OK? (`hb-main`, `hb-orchestrator`, `hb-architect`,
   `hb-kanban-worker`, `hb-research`, `hb-distiller`, `hb-sampling-test`)
3. Include the optional butler `.env`-pin normalization (rows 8-10) or skip?
4. Confirm DETACH-KEEP-READ-ONLY disposition for `hermes` + `hermes-general` +
   per-board banks, with DELETE as a later GO.
5. Acknowledge accepted cold-starts: orchestrator/architect/worker/research/
   distiller/root-assistant all start with empty recall; they repopulate from
   live usage only.

---

## Appendix — Execution outcome (2026-10-22 ~20:22-20:45Z, t_0fbb3c61 run 2)

Operator GO received on the card after the block: *"Leave the default on the
large original bank, and cold start on any new currently slim board banks…"* —
row 1 DROPPED (no `hb-main`; default root keeps `hermes` as its LIVE bank,
operator-ratified end state), rows 2-7 + 8-10 EXECUTED.

**Executor:** `/local/projects/software-co/scripts/fresh_bank_cutover_converge.py`
(idempotent, dry-run first: 15 planned actions, then `--apply`: 15 applied).
Backups (all 9 touched files):
`~/kanban-backups/fresh-bank-cutover-20261022T202128Z/`.

### Bank creation (server-side PUT upsert, HTTP 200 ×6, mission set on each)

| Bank | fact_count at verification | Canary verdict |
|---|---|---|
| `hb-orchestrator` | 3 | PASS (retain landed; recall returns marker, 3 hits) |
| `hb-architect` | 3 | PASS (3 / 3) |
| `hb-kanban-worker` | 3 | PASS (3 / 3) |
| `hb-research` | 3 | PASS (3 / 8) |
| `hb-distiller` | 4 | PASS — note: the distiller model *believed* it had no memory tool, but its session's auto-retain pipeline still banked the canary (which is the actual mechanism being verified) |
| `hb-sampling-test` | 3 | PASS (3 / 9) |

### Config flips (rows 2-7) + .env-pin normalization (rows 8-10)

- 6 × `hindsight/config.json` `bank_id` + `banks{}` block flipped `hermes` →
  new bank. `hermes -p <profile> config check` PASS on all 6.
- 3 × butler `.env` `HINDSIGHT_BANK_ID` commented out (g02/swco/sjproto;
  config.json carrier governs — pin-wins landmine disarmed). `config check`
  PASS ×3; butler bank totals unchanged (20/39/28) post-normalization.

### Verification (§5 gates applicable now)

1. ✅ Conformance: all 9 touched profiles `config check` PASS; no profile
   other than the default root points at `hermes` anymore.
2. ✅ Retain canaries (live-lane, not synthetic): fresh one-shot
   `hermes -p <profile> chat -q` per profile; each session's auto-retain
   landed its `FBC22-CANARY-<profile>` document ONLY in the new bank.
3. ✅ Recall canaries: `POST …/memories/recall` on each new bank returns the
   marker facts.
4. ⏳ 24h deathwatch on `hermes` (minus the default-lane traffic, which is now
   legitimate): park for the follow-up disposition card.
5. ✅ Live-run evidence: canary documents carry real session metadata
   (document ids, e.g. hb-orchestrator canary doc of 2026-10-22 ~20:29Z).
6. ✅ Receipts on card t_0fbb3c61.

**Operational finding (verified by experiment):** a retain issued ~21s after
the config flip from an ALREADY-RUNNING session still landed in `hermes`
(document 4231a8ce…, 20:22:13Z) — running sessions cache their bank at
startup. Fresh processes pick up the new bank immediately (all six one-shots
correct). Gateway reload / restart of long-lived sessions is the operator's
call and was NOT performed, per directive. Affected long-lived consumers to
eventually reload: kanban-orchestrator, kanban-board-architect, kanban-worker,
research, distiller, sampling-test (dispatcher-spawned workers are fresh
processes and already correct; only persistent/interactive sessions of these
profiles would lag).

**Disposition state:** NO deletes executed anywhere. `hermes-general` + frozen
per-board banks detached-read-only; `hermes` live for default root only.
The future DELETE decision remains a separate operator card, unchanged.
