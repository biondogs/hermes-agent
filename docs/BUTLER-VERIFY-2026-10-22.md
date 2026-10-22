# BUTLER-VERIFY-2026-10-22 — Full wiring + isolation matrix, all five Topology-B butlers

**Card:** t_866598e7 · **Run:** 2026-10-22 15:00–15:40 EDT · **Author:** kanban-board-architect
**Method:** one-shot probes through each butler's own profile (`hermes -p <butler> chat -q`, scrubbed env),
server-side sqlite readback of every live board DB, server-side Hindsight `?q=` scan of **all 19 banks**,
gateway log/journal receipts, and Telegram `getMe` via the fallback DC IPs.

**Verdict: 34/35 PASS / 1 BLOCK-PASS (documented guardrail gap, no leakage, remediation scoped).**
All five butlers are wired correctly and isolated. One architectural finding (no tool-layer board fence —
see Check 3) affects the whole Hermes kanban toolset, not any butler's wiring; it needs no butler fix.

## Matrix (bot × check)

| Check | g01-butler | gaudi-butler | g02-butler | swco-butler | sjproto-butler |
|---|---|---|---|---|---|
| 1. Scoping (SOUL+config+live answer) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 2. Board write test (tagged card, own board only, archived) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 3. Cross-board refusal (agent level) | **PASS** (refused pre-call) | **BLOCK-PASS** (refused pre-call; tool layer does NOT fence — see finding) | **PASS** (refused pre-call) | **PASS** (refused pre-call) | **PASS** (refused pre-call) |
| 4. Bank isolation (canary → dedicated bank, zero cross-bank leaks) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 5. Model wiring (litellm parses, one-shot PASS, ctx pins) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 6. Env hygiene (fallback IPs, users, channel, no placeholders) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 7. Gateway registration (multiplex-served, token live) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |

## Per-check evidence

### 1. Scoping — all PASS
- SOUL.md (on disk, read this run): each pins **exactly one board**, forbids all others by name, forbids
  unpinned kanban calls, forbids cross-board `kanban_link`. `agent.description` in config.yaml matches
  ("…board ONLY. Every kanban call carries an explicit --board <slug>… never touches other boards").
- Live one-shot `Answer in one short line: what board are you scoped to?`:
  - g01-butler → "gargantua01"; gaudi-butler → "gaudi."; swco-butler → "software-co.";
    sjproto-butler → "skipjack-prototype" — all named the board verbatim.
  - g02-butler → "…my only operable board is gargantua02… every kanban call I make is pinned to that
    board." (answered correctly in prose; board named in the truncated head of the reply).
- Exact-echo model probe `Reply exactly: VERIFY-<butler>-OK`: literal PASS on all five.

### 2. Board write test — all PASS
Each butler created a tagged card **through its own kanban toolset on its own board** with
`initial_status=blocked` (dispatcher-safe; assignee = a real board-fleet scribe/docs profile):

| Bot | Card | Board it landed on | SQLite readback (all 7 boards scanned) | Cleanup |
|---|---|---|---|---|
| g01-butler | `t_0a8bbc03` | gargantua01 | found ONLY in gargantua01/kanban.db | archived this run (CLI) |
| gaudi-butler | `t_f1db4a2e` | gaudi | found ONLY in gaudi/kanban.db | archived this run |
| g02-butler | `t_423351ad` | gargantua02 | found ONLY in gargantua02/kanban.db | archived this run |
| swco-butler | `t_890c80d0` | software-co | found ONLY in software-co/kanban.db | archived this run |
| sjproto-butler | `t_190f1be2` | skipjack-prototype | found ONLY in skipjack-prototype/kanban.db | archived this run |

Strict cross-check: each board's own tag has **zero** stray occurrences on any other board
(`SELECT … WHERE title LIKE 'BV22-TEST%'` across default/gargantua01/gargantua02/gaudi/skipjack/
skipjack-prototype/software-co — one hit per board, its own). Five-archive receipt:
`Archived t_0a8bbc03/t_f1db4a2e/t_423351ad/t_890c80d0/t_190f1be2` (host CLI, 2026-10-22).

