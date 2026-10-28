> Status: current. Canonical registry entry: hermes-estate/docs/GOVERNANCE.md G-02 (2026-10-26). This file remains the doctrine text of record.

# BUTLER-ROUTING-DOCTRINE — butler-first task flow as fleet default

**Card:** t_5a6b907a · **Author:** kanban-board-architect · **Date:** 2026-10-22
**Predecessors:** BUTLER-WIRING-VERIFY (t_866598e7, 34 PASS / 1 BLOCK-PASS, doc
`BUTLER-VERIFY-2026-10-22.md`) · design `multi-bot-board-isolation-design-2026-10-22.md` (Topology B)
**Status: LIVE — doctrine applied to fleet SOULs + kanban-orchestrator skill this date.**

---

## 1. The doctrine in one line

**Board intake flows through the board's butler bot by default.** The default (orchestrator)
profile keeps full meta + cross-board capability as the **fail-safe**, and workers write only to
their assigned card's board. Nobody below the butler intakes operator requests.

Three routing classes:

| Class | Owner | Examples |
|---|---|---|
| **Per-board intake** (gargantua01, gaudi, gargantua02, software-co, skipjack-prototype) | the board's **butler bot** | "reimage node gargantua02", "watch PR #1890", "new SDLC feature" |
| **Meta / fleet-wide / cross-board / operator-direct** | **default orchestrator profile** (executes meta-work on the `kanban-board-architect` lane per its standing ownership) | profile/board/config/SOUL/skill changes, fleet audits, multi-board campaigns, dispatcher work |
| **Card execution** | **workers**, on their assigned card's board only | everything the dispatcher spawns |

`skipjack` (production cluster, mgmt02) has **no butler** — its intake stays on the default
profile until a sixth butler is stamped from the same kit.

## 2. Routing table (bot handle → board → bank → assignee pool)

Telegram bot usernames are the QR-wizard-managed `hermes_*` handles; the BotFather
provisioning names below are from design §5.1 and the QR runbook §1 (getMe receipts
2026-10-22 in BUTLER-VERIFY §7: ids 8522272075 / 8948894256 / 8825019300 / 8892444888 /
8646424684, no duplicate usernames; live getMe re-probe from the t_5a6b907a run failed on a
transient network timeout to the fallback DC — citing the verified receipts instead).

| Bot (BotFather name) | Profile | Board | Memory bank | Assignee pool |
|---|---|---|---|---|
| gargantua01_proto_bot | `g01-butler` | `gargantua01` | `g01-butler` | g01-orchestrator, g01-planner, g01-ops, g01-auditor, g01-scribe, g01-watcher |
| gaudi_local_bot | `gaudi-butler` | `gaudi` | `gaudi-butler` | gaudi-orchestrator, gaudi-planner, gaudi-perfeng, gaudi-benchrunner, gaudi-deployer, gaudi-dockerops, gaudi-analyst, gaudi-auditor, gaudi-scribe, gaudi-liaison, gaudi-synapse, gaudi-watcher, gaudi-arch |
| gargantua02_ops_bot | `g02-butler` | `gargantua02` | `g02-butler` | g02-orchestrator, g02-planner, g02-ops, g02-auditor, g02-scribe, g02-watcher |
| swco_bot | `swco-butler` | `software-co` | `swco-butler` | sw-pm, sw-architect, sw-dev-a, sw-dev-b, sw-reviewer, sw-qa, sw-devops, sw-docs, sw-ux |
| skipjack_proto_bot | `sjproto-butler` | `skipjack-prototype` | `sjproto-butler` | sjp-orchestrator, sjp-planner, sjp-ops, sjp-auditor, sjp-scribe, sjp-watcher |
| (default bot) | `default` | `default` + `skipjack` intake + meta | hermes | kanban-board-architect (meta lane), kanban-orchestrator (decomposition), kanban-worker, distiller, research; sj-* fleet for the skipjack board |

