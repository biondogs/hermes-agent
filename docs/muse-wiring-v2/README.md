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

0. **orb deployment (LIVE state, run 30)** — muse is live on orb as a **DB
   deployment** (added via the zero-downtime admin endpoint `/model/new` on
   2026-10-22, model_id `93ea75f5-b777-4b9d-bf6a-9c375fde132c`; upstream
   `openai/muse` @ `http://10.99.192.6:30100/v1` — the fleet gateway IP, since
   `gpu416` does not resolve inside the container; upstream key = fleet
   gateway master key, encrypted at rest in `LiteLLM_ProxyModelTable`).
   Remove it WITHOUT touching the file config or restarting anything:
   ```bash
   curl -s -X POST https://orb.arch.jhu.edu/model/delete \
     -H "Authorization: Bearer $ORC_MASTER_KEY" \
     -H "Content-Type: application/json" \
     -d '{"id": "93ea75f5-b777-4b9d-bf6a-9c375fde132c"}'
   ```
   (`$ORC_MASTER_KEY` = the aistack container's `LITELLM_MASTER_KEY`.)
   A subsequent `container restart` is NOT required for removal — but if one
   happens for other reasons, note the file-config entry (see the advisory
   below) reloads muse from the file path.

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

   > **RESTART ADVISORY (run 30 finding, file config NOT touched per operator
   > directive)**: as committed (0ff1adb), the file entry has two defects that
   > only matter if the container is ever restarted/recreated: (a) it points at
   > `http://gpu416:30100/v1` — the hostname does NOT resolve inside the
   > container (use `http://10.99.192.6:30100/v1`); (b) its upstream model is
   > `openai/muse-spark-816b-nvfp4`, which the fleet gateway rejects (the
   > gateway alias is `muse`; correct upstream is `openai/muse`). Until the
   > operator amends the file, any restart will break the muse alias that the
   > live DB deployment currently serves correctly. The DB deployment (step 0)
   > survives restarts and continues to serve.
3. **Fleet lane on gpu418** — per `TEARDOWN-MANIFEST-MUSE-FP4-REVIVE.md`
   (gargantua02 board, card `t_deb6eb11`): delete `rnd-bench/rnd5-muse-nvfp4-tp8`
   deployment + `rnd5-muse-nvfp4-api` service (NodePort 30188), remove weights
   `/mnt/models/hf/rnd5-muse-spark/Muse-Spark-Open-816B-A42B-NVFP4`, and the
   `muse` entry + `fallbacks` in the fleet ConfigMap `gateway/litellm-config`,
   then `kubectl -n gateway rollout restart deploy/litellm`.

## Verification receipts (run 30, all four acceptance items PASS)

1. **orb chat `model=muse` returns**: 200 via the wired-profile client key,
   `model: muse`, 60 completion tokens (probe `patch_orb_muse2.py` receipt).
2. **Spawned worker on a wired seat runs muse**: fresh
   `hermes -p kanban-worker chat --oneshot` (sanitized env) answered
   `WORKER-MODEL-RECEIPT model=muse provider=custom` (probe `spawn_probe.py`).
3. **Muse-scaled-down fallback test**: orb deployment api_base temporarily
   patched to an unroutable IP (upstream conn failure ≡ muse scaled down);
   spawned kanban-worker's turn printed `⚠️ Model fallback: muse via custom
   unavailable (provider server error); using qwen38-flash-fp8 via litellm`
   and answered `FALLBACK-PROBE-REPLY model=qwen38-flash-fp8`; api_base
   restored, muse chat 200 again (probe `fallback_negative_test.py`).
4. **All 8 wired profiles pass `hermes -p <p> config check`; `fallback list`
   shows Primary muse → qwen38-flash-fp8. Unwired judgment seats verified
   untouched (kanban-orchestrator/g01-ops/g02-ops = qwen38-flash-fp8;
   sw-architect/sw-reviewer = glm53; no other profile mentions muse).**

## Honest limitations (receipted on the card)

- The live muse alias is a **DB deployment** (created via `/model/new`), not
  the committed file entry — the file entry carries the two restart-blocking
  defects documented in the advisory above and must be amended before any
  container restart/recreate (operator action; config file untouched per
  2026-10-22 directive).
- Row-level ("trip") LiteLLM fallbacks on orb would need the aistack master
  key (managed-admin-only on this install; ga01 holds only a virtual
  llm-route key). Not attempted; the file-config `litellm_settings.fallbacks`
  chain is the documented path and applies to this specific proxy process.