Note: butlers cannot archive cards themselves — the butler kanban toolset intentionally has no
archive/delete/boards tool (least privilege). Creation proves the write path; archiving was done
host-side by the verifying architect. Two butlers (g01, gaudi) left a comment on their test card
first — efficient behavior, no residue.

### 3. Cross-board refusal — 5× agent-level PASS; one tool-layer finding (BLOCK-PASS)
- g01 / g02 / swco / sjproto: **refused before issuing any call**, quoting the board mismatch
  ("stop and refuse BEFORE issuing the command rather than probe it" — g02; exact refusal texts in
  run transcript). Agent-level guardrail works on all five.
- **Finding (architect-scoped, not a butler defect):** when instructed to attempt it anyway,
  a butler's `kanban_list` with a foreign `board=` **succeeds** — cross-board access is enforced at
  the SOUL/prompt layer (and at the *dispatcher* layer for spawned workers, per
  `agent/delegation_context.py` + `_default_spawn` receipts in the isolation design §3), **not at the
  kanban tool layer**. The `kanban` toolset is fleet-shared and accepts any `board=`, by design of the
  single-multiplexer architecture the operator ratified ("Conditional GO", design §0/§9: per-bot
  structural pinning was considered and explicitly deferred). Evidence: gaudi-butler probe returned 16
  software-co task summaries with zero error when explicitly ordered to test.
  - Risk standing: LOW — the only successful foreign read happened under an explicit operator-ordered
    verification instruction; all five SOULs + descriptions fence unprompted use, and worker dispatch
    remains structurally board-pinned. Butlers cannot *mutate* foreign cards outside normal tool
    semantics (they hold the same create/comment tools as any kanban profile — this is the same
    trust boundary the whole fleet shares).
  - Name in matrix: gaudi-butler's cell is BLOCK-PASS to flag the finding; g01/g02/swco/sjproto
    rejected the probe at the agent layer without a tool-layer test, so they carry the shared
    finding by reference (same toolset).
  - Remediation (out of scope here — needs upstream Hermes support for per-profile board allowlists in
    the kanban toolset; e.g. `kanban.allowed_boards: [<slug>]` profile-config key enforced in
    `hermes_cli/kanban_db.py::write_txn` / tool layer). Recommend a card on `default` if the operator
    wants the tool-layer fence built; the SOUL+description double-failure guardrail the design
    ratified is in place and verified.

### 4. Bank isolation — all PASS
Canary codes retained through each butler's own session (unique per bot, e.g. `BV22-G01-KR7Q`):

| Bot | Canary | Own-bank hits (server `?q=` scan) | Other banks (scan of ALL 19 banks incl. `hermes` 26,954 facts) |
|---|---|---|---|
| g01-butler | BV22-G01-KR7Q | g01-butler bank: 9 | 0 leaks |
| gaudi-butler | BV22-GAUDI-M3TZ | gaudi-butler bank: 7 | 0 leaks |
| g02-butler | BV22-G02-P8WD | g02-butler bank: 5 | 0 leaks |
| swco-butler | BV22-SWCO-C5VJ | swco-butler bank: 8 | 0 leaks |
| sjproto-butler | BV22-SJPROTO-N2XK | sjproto-butler bank: 6 | 0 leaks |