Bank pins: `hindsight/config.json bank_id == <butler>` on all five; `.env HINDSIGHT_BANK_ID`
unset on g01/gaudi, agreeing-pin on g02/swco/sjproto — both resolve to the dedicated bank
(BUTLER-VERIFY §4; canary receipts, zero cross-bank leaks across all 19 banks). Bank law of
record: `docs/BANK-MAP.md`.

## 3. Butler intake behavior (now in every butler SOUL)

When the operator messages a butler a work request for its board, the butler:
1. creates the card on its board — **explicit `board=` on every kanban call, always**;
2. assigns the right specialist from its fleet vocabulary, never itself;
3. encodes in-board prerequisites with `parents=[...]` at create time (never gate-then-link);
   *(extended 2026-10-28, t_0b03f85e: a worker self-parking on a dependency must
   `kanban_link(parent, self)` **before** blocking/parking — GATE-WAIT PATTERN,
   `docs/gate-wait-pattern-2026-10-28.md` R1–R3; SOUL provisioning sync via
   kanban-board-architect follow-up)*;
4. reports the card id + assignee back in one short line.

It does NOT implement the work. Butler SOULs also carry the escalation law:
- **Cross-board / meta / fleet-authority requests →** reply exactly
  `route this to the default orchestrator` — do not act.
- **Housekeeping with a card to stamp (card archive/delete) →** the butler ACTS in-tool (since 2026-10-22, t_aabdf078): comments `HOUSEKEEPING: archive — <reason>` on that exact card, tells the operator the nightly ARCHIVE-GC sweeper archives it by morning (urgent → default orchestrator immediately), and a later `HOUSEKEEPING: cancel` comment on the same card prevents the sweep.
- **Housekeeping with no card to stamp (board unarchive/import) →** acknowledge, do not attempt, reply that housekeeping routes to the default orchestrator (see §5 — tool-layer gap; butlers are terminal-less by design and Hermes has no kanban_archive tool).

Worker SOULs (53 profiles) now carry a **Board Discipline** section: explicit-`board=` writes,
follow-ups on the assigned card's board only, no chat intake of new operator requests, and
cross-board references as plain text only (never link edges — cross-board `kanban_link` is
structurally impossible anyway, one DB per board).

## 4. Fail-safe clause (default orchestrator)

The default profile's SOUL now carries the **Butler-First Routing Doctrine**: per-board intake is
handed to the corresponding butler; the default profile creates board cards directly **only when
the butler is demonstrably down** (unresponsive or erroring), and stamps the card body:

```
fail-safe intake: <butler> unavailable (<evidence>)
```

so the record always shows why a butler was bypassed. Meta / fleet-wide / operator-direct work
is unchanged — it stays on the default profile (meta-work executes on kanban-board-architect).

## 5. Verified butler surface and known tool gaps

**Verified working** (BUTLER-VERIFY 2026-10-22, 34 PASS — do not re-report as butlers-broken):
card **create** (with assignee + parents), managed-board **list**, **show**, **comment**,
**block**, **complete**, **link**, notify subscriptions, board status/summaries.

**Known tool gaps, each with a defined escalation path** (added to butler SOULs + skill):

| Gap | Status | Escalation |
|---|---|---|
| No `kanban_archive` tool in Hermes — archive is CLI-only, butlers are terminal-less by design (live evidence: g01-butler created+assigned+blocked test card t_0a8bbc03 but could not archive it; orchestrator CLI-closed it, verified archived 2026-10-22 15:5x) | CONFIRMED LIVE (operator report, this card) | card archive/delete → butler `HOUSEKEEPING: archive` stamp + nightly ARCHIVE-GC sweeper (bridge until kanban_archive ships); unarchive/import → default orchestrator |
| Kanban tool layer accepts a foreign `board=` (no tool-layer fence) — SOUL + description guardrails are the active fence, verified refusing pre-call on all five; dispatcher pinning remains structural for spawned workers | architect finding (BUTLER-VERIFY Check 3, BLOCK-PASS) | guardrail + fail-loud conventions; treat as upstream gap |

