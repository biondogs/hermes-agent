"""BUTLERS-STAGE-3 step 2: converge the three remaining Topology-B butlers.

g02-butler (gargantua02), swco-butler (software-co), sjproto-butler
(skipjack-prototype) — from the proven g01/gaudi pilot kit.

This is a RECOVERY/AUGMENT pass, not a full restage (operator mid-run note
2026-10-22): the operator already ran the Telegram QR wizard for all three —
real TELEGRAM_BOT_TOKENs are live in each .env. Therefore:
  - .env is AUGMENTED in place (existing lines preserved verbatim, including
    the token); LITELLM_API_KEY + HINDSIGHT_BANK_ID + TELEGRAAM_FALLBACK_IPS
    are appended if missing.
  - config.yaml, hindsight/config.json, SOUL.md are written fresh (the wizard
    stubs/genrics are replaced) — per the card body, pilots, and the gaudi
    golden reference on disk.
  - If run again (convergence): existing values are verified and re-written
    only where drifting.

Per card body (non-negotiables):
  1. config.yaml providers:litellm block (env-indirected ${LITELLM_API_KEY},
     ctx pins qwen38-flash-fp8=262144 / glm53=1000000).
  2. .env: TELEGRAM_FALLBACK_IPS, allowed-users/home-channel 8158007517,
     LITELLM_API_KEY, HINDSIGHT_BANK_ID=<dedicated bank>.
  3. hindsight/config.json bank_id == dedicated bank == .env pin (pair must
     agree). Banks created server-side already (step 1).
  4. SOUL hard-scoped to one board; toolsets kanban/memory/session_search/web;
     qwen38-flash-fp8 model pin. platform_toolsets pinned per-surface.
  5. g02-butler SOUL additionally encodes the COMMS-LAW brevity/persona
     rules reference for board-level advice.
"""
import json
import os
import subprocess
import sys

import yaml

PROFILES = os.path.expanduser("~/.hermes/profiles")
OPERATOR_ID = "8158007517"
FALLBACK_IPS = "149.154.167.220,149.154.166.110"
API_URL = "http://ga01:8888"

BUTLERS = {
    "g02-butler": {
        "board": "gargantua02",
        "board_title": "Gargantua02 — production k8s on Azure VMs 413-418",
        "estate": (
            "Board `gargantua02`: production k8s cluster on Azure VMs 413-418 "
            "(conversion/build phase: VM reclaims, AVSET/RDMA networking, Hornet NIC "
            "moves). Everything built here is production-grade by default. Docs of "
            "record: `/local/projects/gargantua02`."
        ),
        "fleet": (
            "`g02-orchestrator` (decomposition), `g02-planner`, `g02-ops` "
            "(infra execution), `g02-auditor`, `g02-scribe`, `g02-watcher` "
            "(read-only windows). You are the front door; they are the lanes."
        ),
        "other_boards": "default, gargantua01, gaudi, skipjack, skipjack-prototype, software-co",
        "bot": "gargantua02_ops_bot",
        "comms_law": True,
    },
    "swco-butler": {
        "board": "software-co",
        "board_title": "Software Co — full-staff SDLC: pm → architect → dev×2 → reviewer → qa → devops → docs",
        "estate": (
            "Board `software-co`: full-staff SDLC simulation — pm → architect → "
            "dev×2 → reviewer → qa → devops → docs. Management repo of record: "
            "`/local/projects/software-co` (provisioning scripts, design docs, "
            "BANK-MAP). mprov product repos live under `/local/projects/`."
        ),
        "fleet": (
            "`sw-pm`, `sw-architect`, `sw-dev-a`, `sw-dev-b`, `sw-reviewer`, "
            "`sw-qa`, `sw-devops`, `sw-docs`, `sw-ux`. You are the front door; "
            "they are the lanes."
        ),
        "other_boards": "default, gargantua01, gargantua02, gaudi, skipjack, skipjack-prototype",
        "bot": "swco_bot",
        "comms_law": False,
    },
    "sjproto-butler": {
        "board": "skipjack-prototype",
        "board_title": "Skipjack Prototype — k8s on gh207+gh208",
        "estate": (
            "Board `skipjack-prototype`: Skipjack prototype k8s cluster on nodes "
            "gh207+gh208 (HPC/AI hybrid Skipjack programme; the production Skipjack "
            "cluster on mgmt02 is the separate `skipjack` board). Docs of record: "
            "`/local/projects/`."
        ),
        "fleet": (
            "`sjp-orchestrator` (decomposition), `sjp-planner`, `sjp-ops` "
            "(execution), `sjp-auditor`, `sjp-scribe`, `sjp-watcher` (read-only "
            "windows). You are the front door; they are the lanes."
        ),
        "other_boards": "default, gargantua01, gargantua02, gaudi, skipjack, software-co",
        "bot": "skipjack_proto_bot",
        "comms_law": False,
    },
}

