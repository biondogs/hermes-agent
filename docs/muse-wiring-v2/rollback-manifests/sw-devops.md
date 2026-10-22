# Rollback manifest — `sw-devops` (MUSE-WIRING-V2 temp lane)

Card `default/t_5c5305bf`, operator GO 2026-10-22. Byte-exact pre-wire snapshot:
`backups/sw-devops.config.yaml.pre-muse` (sha256 `4e246420897ea4415d0796151f7e517478ab318fa5796e57bda228b70157684c`).

## Why this lane was wired

software-co release/ops engineer — compose/stack build-deploy-teardown execution; mechanical execution lane, production containers are deny-listed at the approvals layer.

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
    "glm53": {
      "context_length": 1000000
    },
    "qwen38-flash-fp8": {
      "context_length": 262144
    },
    "qwen38": {
      "context_length": 1000000
    }
  },
  "ssl_verify": false,
  "transport": "chat_completions"
}
```

## Revert command

```bash
cp /local/projects/software-co/docs/muse-wiring-v2/rollback-manifests/backups/sw-devops.config.yaml.pre-muse \
   /home/arch/.hermes/profiles/sw-devops/config.yaml
# verify: hermes -p sw-devops config check
# (next spawned worker for this profile re-resolves default=qwen38-flash-fp8)
```

Environment keys untouched (temp-lane law): the profile's `.env` is not part of
this change; muse auth rides the existing orb key the profile already uses.
