# Board status + alert flow — study of how worker/board noise reaches you, and cleaner options

**Date:** 2026-11-01 · **Author:** sw-architect · **Card:** t_eef7d4d2 (operator-direct intake)
**Mode:** REPORT ONLY — nothing was changed; every proposal below is an option, not an action.
**Question asked:** *"the current kanban Ops sessions are a little too noisy with alerts; we need to review how all of that is working"* — and, once boards carry their own bot/env (BOARD-LAYERS), *"maybe all of the nodes can report through the butler sessions — that might be too cluttered, needs further review."*

---

## 1. TL;DR

1. **The noise is measurable and mostly one thing.** Of the roughly **380 Telegram messages/day** the fleet pushes into your chats, ~126/day are per-event "task completed / unblocked / blocked" pings, and **~90% of those come from a single known leak**: notification subscriptions on the per-board databases that were never given the event-kind filter. The fix was rolled out on the root board only (2026-10-2x); **~1,056 live unfiltered subscriptions remain** on software-co, gaudi, g02, skipjack boards.
2. **The one alert flow that's supposed to fight noise is dead.** The decision-nudge watchdog (which re-prompts you about blocked needs-input cards) has sent **zero nudges since Oct 31, 12:15** — a self-deadlock between its crontab wrapper lock and its own internal lock, verified by live experiment in this study. So today you get all the churn and none of the "hey, 3 cards are waiting on you."
3. **Consolidation is worth it, but full butler-routing is a big change.** Three candidate models are below (§6). Recommendation: **Model C (hybrid)** — tighten the event filter everywhere + fix the watchdog first (cuts ~70% of message volume for one small card), then decide about stream visibility and butler digests separately.

---

## 2. Current topology — who can message you today

You (chat 8158007517) are reachable through **six+ distinct bot identities** that carry board/machine status:

```
                          ┌──────────────────────────────────────────────┐
                          │  YOUR TELEGRAM (single user, many bots)      │
                          └──────────────────────────────────────────────┘
     ▲         ▲         ▲         ▲         ▲         ▲
     │         │         │         │         │         │
 [home DM] [kanban-ops] [swco_bot][gaudi_local_bot][g02_ops_bot][skipjack_proto_bot][gargantua01_proto_bot]
  default   @ga01_kanban   swco-     gaudi-      g02-      sjproto-     g01-
  bot       ops_23_bot     butler    butler      butler    butler       butler
     │         │             │          │           │         │            │
     │         │             └── each butler = chat front door to ONE board, own bot token
     │         │
     │         ├──(a) LIVE STREAM: one message per running task, edited in place (≤1 edit/5s)
     │         │        all boards stream into the SAME ops DM   [kanban-stream plugin]
     │         ├──(b) daily completion digest 08:00              [kanban-completion-digest.py]
     │         ├──(c) decision nudges (≤1 per 15 min)            [decision-nudge-watch.py] ⚠ DEAD since 10-31
     │         └──(d) incident alerts (gateway dead/stall, aistack health) [alert-sink.sh, direct Bot API]
     │
     ├──(e) gateway notifier → your subscriptions: per-event messages + "wake" pings
     │        delivered THROUGH THE BOT OF THE PROFILE THAT SUBSCRIBED YOU:
     │        mostly the butler bots (swco/gaudi/g02/sjproto), some to home DM
     ├──(f) cron job deliveries (tripwires, upstream watches) — event-driven, quiet
     └──(g) your conversation replies (all bots)
```

Key mechanical facts (all verified in code/config this study):

- **Every card you touch subscribes you** ("notify+wake"): when the card hits a terminal event, the gateway sends a message to the subscribing chat *and wakes that profile's agent session*. The subscription row can carry a **kinds allowlist**; rows without one deliver **every** terminal event kind: completed, unblocked, blocked, crashed, archived, review… — that's the leak.
- The global allowlist (`kanban.stream_notify_kinds` = blocked, gave_up, crashed, timed_out, block_loop_detected, review_requested, changes_requested) exists in config; new subscriptions *should* be stamped with it (upstream fix, cards t_eea7a920 / t_1962d623) — but see §4 F2: on the per-boards it demonstrably is not happening for a large share of rows, and unfiltered rows are **inherited by child cards** when work is decomposed, so the leak regenerates itself.
- The **kanban-ops stream** is fire-and-forget from worker hooks: first tool call → new message; every subsequent activity → edit of that message (throttle 1/5 s). Each retry/reclaim/respawn of a task = another new message.
- The five **butlers** are interactive profiles each pinned to one board; a wake on a butler-stamped subscription makes the **butler agent take a turn** (a model call — even if it only acknowledges). Wakes therefore cost tokens, not just attention.

