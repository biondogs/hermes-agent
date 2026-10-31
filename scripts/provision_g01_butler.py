#!/usr/bin/env python3
"""Provision the g01-butler profile (Topology B pilot, board gargantua01).

Idempotent: converges on re-run. Read-heavy steps print drift without writing.

Ref: /local/projects/software-co/docs/multi-bot-board-isolation-design-2026-10-22.md §§4, 5.1-5.3
Card: t_bd78a263

NO TOKENS: this script writes a .env SHAPE with a placeholder token only.
The operator pastes the real BotFather token into profiles/g01-butler/.env himself.
"""
import os
import sys

import yaml

PROFILES = os.path.expanduser("~/.hermes/profiles")
BUTLER = "g01-butler"
HOMEDIR = f"{PROFILES}/{BUTLER}"
CONFIG = f"{HOMEDIR}/config.yaml"
SOUL = f"{HOMEDIR}/SOUL.md"
ENVF = f"{HOMEDIR}/.env"

OPERATOR_ID = "8158007517"          # operator's Telegram user id (from default home .env)
BOARD = "gargantua01"

# Design §5.2 minimal surface, per-surface pinned (gateway turns would otherwise
# fall back to the full hermes-telegram bundle: _get_platform_tools ->
# _platform_default_toolset("telegram") == "hermes-telegram").
ALLOWED = ["kanban", "memory", "session_search", "web"]

# Complement of ALLOWED over the configurable builtin toolsets (tools_config.py
# _configurable_keys), for agent.disabled_toolsets (global suppression, runs last).
BUILTIN_CONFIGURABLE = [
    "web", "search", "x_search", "vision", "video", "image_gen", "video_gen",
    "computer_use", "terminal", "skills", "browser", "cronjob", "file", "tts",
    "todo", "memory", "context_engine", "session_search", "connections",
    "clarify", "code_execution", "delegation", "kanban", "discord",
    "discord_admin", "yuanbao", "feishu_doc", "feishu_drive",
]
DISABLED = sorted(set(BUILTIN_CONFIGURABLE) - set(ALLOWED))

DESCRIPTION = (
    "Board butler for gargantua01: operator chat front-end on its own Telegram bot "
    "(gargantua01_proto_bot) — board status, card creation and routing to the g01-* fleet, "
    "notify subscriptions, and card summaries for the gargantua01 board ONLY. Every kanban "
    "call carries an explicit --board gargantua01 (board=\"gargantua01\" for kanban_* tools). "
    "Never executes board work itself; never touches other boards."
)

SOUL_MD = """# g01-butler

You are the **g01-butler** — the operator's single chat interface to the **gargantua01** kanban board, served on your own Telegram bot (gargantua01_proto_bot). You took over board management for gargantua01 from the default orchestrator profile.

## The One Board

- The **only** board you ever operate is `gargantua01`.
- **EVERY kanban command or tool call you make MUST carry the explicit board argument** — `--board gargantua01` for CLI and slash commands, `board="gargantua01"` for `kanban_*` tool calls. Never rely on the current-board pointer; never issue an unpinned kanban call. This is a double-failure guardrail: the operator picked this bot AND the board argument must say gargantua01.
- If a command you are about to execute targets, or a request you receive names, any other board (default, gargantua02, gaudi, skipjack, software-co), **stop and refuse**: point out the mismatch and the command's target board before doing anything else.
- If a kanban call fails with "board is archived" or "does not exist", **stop** and tell the operator to import/unarchive the board (`hermes kanban boards import`). Never retry against any other board and never fall back to the default board.
- Other boards do not exist for you except as plain-text references (`gargantua02/t_41f515f2`) the operator pastes. Cross-board `kanban_link` is forbidden; cross-board references go in card bodies/comments as text only.

## Estate context

- Board `gargantua01`: Gargantua01 — prototype k8s cluster (garg-infrastructure origin), nodes gargantua01–03; a rebuild is coming — favor reversible changes and codifying into garg-infrastructure. Docs of record: `/local/projects/gargantua01`.
- Fleet vocabulary: you route work to the g01 specialists — `g01-orchestrator` (decomposition), `g01-planner`, `g01-ops` (execution), `g01-auditor`, `g01-scribe`, `g01-watcher` (read-only windows). You are the front door; they are the lanes.
- The board is currently near-quiet (last lanes: hindsight retain-fix t_76799556 + verifier t_9d9d3d6c, both done).

## Your Role

- Report board status, summaries, and card reads for gargantua01.
- Create cards on gargantua01 with the right g01-fleet assignee; manage notify subscriptions from this chat.
- When asked to DO work rather than report/route: create a card on gargantua01 for the right specialist. Do not execute ops yourself — you have no terminal, file, or code-execution tools by design.

## What You Do NOT Do

- You do NOT operate any board other than gargantua01.
- You do NOT execute infrastructure changes, audits, or documentation sprints (that is g01-ops/g01-auditor/g01-scribe work, via cards).
- You do NOT spawn sub-agents or run cron jobs.
- You do NOT accept task ids from other boards as anything but reference text.
"""

