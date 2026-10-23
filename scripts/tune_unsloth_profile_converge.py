"""UNSLOTH-PROFILE-TUNE (t_7601b273): rebuild unsloth-litellm profile config.

Converges on re-run. Applies:
  1. Slim purpose-built config.yaml (yaml.dump) — server-manager worker,
     no kanban, no orchestrator clone, provider canonical `litellm`,
     safety approvals.deny for the litellm/orb non-disturbance law.
  2. Bank: create hb-unsloth-studio server-side (PUT upsert w/ mission),
     flip hindsight/config.json bank_id + banks{} (config.json carrier
     governs; NO .env HINDSIGHT_BANK_ID pin per ratified post-cutover
     convention).

Backups already taken (pre-mutation):
  ~/kanban-backups/unsloth-profile-tune-20261023T031041Z/unsloth-litellm-full.tar.gz
  /local/projects/software-co/backups/unsloth-profile-tune-2026-10-23/*.pre
"""
import json
import os
import urllib.request
import urllib.error

import yaml

PROFILE = os.path.expanduser("~/.hermes/profiles/unsloth-litellm")
HBASE = "http://ga01:8888"
BANK = "hb-unsloth-studio"
MISSION = (
    "Memory bank for the unsloth-litellm profile: Unsloth Studio server "
    "management and LiteLLM database-configuration working knowledge from "
    "server-manager runs. Created 2026-10-23 (t_7601b273) per ratified bank "
    "policy — fresh start, repopulates from live runs only."
)

INTENDED_TOOLSETS = [
    "file", "terminal", "code_execution", "web", "memory", "skills",
    "mcp-unsloth_studio",
]

DISABLED_TOOLSETS = [
    # service integrations (inherited orchestrator clone list)
    "discord", "discord_admin", "feishu_doc", "feishu_drive",
    "homeassistant", "spotify", "video", "video_gen", "x_search", "yuanbao",
    # not needed by a server-manager worker — end-of-pipeline limiter
    "browser", "vision", "tts", "stt", "todo", "kanban", "context_engine",
    "session_search", "connections", "clarify", "delegation", "cronjob",
    "computer_use", "a2a",
]

DENY_GLOBS = [
    # aistack non-disturbance law: LiteLLM carries the fleet's own model
    # traffic. compose up/down with no args hits the whole stack on this
    # host, so the globs are deliberately broad.
    "*compose down*",
    "*compose stop*",
    "*compose restart*",
    "*compose up*",
    "*docker*stop*litellm*",
    "*docker*restart*litellm*",
    "*docker*kill*litellm*",
    "*docker*rm*litellm*",
    "*docker*stop*orb*",
    "*docker*restart*orb*",
    "*docker*kill*orb*",
    "*docker*rm*orb*",
    "*systemctl*stop*litellm*",
    "*systemctl*restart*litellm*",
    "*systemctl*stop*orb*",
    "*systemctl*restart*orb*",
    # destructive SQL via CLI — DB config goes through unsloth_studio MCP
    "*psql*drop*",
    "*psql*truncate*",
    "*psql*delete*",
    "*psql*alter*",
    # standard fleet guards (kanban-worker precedent)
    "git push --force*",
    "git reset --hard*",
]

SMART_POLICY = (
    "Always ESCALATE any command that touches the LiteLLM database or the "
    "litellm/orb container stack on this host; never auto-approve container "
    "lifecycle (stop/start/restart/kill/rm), docker compose, or DDL against "
    "the litellm DB. LiteLLM carries this fleet's own model traffic — DB and "
    "config changes go through the unsloth_studio MCP tools, not raw psql, "
    "unless the operator explicitly instructs otherwise."
)

