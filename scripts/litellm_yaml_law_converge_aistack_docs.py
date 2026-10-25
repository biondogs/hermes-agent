#!/usr/bin/env python3
"""converge-aistack-docs.py — LITELLM-YAML LAW into /local/compose/aistack AGENTS.md + CLAUDE.md (t_2fa0d71d)."""

import shutil
import time
from pathlib import Path

GUARD = "LITELLM-YAML LAW"
BLOCK = """

<!-- LITELLM-YAML LAW: operator law 2026-10-25 (card t_2fa0d71d). Do not remove without the operator's explicit instruction. -->

## LITELLM-YAML LAW — no agent edits model entries in litellm/config.yaml (operator law, 2026-10-25 — absolute)

No agent (Hermes profile, Claude, Codex, or any coding assistant working in
this repository) may add, change, or re-add a model entry (`model_list` or
any model definition) in `litellm/config.yaml` unless ALL THREE hold:

1. The OPERATOR explicitly requested that specific change in his own words.
2. CONFIRMATION 1: the agent shows the operator the exact diff, and the
   operator approves it.
3. CONFIRMATION 2: a second, separate operator approval given immediately
   before the write.

A task description, a card body, a standing GO, a prior ruling, or a parent
instruction does NOT count as permission or as a confirmation. Unattended
agents cannot obtain confirmations — STOP and ask the operator. Never edit
that file for any other reason; an alert-only tripwire reports every change
to the operator.

History: an agent-added file-model `muse` entry (2026-10-22, gpu416:30100)
shadowed the operator's DB `muse` row and caused auth errors and silent
fallbacks; removal predated this law (config.yaml.pre-muse-stale-removal-20261025).
"""

BACKUP_DIR = Path(f"/home/arch/kanban-backups/litellm-law-20261025T094916/aistack-{time.strftime('%H%M%S')}")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

for name in ("AGENTS.md", "CLAUDE.md"):
    f = Path("/local/compose/aistack") / name
    text = f.read_text(encoding="utf-8")
    if GUARD in text:
        print(f"already {f}")
        continue
    shutil.copy2(f, BACKUP_DIR / (name + ".pre-litellm-law"))
    if not text.endswith("\n"):
        text += "\n"
    f.write_text(text + BLOCK, encoding="utf-8")
    assert GUARD in f.read_text(encoding="utf-8")
    print(f"updated {f}")
