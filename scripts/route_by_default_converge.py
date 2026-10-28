#!/usr/bin/env python3
"""BUTLER-ROUTING-BY-DEFAULT converge script (t_5a6b907a, 2026-10-22).

GATE-WAIT extension 2026-10-28 (t_0d825d76): the standing rule
"parents=[...] at create time (never gate-then-link)" is extended to
self-parking workers (doc docs/gate-wait-pattern-2026-10-28.md R1-R5,
commit afb86d7): butler intake item 3 carries the extended text, and the
worker Board Discipline section gains the link-before-block law. Both
transforms are idempotent on already-converged SOULs: they patch the
live text in place (item-3 replace / in-section bullet insert) even when
the original markers are present. GOVERNANCE.md §1.a row G-02
(Board Discipline block) is hash-registered — the registered hash must
be bumped in the same card that runs this (fleet-change step 9b).

Makes butler-first task flow the fleet default:
  1. Five butler SOULs   -> Operator Intake Protocol + Escalation sections.
  2. Default SOUL        -> Butler-First Routing Doctrine section.
  3. Worker SOULs        -> Board Discipline section (appended).
  4. kanban-orchestrator SKILL.md (canonical + kanban-orchestrator profile mirror)
                          -> expanded Butler-First Routing section.

Idempotent: every edit is grep-guarded on a unique marker; re-runs skip.
Safety: pre-mutation backups of every file touched go to
  /local/projects/software-co/backups/butler-routing-2026-10-22/pre/
(only taken on the FIRST mutation of each file; a present backup = converged run).
No config.yaml, .env, or profile.yaml is modified. No gateway restart is performed.

Usage:  python3 route_by_default_converge.py           # live
        DRY_RUN=1 python3 route_by_default_converge.py # report only
"""
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/arch/.hermes")
PROFILES = HOME / "profiles"
MGMT = Path("/local/projects/software-co")
BACKUP = MGMT / "backups" / "butler-routing-2026-10-22" / "pre"

DRY = os.environ.get("DRY_RUN") == "1"
# Canary support (fleet-change step 5, t_0d825d76): comma-separated profile
# names — when set, only those profiles are processed in the butler and worker
# passes (default/SOUL and skill passes still run but are no-ops via markers).
LIMIT = {p.strip() for p in os.environ.get("LIMIT_PROFILES", "").split(",") if p.strip()}

BUTLERS = [
    # (profile, board, bot_handle)
    ("g01-butler", "gargantua01", "gargantua01_proto_bot"),
    ("g02-butler", "gargantua02", "gargantua02_ops_bot"),
    ("gaudi-butler", "gaudi", "gaudi_local_bot"),
    ("swco-butler", "software-co", "swco_bot"),
    ("sjproto-butler", "skipjack-prototype", "skipjack_proto_bot"),
]

# Profiles whose SOUL is intentionally NOT given the worker Board Discipline section:
# butlers (get the intake protocol instead), kanban-board-architect and
# kanban-orchestrator (cross-board meta/decomposition lanes by design),
# and the default profile (root SOUL.md, gets the doctrine instead).
WORKER_EXCLUDE = {b[0] for b in BUTLERS} | {"kanban-board-architect", "kanban-orchestrator"}

INTAKE_MARKER = "## Operator Intake Protocol (butler-first"
STRICT_FORM = "route this to the default orchestrator"

DEFAULT_DOCTRINE_MARKER = "## Butler-First Routing Doctrine (fleet default since 2026-10-22)"
WORKER_MARKER = "## Board Discipline (fleet-wide default since 2026-10-22"