ENV_SHAPE = f"""# g01-butler — per-profile secrets (Topology B, design 2026-10-22 §5.1).
# API keys and tokens set here override the shell environment.
# Behavioral settings belong in config.yaml, not here.

# LLM endpoint (LiteLLM at orb) — same key every g01 profile uses.
ORB_API_KEY={os.environ.get('ORB_API_KEY', '${{ORB_API_KEY}}')}

# Hindsight memory bank — shared estate bank, per card t_bd78a263 scope item 1.
HINDSIGHT_BANK_ID=hermes

# ==== Telegram (operator fills) ====
# Paste the token BotFather gave you for @gargantua01_proto_bot below.
# NEVER commit this token; never paste it into a kanban card, comment, or chat.
TELEGRAM_BOT_TOKEN=PASTE-BOTFATHER-TOKEN-FOR-gargantua01_proto_bot-HERE
TELEGRAM_ALLOWED_USERS={OPERATOR_ID}
TELEGRAM_HOME_CHANNEL={OPERATOR_ID}
"""


def section(title):
    print(f"\n=== {title} ===")


def main():
    section("precheck: profile dir state")
    already = os.path.exists(HOMEDIR)
    if already and not os.environ.get("PROVISION_FORCE_OVERWRITE"):
        # CLOBBER GUARD (card t_8d962e02, 2026-10-31): an existing profile dir is
        # LIVE, evolved state. The templates below are provisioning-day material:
        # re-running this script over the live g01-butler on 2026-10-30 16:21 EDT
        # wiped the SOUL law blocks (G-01/G-29/G-33), approvals.deny, the
        # kanban.board pin, providers/plugins, skills.disabled and the .env
        # secrets (tokens -> placeholders). Convergence is therefore VERIFY-ONLY:
        # existence + resilience markers, ZERO writes. To intentionally
        # reprovision from templates you must export PROVISION_FORCE_OVERWRITE=1,
        # which asserts the profile SHOULD be reset to provision-day state
        # (secrets included) — repair live drift via the G-30 fleet-change
        # checklist instead, never via this script.
        print(f"note: {HOMEDIR} exists — VERIFY-ONLY convergence (clobber guard t_8d962e02; "
              "export PROVISION_FORCE_OVERWRITE=1 to force a template rewrite)")
        missing = [f for f in (CONFIG, SOUL, ENVF) if not os.path.exists(f)]
        if missing:
            print(f"FAIL: existing profile missing {missing} — rolling hill stopped.")
            return 1
        problems = []
        try:
            ccfg = yaml.safe_load(open(CONFIG))
            deny = (ccfg.get("approvals") or {}).get("deny") or []
            if not any("aistack/litellm/config.yaml" in str(d) for d in deny):
                problems.append("config.yaml: approvals.deny lacks the G-01 litellm entry")
            if not (ccfg.get("kanban") or {}).get("board"):
                problems.append("config.yaml: kanban.board pin missing")
        except Exception as e:
            problems.append(f"config.yaml unreadable: {e}")
        stext = open(SOUL).read()
        for marker in ("LITELLM-YAML LAW", "PUSH-DEFER", "LONG-JOB DETACH"):
            if marker not in stext:
                problems.append(f"SOUL.md: law-block marker missing: {marker}")
        if "PASTE-" in open(ENVF).read():
            problems.append(".env: placeholder token present (never pasted, or a regression)")
        if problems:
            print("VERIFY-ONLY findings (NO WRITES PERFORMED):")
            for p in problems:
                print(f"  - {p}")
            print("FAIL: live profile fails resilience verification — repair via the "
                  "G-30 fleet-change checklist, NOT via this script.")
            return 1
        print("ok: live profile carries provision files + law-block/deny/board-pin "
              "resiliences — nothing written.")
        return 0
    if already:
        print(f"WARNING: {HOMEDIR} exists and PROVISION_FORCE_OVERWRITE=1 — REWRITING "
              "live profile from provisioning-day templates (clobber by design; "
              "guard t_8d962e02).")
    else:
        print(f"ok: {HOMEDIR} absent")

    section("guardrails: board live, dispatcher untouched")
    import json
    BOARD_JSON = os.path.expanduser(f"~/.hermes/kanban/boards/{BOARD}/board.json")
    with open(BOARD_JSON) as fh:
        j = json.load(fh)
    assert j["slug"] == BOARD and not j["archived"], j
    print(f"ok: board {BOARD} live (archived={j['archived']})")
    gc = yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml")))
    assert gc.get("gateway", {}).get("multiplex_profiles") is True, "multiplex_profiles not pinned!"
    print("ok: gateway.multiplex_profiles: true pinned in default home config")
    assert "dispatch_profiles" not in (gc.get("kanban") or {}), "dispatch_profiles unexpectedly set"
    print("ok: kanban.dispatch_profiles unset (design: N/A single-home)")

    # ---------------------------------------------------------------- config
    section("write config.yaml")
    os.makedirs(HOMEDIR, exist_ok=True)
    config = {
        "model": {
            "default": "qwen38-flash-fp8",
            "provider": "custom:LiteLLM",
            "max_tokens": 65536,
            "context_length": 262144,
        },
        "agent": {
            "description": DESCRIPTION,
            "max_turns": 100,
            "reasoning_effort": "low",
            "disabled_toolsets": DISABLED,
        },
        "toolsets": list(ALLOWED),
        "platform_toolsets": {"telegram": list(ALLOWED), "cli": list(ALLOWED)},
        "skills": {"always_load": []},
        "memory": {
            "provider": "hindsight",
            "memory_enabled": True,
            "user_profile_enabled": True,
        },
        "plugins": {"enabled": ["hindsight"], "disabled": []},
        "platforms": {
            "telegram": {
                "extra": {
                    # 03:34 auto-update restarts the single gateway; don't drop
                    # operator messages queued during the bounce (design §5.5).
                    "drop_pending_on_cold_boot": False,
                }
            }
        },
        "onboarding": {"seen": {"tool_progress_prompt": True}},
        "_config_version": 51,
    }
    with open(CONFIG, "w") as fh:
        fh.write("# g01-butler — Topology B board butler for gargantua01 (t_bd78a263).\n")
        fh.write("# Ref: docs/multi-bot-board-isolation-design-2026-10-22.md §§4, 5.1-5.3.\n")
        yaml.dump(config, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"wrote {CONFIG}")

    # ----------------------------------------------------------------- soul
    section("write SOUL.md")
    with open(SOUL, "w") as fh:
        fh.write(SOUL_MD)
    print(f"wrote {SOUL}")

    # ----------------------------------------------------------------- env
    section("write .env shape (placeholder token only)")
    env_body = ENV_SHAPE
    orb_key = os.environ.get("ORB_API_KEY")
    if not orb_key:
        # Same fleet secret the other g01 profiles carry in their profile .env.
        try:
            for line in open(f"{PROFILES}/g01-watcher/.env"):
                if line.startswith("ORB_API_KEY="):
                    orb_key = line.split("=", 1)[1].strip()
                    break
        except OSError:
            pass
    if orb_key:
        env_body = env_body.replace("${ORB_API_KEY}", orb_key)
    with open(ENVF, "w") as fh:
        fh.write(env_body)
    os.chmod(ENVF, 0o600)
    print(f"wrote {ENVF} (mode 0600, TELEGRAM_BOT_TOKEN=PLACEHOLDER — operator pastes real token)")

    # ------------------------------------------------------- routing description
    # Applies via the CLI descriptor (writes agent.description to the live
    # profile registry), grounding it in the config we just wrote. Pattern
    # follows the fleet description sweep t_5f26f34d.
    section("set routing description")
    import subprocess
    for cmd in (["hermes", "profile", "describe", BUTLER, "--text", DESCRIPTION, "--overwrite"],
                ["hermes", "profile", "describe", BUTLER]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        print(f"$ {' '.join(cmd[:4])} …\n{out}\n(rc={r.returncode})")
        if r.returncode != 0:
            return 1

    print("\nAll staged phases done. Next phases run via hermes CLI (see run script).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
