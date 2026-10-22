# Rollback manifest — `kanban-worker` (MUSE-WIRING-V2 temp lane)

Card `default/t_5c5305bf`, operator GO 2026-10-22. Byte-exact pre-wire snapshot:
`backups/kanban-worker.config.yaml.pre-muse` (sha256 `e9ef57f75f2019dd0b480cb8bfcdde7d1e3a6f3a44064d32ab9d25ffd4bef7b1`).

## Why this lane was wired

Global default_assignee — the highest-volume grunt lane (fallback execution across all boards). Mechanical card dispatch, short tool loops; benefits most from compute headroom while Azure ticket is pending.

## Wired state (current)

- `model.default: muse` via `custom:LiteLLM` (orb), provider endpoint unchanged
  (`https://orb.arch.jhu.edu/v1`, key `${LITELLM_API_KEY}` via profile `.env`)
- `model.context_length: 262144` — EXPLICIT pin from the serving config
  (`--max-model-len=262144` on the gpu418 vLLM deployment; orb aliases hide ctx)
- `providers.litellm.models.muse.context_length: 262144`
- `fallback_model: [{provider: LiteLLM, model: qwen38-flash-fp8}]` (new key;
  prior value: null)

## Prior state (verbatim)

### model block (pre-wire)

```json
{
  "default": "qwen38-flash-fp8",
  "provider": "custom:LiteLLM",
  "max_tokens": 65536,
  "context_length": 262144
}
```

### providers.litellm block (pre-wire)

```json
{
  "api": "https://orb.arch.jhu.edu/v1",
  "name": "LiteLLM",
  "api_key": "${LITELLM_API_KEY}",
  "models": {
    "qwen38-flash-fp8": {
      "context_length": 262144
    },
    "qwen38": {
      "context_length": 1000000
    },
    "nemo-fp4": {
      "context_length": 1000000
    },
    "gemma4-fp4": {
      "context_length": 262144
    }
  },
  "ssl_verify": false,
  "transport": "chat_completions"
}
```

## Revert command

```bash
cp /local/projects/software-co/docs/muse-wiring-v2/rollback-manifests/backups/kanban-worker.config.yaml.pre-muse \
   /home/arch/.hermes/profiles/kanban-worker/config.yaml
# verify: hermes -p kanban-worker config check
# (next spawned worker for this profile re-resolves default=qwen38-flash-fp8)
```

Environment keys untouched (temp-lane law): the profile's `.env` is not part of
this change; muse auth rides the existing orb key the profile already uses.
