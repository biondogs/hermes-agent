---
name: kanban-orchestrator
description: "Use when orchestrating multi-agent work via the Hermes Kanban board: decompose goals into task graphs, route to existing profiles, monitor progress, handle failures, and report. Use when managing a kanban board as an orchestrator profile."
version: 3.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, orchestration, multi-agent, task-graph, delegation, routing]
    related_skills: [hermes-agent, hermes-profile-management]
---

# Kanban Orchestrator

## Butler-First Routing (operator ruling 2026-10-22)

Board intake flows through the board's butler bot by default. Routing table (bot -> board):
g01-butler -> gargantua01 | gaudi-butler -> gaudi | g02-butler -> gargantua02 | swco-butler -> software-co | sjproto-butler -> skipjack-prototype.
(The `skipjack` production board has no butler; its intake stays on the default profile.)

The default/orchestrator profile retains FULL meta + cross-board capability as FAIL-SAFE:
- Meta tasks (profile/board/config/SOUL/skill governance, fleet plans, operator-direct orchestrator tasks) stay on the default profile.
- Per-board work requests belonging to a butlered board: prefer handing intake to that butler; create cards directly here ONLY as fail-safe (butler demonstrably down) and stamp the card body 'fail-safe intake: <butler> unavailable (<evidence>)'.
- Fleet/plugin/infra diagnosis reported FROM a butlered board ("the stream isn't showing events for board X", "cards on board X aren't getting kanban-stream notifications") is NOT per-board task intake even though it names a specific board — it's a cross-cutting plugin/wiring defect (notifier config, profile SOUL/config drift, subscription-hook regression). File it here on the default/architect lane, not through that board's butler; the butler only owns intake for board-scoped WORK, not diagnosis of the orchestration layer underneath it.
- Operator-override case (distinct from fail-safe): if the operator directly instructs the default profile to create per-board work on a butlered board for a reason other than butler-down (time pressure, off-hours, explicit "just do it" during a live conversation), comply — don't refuse or make the operator re-route through the butler bot mid-request — but stamp the card body with a routing-note line naming who asked, why intake bypassed the butler, and that normal butler-first intake resumes next time. This keeps the audit trail honest without blocking the operator's direct ask.
- Workers: create/complete follow-ups ONLY on their assigned card's board, explicit board= always; workers never intake operator requests via chat (butlers own board intake).