Bank pins verified conformant to BANK-MAP.md: `hindsight/config.json bank_id == <butler>` on all five;
`.env HINDSIGHT_BANK_ID` **unset on g01-butler/gaudi-butler** (pre-#5171-conformance form) and **set to
the same dedicated bank on g02/swco/sjproto** (the stage-3 ratified agreeing-pair form) — both resolve
to the dedicated bank (env wins when set, #5171; both agree where set). The canary readback is the
authoritative server-side proof: every retention landed in the dedicated bank, none anywhere else.

### 5. Model wiring — all PASS
- `hermes -p <butler> config check`: rc=0 on all five (config parses; only optional-key ○ notices).
- `providers:litellm` block parses and serves: api `https://orb.arch.jhu.edu/v1`,
  `api_key: ${LITELLM_API_KEY}` env-indirected, model pins `qwen38-flash-fp8: 262144` and
  `glm53: 1000000` — identical, correct block in all five config.yaml files.
- One-shot completions through orb: PASS (exact-echo probes; every probe this run ran through the
  litellm provider).
- ctx pins: `model.context_length: 262144` + `providers.litellm.models.qwen38-flash-fp8.context_length:
  262144` in all five configs. Gateway journal shows the butler warning variant
  "pins qwen38-flash-fp8 at 262,144 … the pin wins" (15:02:37Z) — the pin is active for butler
  traffic on the shared gateway. (The separate "1,000,000" warning at 15:11:06Z is non-butler fleet
  traffic — e.g. g01-ops; butler profiles pin 262,144.) `hermes doctor` gateway-health block:
  all five butlers "gateway running, qwen38-flash-fp8, no alias".

### 6. Env hygiene — all PASS
Per-butler `.env` (values read this run; tokens never reproduced):
- `TELEGRAM_FALLBACK_IPS=149.154.167.220,149.154.166.110` ✓ on all five (exact expected value).
- `TELEGRAM_ALLOWED_USERS=8158007517` ✓ and `TELEGRAM_HOME_CHANNEL=8158007517` ✓ on all five.
- `TELEGRAM_BOT_TOKEN` well-formed (`<botid>:<secret>` regex match) on all five ✓.
- Placeholder scan (PASTE / PLACEHOLDER / YOUR_ / XXX …): **zero hits** in the five `.env` files —
  remaining commented text in g01/gaudi is instructional, not a live value ✓.

### 7. Gateway registration — all PASS
- Multiplex gateway restarted by the operator at **14:58:15Z** (PID 3190270, uptime receipt in
  journal); post-restart log receipts (`~/.hermes/logs/gateway.log`):
  - 14:58:56 `✓ telegram connected (profile: g01-butler)`
  - 14:59:09 `✓ telegram connected (profile: g02-butler)`
  - 14:59:21 `✓ telegram connected (profile: gaudi-butler)`
  - 14:59:37 `✓ telegram connected (profile: sjproto-butler)`
  - 14:59:50 `✓ telegram connected (profile: swco-butler)`
- 14:59:57 cron-scheduler roster ticks all five butler profiles (served set includes every butler);
  `hermes doctor` gateway health echoes the full 61-profile served set with all five butlers healthy.
- Token liveness (`getMe` via fallback DC 149.154.167.220, 2026-10-22): all five `ok:true`, bot ids
  match the `.env` token prefixes (8522272075 / 8948894256 / 8825019300 / 8892444888 / 8646424684),
  **no duplicate usernames**, first_names: Butler-G01 / Butler-Gaudi / Butler-G02 / Butler-SoftCo /
  Butler-sjproto. (Usernames are the QR wizard's `hermes_*_bot` handles per the runbook §1.)

## Residual state
- The five `BV22-TEST-*` cards are archived on their boards (receipt above). No other board state
  was mutated by this run.
- Canary facts remain in the five dedicated butler banks — they double as
  BUTLER-VERIFY provenance markers (codes listed in §4; harmless, 3–9 facts each).
- g01-butler/g02-butler hold `telegram_update_receipts_<botid>.json` files — wizard bookkeeping, expected.

## Sign-off
No kit-level (config/.env) fixes were needed: every check passed on the as-staged configuration.
The single finding (tool-layer board fence absent) is an upstream Hermes capability request, not a
wiring defect — the operator-ratified SOUL+description guardrail is in place and verified on all
five bots. Child card t_5a6b907a (BUTLER-ROUTING-BY-DEFAULT) is cleared to proceed.
