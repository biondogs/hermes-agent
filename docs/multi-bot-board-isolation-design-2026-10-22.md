# MULTI-BOT-BOARD-ISOLATION — Design & Go/No-Go

**Card:** t_2f367b34 · **Author:** kanban-board-architect · **Date:** 2026-10-22
**Host:** ga01 · **Hermes:** v0.22.4 (git @ 4d04303818b6, "Up to date")
**Status: DESIGN — no provisioning performed. Operator GO required before anything below is implemented.**

---

## 0. Verdict in one line

**Conditional GO** — the architecture is supported, cheap, and the core hazards are
already eliminated *if and only if* every operator-facing bot is plain multiplex-served
Telegram **plus an explicit `--board` / `--board=` argument per command**, and per-bot
structurally-pinned processes are *not* attempted. See §7 for the one config-level pin we
do recommend adding as a guardrail, and §9 for what would be REQUIRED for true
per-bot hard board pinning with a second gateway (and why we recommend against it under
the current gateway architecture).

**Recommended rollout (single change, no new gateways):** stay on the single default-home
multiplex gateway; create **5 butler profiles** (one per board) on the host's shared profile
root; each gets its own **new BotFather Telegram bot token** in its own profile `.env` (a
profile-scoped secret, never shared, never in the default home's `.env`); each butler's
SOUL.md and routing description name exactly one board and forbid all others; operator
commands use `/kanban --board <slug> …` explicitly. The dispatcher remains exactly one
(the host gateway at PID 2523045, today's live owner of
`~/.hermes/kanban/.dispatcher.lock`).

`HERMES_KANBAN_BOARD`-style per-process env pinning inside the shared gateway process is
**structurally impossible**: `agent/secret_scope.py` (`_GLOBAL_ENV_EXACT`,
`_GLOBAL_ENV_PREFIXES`) classifies `HERMES_KANBAN_DB`, `HERMES_KANBAN_BOARD`, and
`HERMES_KANBAN_WORKSPACES_ROOT` as *process-global environment variables* (by design —
they are per-board, not per-profile), so under multiplexing they are read from
`os.environ` of the single gateway process and cannot vary per served profile. Explicit
`--board` flags per CLI/tool call are the supported per-turn routing primitive today
(`hermes_cli/kanban.py`: "`--board <slug>` pins HERMES_KANBAN_BOARD for the duration of
this call so it inherits the exact resolution the dispatcher uses for workers"; the
gateway `/kanban` slash handler parses leading `--board`/`--board=` tokens the same way).

---

## 1. What the operator asked for

One Telegram bot per active kanban board (gargantua02, gargantua01, gaudi, skipjack+proto,
software-co), each served by a dedicated orchestrator profile whose gateway pins that one
board, so cross-board writes are structurally impossible: "manage each board independently
without ever putting the wrong tasks on the wrong boards."

## 2. Ground truth on ga01, today (all verified this session)

| Fact | Evidence |
|---|---|
| Precisely **one** gateway process (multiplexer), run by the `default` profile | `hermes gateway status` (default at PID 2523045, uptime 28:55…) |
| This gateway **holds the single dispatcher lock**: `~/.hermes/kanban/.dispatcher.lock` (empty file, advisory flock; `fuser` shows PID 2523045 holding it) | `fuser -v` this session |
| The dispatcher **sweeps every live (non-archived) board** each tick | `gateway/kanban_watchers_dispatcher.py::_board_slugs()` → `list_boards(include_archived=False)`; per-board tick logs e.g. `kanban dispatcher [gargantua01]: spawned=4` in `~/.hermes/logs/gateway.log` |
| Live board counts today | `hermes kanban boards list` — `default`, `gargantua01`, `gargantua02`, `gaudi`, `skipjack`, `software-co`, all with same counts (archived=5, blocked=1, done=16, running=1 — snapshot 2026-10-22 04:0x) |
| Global dispatch config | `~/.hermes/config.yaml` `kanban:` block — `dispatch_in_gateway: true`, `dispatch_interval_seconds: 15`, `orchestrator_profile: kanban-orchestrator`, `default_assignee: kanban-worker`, `failure_limit: 3`, `max_in_progress: 24`, `max_in_progress_per_profile: 8`, `auto_decompose: true`, `auto_decompose_per_tick: 5`, `dispatch_stale_timeout_seconds: 14400` |
| Gateway runs under systemd user unit `hermes-gateway.service`, `Restart=always`, `RestartForceExitStatus=75`, `Environment=HERMES_HOME=/home/arch/.hermes` | `systemctl --user cat hermes-gateway.service` |
| Current Telegram bot is a single token in the **default home** `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS=8158007517`, `TELEGRAM_HOME_CHANNEL=8158007517`) | `~/.hermes/.env` (contents redacted in this doc) |
| Host resources | 256 CPUs, 2.0 TiB RAM, 156 GiB used / 1.8 TiB available (`free -h`) — five extra light-profile Telegram adapters are noise |
| Current gateway RSS | ~0.9 GB (PID 2523045) — each *additional gateway process* (not our design) would add roughly this magnitude |
| There is **no** per-profile config `kanban:` block anywhere | skill pitfall 8; spot-checked |
| Descriptions of relevant worker/orchestrator profiles are set for routing (fleet audit 2026-10-21, card t_5f26f34d) | `hermes profile describe` spot checks |

