# GATE-WAIT PATTERN — link-before-block ordering rule (NORMATIVE)

- Status: **in force** on board `software-co` (operator directive 2026-10-28; card t_0b03f85e).
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
