# Butler QR Runbook — 2026-10-22 (BUTLERS-STAGE-3, t_02de9dff)

**Status: STAGED + VERIFIED — awaiting ONE operator action.**

All five Topology-B butlers have live Telegram tokens, provider wiring, and
dedicated memory banks. The operator's QR-wizard steps are **DONE for all
five** (g01/gaudi per pilots; g02/swco/sjproto completed by the operator
2026-10-22 mid-run, before gateway registration). **The single remaining
action is one gateway restart** (§3), then the scoping smoke (§4).

The QR commands below are kept for the record and for one-keystroke bot
reconfiguration (token revocation/replacement). NEVER paste a real token into
a kanban card, comment, chat, or file that goes to git.

† COMMS-LAW/BANK-MAP/board-map refs: `docs/BANK-MAP.md`, board isolation
design `docs/multi-bot-board-isolation-design-2026-10-22.md`.

## 1. Butler roster (all staged)

| Bot (first_name / getMe) | Profile | Board slug | Bank | Model | QR/token state |
|---|---|---|---|---|---|
| G01-Butler | `g01-butler` | `gargantua01` | `g01-butler` | qwen38-flash-fp8 | DONE (pilot t_bd78a263) |
| Gaudi-Butler | `gaudi-butler` | `gaudi` | `gaudi-butler` | qwen38-flash-fp8 | DONE (pilot t_fd8ca6f0) |
| G02-Butler | `g02-butler` | `gargantua02` | `g02-butler` | qwen38-flash-fp8 | DONE (operator, 2026-10-22) |
| SoftCo-Butler | `swco-butler` | `software-co` | `swco-butler` | qwen38-flash-fp8 | DONE (operator, 2026-10-22) |
| sjproto-Butler | `sjproto-butler` | `skipjack-prototype` | `sjproto-butler` | qwen38-flash-fp8 | DONE (operator, 2026-10-22) |

All five tokens verified live via `getMe` (2026-10-22, via fallback DC —
the bots answer to their `hermes_*_bot` wizard usernames; usernames are
managed by the QR wizard and visible in Telegram).

Per-profile kit state (verified receipts, §5): config.yaml with
`providers:litellm` block (`${LITELLM_API_KEY}` env-indirected; ctx pins
qwen38-flash-fp8=262144 / glm53=1000000), `.env` with
`TELEGRAM_FALLBACK_IPS=149.154.167.220,149.154.166.110`,
`TELEGRAM_ALLOWED_USERS`/`TELEGRAM_HOME_CHANNEL=8158007517`,
`LITELLM_API_KEY`, `HINDSIGHT_BANK_ID=<dedicated bank>` (agreeing with
`hindsight/config.json` `bank_id` — the pair must never disagree), toolsets
exactly `[kanban, memory, session_search, web]` (CLI **and** Telegram
surfaces via `platform_toolsets`), SOUL hard-scoped to one board. g02-butler
SOUL also carries the COMMS-LAW brevity/persona reference (operator directive
2026-10-21; full binding text lives in `g02-ops` SOUL.md).

## 2. QR wizard commands (for the record / one-keystroke redo)

These are the five QR steps as originally planned, in order (gaudi
t_fd8ca6f0 staged first, then the BUTLERS-STAGE-3 three; g01 already live
from pilot 1). **The operator already executed the four pending ones** —
they are recorded here so any future token replacement is one keystroke:

```bash
# 1. gaudi-butler (staged on t_fd8ca6f0 — QR DONE)
HERMES_HOME=~/.hermes/profiles/gaudi-butler hermes gateway setup
#   -> Telegram -> reconfigure -> [1] Automatic QR

# 2. g02-butler (QR DONE 2026-10-22)
HERMES_HOME=~/.hermes/profiles/g02-butler hermes gateway setup

# 3. swco-butler (QR DONE 2026-10-22)
HERMES_HOME=~/.hermes/profiles/swco-butler hermes gateway setup

# 4. sjproto-butler (QR DONE 2026-10-22)
HERMES_HOME=~/.hermes/profiles/sjproto-butler hermes gateway setup
```

The wizard writes the real token into the profile `.env`
(`TELEGRAM_ALLOWED_USERS`/`TELEGRAM_HOME_CHANNEL=8158007517` stay). Profiles
are picked up by the multiplex gateway rescan only at (re)start — that is
why registration waits for the single restart in §3.

## 3. THE remaining operator action — one final gateway restart

Run from the **default** home (the gateway-owning profile), ONCE, after all
QR steps (they are done):

```bash
hermes gateway restart
```

Then verify the served set:

```bash
hermes gateway status        # expect all five butlers listed as served profiles
hermes kanban boards list    # boards untouched; dispatcher config untouched
```

Downtime is the usual seconds-long restart window. Queued Telegram messages
are retained (`drop_pending_on_cold_boot: false` on every butler), so
nothing sent during the bounce is lost.

## 4. Post-restart scoping smoke (per bot, from Telegram)

Open a DM with each bot (by its first_name above; usernames are the
`hermes_*_bot` strings shown by the QR wizard / `/whoami`). Say:

| Step | Send to the bot | Expected PASS |
|---|---|---|
| a. identity | `What board do you manage?` | Names exactly its one board; refuses to speak for others |
| b. pinned read | `/kanban --board <its slug> list` | Cards of its own board only |
| c. scoping refusal | `Show me the gaudi board status` (to any bot ≠ gaudi-butler; adapt the slug per bot) | **Refuses**: calls out the mismatch (request names another board) and does not run it |
| d. routing smoke (optional) | `/kanban --board <its slug> create "SMOKE <slug>" --assignee <board fleet worker>` | "(subscribed …)" reply; on completion the notification lands on the SAME bot; then archive the smoke card |

Do d. one board at a time, gargantua02 first. A bot answering with another
board's cards, or executing a foreign-board command, is a STOP-and-report
failure.

## 5. Staging receipts (BUTLERS-STAGE-3 run, 2026-10-22)

All receipts captured in the run log; verifier: `scripts/verify_butlers.py`,
`scripts/verify_tools.py` (idempotent, re-runnable).

| Receipt | g02-butler | swco-butler | sjproto-butler |
|---|---|---|---|
| `hermes -p <P> config check` | PASS | PASS | PASS |
| one-shot `Reply exactly: <P>-OK` (scrubbed-env probe) | PASS | PASS | PASS |
| enabled toolsets == [kanban, memory, session_search, web] (cli+telegram) | PASS | PASS | PASS |
| bank canary retain/recall in dedicated bank (fact_count / canary hits / shared-bank leaks) | PASS 1/1/0 | PASS 3/3/0 | PASS 3/3/0 |
| routing description set (`hermes profile describe`) | PASS | PASS | PASS |
| Telegram token live via `getMe` | PASS | PASS | PASS |

Pre-mutation backup (wizard-stub `.env`+`SOUL.md` of the three, tokens
redacted from nothing — backup stays on host, never committed):
`~/kanban-backups/butlers-stage-3-20261022T143911Z/`. Banks g02-butler /
swco-butler / sjproto-butler created server-side (PUT 200, empty, fact_count
0 at creation; now hold the canary facts above).

NO gateway restarts and NO bot-token creation were performed by the staging
run — restarts are the operator's law.

## 6. Rollback (if the restart surfaces a defect)

Per bot: `hermes -p <butler> gateway stop` (or delete the profile) and
restart once more — butler profiles are additive; boards, dispatcher config,
and the rest of the fleet are untouched by this staging. Restore files from
the backup dir above if a butler's staged config misbehaves.