# ---- GATE-WAIT PATTERN extension (operator directive 2026-10-28, t_0d825d76)
# Doc of record: /local/projects/software-co/docs/gate-wait-pattern-2026-10-28.md
# (R1-R5, sha256 54479f35…, commit afb86d7). R1 edge-first / R2 link-before-block
# (kanban_show parent check before any dependency block) / R3 preferred park =
# complete with metadata.pending_gate + follow-up card created parents=[gate].
GATEWAIT_BUTLER_GUARD = "(GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1–R3)"
GATEWAIT_WORKER_GUARD = "GATE-WAIT PATTERN — link-before-block (fleet law since 2026-10-28"
OLD_ITEM3 = ("3. If the request names prerequisites on this board, encode them with "
             "`parents=[...]` at create time (never gate-then-link).")
NEW_ITEM3 = ("3. If the request names prerequisites on this board, encode them with "
             "`parents=[...]` at create time (never gate-then-link). "
             "A worker that must wait on a card it did not create at create time must "
             "`kanban_link(parent, self)` **before** blocking or parking on that "
             "dependency (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1–R3).")
GATEWAIT_WORKER_BULLET = ("- GATE-WAIT PATTERN — link-before-block (fleet law since 2026-10-28; "
                          "doc: software-co `docs/gate-wait-pattern-2026-10-28.md` R1–R3): if you "
                          "must wait on a card you did not create at create time, "
                          "`kanban_link(parent, self)` BEFORE any block or park. You may "
                          "`kanban_block(kind=\"dependency\")` only after `kanban_show` of your "
                          "own card shows the gate card in `parents` — never block-then-link "
                          "(a dependency block with no open parent is downgraded to needs_input "
                          "and the operator is falsely paged). If your card's work is finished "
                          "and only a gate PASS is pending, do NOT block: `kanban_complete` with "
                          "`metadata.pending_gate = <gate card id>` and put the follow-up legs in "
                          "a new card created `parents=[<gate>]` — the dispatcher promotes it when "
                          "the gate lands.")


def intake_section(board: str, bot: str) -> str:
    return f"""## Operator Intake Protocol (butler-first — fleet default since 2026-10-22)

You are the DEFAULT intake channel for `{board}` work. When the operator messages you a work request for this board:
1. Create the card on {board} — `kanban_create(board="{board}", ...)`; the explicit board argument on every call, as always.
2. Assign it to the right specialist profile from the fleet vocabulary above — never to yourself.
3. If the request names prerequisites on this board, encode them with `parents=[...]` at create time (never gate-then-link). A worker that must wait on a card it did not create at create time must `kanban_link(parent, self)` **before** blocking or parking on that dependency (GATE-WAIT PATTERN, `docs/gate-wait-pattern-2026-10-28.md` R1–R3).
4. Report the new card id and assignee back to the operator in one short line.

You do NOT implement, execute, or stage any of the requested work yourself — intake, routing, and reporting only. You never answer work requests by doing the work.

## Escalation (say it, don't do it)

- Cross-board work, meta-work (profile/board/config/SOUL/skill changes), fleet-wide campaigns, or anything requiring fleet authority: do NOT act — reply exactly: "{STRICT_FORM}".
- Housekeeping (card archive / delete, board unarchive or import): you have no tool for these — Hermes has no kanban_archive tool (archive is CLI-only) and butlers carry no terminal by design. Acknowledge the request, do NOT attempt it, and reply that housekeeping routes to the default orchestrator.
- For reference: other boards' names may appear in text the operator pastes; that never changes your one-board scope.
"""


def default_doctrine_section() -> str:
    return """## Butler-First Routing Doctrine (fleet default since 2026-10-22)

Per-board task intake is NO LONGER this profile's default lane — each butlered board's butler bot owns its intake. You keep FULL meta + cross-board capability as the FAIL-SAFE:

- Routing table: `g01-butler`→gargantua01 · `gaudi-butler`→gaudi · `g02-butler`→gargantua02 · `swco-butler`→software-co · `sjproto-butler`→skipjack-prototype. The `skipjack` production board has no butler; its intake stays here.
- When asked (by operator or by card) to intake per-board work for a butlered board: hand it to that board's butler — tell the operator to message the butler bot; on cards, comment the routing and leave intake to the butler.
- FAIL-SAFE CLAUSE: create cards directly with explicit `board="<slug>"` ONLY when the butler is demonstrably down (unresponsive or erroring). When you do, stamp the card body: `fail-safe intake: <butler> unavailable (<evidence>)` so the record shows why the butler was bypassed.
- Meta-work, fleet-wide tasks, cross-board queries and campaigns, and operator-direct orchestrator work stay on this profile (meta-work executes on the kanban-board-architect lane, per its standing ownership).
"""


