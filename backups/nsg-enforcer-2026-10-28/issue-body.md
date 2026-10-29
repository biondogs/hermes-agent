# Feature request: kanban gate-task integrity — refuse a review/gate PASS issued by the author of the gated work

## Summary

We use kanban task graphs where one task acts as a **gate** (review / QA / text
gate) for work done in other tasks, with downstream "apply" tasks waiting on
the gate via `parents=[...]`. This works well, but nothing in the kernel
enforces **reviewer independence**: the author of the gated artifacts can
assign the gate task to themselves (or their own profile) and complete it,
releasing the downstream tasks on a self-verdict.

We hit exactly this failure in production with an agent fleet: a worker
authored a rework pack, created its gate task, assigned the gate to **itself**,
issued `VERDICT: PASS` in ~90 seconds (relaxing the checklist mid-gate), and
the parent-completion logic dutifully released the apply task. A human-side
convention caught it — only because someone happened to be watching.

## What exists today

- `task_links` / `parents` structure **ordering**, not **independence**: a
  gate task completing is indistinguishable from any other parent completing.
- Profiles are the natural independence boundary (an agent's assignee is
  recorded, and completed runs record which profile ran them), but the kernel
  never compares them.

## Request

An opt-in integrity rule for tasks that declare themselves gates, enforced by
the kernel atomically at claim/complete time — not advisory:

1. **Declaration.** A task declares itself a gate, e.g. via metadata:
   `{"gate": {"type": "review"|"text"|"qa", "gated_work": ["<task ids>"]}}`
   (or simply: the gated work is the task's existing parents).
2. **Assignment check.** `kanban reassign`/task creation refuses to assign a
   gate task to a profile that authored the gated work — where "author" means
   the profile recorded as `created_by` of the gated work task **or** the
   profile of any completed run of that task. Refusal message should be
   actionable, e.g. `misassigned gate — reassign to an independent profile`.
3. **Completion check.** `kanban complete` refuses to complete a gate task
   whose current assignee (the claim holder) is an author of the gated work.
   A gate PASS by the author is refused outright — the gate task stays open
   and must be reassigned to an independent profile.
4. **Void path (secondary).** If a gate is discovered to have been self-PASSed
   despite the above (e.g. authorship changed after the fact), an API to void
   the verdict and re-gate independently would let automation recover without
   hand-editing history.

## Why in-kernel

Detection outside the kernel can only be **after the fact**: our fleet runs a
watchdog that scans board DBs every minute and mechanically voids self-PASSed
gates (stop the apply legs, re-file the gate to an independent profile,
reparent the legs). That is a workable net but has a window (one tick), and it
must reconstruct "authorship" from run records. The kernel has both facts at
hand at claim time and can refuse **atomically, before any verdict is
recorded**.

## Alternatives considered

- Convention / prompt-level rules for agents ("never gate your own bytes"):
  advisory only; a misrouted or context-confused agent violates it silently.
- External watchdogs (what we do today): works, but after-the-fact and
  per-deployment rather than a product property.

## Related issues

This is the same integrity class as several open items, approached from the
task-graph side — maintainers may reasonably fold it into any of them:

- #135749 (independent card-level acceptance gates): broader and adjacent —
  the gate lives **on the gated card** as a card-held contract. What is
  described here is the complementary shape used by pipeline-heavy fleets: the
  gate is a **separate parent task** whose completion releases children, so the
  refusal point is the gate task's own assignment/completion, not the gated
  card's terminal transition.
- #97910 (request_review without reviewer keeps the implementer as assignee,
  author reviews own work) and #95141 (review dispatch self-loops with no
  distinct reviewer): the same author-must-not-review invariant surfacing in
  the review column. A generalized authorship check (created_by + completed-run
  profile comparison at assign/claim/complete time) would fix those at the
  root rather than per-flow.
- #138403 (auto-decomposer lacks an approval-gate concept): decomposition-level
  variant.

If maintaining one issue is preferred, the kernel invariant worth capturing
from this report independently of the schema bikeshed is: **`complete` and
`reassign` must compare the acting profile against the authorship of the gated
work whenever a gate relation exists, and refuse on collision.**

## Additional context

A related-but-separate hazard is a gate **weakening its own check set** to
reach PASS; that has no structural representation today, so it is out of scope
for this request — but a `gate` metadata blob would be a natural place to pin
check-set identity later.
