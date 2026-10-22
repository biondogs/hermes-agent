#!/usr/bin/env python3
"""ARCHIVE-GC-BUTLER-WIRING converge script (t_aabdf078, 2026-10-22).

Replaces the PASSIVE housekeeping clause in the five butler SOULs (until today:
"reply that housekeeping routes to the default orchestrator") with the ACTIVE
ARCHIVE-GC stamp protocol consumed by the nightly GC sweeper
(~/.hermes/scripts/archive_gc.py, cron be9cc3360254 21:30 ET,
log ~/.hermes/kanban/archive-gc.log):

  1. Five butler SOULs -> passive housekeeping bullet replaced with:
       - "card archive/delete" bullet pointing at the new protocol section, and
       - a narrowed passive bullet (board unarchive / import only);
       plus a new section `## Card Housekeeping via ARCHIVE-GC Stamp` inserted
       before `## Your Role` (board-parameterized, marker-guarded).
  2. docs/butler-routing-doctrine-2026-10-22.md ->
       - §3 housekeeping bullet split into stamped-card path vs no-card path,
       - §5 gap-table escalation cell updated for the kanban_archive gap,
       - new "ARCHIVE-GC bridge (LIVE 2026-10-22...)" paragraph after the gap
         table, including the SELF-RETIRING note.

Idempotent: every edit is grep-guarded on a unique marker; re-runs skip.
Safety: pre-mutation backups of every file touched go to
  /local/projects/software-co/backups/archive-gc-butler-wiring-2026-10-22/pre/
(only taken on the FIRST mutation of each file; a present backup = converged run).
No config.yaml, .env, or profile.yaml is modified. No gateway restart is performed.

Usage:  python3 archive_gc_butler_converge.py           # live
        DRY_RUN=1 python3 archive_gc_butler_converge.py # report only
"""
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/arch/.hermes")
PROFILES = HOME / "profiles"
MGMT = Path("/local/projects/software-co")
DOCTRINE = MGMT / "docs" / "butler-routing-doctrine-2026-10-22.md"
BACKUP = MGMT / "backups" / "archive-gc-butler-wiring-2026-10-22" / "pre"

DRY = os.environ.get("DRY_RUN") == "1"

BUTLERS = [
    # (profile, board)
    ("g01-butler", "gargantua01"),
    ("g02-butler", "gargantua02"),
    ("gaudi-butler", "gaudi"),
    ("swco-butler", "software-co"),
    ("sjproto-butler", "skipjack-prototype"),
]

BUTLER_MARKER = "## Card Housekeeping via ARCHIVE-GC Stamp"

PASSIVE_CLAUSE = (
    "- Housekeeping (card archive / delete, board unarchive or import): you have no tool for "
    "these \u2014 Hermes has no kanban_archive tool (archive is CLI-only) and butlers carry no "
    "terminal by design. Acknowledge the request, do NOT attempt it, and reply that housekeeping "
    "routes to the default orchestrator."
)

DOCTRINE_MARKER = "**ARCHIVE-GC bridge (LIVE 2026-10-22, card t_aabdf078):**"

DOCTRINE_SS3_OLD = (
    "- **Housekeeping (archive/delete/unarchive) \u2192** acknowledge, do not attempt, reply that\n"
    "  housekeeping routes to the default orchestrator (see \u00a75 \u2014 this is a tool-layer gap, not a\n"
    "  butler defect; butlers are terminal-less by design and Hermes has no kanban_archive tool)."
)

DOCTRINE_SS3_NEW = (
    "- **Housekeeping with a card to stamp (card archive/delete) \u2192** the butler ACTS in-tool "
    "(since 2026-10-22, t_aabdf078): comments `HOUSEKEEPING: archive \u2014 <reason>` on that exact "
    "card, tells the operator the nightly ARCHIVE-GC sweeper archives it by morning (urgent \u2192 "
    "default orchestrator immediately), and a later `HOUSEKEEPING: cancel` comment on the same card "
    "prevents the sweep.\n"
    "- **Housekeeping with no card to stamp (board unarchive/import) \u2192** acknowledge, do not "
    "attempt, reply that housekeeping routes to the default orchestrator (see \u00a75 \u2014 "
    "tool-layer gap; butlers are terminal-less by design and Hermes has no kanban_archive tool)."
)

DOCTRINE_CELL_OLD = "| housekeeping requests \u2192 default orchestrator |"
DOCTRINE_CELL_NEW = (
    "| card archive/delete \u2192 butler `HOUSEKEEPING: archive` stamp + nightly ARCHIVE-GC sweeper "
    "(bridge until kanban_archive ships); unarchive/import \u2192 default orchestrator |"
)

DOCTRINE_BRIDGE_PARA = (
    DOCTRINE_MARKER + " gap 1 above is now mitigated end-to-end. Nightly sweeper\n"
    "`~/.hermes/scripts/archive_gc.py` (cron `be9cc3360254`, 21:30 ET; log\n"
    "`~/.hermes/kanban/archive-gc.log`) scans every board DB for `HOUSEKEEPING: archive` comments,\n"
    "honors a later `HOUSEKEEPING: cancel` on the same card, accepts stamps ONLY from authors\n"
    "ending `-butler` or equal to `default`, never touches `running` cards, caps at 20 archives per\n"
    "run, and receipts each archive with an `ARCHIVE-GC:` comment before archiving. Butler SOULs now\n"
    "carry the active stamp protocol (marker: `Card Housekeeping via ARCHIVE-GC Stamp`), converged\n"
    "by `scripts/archive_gc_butler_converge.py` (this script, grep-guarded, idempotent;\n"
    "pre-mutation backups in `backups/archive-gc-butler-wiring-2026-10-22/pre/`).\n"
    "**SELF-RETIRING:** the whole bridge \u2014 sweeper cron, script, and the SOUL protocol sections \u2014\n"
    "retires together once upstream ships a real `kanban_archive` tool; the upstream feature request\n"
    "stays recorded (below).\n"
)


