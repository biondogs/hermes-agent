#!/usr/bin/env python3
"""NO-SELF-GATE carrier 3 (t_1a66c496): distiller SOUL ## Process step-1
R6.4 refusal pointer — idempotent single-profile edit.

Doc of record: software-co docs/gate-wait-pattern-2026-10-28.md §R6.4
(commit 31d5b4b, operator directive via t_84b852b9). NOT carried by the
converge script (single-profile edit by design); this script is the
receipt-recorded mechanism. Apply ONLY under flock ~/.hermes/locks/
profile-config.lock (fleet-change step 6).

Usage: python3 nsg_distiller_patch.py /home/arch/.hermes/profiles/distiller/SOUL.md
       (path argument optional, defaults to the live distiller SOUL)
"""
import sys
from pathlib import Path

DEFAULT_SOUL = Path("/home/arch/.hermes/profiles/distiller/SOUL.md")
ANCHOR = ("1. `kanban_show()` the gate card; read its parent card (the work) and\n"
          "   the artifact to be distilled.")
GUARD = "NO-SELF-GATE precondition (R6.4)"
INSERT = ("\n   NO-SELF-GATE precondition (R6.4): if the gate card's assignee is not\n"
          "   `distiller`, record NO verdict — comment exactly \"misassigned gate —\n"
          "   reassign to distiller\" and block `needs_input` before any checklist run.")


def patch_text(text: str):
    """Idempotent: returns (new_text, action) with action in edit|skip|error-*."""
    if GUARD in text:
        return text, "skip"
    if ANCHOR not in text:
        return text, "error-anchor-missing"
    if text.count(ANCHOR) != 1:
        return text, "error-anchor-not-unique"
    return text.replace(ANCHOR, ANCHOR + INSERT, 1), "edit"


def main():
    soul = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOUL
    text = soul.read_text()
    new, action = patch_text(text)
    if action == "edit":
        soul.write_text(new)
    print(f"{soul}: {action}")
    return 0 if action in ("edit", "skip") else 1


if __name__ == "__main__":
    sys.exit(main())
