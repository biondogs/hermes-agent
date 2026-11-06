"""R6(b) prompt-diet regression (t_3f302aea, 2026-10-25).

KANBAN_GUIDANCE was tightened from ~6.6KB to ~4.1KB rendered. This test pins
two things:

1. **Budget**: the kanban worker protocol must stay under BUDGET_BYTES so the
   boilerplate cannot silently regrow.
2. **Guarantees**: every operative rule the orchestrator signed off on
   (comment on t_3f302aea, 2026-10-25 GO) survives the tightening — and, from
   2026-10-26, the G-29 long-job detach rule (operator ruling; t_4628c4aa):
   hjob launcher, forbidden launch modes, re-attach contract — orient,
   workspace, hourly heartbeat duty + stale-reclaim stakes, block-not-guess +
   no clarify, the restored child-inspect clause, complete-releases-children,
   review model, follow-up-as-child-card, hotspot flagging, and the board
   discipline list (kanban_* tools only, no completing unfinished work, real
   assignees / silent drop, created_cards integrity, artifacts declaration,
   attachments, worktree recipe, delegate_task scope, orchestrator decision
   ownership).

Red on the pre-diet base: the budget assertion and the compacted-structure
markers ("## Board discipline", "only board surface", "inspect them with")
all fail against the verbose 6.6KB text.
"""
from agent.prompt_builder import KANBAN_GUIDANCE

BUDGET_BYTES = 4700  # 4200 (R6 diet) + G-29 long-job detach rule (2026-10-26, operator-declared; t_4628c4aa)

# (marker, why it must survive)
GUARANTEES = [
    # orient + workspace
    ("kanban_show()", "orient step"),
    ("$HERMES_KANBAN_WORKSPACE", "workspace discipline"),
    # heartbeat: hourly duty + stale-reclaim stakes
    ("kanban_heartbeat(note=...)", "heartbeat call shape"),
    (">1 hour", "hourly heartbeat duty trigger"),
    ("no heartbeat in the last hour", "stale-reclaim stakes"),
    # block, never guess, never clarify
    ("kanban_block(reason=", "block call shape"),
    ("Do NOT call `clarify`", "headless clarify stall"),
    # restored orchestrator clause (GO change #1, 2026-10-25)
    ("inspect them with `kanban_show(task_id=...)` before "
     "choosing the terminal action", "child-inspect before terminal action"),
    # structured handoff + complete-releases-children + review model
    ("(`summary`, `metadata`)", "structured handoff on transition"),
    ("never put secrets, tokens, or raw PII", "durable-field hygiene"),
    ("completion is what releases it", "complete releases gated children"),
    ("never sticky-block the parent for review", "no sticky review block"),
    ("kanban_request_review(summary=..., metadata=..., reviewer=<optional-profile>)",
     "review request shape"),
    ("kanban_request_changes", "rework path"),
    ("unblock-loop detection", "review is not a block"),
    # follow-up work -> child card
    ("parents=[your-task-id]", "child-card dependency shape"),
    ("never assign follow-ups to yourself", "no self-assign"),
    # hotspot flagging
    ("hotspot: <path>", "collision hotspot flag"),
    # board discipline
    ("never `hermes kanban <verb>`", "kanban_* tools only"),
    ("Never complete a task you didn't actually finish", "no fake completion"),
    ("SILENTLY drops unknown assignees", "real-profile assignee rule"),
    ("`parents=[...]`, never prose", "dependencies as parents"),
    ("phantom ids are rejected", "created_cards integrity"),
    ("artifacts=[<absolute paths>]", "deliverable declaration"),
    ("25 MB cap", "attachment rules"),
    ("git worktree add", "worktree workspace recipe"),
    ("never board handoffs", "delegate_task scope"),
    # G-29 long-job detach rule (2026-10-26, operator ruling; t_4628c4aa)
    ("GOVERNANCE G-29", "long-job rule name"),
    ("hjob start", "long-job launcher command"),
    ("NEVER a worker background process or bare tmux", "forbidden launch modes"),
    ("re-attach, don't relaunch", "respawn re-attach contract"),
    # orchestrator mode decision ownership
    ("Settle every design decision", "decisions before fan-out"),
    ("into BOTH card bodies", "decisions into both card bodies"),
    # compacted structure markers (red on the pre-diet base)
    ("## Board discipline", "merged discipline section"),
    ("they are your only board surface", "compressed header"),
]


def test_kanban_guidance_budget():
    n = len(KANBAN_GUIDANCE.encode("utf-8"))
    assert n <= BUDGET_BYTES, (
        f"KANBAN_GUIDANCE grew to {n} bytes (budget {BUDGET_BYTES}) — "
        "boilerplate is creeping back"
    )


def test_kanban_guidance_nonempty_and_round():
    assert KANBAN_GUIDANCE.strip(), "guidance must not be empty"
    assert KANBAN_GUIDANCE.startswith("# Kanban task execution protocol"), (
        "protocol header lost"
    )


def test_kanban_guidance_guarantees():
    missing = [
        why for marker, why in GUARANTEES
        if marker.encode("utf-8") not in KANBAN_GUIDANCE.encode("utf-8")
    ]
    assert not missing, f"protocol guarantees lost in prompt diet: {missing}"