## 3. Empirical receipts from live sandbox trials (isolated `HERMES_KANBAN_HOME=/tmp/mbb-sandbox`, v0.22.4 on ga01)

Full transcript artifacts: `/tmp/mbb-sandbox-trial.sh` … `/tmp/mbb-trial10.sh` (session
scratch; summarized here). Sandbox used a dummy model endpoint, so spawned workers
failed fast at their first model call — claims/spawns/locks, not turn execution, were the object.

### Receipt 1 — single-spawn under two competing dispatch passes (deliverable #1)

Setup: two boards (`alpha`, `beta`) in the sandbox; ready tasks assigned to a real sandbox
profile (`trial-worker`). Two *concurrent* `hermes kanban dispatch` passes ran against the
same board.

```
pre-state:  t_9c0a3001 ready, t_d9007607 ready (alpha)
pass A:  Spawned: 2   (t_9c0a3001, t_d9007607 → trial-worker)
pass B:  Spawned: 0   Skipped: another dispatcher holds this board's lock (no writes this tick)
post-state: both tasks running, each with exactly ONE run row, one claim event (lock ga01:3603155)
```

An identical second run on a fresh `beta` board reproduced it exactly
(`Spawned: 1` / `Spawned: 0` + `Skipped: another dispatcher holds this board's lock`).
**Mechanism** (confirmed in source): each dispatch tick takes a **per-board** lock in addition
to the machine-global dispatcher singleton lock; the loser performs no DB writes that tick
(`DispatchResult.skipped_locked` in `hermes_cli/kanban_db_dispatch.py`). The claim itself is
an atomic SQLite transaction with claim TTL and run rows (`claimed {'lock': …, 'expires': …,
'run_id': 1}`). Note the CLI passes bypassed the gateway singleton lock but were *still*
serialized by the per-board lock — duplicates would require simultaneous claim-txn wins,
which the DB transaction prevents.

### Receipt 2 — spawned workers are structurally pinned to the source board (deliverable #1/#2)

`/proc/<pid>/environ` of a sandbox-spawned worker:

```
HERMES_KANBAN_DB=/tmp/mbb-sandbox/kanban/boards/alpha/kanban.db
HERMES_KANBAN_BOARD=alpha
HERMES_KANBAN_TASK=t_9c0a3001
HERMES_KANBAN_CLAIM_LOCK=ga01:3603155
HERMES_PROFILE=trial-worker
HERMES_HOME=/tmp/mbb-sandbox/profiles/trial-worker
```

The dispatcher's `_default_spawn` (kanban_db_dispatch.py lines ~2848-2852) pins
`HERMES_KANBAN_DB`, `HERMES_KANBAN_WORKSPACES_ROOT`, and `HERMES_KANBAN_BOARD` to the
board the task was claimed from, and `agent/delegation_context.py` fences delegated
children too. **Workers cannot see other boards by construction** — this is shipped
v0.22.4 behavior, not something to build. Operator's Telegram *commands* (gateway turns)
are the only surface that resolves the current-board pointer (see §5.3).