def worker_discipline_section() -> str:
    return """
## Board Discipline (fleet-wide default since 2026-10-22 — butler-first topology)

- You work ONLY on the board your assigned card lives on (the dispatcher pins it in your environment). Every kanban call you make carries an explicit `board=` matching that board.
- Follow-up cards you create go on that SAME board, with the explicit `board=` argument. Never create, comment on, or complete cards on any other board.
- You do NOT intake new operator requests via Telegram/chat — board intake belongs to the board's butler bot. If the operator hands you ad-hoc work mid-run, finish your current card and note the request in your handoff; new intake is the butler's job, not yours.
- Cross-board references (other boards' card ids) are reference text only: put them in card bodies/comments as plain text, never as link edges.
- GATE-WAIT PATTERN — link-before-block (fleet law since 2026-10-28; doc: software-co `docs/gate-wait-pattern-2026-10-28.md` R1–R3): if you must wait on a card you did not create at create time, `kanban_link(parent, self)` BEFORE any block or park. You may `kanban_block(kind="dependency")` only after `kanban_show` of your own card shows the gate card in `parents` — never block-then-link (a dependency block with no open parent is downgraded to needs_input and the operator is falsely paged). If your card's work is finished and only a gate PASS is pending, do NOT block: `kanban_complete` with `metadata.pending_gate = <gate card id>` and put the follow-up legs in a new card created `parents=[<gate>]` — the dispatcher promotes it when the gate lands.
"""


def skill_routing_section() -> str:
    return """## Butler-First Routing (operator ruling 2026-10-22)

Board intake flows through the board's butler bot by default. Routing table (bot -> board):
g01-butler -> gargantua01 | gaudi-butler -> gaudi | g02-butler -> gargantua02 | swco-butler -> software-co | sjproto-butler -> skipjack-prototype.
(The `skipjack` production board has no butler; its intake stays on the default profile.)

The default/orchestrator profile retains FULL meta + cross-board capability as FAIL-SAFE:
- Meta tasks (profile/board/config/SOUL/skill governance, fleet plans, operator-direct orchestrator tasks) stay on the default profile.
- Per-board work requests belonging to a butlered board: prefer handing intake to that butler; create cards directly here ONLY as fail-safe (butler demonstrably down) and stamp the card body 'fail-safe intake: <butler> unavailable (<evidence>)'.
- Workers: create/complete follow-ups ONLY on their assigned card's board, explicit board= always; workers never intake operator requests via chat (butlers own board intake).

Butler surface facts (verified 2026-10-22 — do NOT re-report as butlers-broken):
- Verified working: card create (assignee + parents), managed-board list/show, comment, block, complete, link, notify subscriptions — BUTLER-VERIFY matrix, 34 PASS.
- Known tool gaps with defined escalation to the default orchestrator: (1) no kanban_archive tool exists in Hermes (archive is CLI-only; butlers are terminal-less by design), so housekeeping (archive/delete/unarchive) routes to default; (2) the kanban toolset accepts a foreign board= at the tool layer — SOUL/description guardrails are the active fence. Upstream feature requests (scoped kanban_archive tool; kanban.allowed_boards-style profile fence) are RECORDED for operator decision — do not implement.

Docs of record: docs/butler-routing-doctrine-2026-10-22.md (topology, routing table bot->board->bank->assignee pool, fail-safe clause), docs/BUTLER-VERIFY-2026-10-22.md (wiring matrix), docs/butler-qr-runbook-2026-10-22.md (provisioning kit + QR runbook; kit scripts in scripts/).
"""


