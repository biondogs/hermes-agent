#!/usr/bin/env python3
"""Provision the gaudi-butler profile (Topology B pilot 2, board gaudi).

Idempotent: converges on re-run. Read-heavy steps print drift without writing.

Ref: /local/projects/software-co/docs/multi-bot-board-isolation-design-2026-10-22.md §§4, 5.1-5.3
Card: t_fd8ca6f0 (GAUDI-BUTLER-PROVISION + butler bank-isolation retrofit)

NO TOKENS: this script writes a .env SHAPE with a placeholder token only.
The operator completes Telegram setup via the managed-bot QR flow himself:
  HERMES_HOME=~/.hermes/profiles/gaudi-butler hermes gateway setup
    -> Telegram -> reconfigure -> [1] Automatic QR
(lesson #3 from the g01 pilot: do NOT provision via BotFather instructions.)

g01-pilot lessons baked in (t_bd78a263 close-out):
  #1 providers: block included in config.yaml (profiles do NOT inherit provider
     registrations; missing block = 'Unknown provider' at first message).
  #2 .env carries TELEGRAM_FALLBACK_IPS=149.154.167.220,149.154.166.110
     (ga01 egress blackholes the primary DC; without this the bot
     connects-timeout-loops).
"""
import os
import sys

import yaml

PROFILES = os.path.expanduser("~/.hermes/profiles")
BUTLER = "gaudi-butler"
HOMEDIR = f"{PROFILES}/{BUTLER}"
CONFIG = f"{HOMEDIR}/config.yaml"
SOUL = f"{HOMEDIR}/SOUL.md"
ENVF = f"{HOMEDIR}/.env"
HINDSIGHT_DIR = f"{HOMEDIR}/hindsight"
HINDSIGHT_CFG = f"{HINDSIGHT_DIR}/config.json"

OPERATOR_ID = "8158007517"          # operator's Telegram user id (from default home .env)
BOARD = "gaudi"

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
    "Board butler for gaudi: operator chat front-end on its own Telegram bot "
    "(gaudi_local_bot) — board status, card creation and routing to the gaudi-* fleet, "
    "notify subscriptions, and card summaries for the gaudi board ONLY. Every kanban "
    'call carries an explicit --board gaudi (board="gaudi" for kanban_* tools). '
    "Never executes board work itself; never touches other boards."
)

BANK_ID = "gaudi-butler"            # per-board butler bank (operator-approved isolation policy)
API_URL = "http://ga01:8888"

SOUL_MD = """# gaudi-butler

You are the **gaudi-butler** — the operator's single chat interface to the **gaudi** kanban board, served on your own Telegram bot (gaudi_local_bot). You took over board management for gaudi from the default orchestrator profile.

## The One Board

- The **only** board you ever operate is `gaudi`.
- **EVERY kanban command or tool call you make MUST carry the explicit board argument** — `--board gaudi` for CLI and slash commands, `board="gaudi"` for `kanban_*` tool calls. Never rely on the current-board pointer; never issue an unpinned kanban call. This is a double-failure guardrail: the operator picked this bot AND the board argument must say gaudi.
- If a command you are about to execute targets, or a request you receive names, any other board (default, gargantua01, gargantua02, skipjack, software-co), **stop and refuse**: point out the mismatch and the command's target board before doing anything else.
- If a kanban call fails with "board is archived" or "does not exist", **stop** and tell the operator to import/unarchive the board (`hermes kanban boards import`). Never retry against any other board and never fall back to the default board.
- Other boards do not exist for you except as plain-text references (`gargantua02/t_41f515f2`) the operator pastes. Cross-board `kanban_link` is forbidden; cross-board references go in card bodies/comments as text only.

## Estate context

- Board `gaudi`: Gaudi — local server (HPU + docker compose): vllm-gaudi porting/benchmarks, upstream vllm-project contrib work (#1840/#1843/#1890 CI-watch), :8001 serving. gaudi-* fleet lanes. Successor of the archived qwen38-perf board. Docs of record: `/local/projects/gaudi`.
- Fleet vocabulary: you route work to the gaudi specialists — `gaudi-orchestrator` (decomposition), `gaudi-planner`, `gaudi-perfeng`/`gaudi-benchrunner` (porting & benchmarks), `gaudi-deployer`/`gaudi-dockerops` (execution), `gaudi-analyst`, `gaudi-auditor`, `gaudi-scribe`, `gaudi-liaison` (upstream comms), `gaudi-synapse`, `gaudi-watcher` (read-only windows), `gaudi-arch`. You are the front door; they are the lanes.
- Live lanes right now: #1890 review-watch (t_02fea007, scheduled, gaudi-watcher). Active upstream threads: vllm PRs #1840/#1843/#1890.
- Your memory bank is `gaudi-butler` (isolated per-board butler bank — butler memories never land in shared banks).

## Your Role

- Report board status, summaries, and card reads for gaudi.
- Create cards on gaudi with the right gaudi-fleet assignee; manage notify subscriptions from this chat.
- When asked to DO work rather than report/route: create a card on gaudi for the right specialist. Do not execute ops yourself — you have no terminal, file, or code-execution tools by design.

## What You Do NOT Do

- You do NOT operate any board other than gaudi.
- You do NOT execute infrastructure changes, benchmarks, or documentation sprints (that is gaudi-deployer/gaudi-benchrunner/gaudi-scribe work, via cards).
- You do NOT spawn sub-agents or run cron jobs.
- You do NOT accept task ids from other boards as anything but reference text.
- You do NOT write memories to any bank other than `gaudi-butler`.
"""