### Receipt 3 — archived-board failure modes (deliverable #4)

With board `beta` archived and a stale `HERMES_KANBAN_BOARD=beta` pin in the environment:

| Operation | Result | Verdict |
|---|---|---|
| `hermes kanban boards switch beta` | `kanban boards switch: board 'beta' is archived.` rc=1 | **fail-loud** |
| `hermes kanban --board beta list` | `kanban: could not initialize database: kanban board 'beta' is archived; refusing to recreate its database` rc=1... but see below | **fail-loud at init** |
| `HERMES_KANBAN_BOARD=beta hermes kanban list` | shows **default board's** tasks, rc=0 | **silent fallback** (the known bug class) |
| `HERMES_KANBAN_BOARD=beta hermes kanban create …` | task created on **default** board (`t_1f7af7c0` found in `/tmp/mbb-sandbox/kanban.db`, verified by direct sqlite read), rc=0 | **SILENT WRONG-BOARD WRITE — the g01-archive task-loss incident class, reproduced** |

Root cause chain: `get_current_board()` treats an archived-slug candidate as "fall through
to default" (kanban_db.py #43243 comment) — deliberate anti-crash design for the
*dispatcher*, but from an operator-facing pinned process it is a silent task-loss vector.
The g01 archive incident is therefore **reproducible on v0.22.4** whenever an ambient
`HERMES_KANBAN_BOARD` pin points at an archived board and a create is issued without an
explicit `--board`.

**Design consequence:** forbid ambient `HERMES_KANBAN_BOARD`/`HERMES_KANBAN_DB` pins in
long-lived operator-facing processes (systemd units, shell profiles, gateway env). Detect
and scrub them in health sweeps (§5.5, §8: nightly audit card).
Also note `hermes kanban --board beta list` returns rc=0 on the stderr path we saw in T5
("could not initialize database" printed but rc 0 documented in transcript) — scripts
must not rely on rc alone; grep stderr. (In the later delegate-fenced run the CLI refused
with rc=1 — explicit-board intent is honored and fenced appropriately. Ambiguity noted
for the implementation card: verify rc semantics of `--board <archived> list` before
building alerting on it.)

### Receipt 4 — `dispatch_in_gateway: false` is honored fail-loud (deliverable #1)

A second sandbox home (`/tmp/mbb-sb2`) with `kanban.dispatch_in_gateway: false` started
`hermes gateway run`: its `logs/gateway.log` shows

```
INFO gateway.run: kanban dispatcher: disabled via config kanban.dispatch_in_gateway=false
```

and **no** dispatcher ticks beyond that line; flipping to `true` produced
`holding singleton dispatcher lock (/tmp/mbb-sb2/kanban/.dispatcher.lock)` and
`embedded in gateway (interval=60.0s)`. Two corroborating live facts:

- Starting a second gateway alongside the production one (different `HERMES_HOME`)
  **refused**: `❌ A gateway already owns this host (PID 3603652)` — the host lock is
  host-wide, "one gateway per host serves every profile" is enforced by default; escape
  requires `HERMES_GATEWAY_LOCK_DIR` isolation (how our sandbox ran) or `--force`/standalone.
- The load-bearing backstop: `gateway/kanban_watchers.py::_kanban_dispatcher_boot()` takes
  an exclusive, non-blocking advisory lock at `<kanban_home>/kanban/.dispatcher.lock`;
  a contending gateway logs `another gateway already holds the dispatcher lock…; this gateway
  will NOT dispatch` and runs as a front-end only.

### Receipt 5 — per-board enumeration hard-fails on typos (deliverable #2/#4)

`hermes kanban --board nosuchboard list` → `kanban: board 'nosuchboard' does not exist.
Create it with …` rc=1 (non-default slugs must already exist — no accidental board
creation from operator typos). This is the property that makes per-command `--board`
routing safe: **wrong board names fail loudly; they never silently create**.

---

## 4. The two viable topologies, judged

### Topology A — per-bot standalone gateways, env-pinned (what the card literally asks to evaluate)