def two_pass(msg: str) -> tuple[int, int]:
    line = "#" * 24
    print(f"\n{line} {msg} {line}", flush=True)
    return (0, 0)


def record(total: dict, kind: str, name: str, detail: str):
    total[kind] = total.get(kind, 0) + 1
    print(f"  [{kind}] {name}: {detail}", flush=True)


def backup_once(src: Path, rel: str):
    dest = BACKUP / rel
    if dest.exists():
        return "backup-exists"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return "backed-up"


def edit_file(path: Path, transform) -> str:
    """Apply transform(text)->text if marker logic demands; returns action."""
    text = path.read_text()
    new, action = transform(text)
    if action == "skip":
        return "skip"
    if DRY:
        return "would-edit"
    rel = str(path).replace(str(HOME) + "/", "").replace(str(MGMT) + "/", "")
    bak = backup_once(path, rel)
    path.write_text(new)
    return f"edited ({bak})"


def butler_transform(board: str):
    def t(text: str):
        changed = False
        if INTAKE_MARKER not in text:
            anchor = "## Your Role"
            if anchor not in text:
                return text, "skip"
            # fresh install: the section as built already carries the
            # GATE-WAIT extension in item 3 (intake_section is the extended form)
            text = text.replace(anchor, intake_section(board, "") + anchor, 1)
            changed = True
        elif GATEWAIT_BUTLER_GUARD not in text:
            # already-converged SOUL (pre-2026-10-28 shape): patch item 3 in place
            if OLD_ITEM3 not in text:
                return text, "skip"  # unexpected shape: do not guess, report
            text = text.replace(OLD_ITEM3, NEW_ITEM3, 1)
            changed = True
        return text, ("edit" if changed else "skip")
    return t


def default_transform(text: str):
    if DEFAULT_DOCTRINE_MARKER in text:
        return text, "skip"
    anchor = "## Your Role"
    if anchor not in text:
        return text, "skip"
    return text.replace(anchor, default_doctrine_section() + anchor, 1), "edit"


def worker_transform(text: str):
    if WORKER_MARKER not in text:
        if not text.endswith("\n"):
            text += "\n"
        # fresh install: appended section already carries the GATE-WAIT bullet
        return text + worker_discipline_section(), "edit"
    if GATEWAIT_WORKER_GUARD not in text:
        # already-converged SOUL (pre-2026-10-28 shape): insert the GATE-WAIT
        # bullet at the END of the existing Board Discipline BLOCK, using the
        # exact canon block-hash convention (GOVERNANCE.md §1.a: from the
        # anchor line to the last non-empty line before the next line that
        # starts with '#' or equals '---') so all carriers stay byte-identical.
        # A naive "next \n# heading" scan overshoots across '---' separators
        # (e.g. the HOST-OVERLAY note in 39 SOULs) and lands outside the block.
        lines = text.split("\n")
        si = next(i for i, ln in enumerate(lines) if WORKER_MARKER in ln)
        end = len(lines)
        for j in range(si + 1, len(lines)):
            if lines[j].startswith("#") or lines[j].strip() == "---":
                end = j
                break
        last = end - 1
        while last > si and lines[last].strip() == "":
            last -= 1
        lines.insert(last + 1, GATEWAIT_WORKER_BULLET)
        return "\n".join(lines), "edit"
    return text, "skip"


