#!/usr/bin/env python3
"""RETROFIX (card t_fd8ca6f0, spec #5): g01-butler bank isolation.

g01-butler currently falls back to the shared 'hermes' bank via HINDSIGHT_BANK_ID=hermes
in its profile .env. Per the operator-approved per-board-butler-bank policy:

1. Write an explicit hindsight/config.json with bank_id 'g01-butler'
   (mode local_external, api_url http://ga01:8888).
2. REMOVE HINDSIGHT_BANK_ID from the profile .env — a non-empty env value WINS over
   config.json (plugin #5171, test_bank_id_env_wins_over_config_json), so leaving it
   would keep routing to the shared bank.
3. Migrate nothing; the new bank starts empty (operator-accepted).

Takes effect on the next gateway restart (the bot's loaded plugin config caches at boot;
the same restart that brings up gaudi-butler covers this).

Idempotent: re-run detects convergence and only re-applies what drifted.
"""
import json
import os
import shutil
import sys
import time

PROFILES = os.path.expanduser("~/.hermes/profiles")
BUTLER = "g01-butler"
HOMEDIR = f"{PROFILES}/{BUTLER}"
ENVF = f"{HOMEDIR}/.env"
BACKUPS = f"{HOMEDIR}/backups"
HINDSIGHT_DIR = f"{HOMEDIR}/hindsight"
HINDSIGHT_CFG = f"{HINDSIGHT_DIR}/config.json"

BANK_ID = "g01-butler"
API_URL = "http://ga01:8888"


def main():
    print("=== g01-butler bank-isolation retrofix (t_fd8ca6f0 spec #5) ===")

    if not os.path.isdir(HOMEDIR):
        print(f"FAIL: {HOMEDIR} does not exist")
        return 1

    # ---------------------------------------------------------------- read .env
    with open(ENVF) as fh:
        lines = fh.read().splitlines()

    env_bank_lines = [i for i, l in enumerate(lines) if l.strip().startswith("HINDSIGHT_BANK_ID=")]
    token_lines = [i for i, l in enumerate(lines) if l.strip().startswith("TELEGRAM_BOT_TOKEN=")]
    has_real_token = bool(token_lines) and "PASTE" not in lines[token_lines[0]]
    print(f".env: {len(env_bank_lines)} HINDSIGHT_BANK_ID line(s); Telegram token: "
          f"{'REAL (must preserve)' if has_real_token else 'placeholder/absent'}")

    # ------------------------------------------------------- write config.json
    cfg_current = None
    if os.path.exists(HINDSIGHT_CFG):
        try:
            cfg_current = json.load(open(HINDSIGHT_CFG))
        except Exception as exc:
            print(f"WARN: corrupt {HINDSIGHT_CFG} ({exc}) — will overwrite")
    if cfg_current and cfg_current.get("bank_id") == BANK_ID and cfg_current.get("api_url") == API_URL:
        print(f"hindsight/config.json already correct (bank_id={BANK_ID})")
    else:
        if cfg_current is None or cfg_current.get("bank_id") != BANK_ID:
            os.makedirs(BACKUPS, exist_ok=True)
            if os.path.exists(HINDSIGHT_CFG):
                stamp = time.strftime("%Y%m%d-%H%M%S")
                shutil.copy2(HINDSIGHT_CFG, f"{BACKUPS}/hindsight-config.pre-retrofix.{stamp}.json")
                print(f"backup: {BACKUPS}/hindsight-config.pre-retrofix.{stamp}.json")
        if not os.path.exists(HINDSIGHT_DIR):
            os.makedirs(HINDSIGHT_DIR)
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
                BANK_ID: {"bankId": BANK_ID, "budget": "mid", "enabled": True},
            },
            "api_url": API_URL,
            "bank_id": BANK_ID,
            "recall_budget": "mid",
        }
        with open(HINDSIGHT_CFG, "w") as fh:
            json.dump(cfg, fh, indent=2)
            fh.write("\n")
        os.chmod(HINDSIGHT_CFG, 0o600)
        print(f"wrote {HINDSIGHT_CFG} (bank_id={BANK_ID}, mode local_external, api_url {API_URL})")

    # --------------------------------------------------------- scrub .env bank
    if not env_bank_lines:
        print(".env: no HINDSIGHT_BANK_ID line — already scrubbed")
    else:
        os.makedirs(BACKUPS, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(ENVF, f"{BACKUPS}/env.pre-gaudi-pilot-retrofix.{stamp}")
        print(f"backup: {BACKUPS}/env.pre-gaudi-pilot-retrofix.{stamp} (0600 preserved by copy2+chmod)")
        os.chmod(f"{BACKUPS}/env.pre-gaudi-pilot-retrofix.{stamp}", 0o600)
        new_lines = []
        removed = 0
        for l in lines:
            if l.strip().startswith("HINDSIGHT_BANK_ID="):
                removed += 1
                continue
            if l.strip().startswith("# Hindsight memory bank"):
                new_lines.append("# Hindsight memory bank — pinned in hindsight/config.json (bank_id "
                                 f"'{BANK_ID}', per-board butler bank, card t_fd8ca6f0).")
                new_lines.append("# HINDSIGHT_BANK_ID deliberately UNSET: env would win over config.json (#5171).")
                continue
            new_lines.append(l)
        with open(ENVF, "w") as fh:
            fh.write("\n".join(new_lines) + "\n")
        os.chmod(ENVF, 0o600)
        print(f"scrubbed {removed} HINDSIGHT_BANK_ID line(s) from .env (token untouched: "
              f"{'yes' if has_real_token else 'n/a'})")

    # -------------------------------------------------------------- verify
    with open(ENVF) as fh:
        final = fh.read()
    assert "HINDSIGHT_BANK_ID=hermes" not in final, "scrub failed"
    assert not any(l.strip().startswith("HINDSIGHT_BANK_ID=") for l in final.splitlines()), "any bank env remains"
    if has_real_token:
        assert any(("PASTE" not in l) and l.strip().startswith("TELEGRAM_BOT_TOKEN=") for l in final.splitlines()), \
            "token lost!"
    cfg = json.load(open(HINDSIGHT_CFG))
    assert cfg["bank_id"] == BANK_ID and cfg["api_url"] == API_URL and cfg["mode"] == "local_external"
    print("verified: .env has no HINDSIGHT_BANK_ID; config.json bank_id=%s; mode=%s" % (cfg["bank_id"], cfg["mode"]))
    print("\nRetrofix complete. (Effective for the live bot at next gateway restart — same restart as the gaudi-butler QR step.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