One Hermes process per board, each with `HERMES_KANBAN_BOARD=<slug>` in its unit
environment, each its own Telegram bot token.

**Why we reject it (on v0.22.4):**

1. **The pin does not pin.** Within one gateway process the board env vars are process-global
   (`secret_scope._GLOBAL_ENV_EXACT`/`_GLOBAL_ENV_PREFIXES`); every served profile of that
   gateway resolves the same `os.environ["HERMES_KANBAN_BOARD"]`. To get one *board* per
   process you need one **gateway process** per board — but the gateway is now a
   multiplexer that actively refuses to stand up per-profile gateways without
   `--force`/`standalone` shims (live receipt: "A gateway already owns this host"; docs:
   "No new per-profile gateways", `gateway.standalone: true` is an explicitly temporary shim
   slated for removal). Fighting the shipped topology guarantees an update someday removes
   the shim underneath us.
2. **N dispatcher sweeps.** With N gateways, each still enumerates the (same) live boards
   by default; `dispatch_in_gateway: false` on N−1 of them is the supported fix — but now
   every bot process is a *notification* owner for its profiles (`notify_in_gateway` runs
   per-gateway) while none of them dispatch, and the ONE dispatching gateway is a single
   point of failure for the whole estate (see 3).
3. **Restart/update coupling.** `hermes update` bounces the gateway it runs in; the 03:34
   auto-update restart would bounce **every** bot at once (all five systemd units restart
   on update if configured like today's default unit) — the exact storm the card worries
   about, now multiplied.
4. **Telegram token hard-binding.** One bot token per gateway process is natural, but
   five `Restart=always` units polling Telegram add five failure surfaces with no offsetting
   isolation gain, given (1) fails anyway: the env pin inside each gateway is still
   process-global, so the isolation comes *only* from the `--board` convention, which
   Topology B achieves with one process.

### Topology B — single multiplex gateway + per-board butler profiles (RECOMMENDED)

One gateway (the current one). Five new lightweight profiles — `g02-butler`,
`g01-butler`, `gaudi-butler`, `sjproto-butler`, `swco-butler` — each served by the
multiplexer with **its own Telegram bot token** in its own profile `.env`
(`profiles/<name>/.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS=<operator id>`,
`TELEGRAM_HOME_CHANNEL=<operator id>`; credential-scope fact: Telegram tokens are
per-profile `.env` secrets under multiplexing — resolved from the routed profile's home,
"credentials are never shared across profiles" per the multiplexing doc).

**What this buys structurally:**

- **Per-bot chat surface:** five distinct bots the operator can pin in Telegram; each butler
  has its own SOUL, memory, sessions. Asking the g02 bot for "the board status" gets a g02
  answer in g02 language, from a session that cannot be confused with gaudi.
- **Per-bot notification routing:** task notification subs carry
  `notifier_profile` (stamped at subscribe time, `_kanban_auto_subscribe` in
  `gateway/slash_commands.py`); the notifier tick delivers only to the profiles *its own
  gateway serves* — i.e., all five butlers under one gateway, each sub routed back through
  the butler whose chat created it (`list_notify_subs ... notifier_profiles=<owned profiles>`).
  So "operator's Telegram notifs follow the right board" = **subscribe from the right bot**.
- **Dispatcher: still exactly one.** No new gateways → no new dispatchers. The existing
  per-board tick + per-board lock + atomic claims remain the only spawn path (§3 Receipt 1).
- **Command routing as convention + prompt guardrail:** butler SOUL.md mandates the
  explicit `--board <slug>` argument on every kanban call it makes or suggests, and forbids
  its slug's absence. Wrong-board writes are then a two-failure event (operator picks the
  wrong bot AND omits/types the wrong `--board`), and `--board <other>` is still *possible*
  unless a config guardrail raises it to three failures.

### The guardrail that closes the last gap: `kanban.dispatch_profiles` per home? — NO for this host