**ARCHIVE-GC bridge (LIVE 2026-10-22, card t_aabdf078):** gap 1 above is now mitigated end-to-end. Nightly sweeper
`~/.hermes/scripts/archive_gc.py` (cron `be9cc3360254`, 21:30 ET; log
`~/.hermes/kanban/archive-gc.log`) scans every board DB for `HOUSEKEEPING: archive` comments,
honors a later `HOUSEKEEPING: cancel` on the same card, accepts stamps ONLY from authors
ending `-butler` or equal to `default`, never touches `running` cards, caps at 20 archives per
run, and receipts each archive with an `ARCHIVE-GC:` comment before archiving. Butler SOULs now
carry the active stamp protocol (marker: `Card Housekeeping via ARCHIVE-GC Stamp`), converged
by `scripts/archive_gc_butler_converge.py` (this script, grep-guarded, idempotent;
pre-mutation backups in `backups/archive-gc-butler-wiring-2026-10-22/pre/`).
**SELF-RETIRING:** the whole bridge — sweeper cron, script, and the SOUL protocol sections —
retires together once upstream ships a real `kanban_archive` tool; the upstream feature request
stays recorded (below).

**Recorded for operator decision — NOT implemented** (upstream Hermes feature requests):
1. A **scoped `kanban_archive` tool** (or per-profile housekeeping allowlist) so butlers can do
   board housekeeping without a terminal.
2. A **`kanban.allowed_boards: [<slug>]`-style profile-config key** enforced at the kanban tool
   layer (`write_txn` / tool layer) to convert the SOUL-prompt fence into a structural fence.

## 6. Where the doctrine is encoded

- **Butler SOULs** (5): `profiles/<butler>/SOUL.md` — `## Operator Intake Protocol` +
  `## Escalation` sections (marker: `butler-first — fleet default since 2026-10-22`).
- **Default profile SOUL**: `~/.hermes/SOUL.md` (home root) — `## Butler-First Routing Doctrine`.
- **Worker SOULs** (53): `profiles/<worker>/SOUL.md` — appended `## Board Discipline`.
- **kanban-orchestrator skill**: canonical `~/.hermes/skills/devops/kanban-orchestrator/SKILL.md`
  + the `kanban-orchestrator` profile's skill mirror (`profiles/kanban-orchestrator/skills/...` —
  mirrors are STALE SNAPSHOTS, not auto-synced; both were updated this run; the sampling-test
  profile holds an older stale copy intentionally left untouched).
- **This document** is the doc of record for the topology.

Apply mechanism: converged by `route_by_default_converge.py` (grep-guarded, idempotent;
pre-mutation backups in `backups/butler-routing-2026-10-22/pre/`) — script filed with this card.

## 7. Provisioning kit + QR runbook pointers

- Provisioning kit (idempotent per-butler stamping): `scripts/provision_g01_butler.py`,
  `scripts/provision_gaudi_butler.py` (parameterizable patterns), `scripts/stage3_converge.py`
  (g02/swco/sjproto), `scripts/verify_butlers.py` / `verify_tools.py` (verification sieves).
- QR/token runbook (bot creation, token hygiene, one-keystroke re-do):
  `docs/butler-qr-runbook-2026-10-22.md` — tokens never touch cards, comments, or git.
- Wiring + isolation evidence: `docs/BUTLER-VERIFY-2026-10-22.md`.
- Bank law: `docs/BANK-MAP.md`.
- New butlers (e.g. a future `sj-butler` for the production skipjack board): stamp from the
  kit, same bank pattern (`<profile>` bank), add one row to §2 here and the routing lines in
  the skill + default SOUL.

## 8. Reload note (operator gate)

SOUL.md is read at session start (`prompt_builder.load_soul_md`), and the skill copy loads per
session. Long-lived gateway sessions serving the five butlers and the default profile will
keep their pre-doctrine prompts until their sessions reset (daily at 04:00 per
`session_reset: at_hour: 4`, or 7 days idle) **or** the gateway is restarted. **Restart is deliberately left to the operator** (restarts kill in-flight
workers). Profiles needing a reload to pick the doctrine up immediately: **g01-butler,
g02-butler, gaudi-butler, swco-butler, sjproto-butler, default**. Workers pick the SOUL change
up on their next dispatch (fresh process per card) — no restart needed.