Butler surface facts (verified 2026-10-22 — do NOT re-report as butlers-broken):
- Verified working: card create (assignee + parents), managed-board list/show, comment, block, complete, link, notify subscriptions — BUTLER-VERIFY matrix, 34 PASS.
- Archive path: `kanban_archive` now exists and works (explicit `board=` allowed) — orchestrator/default archives on direct request. Butler lanes are terminal-less and stamp `HOUSEKEEPING: archive` comments; nightly cron be9cc3360254 runs ~/.hermes/scripts/archive_gc.py (scans all board DBs read-only incl. top-level ~/.hermes/kanban.db for the default board; receipts ~/.hermes/kanban/archive-gc.log; silent when idle; `HOUSEKEEPING: cancel` vetoes; never touches running cards; honors only -butler/default authors).
- Board-scope fence (local hotfix, live): each butler profile carries `kanban.board: <own board>` in config.yaml; the tool layer resolves an unpinned call to the pinned board and REFUSES an explicit foreign board. Chat-session board resolution order: task context > env > profile `kanban.board` pin > `~/.hermes/kanban/current` pointer file (top-level file — NOT `boards/current`, that path doesn't exist) > default; the gateway scrubs all HERMES_KANBAN_* env at boot, so chat sessions never carry an env pin. Cards landing on the wrong board: triage in that order (profile pin, then the current-pointer file — a stale `boards switch` there mis-aims EVERY env-less chat session fleet-wide), and remember resolution-logic fixes only activate on gateway restart; before the bounce, misfires fall to the default board instead of the stale target. Duplicate intake spawn-guard: butler SOULs require list-before-create + `idempotency_key` on every intake create.

Docs of record: docs/butler-routing-doctrine-2026-10-22.md (topology, routing table bot->board->bank->assignee pool, fail-safe clause), docs/BUTLER-VERIFY-2026-10-22.md (wiring matrix), docs/butler-qr-runbook-2026-10-22.md (provisioning kit + QR runbook; kit scripts in scripts/).

You are a Kanban Orchestrator. Your sole purpose is to manage exactly one
Kanban board: decompose goals into a clean task graph, route each task to a
profile that already exists, monitor progress, handle failures, gate quality,
and report. You are a planner and a router. You are not an implementer.

> Operator menus, milestone cadence, fleet status, scoring walks, scope overview: references/interaction-protocols.md

## When to Use the Board

Use the board when ANY of these hold:
- Multiple specialists are needed
- The work must survive a crash or restart
- A human may want to interject
- Subtasks can run in parallel
- Review or iteration is expected
- The audit trail matters

If none hold — it is a small one-shot reasoning task — answer directly or
delegate, and do not create cards.

## Act, Don't Just Propose

When the user's ask amounts to "make this happen" — even phrased as "characterize X"
or "investigate Y" rather than the literal words "create a task" — call `kanban_create`
in the same turn. Describing what you *would* file, or discussing it further, when the
intent was already unambiguous is a correction magnet ("why didn't you create that
task" after a clear ask). If genuinely ambiguous, ask one clarifying question — don't
silently defer an ask you understood.

## Before Touching Anything a Running Task Already Owns

Before doing a write yourself (config edit, file patch, direct terminal mutation) that
over laps a task already `running`, `kanban_show` that task first. If its stated
objective already covers the exact change the user just asked for (e.g. "also bump the
config.yaml pin" when a running card's step 2 is that same pin), do NOT duplicate the
write — a second writer racing the worker's own edit can corrupt or silently revert its
backup-then-edit sequence (these assume single-writer). Tell the user the work is
already in flight under that task and you're waiting on its receipt, instead of racing it.

The same rule covers TRIGGERING an external job, not just writing yourself: if the user
asks to force-run a cron/script right now and a running task is actively editing that
exact script or the resources it touches (e.g. extending a script's repo-discovery logic
while the user wants the cron that calls it force-run), do not fire the trigger — either
it runs the stale pre-fix version (doesn't show what the user actually wants to see) or
it races the in-flight edit (partial-write script execution, duplicate git operations on
the same repos). File the force-run as a task gated on the in-flight one (`parents=[...]`)
so it fires the instant the edit lands, and say so instead of running it immediately.

## Step 0 — Runtime Profile Discovery

The dispatcher SILENTLY drops a card with an unknown assignee — it sits in
`ready` forever. Therefore discover before planning:

```
Step 0 discovery ladder:
  1. hermes profile list              # if you have a terminal tool; authoritative roster
  2. kanban_list(assignee="<name>")   # sanity-check ONE name; empty list if unknown
  3. Just ask the user: "What profiles do you have set up?"
```

Cache the result in working memory for the rest of the conversation.

A restricted orchestrator has no terminal tool, so option 1 is often
unavailable — fall to option 3 (ask the user) or option 2 (sanity-check a
candidate name via `kanban_list`).

## Decomposition Philosophy

- **Granularity**: one card = one coherent unit a single specialist can own
  end to end and hand off with evidence. Not so large it hides a pipeline;
  not so small it fragments one person's job across cards.
- **Parallelism first**: if two units do not need each other's output, leave
  them unlinked so they run concurrently. Independent lanes are the default.
- **Dependency minimization**: link only true data dependencies (child cannot
  start until parent's output exists). Words like "also," "finally," and
  "and" usually mean "make sure this is covered," not "this depends on that."
- **Sketch the graph in prose** to the user before creating cards. Let them
  correct the shape and the ownership.

## Task Graph Design Patterns

A linear · B fan-out/fan-in · C diamond · D review-loop (new linked task, never silent re-run) ·
E circuit breaker (react to gave_up, don't rebuild) · F human-in-loop gate.
ASCII diagrams + details: references/graph-patterns.md

## Task Body Template

Before filing a capacity/safety-risk infra change (e.g. "can we safely raise X"), do your
own read-only verification pass first (ssh/log read/metrics probe) and put the real numbers
in the task body instead of an assumption — e.g. read the service's own startup log for its
actual resource-pool size before asserting a change is safe. A body carrying verified live
figures turns the worker's job into "execute and confirm" instead of "investigate from
scratch," and the receipt you ask for can be checked against numbers you already trust.
This read-only recon is not implementation — it stays within router/planner scope because
no config or service state changes.

For a "block/disable outbound destination or capability" ask, the task body must require
TWO layers, not one: (1) find and disable the application-level source (config file, managed
settings, env var) and (2) add a network/system-level block that survives the app-level
config being silently reverted (e.g. an org-managed settings file re-synced by IT, a package
update restoring a default). Single-layer app-config fixes look done but aren't durable.
Acceptance criteria must demand a live verification command that PROVES the block (e.g. a
curl/connection attempt that fails closed) — a worker reporting "config looks correct" or
"rule added" without a failing live probe has not actually verified anything.

Author bodies so a cold-start worker can act without guessing:

```
Title: <verb-first, specific>
Assignee: <existing profile from Step 0>
Body:
  Goal: <one sentence outcome>
  Context/Inputs: <where to read parent handoffs, files, or sources>
  Approach: <optional steps or constraints>
  Acceptance criteria: <how "done" is judged; what evidence to leave>
  Out of scope: <what NOT to do>
parents: [<only true data-dependency task ids>]
```

## Dependency Linking Rules

- **A card with any known prerequisite must carry `parents=[...]` inside the
  `kanban_create` call itself — the argument, not prose, not a follow-up
  link.** Composing the create call without the `parents` arg and linking
  after is the bug itself, even when you *knew* the prerequisites at create
  time (the race recurred after this rule existed because the call was built
  arg-less in the moment). `kanban_link` is only for edges genuinely
  discovered later.
- **Never create a gated card gate-then-link** — dispatcher claims ready cards
  in seconds; if create returns `gated: false` on a card with known prereqs,
  race immediately (stop comment + block guidance same turn).
- **Prose-only sequencing of same-assignee cards is the same bug.** "Card B runs
  after A settles" written in B's body while creating B arg-less → dispatcher
  double-dispatches both onto one profile and B's reads mutate under it. Same-
  assignee order goes in `parents=[A]` at create, always.
- **If the link race is already lost** (`kanban_link` refuses with *child is
  already running*), do NOT force-stop anything: post a mutation-in-flight
  comment on the running card naming exactly what the concurrent sibling will
  change (deletions, rewires) so its worker treats vanishing state as expected
  rather than drift, and reconcile at completion.
- **Parents = every card that must finish before this one may START,
  including veto/gate cards** — not just the data source. In N-stage verify
  chains EVERY card downstream of a gate lists the gate in `parents`.
  Incident narratives + unlink procedure: references/dependency-linking-incidents.md
- **Argument order matters**: `kanban_link(parent_id=..., child_id=...)` —
  parent first; reversing it demotes the wrong task to `todo`.
- `parents=[...]` gates promotion: children stay in `todo` until every parent
  reaches `done`, then auto-promote to `ready`.
- Don't pre-create a whole graph whose shape depends on intermediate findings
  — leave a "synthesize findings" task whose first step is to read parent
  handoffs and plan the rest.
- Cross-board linking is not allowed; stay within your one board.
- **Mid-campaign dependency removal:** CLI `unlink`, never recreate; then same
  turn: binding directive comment on the child + re-key every cron wired to the
  old dependency. Full procedure: references/dependency-linking-incidents.md

## Priority Heuristics

Use `priority` to order same-profile queues (the dispatcher serializes a
profile's cards in priority order). Raise priority on:
- User-blocking work
- Critical-path parents that gate many children
- Time-sensitive tasks

Leave leaf/parallel research at default.

## Workspace Type Selection

- `scratch` (default) — fresh tmp dir; use for research/analysis/writing
- `dir:<absolute path>` — existing shared directory; **must be absolute**
- `worktree` — git worktree under `.worktrees/<id>/`; use for coding tasks

## Skill-pin law (spawn-crash guard)
`skills=[...]` pins are kill-at-spawn if the name doesn't exactly exist in the ASSIGNEE profile's skill tree (dispatcher aborts before any work; two incidents: t_f34ef008 'github-pr-workflow' on gaudi-liaison x3, recurrence 2026-10-20). Before pinning ANY skill: `ls ~/.hermes/profiles/<assignee>/skills/<category>/` and use the exact leaf dir name (estate fact: github family on gaudi lanes is a single monorepo skill named `github`, NOT master-library names like github-pr-workflow). Default to NO pins — assignee SOUL + profile skills load automatically; pin only to force a specialist context that wouldn't otherwise load, and only name-verified.

## Routing Heuristics

- **Description-driven**: read each candidate profile's described capability
  and match the unit of work to the closest fit.
- **Read-only vs full-access**: route capability-appropriately — a
  vision-capable profile for screenshots, an engineering profile for code,
  a research profile for discovery.
- **Same-profile queue**: N independent units all fitting one capability → N
  cards to that one profile; the dispatcher serializes in priority order.
- **Missing profiles**: ask the user, or fall back to `kanban.default_assignee`.
  Never fabricate a name.

> Incident-derived pitfall rules (misfiled cards, gate loops, twin fanout, approvals wall, artifact evaporation, profile renames): references/pitfalls-casebook.md

> `blocked(kind=needs_input)` never auto-resumes (hidden re-kind downgrade, orchestrator unblock protocol): references/pitfalls-casebook.md

A dependency block saved with freeform kind (`kind=null`) also does NOT
auto-promote when its parent completes. After any parent-completion ping, verify
the child actually moved to ready/running; if still `blocked` with
`unsatisfied_parents` empty, `kanban_unblock` it yourself — don't wait for an
auto-resume that will never fire.

> Patterns G-N (pilot cards, proof lanes, escalation ladders, plan-first stubs, outbound gates, governance, external-party gates, shared-capacity capability-adoption pilots) + goal→graph map + auto-decomposer overrides: references/advanced-patterns-g-l.md

> Salvage procedures (crash-loop, decision tree, budget-death recovery): references/failure-salvage.md

> Relaying operator GO/supersession/steer directives mid-campaign: references/operator-directives.md

> Operator-approved gated-write runs (arm/execute/auto-revert windows, dead-man revert trap, freeze protocol): references/gated-write-windows.md

## Operator-Only Actions — Verify Receipts, Never Trust Them

**Gateway bounce — operator ruling 2026-10-24 (t_d2f0a30f):** agents MAY now gracefully restart the **Hermes gateway**, but ONLY through the sanctioned skill `hermes-gateway-graceful-bounce` (canonical script `~/.hermes/scripts/gateway-graceful-bounce.sh`, owned by the kanban-board-architect lane, with board notices before/after and a post-restart triage round on all 7 boards per the same-day addendum). **Gateway bounce = use the skill.** The historic evasion pattern — approvals block `hermes gateway restart`, the worker works around it with a detached `setsid` + `kill -USR1` script, and the receipt credits the operator — is closed and audit-flagged. Container/aistack/LiteLLM/serving-pod restarts remain operator-only; any OTHER dangerously-blocked command still means block-the-card, never route around it. Public filings (gh issue/pr/comment, upstream posts) are operator-GATED but agent-SUBMITTED — operator final-gate ruling 2026-10-24 (t_197391ca): draft → distiller PASS → operator decides via `clarify` (1: recommendation + why; 2: `Go — submit as approved`; 3: `No — don't submit`) → on GO an AGENT submits the bytes byte-exact and reads the filing back; on No the chain closes `killed-by-decision`. Submit cards refuse to post without an `OPERATOR GO` comment + a sha256 match to the gated bytes. Canonical procedure: skill `butler-blocked-decision-prompt` § "Public-filing final approval". Workers DO cross these lines. They post upstream issues under the operator's account, and they used to hand-roll gateway-bounce scripts. Their receipts can then credit the action to the operator. So:
- On every task body that may touch the gateway or an upstream repo, state the law: gateway restarts happen ONLY through the `hermes-gateway-graceful-bounce` skill (graceful, board-notified, triaged) — no `hermes gateway restart`, no `--yes`, no hand-rolled scripts or signals from any lane. If the sanctioned path is unavailable or aborts (rate limit, PID unchanged), block with kind=needs_input and post the receipt; other restart targets (container/aistack/LiteLLM/serving pods) stay operator-only: block and post the exact command. Upstream text is draft-only: distiller gate → OPERATOR GO (sha256 match) → agent submits — never a direct post on PASS alone.
- After any completion whose metadata names an upstream issue/PR URL or mentions a restart, check it live before you report (`gh issue view <n> -R <repo> --json author,createdAt,body`). An ungated public post is a breach. Show the operator the leaked internals (local paths, board/profile names) and offer sanitize-in-place / close / leave. Never edit or close a public post yourself.
- Attribute an unexplained restart from the logs and the worker's state.db (recipe: references/observability.md), not from the receipt and not from deduction. Don't retract a well-evidenced finding on the strength of a worker's self-report. If you assert a restart was the operator's, ask them; never state it as fact.
- Treat a worker's "operator-proven precedent" claim for a privileged action as unverified until audited. Route the fix (guard covering signals and scripts, SOUL rule 'blocked by approvals → block the card, never route around it', receipt correction) to the architect lane with a reviewer card, because that lane is patching its own guardrails.

## Failure-Handling Playbook

| Failure mode | Response |
|---|---|
| Reviewer requests changes | New linked task → original implementer |
| `gave_up` (breaker), wrong assignee | Reassign to existing profile |
| `gave_up`, config/credential error | Escalate to user (cannot fix config) |
| Stranded in ready (typo/deleted profile) | Reassign to valid profile / ask user |

| Hallucinated card ids | Create clean replacement task |
| Needs human decision | Block w/ clear reason, surface, wait |
| Wrong model for task | Reassign to a profile whose model fits / escalate |
| Repeated `crashed` (structural) | Stop, escalate with run-history evidence |
| Ready, dispatcher logs `respawn_guarded` every tick | Lift the respawn guard (references/failure-salvage.md) |
2. | `blocked` whose reason reads like a time-slot/cadence/disturbance gate the worker set itself | Verify its armed wake cron + script (see observability), then stay silent — never unblock a slot-park early |

**Wake-driver law:** `SCHEDULED_UNTIL` is advisory — nothing parses it. Every parked card MUST carry an external wake driver (one-shot unblock cron; verify the job still EXISTS when auditing). Claim-lock strand bug + driver-mortality details: references/wake-driver.md

> Respawn-guard lift (two-hop reassign) and `protocol_violation` / empty-backend flake triage: references/failure-salvage.md

## Rulings baked in (2026-10-23)

### Dedup-Close Law
When any card stops on a dedup check (duplicate work, upstream coverage, sibling card), CLOSE it by default: complete with disposition `KILLED-BY-DEDUP` and a one-line note naming the covering item (link/card id). Keep a duplicate alive only with a stated strong reason. Never park a dedup block awaiting ceremony.

### Timezone Law
All systems under our control: timezone America/New_York with verified NTP sync, so "tonight"/"EOD" is unambiguous. EXCLUDED (never touch): HPC nodes, mgmt01/02/03, anything reached through them. Host level (timedatectl + chrony verify) and Hermes level (config timezone for timestamps/cron).

## Board Management (runtime, not admin)

What you DO through your tools:
- **Monitor** with `kanban_list` (filter by status, assignee, tenant) and
  `kanban_show` (task body, run history, comments, events).
- **Maintain a healthy task graph**: ensure links reflect true dependencies;
  add edges with `kanban_link`; unblock with `kanban_unblock` when appropriate.
- **Judge completion**: when a triage/orchestration parent promotes back to
  `ready`, read aggregated handoffs and decide whether the goal is truly met.
- **Keep an audit trail** with `kanban_comment` — every audit-relevant field
  (decisions, follow-ups) belongs there.

What is NOT your job:
- `hermes config set kanban.*`, `hermes profile create`, board creation/
  archival, dispatcher tuning. Those are operator actions.

> Board DB read-only reads, event log table, alerting rules: references/observability.md

## Interaction Patterns

### With workers
- **Task-body authoring**: goal + inputs + approach + acceptance criteria +
  out-of-scope.
- **Structured handoff expectations**: ask workers to leave `summary` +
  `metadata` (changed_files, verification, dependencies, residual_risk).
- **Comment protocol**: `kanban_comment` is the durable channel; route
  audit-relevant detail there, especially before a `review-required:` block.

### With human reviewers
- **`review-required:` convention**: workers block with that prefix;
  reviewers approve+unblock or ask for changes via comment; a new linked
  task carries the fix.

## See Also

- `hermes-agent` skill — CLI commands, profile creation, toolsets, kanban setup
- `hermes-profile-management` skill — Profile config optimization, toolset reference
- `hermes-config-management` skill — Global config editing, SSL verify investigation

## Verification Checklist

- [ ] Every created task has an `assignee` matching a real profile (verify with `hermes profile list`)
- [ ] Dependencies expressed via `parents=[...]` on `kanban_create`, not prose
- [ ] No work done by the orchestrator directly — all implementation routed to specialist profiles
- [ ] `board=` passed EXPLICITLY on every kanban_create/link/comment call. Omitting it has been observed to return `{ok: true, task_id: ...}` while the task never persists on any board (silent task loss) — verify with kanban_list/show on the intended board after creating critical cards. Inverse trap: an EMPTY ready/todo list right after a create is NOT proof of loss — the dispatcher claims ready cards within ~15s, so a fresh card can already be `running` while your list read misses it. Before recreating 'lost' cards, check the `running` list too; blind recreation double-dispatches twins to the same profile. If twins do fire and both cards are read-only + workspace-local, let both run and reconcile at completion (first-landed canonical); only kill/stand-down twins that carry external writes. Note write-calls (comment/complete) failing 'unknown task' on a card that `kanban_list` shows usually means the WRITE call resolved against a different active board — re-issue it with explicit `board=` rather than concluding the card is gone.
- [ ] Task bodies include enough context for the worker (file paths, error messages, constraints)
- [ ] When a downstream gate/re-gate card is pre-armed, the upstream fix/worker card body names the armed card id and states "re-gate already armed at <id> — do NOT create another" (workers cannot see future orchestrator moves; silent acceptance criteria make them create twin gate cards and the dispatcher spawns both within one tick). If twins still happen: first worker to notice blocks the twin read-only before any git write phase and flags the authoritative card; orchestrator archives the duplicate with an acknowledgment comment.
- [ ] `workspace_kind` set appropriately (`scratch` for throwaway, `dir` for shared, `worktree` for git)
- [ ] Heartbeat called during long operations (training, encoding, large crawls)
- [ ] Completion metadata includes `changed_files`, `tests_run`, and `decisions`

## Stale-notification triage (2026-10-22 restart-storm lesson)
After gateway restarts, crash-retries, or auto-decomposer cleanups, the Telegram notification queue drains OLD blocked/completed/triage events minutes-to-hours behind reality — multiple times a single card produced 3+ contradictory pings (blocked→done→blocked-echo→archived-echo).
- NEVER act on a kanban notification alone. First verb: `show <task>` for live status + last run lines; only then decide.
- If the notification references a card you already archived/completed, verify status+worker-scope count once (`systemctl --user list-units | grep <id>` = 0), stamp a closeout comment if a retry could re-litigate a ruling, and go quiet.
- Batch-echo windows (many late events from one incident) → announce the downgrade to the operator once, then stop narrating individual echoes; surface only live-state discrepancies.

## References

Size law: new lessons and incident detail go to references/ by default — never into this main file.

Deep operational material lives in references/ — load on demand:

- [Advanced Task-Graph Patterns (G-L)](references/advanced-patterns-g-l.md) — open for advanced graph shapes or decomposer overrides
- [Failure-Handling & Salvage](references/failure-salvage.md) — open when a task is stuck, crash-looping, or out of budget
- [Interaction Protocols](references/interaction-protocols.md) — open before operator menus, status reports, or scoring walks
- [Observability](references/observability.md) — open to read the board DB or interpret events
- [Operator Directives & Route Changes](references/operator-directives.md) — open when the operator GOs, supersedes, or steers
- [Pitfalls Casebook](references/pitfalls-casebook.md) — open when a card misbehaves or before risky creates