v0.22.4 ships `kanban.dispatch_profiles` (kanban_db_dispatch.py #110995/#113620): a
**fail-closed per-home claim allowlist** — when set, the dispatcher of THAT home only
claims cards whose assignee is listed. But it gates *claiming*, not *creation or routing*,
and on ga01 all boards live under one shared kanban home, so there is exactly one
"home" to configure — a per-board allowlist cannot be expressed this way. It becomes
useful only in the multi-home variant (§9). Not applicable here; do not set it.

**What IS worth setting (one line, low blast radius):** pin
`gateway.multiplex_profiles: true` explicitly in the default home config (it is currently
unset-resolving-to-true; docs advise pinning on the host-process profile so boot-time
preflight can never quietly change the served set as profiles are added/removed).

---

## 5. Design detail (Topology B)

### 5.1 Routing table (single source of truth; goes in the management repo beside the provisioning script)

| Telegram bot (BotFather username) | Profile (`profiles/<name>/`) | Pinned board | Board theme | Model |
|---|---|---|---|---|
| `gargantua02_ops_bot` | `g02-butler` | `gargantua02` | production k8s, Azure VMs 413–418 | qwen38-flash-fp8 (execution tier — butler work is listing/summarizing/routing, evidenced fine on flash tier) |
| `gargantua01_proto_bot` | `g01-butler` | `gargantua01` | prototype k8s | qwen38-flash-fp8 |
| `gaudi_local_bot` | `gaudi-butler` | `gaudi` | local server, HPU + docker compose | qwen38-flash-fp8 |
| `skipjack_proto_bot` | `sjproto-butler` | `skipjack` (+proto context) | HPC/AI hybrid cluster mgmt02 | qwen38-flash-fp8 |
| `swco_bot` | `swco-butler` | `software-co` | full-staff SDLC | qwen38-flash-fp8 |

All five `.env` files also set `TELEGRAM_ALLOWED_USERS=8158007517` and
`TELEGRAM_HOME_CHANNEL=8158007517` (operator's current ID) — a butler that cannot talk to
anyone but the operator is itself a guardrail against its board content leaking.

The default profile keeps the existing bot and becomes the *estate* bot: cross-board views
(e.g. "what's running everywhere"), dispatcher health, updates. Its description/SOUL gains
"cross-board queries only via explicit `--board`; never creates task cards without an
explicit board argument."

### 5.2 Profile shape (least privilege)

```
toolsets:        [kanban, memory, session_search, web]        # kanban CLI surface + light lookups
skills.always_load: []                                        # none required; kanban lifecycle auto-injected
model:           qwen38-flash-fp8 (+ local aux slots)
```

SOUL.md (per butler, one-line-differentiated): *"You are the <board> butler. You are the
operator's single interface to the <slug> kanban board. EVERY kanban command or tool call
you make MUST carry the explicit argument `--board <slug>` (or `board="<slug>"` for kanban_*
tools). You never create, edit, or link cards on any other board; other boards do not exist
for you except as URLs the operator pastes. When asked to do work rather than report, create
a card on <slug> with the right assignee — do not execute ops yourself."*

`hermes profile describe <name> --text` (routing boundary, capability-first):
*"Board butler for <slug>: operator chat front-end — board status, card creation,
subscriptions, and task summaries for <board> ONLY. Every kanban call carries --board <slug>.
Never executes board work itself; never touches other boards."*

### 5.3 Command and notification paths (why notifs follow the right board)

- **Command path**: operator → bot → that butler's gateway turn → `/kanban --board <slug> …`
  (slash) or butler-initiated `hermes kanban --board <slug>` / `kanban_*` tool call with
  `board="<slug>"`. The current-board pointer is honored but NEVER relied on: butlers
  always pass the explicit slug (the same resolution the dispatcher uses for workers —
  kanban.py CLI scope comment). A mis-typed slug fails loudly (Receipt 5); a stale
  `kanban/current` file only affects which board an *unpinned* call lands on, and butler
  SOUL forbids unpinned calls.
- **Notification path**: every sub row stores the subscribing chat + `notifier_profile`
  = the butler whose bot received the `/kanban create` (auto-subscribe appends
  "(subscribed …)" on create; explicit `notify-subscribe` for pre-existing cards). One
  gateway hosts all five butlers, so its notifier delivers every butler's subs — a sub
  created from the g02 bot wakes/sends on the g02 bot, always. Subscriptions persist on
  the (per-board) DB with cursors; `notify+wake` wakes the exact chat so the butler can
  comment with current card state. This is profile-owned delivery per the shipped design
  (docs: "Multi-profile setups: delivery is profile-owned"; source:
  `kanban_db_notify._notify_profile_filter`, `list_notify_subs(notifier_profiles=…)`).

### 5.4 Cross-board reference policy (deliverable #3) — recommendation: reference by URL, never by link

- **`kanban_link` across boards: FORBIDDEN.** Not merely disallowed by policy — it is
  not a supported operation on this build: a link row lives inside ONE board's DB and
  cannot span DBs; a cross-board parent simply cannot gate a child on another board, so a
  "link" would be a silent no-op or a same-board footnote. Workers are already structurally
  fenced (Receipt 2) and can never write another board.
- **Butlers: URL references ONLY, in card bodies/comments.** A gaudi card consuming
  g02 ops output references the g02 card id/text as plain text (`gargantua02/t_41f515f2`),
  never a dependency edge. Dependency ordering across boards is an OPERATOR duty: the
  consuming card gets a body line "BLOCKED-ON (external): g02 <card-id> — operator to
  confirm done" and the butler reminds on `notify+wake`. (For genuinely coupled cross-board
  campaigns, the alternative is a thin coordinating card on the *requesting* board that the
  operator closes manually — keep it manual; automation across boards is where the
  task-loss bugs live.)
- **Estate-default profile** may run cross-board *reads* with explicit `--board` per call.

### 5.5 Failure modes + responses (deliverable #4)

| Event | Behavior on Topology B | Action |
|---|---|---|
| Butler's board archived | `--board <slug>` calls fail loud (`board is archived` / `does not exist`, Receipts 3+5); auto-subscribe find no sub-able events; dispatcher stops sweeping the board (`include_archived=False`) | Butlers' SOUL: on `is archived` error, reply STOP + instruct operator to import/unarchive (`boards import`); never retry against default. **Nightly audit card: detect butler→archived-board and any task rows created via ambient-pin fallback** (compare `created_by` authorship vs board) |
| Ambient `HERMES_KANBAN_BOARD` pin drift (the g01 class) | Silent default-board fallback reproduced (Receipt 3) | Prohibition + sweep: no `HERMES_KANBAN_*` pins in any unit file, shell rc, cron wrapper, or gateway env; nightly `grep` sweep in audit cron (already exists as NIGHTLY-BOARD-AUDIT lane — extend it) |
| Dispatcher dies / gateway down | All bots down together (single process) — the price of one dispatcher; workers keep running (dispatched processes are independent), completion transitions land in DB, notifications resume on restart with cursor dedup | systemd `Restart=always` (already); health sweep alerts on `.dispatcher.lock` holder missing while ready cards exist |
| `hermes update` restart | All five bots bounce with the gateway (seconds of downtime; Telegram updates queue server-side; `drop_pending_on_cold_boot` default `true` will DROP queued messages sent during downtime — **set `drop_pending_on_cold_boot: false` in each butler's telegram extra** so an update-bounce doesn't eat operator messages) | Acceptable at current cadence; note mitigation |
| Wrong bot used by operator | Butler replies in its board's frame; a `--board` for a different slug in that chat contradicts its SOUL → butler must call out the mismatch and the command's target before executing (put this refusal rule in SOUL explicitly) | Prompt guardrail; residual risk accepted |
| Token leak per bot | Blast radius = one board's butler; revoke via BotFather `/revoke`; other four bots unaffected | Per-bot tokens are themselves the mitigation |

**Never-silent-fallback rule, restated:** the ONLY silent fallback class on v0.22.4 is the
ambient-env-pin → default-board path (Receipt 3). Topology B leaves no ambient pins in
operator-facing processes, so every wrong-board scenario fails loudly at the explicit
`--board` check. That is the strongest fail-loud posture available without code changes.

### 5.6 Resource & update cost (deliverable #5)

- **Memory:** zero additional gateway processes. Five butler profiles add five *served
  profile slots* on the existing gateway — per-profile config/memory/sessions, no per-process
  cost. Adaptive capacity (Python GC) grows with actual chat volume; butlers are idle
  unless messaged (gateway `scale_to_zero` exists but is irrelevant at current load).
  Against 1.8 TiB available, the marginal cost is unmeasurable.
- **Telegram polling:** five extra long-poll connections (one per bot token) inside one
  process — trivially cheap; Telegram allows this without special handling (each token is
  independent). Bots see only DMs/chats they're in; privacy mode defaults on.
- **Restart/update:** one gateway to bounce, all bots ride the existing
  `hermes-gateway.service` lifecycle (Restart=always; `hermes update` already restarts it).
  Compare Topology A: five units × update bounce = the 03:34 storm on every bot, plus five
  lock files and five logs to sweep. **Topology B strictly dominates** on this axis.

## 6. Migration plan (implementation cards, gated on GO)

Ordered; each card is independently revertible; nothing touches the live gateway until card 3.

1. **MBB-PREP** (kanban-board-architect): operator creates 5 BotFather bots
   (`/newbot`, collect tokens out-of-band — tokens must never touch a card body); decide
   bot usernames per §5.1; commit the routing table + provisioning script skeleton to the
   management repo. Provisioning script = idempotent: grep-guarded `profile create --clone-from default --no-alias`,
   `yaml.dump`-written config, SOUL.md + description writes, `.env` token placement done by
   the OPERATOR (not the script — tokens don't belong in git).
2. **MBB-PROFILES** (after GO on 1): run the script — 5 butler profiles created, configured
   (§5.2), `hermes -p <name> config check` × 5, `hermes -p <name> tools list` shows exactly
   kanban+memory+session_search+web, descriptions set. Cost: zero gateway impact (profiles
   are picked up by the multiplexer rescan ≤30s once they have platform creds).
3. **MBB-TOKENS** (operator-assisted): operator pastes each token into
   `profiles/<butler>/.env` (TELEGRAM_BOT_TOKEN/ALLOWED_USERS/HOME_CHANNEL), then ONE
   `hermes gateway restart` (default profile) brings all five adapters up. Verify via
   `hermes gateway status` (served set) + `/whoami` from each bot in Telegram.
   Downtime: the usual gateway restart window (~seconds), same as any config change today.
4. **MBB-SUBS-NOTIFS**: smoke test per board — `/kanban --board <slug> create "SMOKE <slug>"
   --assignee <board-appropriate-worker>` from that butler → confirm "(subscribed …)" line,
   let it run, confirm completion notification arrives on THE SAME bot, then archive/clean
   the smoke card. One board at a time, gargantua02 first (the board the operator watches
   most, per ops history).
5. **MBB-ARCHIVED-FAILLOUD-TEST**: sandbox-replay Receipt 3 against a THROWAWAY board on the
   live host (create board `mbb-probe`, subscribe, archive it, verify each butler fails loud,
   delete the probe). Receipt posted on this card.
6. **MBB-DEFAULT-REFIT**: default profile SOUL/description gain estate-bot duties
   (cross-board reads with explicit `--board`; future NIGHTLY-AUDIT notif target);
   set `drop_pending_on_cold_boot: false` on all six bots' telegram extra (one gateway
   restart, can be merged with card 3's restart if sequenced together).
   ALSO pin `gateway.multiplex_profiles: true` explicitly per §4 guardrail note.
7. **MBB-NIGHTLY-AUDIT-EXTEND**: extend the nightly audit lane with: (a) sweep for ambient
   `HERMES_KANBAN_` pins in `/etc/systemd/user`, shell rc files, cron wrappers; (b) butler→
   board liveness check (each live butler's board exists and is unarchived); (c) dispatcher
   lock holder alive; (d) per-board: tasks created while board archived (authorship anomaly
   detector for the silent-fallback class).

**Rollback:** `hermes -p <butler> gateway stop` (or delete profile) per bot; remove
platform creds; gateway restart. No data drift to unwind — boards and dispatch config are
untouched throughout (Topology B changes only profiles + tokens).

## 7. Go/No-Go summary

| Question | Answer |
|---|---|
| Can each board get its own Telegram bot, today, on v0.22.4? | **YES**, via multiplex-served butler profiles with per-profile tokens — no new gateways. |
| Can each bot be *structurally* pinned so wrong-board writes are impossible? | **Not within one process** — board env pins are process-global; explicit `--board` per call is the supported isolation for chat-originated commands, plus shipped structural pinning for all dispatched workers. Structural for humans, conventional for chat. |
| Exactly one dispatcher under N bots? | **YES and already enforced** — machine-global singleton lock + per-board dispatch locks + atomic claims (Receipts 1+4). Duplicate-spawn class was tested head-on and did not reproduce. |
| Fail-loud on archived boards? | Loud wherever an explicit slug is involved; the silent-fallback path (ambient env pin) is REAL and reproduced (Receipt 3) — design eliminates ambient pins and adds a nightly sweep for the residual class. |
| Worth it? | **GO for Topology B**: ~zero standing cost, meaningful per-board chat + notification isolation, and it rides the shipped multiplex architecture instead of fighting it (Topology A fights it and loses on three axes: isolation, dispatch ownership, update storms). |

**Operator GO gates progression at cards 2 and 3 (profiles + tokens); deliverable design cards 1 and 5 are safe to run without touching the live estate.**

## 8. Residual risks (accepted, with mitigations)

1. **Convention residual:** a butler could still be *told* to pass `--board <other>`; SOUL
   refusal rule + wrong-bot answers in the wrong frame make this a deliberate act, not an
   accident. If this ever bites, the escalation is §9's true pinning — costed there.
2. **`--board <archived>` rc semantics** (Receipt 3 footnote): list-vs-init rc discrepancy —
   verify before alerting scripts rely on rc; captured as a check inside card 5.
3. **One gateway = one blast radius** for restarts: accepted because Message queue retention
   (`drop_pending_on_cold_boot: false`) covers the update-bounce case.
4. **proto/skipjack naming**: if "skipjack+proto" is meant as ONE board pair, the sjproto
   butler handles both slugs explicitly (SOUL lists both); if proto is later its own board,
   add a sixth butler from the same provisioning parameterization.
5. **Memory bleed across boards via shared butler model tier**: none — per-profile homes
   isolate memory/hindsight (estate-design reference, memory isolation section).

## 9. Appendix — what TRUE per-bot structural pinning would require (and why deferred)

If, post-rollout, the convention residual (§8.1) proves unacceptable, the structural fix is
**one Hermes home (and thus one gateway process) per board**, relying on shipped support:

- Each home carries `kanban.dispatch_profiles: [<that board's assignees>]` — the fail-closed
  per-home claim allowlist (#110995) — so each home's dispatcher claims ONLY its board's
  cards, converting cross-board bleed into a claim-time hard failure.
- Each home's butler has its own gateway, `HERMES_KANBAN_HOME`/board env pins set in the
  unit (now genuinely per-process), `dispatch_in_gateway: false` on all but one, OR the
  shipped multi-gateway posture (one dispatch owner, N−1 notifier-only gateways; singleton
  lock arbitrates ownership at boot).
- Cost: 5 gateway processes (~0.9 GB RSS each observed → ~4.5 GB standing, trivial vs RAM
  but real vs attack surface), 5 systemd units, 5 update-restart storms, 5 log directories,
  and reliance on the `--force`/`HERMES_GATEWAY_LOCK_DIR` escape hatches the multiplex-first
  roadmap is actively closing — the reason this is deferred until §8.1 is proven insufficient.

**Command quick-reference for the operator (all per-call explicit):**

```
/kanban --board gargantua02 list                       # from ANY chat, but use the right bot
/kanban --board gaudi create "TITLE" --assignee sw-dev-a
/kanban --board software-co show t_xxx
hermes kanban --board skipjack diagnostics             # from CLI (be aware: diagnostics has no --board; use --board scope)
```

*(Correction merged from review: `hermes kanban diagnostics` accepts the global `--board`
scope via the shared kanban front-door; the per-board DB read-only sqlite URI remains the
safe inspection fallback for scripts.)*

---

*Evidence appendix (raw): sandbox scripts `/tmp/mbb-sandbox-trial.sh` … `/tmp/mbb-trial10.sh`;
log extracts quoted inline; source refs are file+function against git 4d04303818b6 (v0.22.4).*
