# HERMES CONFIG-DIVERGENCES — the record-why file

**Created:** 2026-10-24 · **Card:** PERF-PORT QW5 (t_36eda488) · **Basis:** HERMES-PERF-PORTABILITY-STUDY.md §B11 + full-fleet re-measurement 2026-10-24 (59 configs: root + 58 profiles, parsed with proper nested-yaml paths)

**Purpose:** every deliberate divergence from "plain default Hermes config" gets a recorded
reason here, so nobody "fixes" a pin that is load-bearing, and nobody re-learns why the
fleet looks the way it does. When you change a divergence, change its row here in the
same commit/opus. Numbers below were re-measured 2026-10-24; they are counts of configs,
not prose estimates.

**Conventions that are NOT divergences** (universal in all 59 configs, single source of
truth, no per-profile variation to record): model/provider/auxiliary structure,
`timezone: America/New_York`, memory provider hindsight, kanban stream-notify settings.

---

## 1. `model.max_tokens: 65536` — 58 of 59 configs

- **What:** generation cap pinned at 65536 everywhere except `plugin-ab` (8192 — the
  A/B harness profile caps cheap throwaway runs deliberately).
- **Why:** the fleet's workhorse models (qwen38 family, glm53 via orb/LiteLLM) accept up
  to 64 K output tokens; agents emit long card bodies, receipts and diffs in one turn, and
  a lower cap silently truncates them mid-JSON. The pin is the *ceiling request*, not a
  per-turn cost — output is not pre-allocated.
- **Known caveat (study B11):** some LiteLLM validation paths reject max_tokens values
  above model-specific limits — this exact class surfaced as agent-init
  `invalid_params` during the plugin A/B harness (t_4ddfc8b8). Do not raise it; if a
  model refuses it, pin that profile's value down, not the fleet's.

## 2. `model.context_length` explicit pins — 31 configs @ 262144, 28 configs @ 1000000

- **What:** every profile pins its context window explicitly instead of letting Hermes
  auto-detect. glm53 and qwen38-full lanes pin 1 000 000; qwen38-flash-fp8, qwen36-fast
  and mixed lanes pin 262 144. Per-alias pins also live under
  `providers.litellm.models.*`.
