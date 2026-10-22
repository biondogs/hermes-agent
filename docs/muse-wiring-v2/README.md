# MUSE-WIRING-V2 (temp lane) — rollback manifests

Card `default/t_5c5305bf` · Operator GO 2026-10-22 · architect jurisdiction
(mirrors the archived `t_2d482db4` law and the `t_deb6eb11` teardown pattern)

## Scope

Two legs, everything reversible:

- **Leg A — aistack/orb exposure**: additive `muse` model entry + `fallbacks:
  muse → [qwen38-flash-fp8]` in `/local/compose/aistack/litellm/config.yaml`
  (git repo `biondogs/ai-stack`, commit `0ff1adb`). Applies on the next
  `aistack-litellm-1` container restart (operator command — see below).
- **Leg B — profile wiring**: `default=muse` + explicit `context_length:
  262144` pin + `fallback_model: → qwen38-flash-fp8` on 8 strength-matched
  high-throughput mechanical lanes (list + justification in
  `wired-profiles.md`).

Judgment seats **STAY OFF muse** (glm53 + qwen38-flash-fp8 command path):
kanban-orchestrator, kanban-board-architect, g0[12]-orchestrator/planner,
g0[12]-auditor, sw-architect, sw-reviewer, g01/g02-ops, gaudi decision seats,
distiller, g01-auditor — untouched by this change.

## Per-profile manifests

Each `rollback-manifests/<profile>.md` records the verbatim prior `model:` +
`fallback_model:` + `providers.litellm:` blocks and the exact revert command.
Byte-exact pre-wire config snapshots live in `rollback-manifests/backups/`
(`sha256` recorded in each manifest).

## Teardown (operator-triggered, or when the Azure support reply makes the
temp lane moot)

1. **Profiles** — restore each wired profile from its backup:
   ```
   cp docs/muse-wiring-v2/rollback-manifests/backups/<profile>.config.yaml.pre-muse \
      /home/arch/.hermes/profiles/<profile>/config.yaml
   ```
   8 profiles: kanban-worker, g01-scribe, g02-scribe, sw-docs, sw-dev-a,
   sw-dev-b, sw-qa, sw-devops.
2. **aistack/orb** — revert the file config in the ai-stack repo:
   ```
   git -C /local/compose/aistack revert 0ff1adb
   docker restart aistack-litellm-1   # remove muse from /v1/models on reload
   ```
   (No restart needed if the temp lane is being torn down together with the
   container anyway.)
3. **Fleet lane on gpu418** — per `TEARDOWN-MANIFEST-MUSE-FP4-REVIVE.md`
   (gargantua02 board, card `t_deb6eb11`): delete `rnd-bench/rnd5-muse-nvfp4-tp8`
   deployment + `rnd5-muse-nvfp4-api` service (NodePort 30188), remove weights
   `/mnt/models/hf/rnd5-muse-spark/Muse-Spark-Open-816B-A42B-NVFP4`, and the
   `muse` entry + `fallbacks` in the fleet ConfigMap `gateway/litellm-config`,
   then `kubectl -n gateway rollout restart deploy/litellm`.

## Honest limitations (receipted on the card)

- `fallback_model` in profile configs is a Hermes-side failover chain
  (fires on 429/5xx/connection failures from orb). It has never been live in
  this fleet before this card; the muse-scaled-down fallback verification is
  pending the Leg A restart — see card acceptance criteria.
- Row-level ("trip") LiteLLM fallbacks on orb would need the aistack master
  key (managed-admin-only on this install; ga01 holds only a virtual
  llm-route key). Not attempted; the file-config `litellm_settings.fallbacks`
  chain is the documented path and applies to this specific proxy process.