---

## 3. Measured volume — last 7 days (Oct 25 – Nov 1, all boards, read-only DB sampling)

### 3.1 Messages you receive, by channel (est. from event data + logs)

| Channel | Volume / 7d | Per day | What it is |
|---|---|---|---|
| **Ops feed** — live stream (new messages) | ~1,758 task-run messages | ~250 avg, **peak 354** (Oct 27) | one live message per task run; software-co alone = 1,030 (~147/day) |
| **Ops feed** — edits on those messages | unlogged (throttled ≤1/5 s per active task) | constant while fleet is busy | the "chat is always alive" effect |
| **Gateway notifier** → butler chats + home DM | **~881 messages** | ~126 | see breakdown below |
| …of which additionally **wake** an agent | ~600 of the above | ~86 | butler/home agent takes a turn (token cost) |
| **Ops feed** — daily completion digest | 1/day (new, first fired Nov 1 08:00) | 1 | all boards' yesterday completions in one message |
| **Ops feed** — decision nudges | **0** (intended ≤96/day cap, ≥4 pending → digest) | 0 | ⚠ watchdog deadlocked since Oct 31 |
| **Ops feed / home DM** — incident alerts (deadman, stall watch, aistack health) | ~3 real this week (today's were a self-test) | ~0–1 | event-driven, correctly rare |
| **Home DM / butler chats** — cron deliveries | ~25 (20 = g02 vigil "still watching Azure ticket" every ~20 min, only-something-to-report) | ~3 | already quiet; trips only on changes |

### 3.2 The ~881 notifier messages, by event kind (7d, fleet)

| Kind | Count | Share | Classification (§5) |
|---|---|---|---|
| completed | 557 | 63% | **redundant** — already in the daily digest |
| unblocked | 129 | 15% | **redundant** — pure bookkeeping (dependency opened) |
| blocked | 103 | 12% | actionable (only when needs_input) |
| crashed | 39 | 4% | actionable-ish (many self-heal via re-dispatch) |
| block_loop_detected / review_requested | 18 + 18 | 4% | actionable |
| gave_up / changes_requested / timed_out | 12 + 3 + 2 | 2% | actionable |

### 3.3 The same 881, by receiving bot (7d)

| Delivering profile (bot) | Messages / 7d | /day |
|---|---|---|
| swco-butler (`@swco_bot`) | 430 | ~61 |
| gaudi-butler (`@gaudi_local_bot`) | 188 | ~27 |
| g02-butler (`@gargantua02_ops_bot`) | 123 | ~18 |
| sjproto-butler (`@skipjack_proto_bot`) | 100 | ~14 |
| default (home DM) | 40 | ~6 |

**So the "kanban Ops sessions are too noisy" experience decomposes into**: ~250 live-stream messages/day in the ops DM (by design — it's a glanceable execution view), plus ~126 pings/day scattered across your five butler chats, **78% of which are churn (completed/unblocked)** that the daily digest already covers.

### 3.4 Underlying fleet event volume (context)

7 days, all boards: 1,758 task runs · 756 completions · 119 blocked · ~23,000 heartbeats. software-co is 60–70% of all activity.

---

## 4. Findings (each verified; nothing changed)

**F1 — The completion-churn leak is the single biggest noise source.**
~686 of 881 notifier messages/week are `completed`/`unblocked` pings into butler chats, each often also waking the butler (≈600 butler agent turns/week ≈ 86/day — a real token cost on top of the attention cost). The daily digest (`kanban-completion-digest.py`, B2-2) already reports completions once a day. The pings are duplicated signal.

**F2 — The event-kind filter exists but is not effective on the per-board DBs.**
- Live operator subscriptions: default board = **263 live, 0 unfiltered** (retrofit worked there). Per-boards = **1,126 live, 1,056 unfiltered (94%)**.
- New rows are still being born unfiltered: e.g. software-co, last 48 h: 27 of 87 new rows unfiltered; g02: 17/21.
- Two mechanisms found in code: (a) subscription **inheritance** — a child card inherits the parent's subscription *including a NULL kinds value*, so one legacy unfiltered row propagates through every decomposition; (b) subscriptions created in profile contexts (butler chats) don't reliably pick up the root config knob. Exact mix needs a small follow-up to pin down, but the population and its regeneration path are established.

**F3 — The decision-nudge watchdog is deadlocked (silent since Oct 31, 12:15).**
The crontab wraps it with `flock -n LOCKFILE script`; the script *also* `flock`s the same file internally (guard added 10-31 after a double-send race). A child process **cannot** re-acquire a flock its own wrapper holds → every cron tick since the guard landed logs *"another instance is running; exiting (lock held)"* and exits without scanning. Verified by a live repro experiment on a scratch file (child always fails under the wrapper; succeeds without it). The last real nudge digest was Oct 31 12:00 ("4 cards nudged, 15 due"). Net effect today: **decision reminders — the one alert class you actually asked for — are off**, while churn is on. One-line fix options: drop the internal flock (the wrapper already guards), or use a different lock file inside the script.

**F4 — The stream is working as designed, but it is the largest single channel by volume.**
~250 new messages/day fleet-wide, all boards interleaved in one DM, each buzzing with ≤5 s edits while its task runs. It is genuinely useful as a live grid during an active watch (e.g. FLIRPHONE/W8 sessions), but its default-on nature means quiet periods still accumulate hundreds of messages/day fleet-wide, and every crash-retry loop mints new messages for the same card.

**F5 — The cron/alert lanes are already healthy.**
Cron Telegram deliveries are mostly suppressed (only ~25 delivered/week, mostly the g02 vigil); tripwires and watches fire only on real changes; the deadman/stall/health alert path is incident-gated and correctly rare. The 2026-10-30 rerouting of cron reports away from the home DM (`kanbanops_send.py`, card t_3f0fe088) did its job. **No work needed here.**

---

## 5. Noise classification — what deserves to interrupt you

| Class | Events | Desired handling |
|---|---|---|
| **Interrupt** (a human decision or an incident) | blocked needs_input, review_requested / changes_requested, gave_up, decision nudges, gateway dead/stall, model-serving outage | push immediately, any hour; today's alert paths already do this — except the dead nudges (F3) |
| **Notice** (abnormal but self-healing) | crashed / timed_out (dispatcher will retry), block_loop_detected | push, but consider folding repeats of the same card into one line/day |
| **Digest** (normal progress) | completed, unblocked, daily summaries, vigil all-clear | 1–3 digests/day per board (already exists fleet-wide; the per-event pings should stop) |
| **On-demand** (ambient execution detail) | live stream frames, tool-call rollups | available when you open the chat / ask a butler; not pushed as new messages by default |

---

## 6. Candidate models

### Model A — Status quo + tighten the filter (minimal)
Keep all channels; fix the two mechanical faults.

- **Do:** (1) stamp the kinds allowlist on the ~1,056 live unfiltered subscription rows (one read-only-then-write SQL sweep, same playbook as the default-board retrofit); (2) make child-card inheritance stamp kinds at creation (upstream-sized fix or a small `kinds-restamp-watch`-style sweeper as a stopgap); (3) fix the nudge flock deadlock (one line); (4) optionally: nudge only for needs_input (already its design) and confirm the auto-subscribe stamping in butler contexts.
- **Consequences:** butler-chat volume drops ~78% (881 → ~195/week ≈ 28/day, nearly all actionable); decision nudges return; stream untouched (still ~250/day).
- **Migration cost:** one small card + one follow-up; hours, low risk, no habit change, entirely reversible.

### Model B — Butler-as-single-reporter per board (your hypothesis, maximal form)
All board-local events route to that board's butler; the butler is the only thing that messages you, choosing between "interrupt now" (decisions, incidents) and "include in next digest" (everything else). The ops stream DM is retired or kept only for fleet-wide incidents.

- **Consequences (good):** one conversational surface per board; the butler can explain context, group related events, and answer follow-ups — strictly better than raw event text. Fits BOARD-LAYERS naturally (board + its butler become a self-contained "device").
- **Consequences (bad):** you were right to suspect clutter — if events still *wake the butler on arrival*, the noise and the token cost just move to a different bot, and the butler turns become the bottleneck (86 wake-turns/day today). To not be clutter, the butler must run on a **digest cadence with an interrupt override**, which means: the gateway notifier must stop waking butlers on routine kinds (same fix as A), the butler needs a scheduled digest prompt (new cron per butler, not per event), and the "glanceable live grid" of the stream is lost unless kept somewhere. Also couples board visibility to butler availability (a crashed butler profile = a silent board — needs the deadman treatment).
- **Migration cost:** medium-high. Touches the core notifier's wake policy, five butler SOULs/skills, per-butler cron, and your habits; ~1–2 weeks of staged rollout with a quiet-period bake. Highest risk of *trading* noise for silence-with-surprises.

### Model C — Hybrid: three channels, three explicit contracts (recommended)
Keep the channel separation but write each channel's contract down and enforce it mechanically:

1. **Interrupt lane (any bot, immediate):** needs_input blocks, review gates, gave_up, incidents, and the (repaired) decision nudges. Mechanically: the kinds allowlist **must** be stamped on every subscription on every board (A's step 1+2) so nothing else pushes.
2. **Digest lane (butlers, cadence):** each butler sends a short board digest 2–3×/day (morning / midday / evening) covering completions, review outcomes, failures-recovered; the fleet-wide completion digest moves to a pinned evening slot or folds into butler digests. The g02 vigil-style "still watching" reports also land here.
3. **Live lane (ops stream, opt-in):** the stream stays exactly as it is *for cards you're actively watching*; make streaming opt-in per card (invert `[no-stream]` to `[stream]`, or auto-stream only while a card is < N minutes old / in a watch card chain). Background lanes stop minting messages; the DM becomes quiet between active watches.

- **Consequences:** interrupt lane stays untouched-fast; digests give you finite, predictable reading (3 chats × 3 messages instead of 126 pings); stream becomes a tool you pick up rather than weather you live under. Compatible with BOARD-LAYERS: when boards get their own envs, their butler *is* their digest+interrupt reporter; the ops stream stays as a fleet-wide "wire" you can also mute per board.
- **Migration cost:** staged. **Stage 0 = Model A verbatim** (mechanical fixes, one card, immediate ~70% cut). Stage 1 = butler digest skill + cron (small, per-board, reversible). Stage 2 = stream opt-in default flip (one config knob + a norm in card authoring; needs a one-week observation window to confirm nothing you rely on goes dark).

---

## 7. Recommendation

Adopt **Model C, starting with Stage 0 this week** because it is Model A, and Model A is nearly free:

- Stage 0 fixes the two verified faults (unfiltered subscription sweep + inheritance stamping; nudge flock deadlock). Effect: butler chats drop from ~126 to ~28 messages/day (nearly all actionable), the decision nudges (the thing you *want* to be interrupted by) come back, and the completion digest keeps covering the routine. No habit change for you at all.
- Defer Stage 1 (butler digests) and Stage 2 (stream opt-in) until after you've lived with Stage 0 for a few days — it may be enough. Revisit this doc when (a) Stage 0 has run for a week (measure again with the same probes), or (b) BOARD-LAYERS lands its first board-scoped env, whichever comes first.
- Against the "all nodes report through the butlers" hypothesis specifically: **don't route raw events to butlers — route decisions to butlers and events to digests.** Butlers are the right *voice* for a board; they are the wrong *transport* for per-event fan-out (each wake is a model turn, and 86 wake-turns/day is the clutter you're feeling, in tokens).

### What would falsify this recommendation
- If, after Stage 0, you still find the butler chats too chatty, the interrupt lane is wider than the measured 7-kind allowlist suggests → go to Stage 1 early.
- If the stream opt-in flip (Stage 2) ever causes you to *miss* a stalled card you'd have caught by glancing at the stream, revert the flip and keep the stream default-on for `watch`-type cards only.

---

## 8. Method & provenance (what was actually measured, what is estimated)

- **Measured directly (read-only):** all seven board DBs (`task_events`, `task_runs`, `kanban_notify_subs`, streams state), root `~/.hermes/config.yaml`, crontab, `cron/jobs.json` + `deliveries.db`/`executions.db`, `kanbanops-send.log`, `critical-alerts.log`, `decision-nudge-watch.log`, plugin source (`~/.hermes/plugins/kanban-stream`), notifier source (`gateway/kanban_watchers_notifier.py`, `hermes_cli/kanban_db_notify.py`, `tools/kanban_tools.py`).
- **Notifier message counts are estimates** derived by joining live subscriptions × terminal events × kinds filter over the last 7 days — upper bound for delivered messages (cursors and delivery failures can only reduce it); the direction and ratios are solid, the exact number ±15%.
- **Wake-turn counts** are estimated as `_WAKE_KINDS` events on notify+wake rows (~600/7d); actual butler turn behavior (reply vs silent ack) was not sampled per-event.
- **Stream message counts** assume ~1 new message per task run (plugin design; retries add). Edits are unlogged server-side and reported qualitatively.
- **Flock deadlock (F3) proven by experiment:** repro with a scratch lock file under the same wrapper pattern — child `fcntl.flock` reliably fails under the parent `flock -n` wrapper; control (no wrapper) acquires. Log shows 96/96 ticks since Oct 31 12:15 exiting on lock-held with no process holding the lock between ticks.
- Boards gargantua01 and skipjack had **zero runs** in the window (quiet boards; their 15 events/week are comments only) — the noise problem is concentrated in software-co (~60%), gaudi, g02, sj-proto.

*No cron, config, allowlist, SOUL, or code was modified during this study. All options require their own card + your approval before anything changes.*