- **Why:** our models are served through a custom alias provider (`custom:litellm` /
  `https://orb.arch.jhu.edu/v1`) that **hides model metadata**, so the gateway cannot
  auto-detect context windows — without the pin it assumes a small default and either
  over-triggers compression or over-sends. Explicit pins are the only reliable signal.
  (QWEN36-FAST-CTX-PROBE-2026-10-23.md measured qwen36-fast's real window to set its pin.)

## 3. `providers.litellm.ssl_verify: false` — 53 profiles

- **What:** TLS certificate verification disabled on the LiteLLM provider block for the
  worker/research/auditor/sw lanes (butlers and a few others run with verification on).
- **Why:** orb.arch.jhu.edu serves a JHU-internal CA that is not in the default trust
  store; `HERMES_CA_BUNDLE` is exported in 71 .env files but not every HTTP client in
  the inference path honors it. Disabling verification is the pragmatic fix on the
  trusted internal network. **Security tradeoff, accepted and recorded** — revisit under
  PERF-PORT R4 (per-host overlay + CA plumbing) rather than silently.

## 4. Compression policy (`compression:` section) — root + 3 heavy-lane overrides

- **What:** root defines the fleet policy: `threshold 0.85, target_ratio 0.2,
  protect_last_n 20, protect_first_n 3, micro_compact on`. Only three profiles override,
  each for measured token weight (study B6):
  - `kanban-orchestrator`: `protect_last_n: 30`
  - `kanban-worker`: `protect_last_n: 50`
  - `research`: `protect_last_n: 50, target_ratio: 0.3, threshold: 0.6`
- **Why:** policy is deliberately **single-sourced at root** so a fleet behavior change
  is one edit; the three overrides exist because those lanes run 3–18 K-token system
  prompts and 2–5 M cumulative input per session — they need a bigger protected tail
  (protocol integrity) and, for research, an earlier trigger + softer ratio because its
  sessions compress rarely and hard otherwise.

## 5. `auxiliary.compression.model: qwen36-fast` — pinned on ALL 59 configs ⚠ load-bearing

- **What:** every config pins the compression aux model to qwen36-fast.
- **Why:** 2026-10-23 storm (study B7): 74 compression calls were routed to
  **qwen38-flash-fp8** — 49 InternalServerErrors (~66% fail), every failure a 90 s
  timeout + retry, all in one day. qwen38-flash-fp8 is an excellent main-lane model and
  a catastrophically bad *compression* model at obese inputs. **Never unpin this, never
  point compression at the main model, and note the aux→main fallback path**
  (`agent/context_compressor.py:3772 _fallback_to_main_for_compression`, telemetry class
  `aux_model_fallback`) which silently lands compression on the session's main model
  when the aux model fails once.
- **Tripwire (QW3, live since 2026-10-24):** `scripts/compression-tripwire.py`, daily
  no-agent cron `compression-tripwire` (09:07 ET, job 8764ebf460b6), Telegram-delivered —
  alerts on ANY `aux_task: compression` ledger row touching qwen38-flash-fp8.

## 6. `fallback_model` (top-level) — 8 profiles only

- **What:** g01-scribe, g02-scribe, kanban-worker, sw-dev-a, sw-dev-b, sw-devops,
  sw-docs, sw-qa — all `[{provider: LiteLLM, model: qwen38-flash-fp8}]`.
- **Why:** these are the production workhorse lanes that must survive a primary-model
  outage by failing over to the orb default instead of dying. Deliberately **not**
  fleet-wide: failover chains multiply unpredictability, and the fixed-role lanes
  (butlers, auditors, watchers, orchestrators) prefer dying loudly over silently
  answering on a different model.

## 7. `kanban.board` pins in the 5 butler configs — DOCUMENTED DEVIATION (not a defect)

- **What:** g01-butler→gargantua01, g02-butler→gargantua02, gaudi-butler→gaudi,
  sjproto-butler→skipjack-prototype, swco-butler→software-co.
- **Why:** local hotfix `602ea0a874` (per-profile board pin + butler fence) — each butler
  is fenced to exactly its own board so cross-board crosstalk is impossible. Full record:
  KANBAN-SYSTEM-AS-BUILT.md. (Note: `kanban:` keys belong in the GLOBAL config only for
  every profile *except* this documented butler-pin case.)

## 8. GitHub token spelling: `GH_TOKEN` only (convention, enforced 2026-10-24)

- **What/why:** gh CLI reads both spellings (GH_TOKEN takes precedence); the fleet
  carried both `GH_TOKEN=` and a value-identical `GITHUB_TOKEN=` line in 5 profile .env
  files. Consumer check (scripts, cron/jobs.json, git-hooks, config expansion, bashrc,
  crontab — 2026-10-24) found **zero** references to either spelling by name, and all
  values hash-identical fleet-wide → the duplicate `GITHUB_TOKEN=` lines were removed
  from distiller, kanban-board-architect, kanban-orchestrator, kanban-worker, research
  (root was already single-spelled). 33 stale `backups/*/.env` copies deleted in the
  same op (secrets sprawl, study A3). **Rule: new GitHub token consumers use GH_TOKEN.**

## 9. Probe profiles stripped of shared platform creds — 2026-10-23 (VERIFIED 2026-10-24)

- **What:** `coding` and `kworker-muse-probe` previously carried copies of the default
  profile's TELEGRAM/SLACK bot credentials, producing 4 duplicate-credential errors at
  every gateway start ("one credential cannot be consumed twice") and refusing the
  duplicate platform starts.
- **Resolution + verification:** creds stripped and the two known-broken probe profiles
  emptied (dirs empty since 2026-10-23 23:44, no registry entries); the 2026-10-24
  post-bounce gateway startup logged **zero** duplicate-credential warnings (last such
  error in gateway.log: 2026-10-23 16:47:45). Recorded here because the 10-23 bounce
  banner still shows the warnings — that banner predates the fix.

## 10. Not yet recorded (surveyed as divergent, reason unknown at time of writing)

- Per-profile `agent.disabled_toolsets` lists and `platform_toolsets` differences
  (least-privilege shaping per lane — spot-checked sane, never formally tabulated).
- `delegation.model: qwen38-flash-fp8` at root (delegate children ride the cheap
  workhorse — deliberate cost choice, unrecorded until now).
- `model_catalog.ttl_hours: 24`, `sessions.retention_days: 60` at root — defaults
  changed at some point; original motivation not recoverable from history. Flag for the
  R10 config-hygiene pass if it matters.

---

*Measurement provenance: re-measured 2026-10-24 by t_36eda488 pre-flight
(qw_preflight.py / qw_docfacts.py in the card workspace); study baseline HERMES-PERF-PORTABILITY-STUDY.md §B11 (commit 757b729). Rollback for any row: estate hourly git snapshot.*