def new_bullets() -> str:
    return (
        "- Card archive / delete (a specific card the operator wants gone): do NOT escalate "
        "\u2014 action it yourself with the ARCHIVE-GC stamp protocol in the next section.\n"
        "- Housekeeping with no card to stamp (board unarchive or import): you have no tool for "
        "these \u2014 Hermes has no kanban_archive tool (archive is CLI-only) and butlers carry no "
        "terminal by design. Acknowledge the request, do NOT attempt it, and reply that housekeeping "
        "routes to the default orchestrator."
    )


def stamp_section(board: str) -> str:
    return (
        "## Card Housekeeping via ARCHIVE-GC Stamp (nightly GC sweeper)\n"
        "\n"
        "Hermes still has no `kanban_archive` tool (archive is CLI-only) and you carry no terminal "
        "\u2014 but card archive/delete requests from the operator are now ACTIONABLE in-tool: you "
        "stamp a comment that the nightly ARCHIVE-GC sweeper executes.\n"
        "\n"
        "When the operator asks you to archive or delete a card:\n"
        "1. Comment on that exact card: `HOUSEKEEPING: archive \u2014 <one-line reason from the "
        "operator>` \u2014 e.g. `kanban_comment(board=\"" + board + "\", task_id=..., body=\"HOUSEKEEPING: "
        "archive \u2014 <reason>\")`. Commenting is in-tool; this is the whole action.\n"
        "2. Tell the operator: the nightly ARCHIVE-GC sweeper (cron `archive-gc`, 21:30 ET) will "
        "archive the card by morning. If it is urgent, tell them the default orchestrator can "
        "archive it immediately.\n"
        "3. If the operator changes their mind before the sweep, comment `HOUSEKEEPING: cancel` on "
        "the same card \u2014 a cancel stamp later than the archive stamp prevents the GC for that "
        "card.\n"
        "4. Stamp ONLY cards on `" + board + "` \u2014 your one board, as always. The GC ignores "
        "HOUSEKEEPING stamps from any author that is not a butler or the default profile, and never "
        "touches cards in `running` status.\n"
        "\n"
        "This bridge is SELF-RETIRING: it exists only until upstream Hermes ships a real "
        "`kanban_archive` tool.\n"
        "\n"
    )


def two_pass(msg: str):
    line = "#" * 24
    print(f"\n{line} {msg} {line}", flush=True)


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
    """Apply transform(text)->(new_text, action); returns action string."""
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
        if BUTLER_MARKER in text:
            return text, "skip"
        if PASSIVE_CLAUSE not in text:
            return text, "error: passive housekeeping clause not found"
        if "## Your Role" not in text:
            return text, "error: anchor '## Your Role' not found"
        new = text.replace(PASSIVE_CLAUSE, new_bullets(), 1)
        new = new.replace("\n## Your Role", "\n" + stamp_section(board) + "## Your Role", 1)
        return new, "edit"
    return t


def doctrine_transform(text: str):
    if DOCTRINE_MARKER in text:
        return text, "skip"
    missing = [s for s in (DOCTRINE_SS3_OLD, DOCTRINE_CELL_OLD, "**Recorded for operator decision") if s not in text]
    if missing:
        return text, "error: missing expected substring(s): " + " | ".join(repr(m[:60]) for m in missing)
    new = text.replace(DOCTRINE_SS3_OLD, DOCTRINE_SS3_NEW, 1)
    new = new.replace(DOCTRINE_CELL_OLD, DOCTRINE_CELL_NEW, 1)
    anchor = "**Recorded for operator decision"
    idx = new.index(anchor)
    new = new[:idx] + DOCTRINE_BRIDGE_PARA + "\n" + new[idx:]
    # collapse any triple newline introduced before the anchor
    new = new.replace("\n\n\n\n", "\n\n")
    return new, "edit"


def main():
    if DRY:
        print("DRY RUN — no files will be modified.")
    total: dict = {}
    BACKUP.mkdir(parents=True, exist_ok=True)

    two_pass("1. Butler SOULs: passive clause -> ACTIVE ARCHIVE-GC stamp protocol")
    for prof, board in BUTLERS:
        soul = PROFILES / prof / "SOUL.md"
        if not soul.exists():
            record(total, "MISSING", prof, "no SOUL.md")
            continue
        act = edit_file(soul, butler_transform(board))
        if act.startswith("error"):
            record(total, "ERROR", prof, act)
        else:
            record(total, act.split(" ")[0], prof, act)

    two_pass("2. Doctrine doc: housekeeping section describes the GC path")
    if not DOCTRINE.exists():
        record(total, "MISSING", str(DOCTRINE), "doc absent")
    else:
        act = edit_file(DOCTRINE, doctrine_transform)
        if act.startswith("error"):
            record(total, "ERROR", "doctrine", act)
        else:
            record(total, act.split(" ")[0], "doctrine", act)

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
