#!/usr/bin/env python3
"""converge-skills.py — LITELLM-YAML LAW propagation into skills (t_2fa0d71d).

Idempotent, grep-guarded. Edits master skills + live profile copies.
Backups: /home/arch/kanban-backups/litellm-law-20261025T094916/skills-<ts>/.
"""

import shutil
import sys
import time
from pathlib import Path

GUARD = "LITELLM-YAML LAW"
BACKUP_DIR = Path(
    f"/home/arch/kanban-backups/litellm-law-20261025T094916/skills-{time.strftime('%H%M%S')}"
)
SK = Path("/home/arch/.hermes/skills")
PR = Path("/home/arch/.hermes/profiles")

LAW_FULL = """## LITELLM-YAML LAW — LiteLLM config.yaml model entries are triple-gated (operator law 2026-10-25)

No agent may add, change, or re-add a model entry (`model_list` or any model
definition) in `/local/compose/aistack/litellm/config.yaml` unless ALL THREE
hold: (1) the OPERATOR explicitly requested that specific change in his own
words; (2) CONFIRMATION 1 — the agent shows the operator the exact diff and
the operator approves it; (3) CONFIRMATION 2 — a second, separate operator
approval given immediately before the write. A kanban card body, a standing
GO, a prior ruling, or a parent card does NOT count as permission or as a
confirmation. Workers are headless and cannot obtain confirmations:
`kanban_block(kind="needs_input")` and STOP. Confirmations are collected only
via operator-facing chat (a clarify answer or a direct reply). Never edit
that file otherwise; an alert-only tripwire reports every change to the
operator.

History: a file-model `muse` entry added by an agent on 2026-10-22 shadowed
the operator's DB `muse` row and caused auth errors and silent fallbacks.
"""

ORCH_LINE = (
    "**LiteLLM config.yaml model entries (LITELLM-YAML LAW, 2026-10-25):** "
    "never route or accept a task that adds, changes, or re-adds a model entry in "
    "`/local/compose/aistack/litellm/config.yaml`. Triple gate: the operator's "
    "explicit request in his own words + approval of the shown exact diff + a "
    "second, separate approval immediately before the write. A card body, "
    "standing GO, prior ruling, or parent card NEVER counts. Workers are "
    "headless and cannot collect confirmations — correct disposition is "
    '`kanban_block(kind="needs_input")` on the card, never an implement child. '
    "Law text: references/operator-gate-law.md; routing pitfall: references/pitfalls-casebook.md."
)

CASEBOOK = """## Pitfall: model-entry edits to the LiteLLM config.yaml — a card can never carry the permission (LITELLM-YAML LAW 2026-10-25)
Never create, route, or accept a task that adds, changes, or re-adds a model entry in `/local/compose/aistack/litellm/config.yaml`. The write is triple-gated (explicit operator request + shown-diff approval + separate immediate pre-write approval), and NONE of the three can be supplied by a card body, a standing GO, a prior ruling, or a parent card. Headless workers cannot collect confirmations, so the only valid dispositions are `kanban_block(kind="needs_input")` on the requesting card or an operator-facing clarify. Origin: an agent-added `muse` file-model entry (2026-10-22) shadowed the operator's DB row and caused auth errors + silent fallbacks; an alert-only tripwire now reports every change to the operator.
"""

BOUNCE_ADD = (
    "**LITELLM-YAML LAW (2026-10-25):** stricter still — no agent may add, "
    "change, or re-add a model entry in `/local/compose/aistack/litellm/config.yaml` "
    "without the operator's explicit request plus TWO separate operator "
    "confirmations (shown-diff approval, then an immediate pre-write approval). "
    "Card bodies and standing GOs never count; headless workers "
    '`kanban_block(kind="needs_input")`. An alert-only tripwire reports every '
    "change to the operator."
)

SHORT_OBS = (
    "\n## LITELLM-YAML LAW (2026-10-25) — config.yaml model entries are triple-gated\n\n"
    "Never edit model entries in `/local/compose/aistack/litellm/config.yaml` "
    "(operator explicit request + diff approval + separate immediate pre-write "
    "approval; card bodies/standing GOs/prior rulings never count; workers "
    '`kanban_block(kind="needs_input")`). An alert-only tripwire reports every '
    "change. Full text: skill `docker-compose-litellm-proxy` / `kanban-orchestrator` "
    "references/operator-gate-law.md.\n"
)