ENV_SHAPE = f"""# gaudi-butler — per-profile secrets (Topology B, design 2026-10-22 §5.1).
# API keys and tokens set here override the shell environment.
# Behavioral settings belong in config.yaml, not here.

# LLM endpoint (LiteLLM at orb) — same key every gaudi profile uses.
ORB_API_KEY=ORB_KEY_FROM_ENV

# Hindsight memory bank — deliberately NOT set as an env var: bank is pinned in
# hindsight/config.json (bank_id gaudi-butler).
# (Env HINDSIGHT_BANK_ID would WIN over config.json — plugin #5171 — so it must stay unset.)

# ==== Telegram (operator completes via managed-bot QR flow) ====
# Placeholder so `hermes gateway setup` wizard reconfigure is one keystroke:
#   HERMES_HOME=~/.hermes/profiles/gaudi-butler hermes gateway setup
#     -> Telegram -> reconfigure -> [1] Automatic QR
# NEVER commit a real token; never paste it into a kanban card, comment, or chat.
TELEGRAM_BOT_TOKEN=PASTE-TOKEN-FOR-gaudi_local_bot-HERE
TELEGRAM_ALLOWED_USERS={OPERATOR_ID}
TELEGRAM_HOME_CHANNEL={OPERATOR_ID}
TELEGRAM_FALLBACK_IPS=149.154.167.220,149.154.166.110
"""


def section(title):
    print(f"\n=== {title} ===")