CONFIG = {
    "model": {
        "default": "qwen38-flash-fp8",
        "provider": "litellm",          # canonical named provider (block key)
        "context_length": 262144,       # pin: orb aliases hide ctx
        "max_tokens": 65536,
    },
    "agent": {
        "max_turns": 150,
        "reasoning_effort": "medium",
        "disabled_toolsets": DISABLED_TOOLSETS,
    },
    "toolsets": list(INTENDED_TOOLSETS),
    "platform_toolsets": {"cli": list(INTENDED_TOOLSETS)},
    "auxiliary": {
        "compression": {"provider": "auto", "model": "", "reasoning_effort": ""},
        "skills_hub": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
        "approval": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
        "mcp": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
        "title_generation": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
        "memory_query_rewrite": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
        "web_extract": {"provider": "litellm", "model": "qwen38", "reasoning_effort": "none"},
    },
    "memory": {
        "memory_enabled": True,
        "user_profile_enabled": True,
        "provider": "hindsight",
        "budget": "mid",
    },
    "web": {
        "backend": "firecrawl",
        "search_backend": "searxng",
        "extract_backend": "firecrawl",
        "search_url": "http://ga01:8085",
        "use_gateway": False,
    },
    "approvals": {
        "mode": "smart",
        "cron_mode": "deny",
        "smart_policy": SMART_POLICY,
        "deny": DENY_GLOBS,
    },
    "mcp_servers": {
        "unsloth_studio": {
            "url": "http://10.99.136.90:8000/mcp/",
            "headers": {"Authorization": "Bearer ${UNSLOTH_API_KEY}"},
        },
    },
    "providers": {
        "litellm": {
            "api": "https://orb.arch.jhu.edu/v1",
            "name": "LiteLLM",
            "api_key": "${LITELLM_API_KEY}",
            "transport": "chat_completions",
            "models": {
                "qwen38": {"context_length": 1000000},
                "qwen38-flash-fp8": {"context_length": 262144},
            },
        },
    },
    "plugins": {"enabled": ["hindsight", "web/firecrawl", "web/searxng"], "disabled": []},
    "timezone": "America/New_York",
    "_config_version": 51,
}


def main():
    # --- receipts before ---
    with open(f"{PROFILE}/config.yaml") as f:
        old = yaml.safe_load(f)
    print(f"pre-mutation config keys: {len(old)} top-level keys, "
          f"provider={old['model']['provider']!r}, kanban section={'kanban' in old}")

    # --- 1. write slim config ---
    with open(f"{PROFILE}/config.yaml", "w") as f:
        yaml.dump(CONFIG, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    with open(f"{PROFILE}/config.yaml") as f:
        check = yaml.safe_load(f)
    assert check["model"]["provider"] == "litellm", "provider not canonical"
    assert "kanban" not in check, "kanban section leaked"
    assert check["approvals"]["deny"] == DENY_GLOBS, "deny list roundtrip mismatch"
    print(f"config.yaml rewritten: {len(CONFIG)} top-level keys; "
          f"yaml.safe_load roundtrip OK; provider=litellm; no kanban section")

    # --- 2. bank: server-side PUT upsert ---
    body = json.dumps({"name": BANK, "mission": MISSION}).encode()
    req = urllib.request.Request(
        f"{HBASE}/v1/default/banks/{BANK}", data=body, method="PUT",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"bank PUT {BANK}: HTTP {r.status}")
    except urllib.error.HTTPError as e:
        print(f"bank PUT {BANK}: HTTP {e.code} (may be upsert-already-exists) — {e.read()[:200]!r}")
    with urllib.request.urlopen(f"{HBASE}/v1/default/banks", timeout=20) as r:
        banks = {b["bank_id"]: b for b in json.load(r)["banks"]}
    if BANK in banks:
        print(f"bank readback: fact_count={banks[BANK]['fact_count']} "
              f"mission_set={bool(banks[BANK].get('mission'))}")
    else:
        raise SystemExit(f"FATAL: bank {BANK} not on server after PUT")

    # --- 3. hindsight config.json flip (config.json carrier governs) ---
    hpath = f"{PROFILE}/hindsight/config.json"
    hcfg = json.load(open(hpath))
    prev = hcfg.get("bank_id")
    hcfg["bank_id"] = BANK
    hcfg["banks"] = {BANK: {"bankId": BANK, "budget": "mid", "enabled": True}}
    with open(hpath, "w") as f:
        json.dump(hcfg, f, indent=2)
        f.write("\n")
    rb = json.load(open(hpath))
    assert rb["bank_id"] == BANK and BANK in rb["banks"]
    print(f"hindsight config.json: bank_id '{prev}' -> '{BANK}' (roundtrip OK)")

    # --- 4. .env: assert no HINDSIGHT_BANK_ID pin (convention: unset) ---
    with open(f"{PROFILE}/.env") as f:
        env = f.read()
    pins = [ln for ln in env.splitlines() if ln.startswith("HINDSIGHT_BANK_ID=")]
    print(f".env HINDSIGHT_BANK_ID pin lines: {len(pins)} (must be 0 — config.json governs)")
    assert not pins, "unexpected .env pin!"

    print("CONVERGE OK")


if __name__ == "__main__":
    main()
