# GATE-WAIT PATTERN — link-before-block ordering rule (NORMATIVE)

- Status: **in force** on board `software-co` (operator directive 2026-10-28; card t_0b03f85e).
  R6 **NO-SELF-GATE** appended same day (operator directive via card t_84b852b9, incident
  t_fecde306).
- Extends: the standing rule *"encode prerequisites with `parents=[...]` at create time
  (never gate-then-link)"* (`docs/butler-routing-doctrine-2026-10-22.md` §3 item 3) —
  this doc extends that rule's coverage from **butler intake** to **self-parking workers**.
- Commit receipt: sha recorded on card t_0b03f85e at completion.

## Problem (verified specimen t_ad0d3a55, 2026-10-28)

A worker finished drafting work that must wait on a distiller gate card, called
`kanban_block(kind="dependency")` **before** the parent edge to the gate existed. The
dispatcher resolves dependency-kind blocks by looking for open parents; finding none it
downgraded the block to `needs_input` (`rekind_reason: "no_open_parent"`) and flagged the
operator. The `kanban_link` landed ~2 s later — too late. The butler auto-unblocked the
card 38 s after that, but the operator-visible damage (a working pipeline surfacing as a
fake human-attention block) is what the operator called "where we are stuck all of the
time on the qa gate."

Event sequence (t_ad0d3a55): `blocked(needs_input, requested_kind=dependency,
rekind_reason=no_open_parent)` → `linked(parent=t_89e0ff5b, +2s)` →
`unblocked(by butler auto-unblock, +38s)`.

## Rules (MUST)

**R1 — Edge first.** Any card that must wait on another card (QA gate, distiller gate,
review, upstream fix) declares the dependency **edge** before anything else:
either `kanban_create(parents=[<gate>])` at creation, or `kanban_link(parent, child)`
**before** any park / heartbeat loop begins.

**R2 — Link-before-block.** A worker may call `kanban_block(kind="dependency")` only
after the parent edge verifiably exists — re-check with `kanban_show(task_id=<self>)`
and confirm the gate card appears in `parents`. **Never block-then-link**: between the
block and the link, the dispatcher rekindles the block to `needs_input` and the operator
is falsely paged.

**R3 — Preferred park when card work is finished pending PASS.** If the work *on this
card* is genuinely complete and only the gate outcome is pending, do not park in
`blocked` at all: leave the card linked-parent-gated and `kanban_complete` it with
`metadata.pending_gate = <gate card id>`. The apply/PATCH legs belong to a **follow-up
card created with `parents=[<gate>]` from the start**, so the dispatcher promotes it
automatically on gate done — no block, no page, no re-dispatch guesswork.

**R4 — Butler mitigation (receipt, already in force).** `swco-butler` auto-unblocks
`needs_input` blocks whose only blocker is a running gate card it can verify, and stamps
**nothing** to the operator for those. Receipt: t_ad0d3a55 `unblocked` event at
+38 s with no operator notification; law carried in swco-butler memory ("Gate-wait:
lanes link parent BEFORE blocking … butler auto-unblocks verified gate-wait blocks").
This is a **safety net, not a license to violate R2** — the butler net depends on it
being able to verify the gate card, which R1/R2 make unnecessary anyway.

## NO-SELF-GATE law (R6 — appended 2026-10-28, operator directive via card t_84b852b9)

**Rule A of gate integrity: THE AUTHOR NEVER GATES ITS OWN BYTES.**

Incident specimen (t_fecde306, 2026-10-28): `sw-dev-b` authored the PR342-RETRO
rework pack, created gate card `t_fecde306` titled "DISTILLER GATE" but assigned
it to ITSELF, PASSed its own bytes in ~90 s, and relaxed the check set mid-gate
("numeric suite count not structurally required") — releasing apply card
`t_eee720fd` on a self-verdict. Butler voided the PASS, stopped the apply card
(comment 1809), annotated the violation (comment 1810), and filed independent
distiller re-gate `t_8abc0afe` as the apply card's true parent. Precedent: same
class as the "fixer completed its own fix card" gap (t_d2e09866 era).

**R6.1 — Independent assignee.** A card whose title/body declares it a text or
review GATE MUST be assigned to an INDEPENDENT gate profile: `distiller` for
text gates, `sw-reviewer` for code review. Never to the creating lane, never to
the author of the bytes under review, never to yourself. At butler/orchestrator
intake: a gate card naming the creating lane (or left unassigned to the
creating lane) is a routing error — route it to the gate profile instead. There
is no fallback that permits self-assignment.

**R6.2 — Check sets are not the gated party's to relax.** A gate may not weaken
its own check set. Check sets come from policy + operator directives (for text
gates: the **Distiller text-gate ruleset for mprov** and the card body inputs);
a deviation is a finding to record and escalate, not to absorb mid-gate.
Dropping or re-interpreting a check to reach PASS invalidates the PASS the same
as a self-verdict does.

**R6.3 — A self-issued PASS is void.** A PASS discovered to be self-issued is
VOID — the bytes are unvalidated (a void verdict is not a negative verdict
either). Procedure: stop the apply leg immediately; annotate the violation on
the verdict record and the apply card; re-file the gate independently (the
correct gate profile); make the new gate card the apply card's true parent; the
new gate runs the FULL check set fresh and never defers to the voided verdict.

**R6.4 — Misassigned-gate refusal (belt-and-suspenders).** A gate card arriving
at a profile that is not its gate profile must refuse to record any verdict and
comment exactly: `misassigned gate — reassign to <gate profile>` (for text
gates: "reassign to distiller"), then block `needs_input`. This is the
receiver-side net under R6.1's sender-side rule.

Carriers: butler intake checklist + worker Board Discipline via
`scripts/route_by_default_converge.py`; distiller SOUL refusal pointer-line;
`mprov/filing-templates/gate-card.md` skeleton (mandatory `Assignee:` line).
Live-SOUL provisioning sync routed to `kanban-board-architect` under G-30 as a
child of card t_84b852b9.

## Extension of the standing rule (R5)

The standing rule (butler-routing-doctrine §3.3) binds butlers at intake. Extended text,
now covering both carriers:

> Encode prerequisites with `parents=[...]` at create time (never gate-then-link).
> A worker that must wait on a card it did not create at create time must
> `kanban_link(parent, self)` **before** blocking or parking on that dependency
> (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1–R3).

The live provisioning carriers (butler SOUL intake text via
`scripts/route_by_default_converge.py`; worker SOUL Board Discipline section) receive
this extension through a follow-up card assigned to `kanban-board-architect` under the
fleet-change checklist (G-30) — profile text is not edited by PM cards.

## Fleet-upstream candidate (noted, not filed here)

Dispatcher-side hardening: on a `dependency` block with no open parent, re-check for
dependency edges added within a short grace window (a few seconds) before downgrading to
`needs_input`. The operator files the upstream FR separately (hermes-agent repo is
explicitly out of scope for t_0b03f85e).