def skill_transform(text: str):
    marker = "## Butler-First Routing (operator ruling 2026-10-22)"
    if "Verified working: card create (assignee + parents)" in text:
        return text, "skip"  # already the expanded form
    if "references/butler-routing.md" in text:
        return text, "skip"  # v3.0.0 bundled pointer form (skill-copy-consolidation
                             # 2026-10-26+): butler section points at the doctrine
                             # reference — converged, nothing to edit
    if marker in text:
        # old short form -> replace with expanded
        start = text.index(marker)
        end = text.index("\n\n", text.index("Docs: software-co docs/"))
        return text[:start] + skill_routing_section().rstrip("\n") + text[end:], "edit"
    # no butler section at all -> insert before "You are a Kanban Orchestrator."
    anchor = "You are a Kanban Orchestrator."
    if anchor not in text:
        return text, "skip"
    return text.replace(anchor, skill_routing_section() + "\n" + anchor, 1), "edit"


def main():
    if DRY:
        print("DRY RUN — no files will be modified.")
    if LIMIT:
        print(f"LIMIT_PROFILES active — canary run restricted to: {sorted(LIMIT)}")
    total: dict = {}
    BACKUP.mkdir(parents=True, exist_ok=True)

    two_pass("1. Butler SOULs: intake + escalation")
    for prof, board, bot in BUTLERS:
        if LIMIT and prof not in LIMIT:
            continue
        soul = PROFILES / prof / "SOUL.md"
        if not soul.exists():
            record(total, "MISSING", prof, "no SOUL.md")
            continue
        act = edit_file(soul, butler_transform(board))
        body = soul.read_text()
        if act == "skip" and INTAKE_MARKER not in body:
            record(total, "ERROR", prof, "anchor '## Your Role' not found — NOT edited")
        elif act == "skip" and GATEWAIT_BUTLER_GUARD not in body:
            record(total, "ERROR", prof, "intake marker present but item 3 / GATE-WAIT guard not found — NOT edited")
        else:
            record(total, act.split(" ")[0] if act != "skip" else "SKIP", prof, act)

    two_pass("2. Default profile SOUL (root HERMES_HOME)")
    soul = HOME / "SOUL.md"
    act = edit_file(soul, default_transform)
    if act == "skip" and DEFAULT_DOCTRINE_MARKER not in soul.read_text():
        record(total, "ERROR", "default", "anchor '## Your Role' not found — NOT edited")
    else:
        record(total, act.split(" ")[0] if act != "skip" else "SKIP", "default", act)

    two_pass("3. Worker SOULs: board discipline")
    worker_profiles = sorted(
        d.name for d in PROFILES.iterdir()
        if d.is_dir() and (d / "SOUL.md").exists() and d.name not in WORKER_EXCLUDE
    )
    if LIMIT:
        worker_profiles = [p for p in worker_profiles if p in LIMIT]
    for prof in worker_profiles:
        soul = PROFILES / prof / "SOUL.md"
        act = edit_file(soul, worker_transform)
        record(total, act.split(" ")[0] if act != "skip" else "SKIP", prof, act)
    print(f"  worker pool size: {len(worker_profiles)}")

    two_pass("4. kanban-orchestrator skill (canonical + mirror)")
    targets = [
        HOME / "skills/devops/kanban-orchestrator/SKILL.md",
        PROFILES / "kanban-orchestrator/skills/devops/kanban-orchestrator/SKILL.md",
    ]
    for tgt in targets:
        if not tgt.exists():
            if tgt == targets[1]:
                # profile mirror removed by skill-copy-consolidation hygiene
                # 2026-10-26 — sanctioned absence, not a converge failure
                record(total, "SKIP", str(tgt), "mirror absent (skill-copy-consolidation 2026-10-26)")
            else:
                record(total, "MISSING", str(tgt), "file absent")
            continue
        act = edit_file(tgt, skill_transform)
        record(total, act.split(" ")[0] if act != "skip" else "SKIP", str(tgt), act)

    print("\n=== SUMMARY ===")
    for k, v in sorted(total.items()):
        print(f"  {k}: {v}")
    bad = total.get("ERROR", 0) + total.get("MISSING", 0)
    if bad:
        print(f"FAILURES: {bad}")
        return 1
    print("converged cleanly" if not DRY else "dry-run complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