ALLOWED = ["kanban", "memory", "session_search", "web"]
BUILTIN_CONFIGURABLE = [
    "web", "search", "x_search", "vision", "video", "image_gen", "video_gen",
    "computer_use", "terminal", "skills", "browser", "cronjob", "file", "tts",
    "todo", "memory", "context_engine", "session_search", "connections",
    "clarify", "code_execution", "delegation", "kanban", "discord",
    "discord_admin", "yuanbao", "feishu_doc", "feishu_drive",
]
DISABLED = sorted(set(BUILTIN_CONFIGURABLE) - set(ALLOWED))

COMMS_LAW_SECTION = """
## External Comms Law (operator directive 2026-10-21 — binding reference)

You do not post to external venues yourself, but when you draft or advise on
ANY externally-visible communication arising from this board's work (Azure
support tickets, community repo issues/PRs, upstream threads), the operator's
COMMS-LAW applies — verify drafts against it:

- **No internal specifics, ever.** Nothing externally visible may carry task
  ids (`t_...`), internal card titles, board/lane names, gate names
  ("distiller gate", "operator GO"), approval or workflow vocabulary (gates,
  ceremonies, temp-trust windows, approval matrices, hubs, cards), admin
  tasks, or any reference to the operator's activities or the automation
  behind the work. Never mention kanban tasks, boards, agents, or gates
  explicitly — the reader sees one competent human doing the work, nothing
  else. (Full binding text: `g02-ops` SOUL.md, "External Comms Law".)
- **Persona.** All external posts are authored from the operator's persona —
  a single human voice, first person (Joe, jbiondo2@jh.edu). Never say or
  imply that an agent, bot, process, or "team" produced or reviewed the text.
- **Brevity discipline.** Mirror the counterpart. A short, clearly human,
  one-sentence question gets a short, accurate answer — a few sentences, not
  a page of text. Detailed technical questions may get detailed answers, but
  never pad. Answer the question asked; enough info to be accurate, no more.
- When advising on a draft: check it against this law BEFORE presenting it,
  and say plainly what must be stripped.
"""


def make_soul(butler, spec):
    soul = f"""# {butler}

You are the **{butler}** — the operator's single chat interface to the **{spec['board']}** kanban board, served on your own Telegram bot ({spec['bot']}). You took over board management for {spec['board']} from the default orchestrator profile.

## The One Board

- The **only** board you ever operate is `{spec['board']}`.
- **EVERY kanban command or tool call you make MUST carry the explicit board argument** — `--board {spec['board']}` for CLI and slash commands, `board="{spec['board']}"` for `kanban_*` tool calls. Never rely on the current-board pointer; never issue an unpinned kanban call. This is a double-failure guardrail: the operator picked this bot AND the board argument must say {spec['board']}.
- If a command you are about to execute targets, or a request you receive names, any other board ({spec['other_boards']}), **stop and refuse**: point out the mismatch and the command's target board before doing anything else.
- If a kanban call fails with "board is archived" or "does not exist", **stop** and tell the operator to import/unarchive the board (`hermes kanban boards import`). Never retry against any other board and never fall back to the default board.
- Other boards do not exist for you except as plain-text references (`gargantua02/t_41f515f2`) the operator pastes. Cross-board `kanban_link` is forbidden; cross-board references go in card bodies/comments as text only.

## Estate context

- {spec['estate']}
- Fleet vocabulary: you route work to the specialists — {spec['fleet']}
- Your memory bank is `{butler}` (isolated per-board butler bank — butler memories never land in shared banks).

## Your Role

- Report board status, summaries, and card reads for {spec['board']}.
- Create cards on {spec['board']} with the right fleet assignee; manage notify subscriptions from this chat.
- When asked to DO work rather than report/route: create a card on {spec['board']} for the right specialist. Do not execute ops yourself — you have no terminal, file, or code-execution tools by design.
"""
    if spec["comms_law"]:
        soul += COMMS_LAW_SECTION
    soul += f"""
## What You Do NOT Do

- You do NOT operate any board other than {spec['board']}.
- You do NOT execute infrastructure changes, audits, or documentation sprints (that is fleet specialist work, via cards).
- You do NOT spawn sub-agents or run cron jobs.
- You do NOT accept task ids from other boards as anything but reference text.
- You do NOT write memories to any bank other than `{butler}`.
"""
    return soul


