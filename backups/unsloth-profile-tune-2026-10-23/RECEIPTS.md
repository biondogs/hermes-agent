# UNSLOTH-PROFILE-TUNE receipts — t_7601b273 (2026-10-23)

Profile: `~/.hermes/profiles/unsloth-litellm` (imported 2026-10-23 02:44).
Pre-mutation backup: `~/kanban-backups/unsloth-profile-tune-20261023T031041Z/unsloth-litellm-full.tar.gz`
(non-secret `.pre` copies in this directory). Converge script:
`scripts/tune_unsloth_profile_converge.py` (idempotent, re-runnable).

## Findings applied (7/7 from card + 1 new)

1. **Identity**: SOUL.md was a verbatim orchestrator clone (verified: 46 lines of
   butler-first doctrine). Replaced with purpose-built SOUL (Unsloth Studio
   manager, LiteLLM DB config via MCP, non-disturbance law, explicit
   no-orchestration/no-meta-work boundaries). Routing description replaced
   (was the cloned 'Orchestrator: ...' text in config.yaml; profile.yaml now
   carries a capability-first, boundary-last description; applied via
   neutral-env CLI, on-disk readback OK, architect's own profile.yaml
   un-clobbered).
2. **Toolsets**: trimmed [kanban, memory, session_search, terminal, file,
   code_execution, web] → [file, terminal, code_execution, web, memory,
   skills, mcp-unsloth_studio]; `agent.disabled_toolsets` set as the
   end-of-pipeline complement (24 toolsets incl. kanban, delegation, cronjob,
   browser, computer_use); `platform_toolsets.cli` pinned identically.
   Verified via `hermes -p unsloth-litellm tools list`: exactly the intended
   surface, MCP server listed.
3. **Bloat**: 52 → 13 top-level config keys (13,721 B → 146 lines).
   Removed: cron.script_timeout_seconds, personalities, max_live_sessions,
   verify_on_stop, gateway tuning, dashboard block (incl. duplicated root
   secrets), delegation, stt/tts, curator, model_catalog, streaming, display,
   sessions, lsp, onboarding, updates, checkpoints, tool_loop_guardrails,
   goals, telemetry, smart_model_routing, known_plugin_toolsets, the
   `kanban:` dispatcher block (global-only), comment cruft. Kept: tuned aux
   models via litellm, compression, plugins [hindsight, web/firecrawl,
   web/searxng], web backends (firecrawl/searxng @ ga01).
4. **Provider**: `model.provider` `custom:litellm` → `litellm` (canonical named
   key; `custom:litellm` fails resolution — name case is LiteLLM). Aux
   `web_extract` `custom:LiteLLM` → `litellm`. Ctx pins kept
   (qwen38: 1000000, qwen38-flash-fp8: 262144). Live proof: headless probe
   replied (see verification).
5. **MCP**: server entry kept (`http://10.99.136.90:8000/mcp/`, Bearer
   ${UNSLOTH_API_KEY}). **`.env` carries a placeholder key
   (`REPLACE_WITH…`) — no real key exists anywhere on this host.** Server
   responds 401 with: "Unsloth Studio MCP needs an Unsloth Studio API key
   (sk-unsloth-…). Create one in Settings > API." Authenticated discovery is
   therefore PENDING OPERATOR KEY — the only unfinished acceptance item.
6. **Bank**: dedicated bank `hb-unsloth-studio` created server-side
   (PUT upsert, HTTP 200, mission set). `hindsight/config.json` flipped
   `hermes` → `hb-unsloth-studio` (bank_id + banks{}), NO `.env` pin (0
   lines, post-cutover convention). Canary PASS: explicit retain one-shot →
   4 facts, 3 canary content hits, **0 leaks into shared `hermes`**.
   BANK-MAP.md updated with the new lane.
7. **Safety**: `approvals.deny` (23 fnmatch globs): compose down/stop/restart/
   up (broad — bare `compose up` recreates the whole aistack on this host),
   docker stop/restart/kill/rm of litellm/orb, systemctl stop/restart of
   litellm/orb, psql DROP/TRUNCATE/DELETE/ALTER, git push --force/reset
   --hard. `approvals.smart_policy` escalates anything touching the LiteLLM
   DB or the container stack and channels DB config to the studio MCP tools.

## Verification checklist (card acceptance)

- yaml.safe_load parses (roundtrip assert in converge script) — PASS
- no moa (grep=0), no ssl_verify, no base_url/api_key in model:, no
  /home/arch paths, no kanban: section, no personalities/dashboard/cron — PASS
- provider canonical + resolves: `hermes -p unsloth-litellm chat -q
  "Reply with exactly: OK"` → **OK** in 3s (1 api call) — PASS
- `config check` — version 51 ✓, no required issues — PASS
- description set, routing-safe, boundary-last; on-disk readback — PASS
- SOUL reflects purpose + non-disturbance law — PASS
- Headless verify succeeded with `env -i` scrubbed environment (no
  HERMES_HOME set; pitfall 24), no gateway restart performed — PASS
- Bank canary retain + server-side readback + shared-bank leak check — PASS
- MCP tools listed (config + tools list) — PASS; **authenticated discovery —
  PENDING (needs real key from Unsloth Studio Settings > API, into
  `~/.hermes/profiles/unsloth-litellm/.env` line `UNSLOTH_API_KEY=`)**
- Backup before mutation — DONE (full tar + .pre copies)

## Notes

- Toolset judgment call: added `skills` beyond the card's list (procedural
  skill loading is standard worker operation; trim if unwanted).
- Aux tasks trimmed to those reachable from this profile's surface
  (compression, skills_hub, approval, mcp, title_generation,
  memory_query_rewrite, web_extract). Vision/tts/kanban/curator aux dropped
  with their toolsets.
- Out of scope per card: `kworker-muse-probe`, `coding` (operator flagged
  separately 2026-10-23 02:43).