def main():
    orb_key = os.environ.get("ORB_API_KEY")
    if not orb_key:
        # Same fleet secret the other gaudi profiles carry in their profile .env.
        try:
            for line in open(f"{PROFILES}/gaudi-watcher/.env"):
                if line.startswith("ORB_API_KEY="):
                    orb_key = line.split("=", 1)[1].strip()
                    break
        except OSError:
            pass

    section("precheck: profile dir state")
    already = os.path.exists(HOMEDIR)
    if already and not os.environ.get("PROVISION_FORCE_OVERWRITE"):
        # CLOBBER GUARD (card t_8d962e02, 2026-10-31): an existing profile dir is
        # LIVE, evolved state. The templates below are provisioning-day material:
        # re-running this script over the live gaudi-butler on 2026-10-30 16:22 EDT
        # wiped the SOUL law blocks (G-01/G-29/G-33), approvals.deny, the
        # kanban.board pin, providers, skills.disabled and the .env secrets
        # (tokens -> placeholders). Convergence is therefore VERIFY-ONLY:
        # existence + resilience markers, ZERO writes (including the hindsight
        # bank config below). To intentionally reprovision from templates you
        # must export PROVISION_FORCE_OVERWRITE=1, which asserts the profile
        # SHOULD be reset to provision-day state (secrets included) — repair
        # live drift via the G-30 fleet-change checklist instead, never here.
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
        print(f"ok: {HOMEDIR} absent (fresh provisioning)")

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
        # LESSON #1 (g01 pilot): profiles do NOT inherit provider registrations.
        # Missing block = 'Unknown provider' at first message.
        "providers": {
            "litellm": {
                "api": "https://orb.arch.jhu.edu/v1",
                "name": "LiteLLM",
                "api_key": "${ORB_API_KEY}",
                "models": {
                    "qwen38-flash-fp8": {"context_length": 262144},
                    "glm53": {"context_length": 1000000},
                },
            }
        },
    }
    with open(CONFIG, "w") as fh:
        fh.write("# gaudi-butler — Topology B board butler for gaudi (t_fd8ca6f0).\n")
        fh.write("# Ref: docs/multi-bot-board-isolation-design-2026-10-22.md §§4, 5.1-5.3.\n")
        fh.write("# Lessons baked in: providers block (g01 #1), TELEGRAM_FALLBACK_IPS (g01 #2), QR flow (g01 #3),\n")
        fh.write("# per-board butler bank via hindsight/config.json (bank isolation, this card #4).\n")
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
    if orb_key:
        env_body = env_body.replace("ORB_KEY_FROM_ENV", orb_key)
    else:
        print("WARN: no ORB_API_KEY found (env or gaudi-watcher .env) — placeholder left in .env")
        env_body = env_body.replace("ORB_KEY_FROM_ENV", "PASTE-ORB-KEY-HERE")
    with open(ENVF, "w") as fh:
        fh.write(env_body)
    os.chmod(ENVF, 0o600)
    print(f"wrote {ENVF} (mode 0600, TELEGRAM_BOT_TOKEN=PLACEHOLDER — operator completes via QR flow)")

    # ----------------------------------------------- hindsight bank config (spec #4)
    section("write hindsight/config.json (bank gaudi-butler, mode local_external)")
    import json as _json
    write_bank_cfg = True
    if os.path.exists(HINDSIGHT_CFG):
        existing = _json.load(open(HINDSIGHT_CFG))
        if existing.get("bank_id") == BANK_ID and existing.get("api_url") == API_URL:
            print(f"already correct (bank_id={BANK_ID}); leaving untouched")
            write_bank_cfg = False
        else:
            print(f"drift: existing bank_id={existing.get('bank_id')!r} != {BANK_ID!r} — overwriting")
    if not os.path.exists(HINDSIGHT_DIR):
        os.makedirs(HINDSIGHT_DIR, exist_ok=True)
    if write_bank_cfg:
        # Shape copied verbatim from live estate configs (e.g. gaudi-planner),
        # with bank_id/api_url for the per-board butler bank.
        cfg = {
            "mode": "local_external",
            "apiKey": "",
            "timeout": 240,
            "idle_timeout": 300,
            "retain_tags": "",
            "observation_scopes": "",
            "retain_source": "",
            "retain_user_prefix": "User",
            "retain_assistant_prefix": "Assistant",
            "banks": {
                BANK_ID: {
                    "bankId": BANK_ID,
                    "budget": "mid",
                    "enabled": True,
                }
            },
            "api_url": API_URL,
            "bank_id": BANK_ID,
            "recall_budget": "mid",
        }
        with open(HINDSIGHT_CFG, "w") as fh:
            _json.dump(cfg, fh, indent=2)
            fh.write("\n")
        os.chmod(HINDSIGHT_CFG, 0o600)
        print(f"wrote {HINDSIGHT_CFG}")
    # No HINDSIGHT_BANK_ID in .env — env would win over config.json (#5171);
    # the ENV_SHAPE above deliberately omits it.

    # ------------------------------------------------------- routing description
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