def make_description(butler, spec):
    return (
        f"Board butler for {spec['board']}: operator chat front-end on its own "
        f"Telegram bot ({spec['bot']}) — board status, card creation and routing "
        f"to the {spec['board']} fleet, notify subscriptions, and card summaries "
        f"for the {spec['board']} board ONLY. Every kanban call carries an "
        f"explicit --board {spec['board']} (board=\"{spec['board']}\" for "
        f"kanban_* tools). Never executes board work itself; never touches "
        f"other boards."
    )


def main():
    # fleet LITELLM key: env first, then a known fleet profile .env
    litellm = os.environ.get("LITELLM_API_KEY")
    if not litellm:
        try:
            for line in open(f"{PROFILES}/g02-watcher/.env"):
                if line.startswith("LITELLM_API_KEY="):
                    litellm = line.split("=", 1)[1].strip()
                    break
        except OSError:
            pass
    if not litellm:
        print("FATAL: no LITELLM_API_KEY found (env or g02-watcher .env)")
        return 1

    # guardrails (from the kit): boards live + global config untouched
    for slug in ("gargantua02", "software-co", "skipjack-prototype"):
        bj = json.load(open(os.path.expanduser(f"~/.hermes/kanban/boards/{slug}/board.json")))
        assert bj["slug"] == slug and not bj["archived"], bj
        print(f"ok: board {slug} live (archived={bj['archived']})")
    gc = yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml")))
    assert gc.get("gateway", {}).get("multiplex_profiles") is True
    print("ok: gateway.multiplex_profiles: true pinned")

    for butler, spec in BUTLERS.items():
        home = f"{PROFILES}/{butler}"
        board = spec["board"]
        os.makedirs(home, exist_ok=True)
        print(f"\n=== {butler} (board {board}) ===")

        # ---------------------------------------------------------- config.yaml
        cfg_path = f"{home}/config.yaml"
        cfg = {
            "model": {
                "default": "qwen38-flash-fp8",
                "provider": "custom:LiteLLM",
                "max_tokens": 65536,
                "context_length": 262144,
            },
            "agent": {
                "description": make_description(butler, spec),
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
                "telegram": {"extra": {"drop_pending_on_cold_boot": False}}
            },
            "onboarding": {"seen": {"tool_progress_prompt": True}},
            "_config_version": 51,
            # LESSON #1 (g01 pilot): profiles do NOT inherit provider registrations.
            "providers": {
                "litellm": {
                    "api": "https://orb.arch.jhu.edu/v1",
                    "name": "LiteLLM",
                    "api_key": "${LITELLM_API_KEY}",
                    "models": {
                        "qwen38-flash-fp8": {"context_length": 262144},
                        "glm53": {"context_length": 1000000},
                    },
                }
            },
        }
        with open(cfg_path, "w") as fh:
            fh.write(f"# {butler} — Topology B board butler for {board} (t_02de9dff).\n")
            fh.write("# Ref: docs/multi-bot-board-isolation-design-2026-10-22.md §§4, 5.1-5.3.\n")
            fh.write("# Lessons baked in: providers block (g01 #1), TELEGRAM_FALLBACK_IPS (g01 #2),\n")
            fh.write("# QR flow — operator completed tokens 2026-10-22, bank pin .env+config.json agree (#4).\n")
            yaml.dump(cfg, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"wrote {cfg_path}")

        # -------------------------------------------------------------- SOUL.md
        soul_path = f"{home}/SOUL.md"
        with open(soul_path, "w") as fh:
            fh.write(make_soul(butler, spec))
        print(f"wrote {soul_path}")

        # ------------------------------------- .env AUGMENT (preserve token!)
        env_path = f"{home}/.env"
        env_lines = []
        if os.path.exists(env_path):
            env_lines = open(env_path).read().splitlines()
        have = {ln.split("=", 1)[0] for ln in env_lines if "=" in ln and not ln.startswith("#")}
        additions = []
        if "LITELLM_API_KEY" not in have:
            additions.append(f"LITELLM_API_KEY={litellm}")
        if "HINDSIGHT_BANK_ID" not in have:
            additions.append(f"HINDSIGHT_BANK_ID={butler}")
        else:
            # ensure the pin agrees with the dedicated bank
            for i, ln in enumerate(env_lines):
                if ln.startswith("HINDSIGHT_BANK_ID="):
                    cur = ln.split("=", 1)[1].strip()
                    if cur != butler:
                        print(f"drift: HINDSIGHT_BANK_ID={cur} -> {butler}")
                        env_lines[i] = f"HINDSIGHT_BANK_ID={butler}"
        if "TELEGRAM_FALLBACK_IPS" not in have:
            additions.append(f"TELEGRAM_FALLBACK_IPS={FALLBACK_IPS}")
        if "TELEGRAM_ALLOWED_USERS" not in have:
            additions.append(f"TELEGRAM_ALLOWED_USERS={OPERATOR_ID}")
        if "TELEGRAM_HOME_CHANNEL" not in have:
            additions.append(f"TELEGRAM_HOME_CHANNEL={OPERATOR_ID}")
        header = [] if env_lines and env_lines[0].startswith("#") else [
            f"# {butler} — per-profile secrets (Topology B, design 2026-10-22 §5.1).",
            "# Behavioral settings belong in config.yaml, not here.",
        ]
        out = env_lines[:]
        if additions:
            if out and out[-1].strip():
                out.append("")
            out += additions
        with open(env_path, "w") as fh:
            fh.write("\n".join(header + out) + "\n")
        os.chmod(env_path, 0o600)
        token_state = "PRESERVED" if any(l.startswith("TELEGRAM_BOT_TOKEN=") and "PASTE" not in l for l in env_lines) else "MISSING!"
        print(f"augmented {env_path} (0600; operator token {token_state}; +{len(additions)} additions)")

        # ----------------------------------------------- hindsight/config.json
        hdir = f"{home}/hindsight"
        hpath = f"{hdir}/config.json"
        os.makedirs(hdir, exist_ok=True)
        write = True
        if os.path.exists(hpath):
            existing = json.load(open(hpath))
            if existing.get("bank_id") == butler and existing.get("api_url") == API_URL:
                print(f"hindsight config already correct (bank {butler}); leaving untouched")
                write = False
            else:
                print(f"drift: bank_id={existing.get('bank_id')!r} != {butler!r} — overwriting")
        if write:
            hcfg = {
                "mode": "local_external",
                "apiKey": "",
                "timeout": 240,
                "idle_timeout": 300,
                "retain_tags": "",
                "observation_scopes": "",
                "retain_source": "",
                "retain_user_prefix": "User",
                "retain_assistant_prefix": "Assistant",
                "banks": {butler: {"bankId": butler, "budget": "mid", "enabled": True}},
                "api_url": API_URL,
                "bank_id": butler,
                "recall_budget": "mid",
            }
            with open(hpath, "w") as fh:
                json.dump(hcfg, fh, indent=2)
                fh.write("\n")
            os.chmod(hpath, 0o600)
            print(f"wrote {hpath} (bank_id={butler})")

        # ------------------------------------------------ routing description
        r = subprocess.run(
            ["hermes", "profile", "describe", butler, "--text",
             make_description(butler, spec), "--overwrite"],
            capture_output=True, text=True)
        print(f"profile describe {butler}: rc={r.returncode} {(r.stdout + r.stderr).strip()[:120]}")
        if r.returncode != 0:
            return 1

    print("\nStep 2 complete: all three butlers converged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