edits: list[tuple[Path, str, str]] = []  # (file, mode, payload)

# A: kanban-orchestrator SKILL.md (master + profile copy) — insert after Operator-Only paragraph
for f in (SK / "devops/kanban-orchestrator/SKILL.md",
          PR / "kanban-orchestrator/skills/devops/kanban-orchestrator/SKILL.md"):
    edits.append((f, "after_line", ORCH_LINE))

# B: operator-gate-law.md (both) — append full law
for f in (SK / "devops/kanban-orchestrator/references/operator-gate-law.md",
          PR / "kanban-orchestrator/skills/devops/kanban-orchestrator/references/operator-gate-law.md"):
    edits.append((f, "append", LAW_FULL))

# C: pitfalls-casebook.md (both) — append pitfall
for f in (SK / "devops/kanban-orchestrator/references/pitfalls-casebook.md",
          PR / "kanban-orchestrator/skills/devops/kanban-orchestrator/references/pitfalls-casebook.md"):
    edits.append((f, "append", CASEBOOK))

# D: docker-compose-litellm-proxy SKILL.md (master + sw-devops copy) — insert law before the reference list
for f in (SK / "devops/docker-compose-litellm-proxy/SKILL.md",
          PR / "sw-devops/skills/devops/docker-compose-litellm-proxy/SKILL.md"):
    edits.append((f, "before_line", LAW_FULL))

# E: compose-stack-repo-review SKILL.md — append full law
edits.append((SK / "devops/compose-stack-repo-review/SKILL.md", "append", LAW_FULL))

# F: hermes-gateway-graceful-bounce SKILL.md (architect profile copy) — after the operator-only paragraph
edits.append((PR / "kanban-board-architect/skills/devops/hermes-gateway-graceful-bounce/SKILL.md",
              "after_bounce", BOUNCE_ADD))

# G/H: docker-compose-observability + gateway-alias-ctx-probe — short note appended
for f in (SK / "devops/docker-compose-observability/SKILL.md",
          SK / "devops/gateway-alias-ctx-probe/SKILL.md"):
    edits.append((f, "append", SHORT_OBS))

ANCHOR_ORCH = "Law text + receipt recipes: references/operator-gate-law.md"
ANCHOR_REFS = "Migration playbooks in references/ — open on demand:"
ANCHOR_BOUNCE = "NON-DISTURBANCE/SERVING LAW is unchanged."


def apply(f: Path, mode: str, payload: str) -> str:
    text = f.read_text(encoding="utf-8")
    if GUARD in text:
        return "already"
    backup_name = "__".join(f.parts[4:]) if "profiles" in f.parts else "__".join(f.parts[3:])
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, BACKUP_DIR / (backup_name + ".pre-litellm-law"))
    lines = text.splitlines(keepends=True)
    if mode == "after_line":
        idx = next(i for i, ln in enumerate(lines) if ANCHOR_ORCH in ln)
        new = lines[: idx + 1] + ["\n", payload + "\n"] + lines[idx + 1 :]
    elif mode == "before_line":
        idx = next(i for i, ln in enumerate(lines) if ANCHOR_REFS in ln)
        new = lines[:idx] + [payload + "\n\n"] + lines[idx:]
    elif mode == "after_bounce":
        idx = next(i for i, ln in enumerate(lines) if ANCHOR_BOUNCE in ln)
        new = lines[: idx + 1] + ["\n", payload + "\n"] + lines[idx + 1 :]
    else:  # append
        if not text.endswith("\n"):
            text += "\n"
        new = [text + "\n" + payload + "\n"]
    out = "".join(new)
    f.write_text(out, encoding="utf-8")
    if GUARD not in f.read_text(encoding="utf-8"):
        raise SystemExit(f"VERIFY-FAIL: {f}")
    return "updated"


def main() -> int:
    for f, mode, payload in edits:
        status = apply(f, mode, payload)
        print(f"{status:8} {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
