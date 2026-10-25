# HERMES CONFIG-DIVERGENCES — the record-why file

**Created:** 2026-10-24 · **Card:** PERF-PORT QW5 (t_36eda488) · **Basis:** HERMES-PERF-PORTABILITY-STUDY.md §B11 + full-fleet re-measurement 2026-10-24 (59 configs: root + 58 profiles, parsed with proper nested-yaml paths) · **Amended:** 2026-10-24 by the R10 config-hygiene sweep (t_fab224e9): §4 rewritten post-R3, §10 closed, rows 11–19 added.

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

## 4. Compression policy (`compression:` + `auxiliary.compression:`) — root base + R3 per-lane explicit blocks

- **What (re-measured 2026-10-24 post-R3, live read of all 59 configs):**
  - **Root** defines the fleet base block: `threshold 0.85, target_ratio 0.2, protect_last_n 20, micro_compact on, keep_first_n 3`.
  - **11 configs carry an explicit compression block** (live census t_fab224e9): root + the 8 heavy dev/eng lanes (`kanban-board-architect`, `kanban-worker`, `research`, `sw-architect`, `sw-dev-a/b`, `sw-qa`, `sw-reviewer`, `sw-ux`) mirroring the root block (`0.85 / 0.2 / protect 20`), plus `kanban-orchestrator` with its single override `protect_last_n: 30`. All other profiles run on the implicit default (threshold 0.75).
  - **Superseded (historical):** the pre-R3 override set documented here originally — `kanban-worker: protect_last_n 50` and `research: 50 / target 0.3 / threshold 0.6` — was REPLACED 2026-10-24 by the R3 per-lane explicit blocks above (COMPRESSION-RCA-2026-10-23 §7(d) table, landed by t_fe23cd4b with its own receipts + backup `~/.hermes/config-backups/r3-degr-20261024/`). The old 50-value tail-protection design is retired; do not reintroduce it without a new measured reason.
  - **1M-window caveat (RCA §7(d), standing):** `compression.threshold` on the 1 000 000-context lanes is a de-facto no-op today (aux model window 262 144 silently clamps the trigger) — don't "tune" those lanes until the aux model's window ≥ 1 M.
- **Why:** policy is deliberately single-sourced at root; the R3 explicit blocks equalize the heavy lanes at the root's measured-storm-safe trigger (explicit 0.85 vs implicit 0.75 → −29…−80 % compression events on those lanes, per the RCA's dwell arithmetic), and `kanban-orchestrator` keeps its bigger protected tail (30) for protocol integrity. `auxiliary.compression.model: qwen36-fast` + storm guard/cooldown machinery are R3's (c) items — see row 5 below and t_fe23cd4b's receipt for the degradation-mode config (`auxiliary.compression.fallback_model: qwen38`, `agent.compression_degraded_models: [qwen38-flash-fp8]`).

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
  is fenced to exactly its own board so cross-board crosstalk is impossible. **Full record
  (collapsed 2026-10-24, PERF-PORT R10 t_fab224e9): KANBAN-SYSTEM-AS-BUILT.md §5
  "Documented deviation — per-profile `kanban.board` pins"** — the record of truth for
  this deviation. (Note: `kanban:` keys belong in the GLOBAL config only for
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

## 10. Formerly-unrecorded divergences — CLOSED by the R10 sweep (2026-10-24, t_fab224e9)

The three items listed here as "not yet recorded" are now recorded (rows 11–12 + the
flagged entry below); the R10 full-fleet nested-path re-measurement (59 configs, raw
output attached to card t_fab224e9) is the formal tabulation the old text said was owed:

- **Per-profile toolset shaping** (`toolsets`, `agent.disabled_toolsets`, `platform_toolsets`,
  `approvals.deny`, `agent.max_turns` 100/150/200/250/300, `agent.reasoning_effort`
  low/medium/high) → recorded as row 11.
- **`delegation.model: qwen38-flash-fp8` at root** → recorded as row 12.
- **`sessions.retention_days: 60`, `model_catalog.ttl_hours: 24` at root** → retention_days
  recorded as row 13 (governed by the R7 policy); `model_catalog.ttl_hours: 24` remains
  **flagged-accepted-unattributed**: motivation not recoverable from history, effect is a
  24 h TTL on the model-catalog cache — harmless; revisit only if catalog staleness is
  ever observed.

## 11. Per-lane capability shaping (toolsets / disabled_toolsets / platform_toolsets / approvals.deny / max_turns / reasoning_effort) — fleet convention, RECORDED 2026-10-24

- **What:** each profile's toolset list, disabled-list, per-platform lists, approval deny
  lists, turn cap, and reasoning effort differ per lane (5 distinct `toolsets` patterns:
  butlers, meta pair, workers, research-ro, sw staff; butlers/auditors read-only-shaped;
  ops lanes carry docker/system deny-lists; workers carry git-destructive deny-lists).
- **Why:** least-privilege by design — butlers are terminalless, orchestrators
  kanban-only, research is read-only, ops lanes are fenced from infra-destroying
  commands. The roster in KANBAN-SYSTEM-AS-BUILT §3 is the authority; the R10 sweep
  output (card t_fab224e9) is the first full formal tabulation (22 varying paths,
  every one mapped to a recorded row or a roster-design convention). Changing any
  lane's toolset is a roster decision, not a hygiene fix.

## 12. `delegation.model: qwen38-flash-fp8` at root — RECORDED 2026-10-24

- **What/why:** delegate children ride the cheap generalist workhorse instead of the
  delegating session's (often frontier-priced) model — deliberate cost choice for
  mechanical subtasks. Related root keys in the same spirit: `delegation.provider: litellm`,
  `delegation.reasoning_effort: medium`, `delegation.max_concurrent_children: 10`.

## 13. `sessions.retention_days: 60` at root — RECORDED 2026-10-24 (governed by R7 policy)

- **What/why:** legacy knob from the pre-R7 era (`auto_prune` was `true` with this value —
  a live delete path, found and disabled 2026-10-24). Retention is now governed by
  HERMES-STATEDB-RETENTION-POLICY.md (ARCHIVE-NOT-DELETE; 60-day export window; weekly
  engine; card t_c8bd58a3). The knob itself is inert while `sessions.auto_prune: false`
  and is kept only so a future re-enable can't silently diverge from the policy window.

## 14. `security.redact_secrets: false` — INTENTIONAL operator deviation (⚠ never treat as hygiene drift)

- **What:** root config runs with secret redaction OFF; the gateway prints "Secret redaction: DISABLED …" at every start.
- **Why:** **standing operator canon** — redaction off is deliberate (confirmed by operator post-close note 2026-10-24 after the R10 card flipped it to `true` on a provenance-unknown assumption: "Secret redaction is off deliberately per standing operator canon, so it is not hygiene drift"). The R10 flip was **REVERSED** (revert routed to t_c0969a7f, before its bounce). Chat-platform egress stays force-scrubbed regardless (fails-closed egress scrub, upstream #23810), so this governs session JSONs/logs/internal state only.
- **Standing rule for every future config-hygiene sweep:** list `security.redact_secrets: false` as an INTENTIONAL deviation (this row); do not flag, do not flip. If the operator ever wants redaction on, that is an operator-issued change, not a hygiene fix.

## 15. Langfuse plugin — enabled with no credentials → DISABLED 2026-10-24 (R10, t_fab224e9)

- **What:** root `plugins.enabled` listed both `langfuse` and its legacy core-era alias
  `observability/langfuse` (same plugin; left-core migration keeps the alias), but ZERO
  Langfuse credentials exist anywhere in the fleet (root + 58 profile .env files and the
  R2 secrets manifest all checked). Every gateway start warned "missing credentials …
  traces will NOT be emitted" and the plugin never emitted one trace.
- **Action:** `hermes plugins disable langfuse` (both keys go with it). Rollback:
  `hermes plugins enable langfuse` + add HERMES_LANGFUSE_PUBLIC_KEY/SECRET_KEY through
  the R2 secrets manifest (secrets.yaml + blueprint + vault), never a raw .env edit.

## 16. api_server public bind (`API_SERVER_HOST=0.0.0.0`) — deliberate, ACCEPTED, RECORDED 2026-10-24

- **What/why:** the API server binds all interfaces to serve the remote dashboard
  (CORS origins include `http://100.85.215.88:3000`); access requires `API_SERVER_KEY`;
  terminal backend is `local` (unsandboxed) — the combination prints a "network-accessible
  AND unsandboxed" gateway-start warning **by design**. Host firewall posture is
  operator-owned (aistack/host law: agents don't touch firewalling).
- **Status:** accepted deviation; the warning line stays. If the dashboard ever moves to
  localhost-only, tighten the bind in the R2 blueprint (bp_root) + `API_SERVER_HOST`.

## 17. `camofox` in `platform_toolsets` (cli/slack at root; some profiles) — forward-compat spelling, DO NOT "FIX"

- **What:** `platform_toolsets.cli/.slack` name toolset `camofox`, which `hermes config
  check` flags as "unknown toolset" on cores that still bundle the Camofox browser
  backend (plugin inactive ⇒ name unresolvable).
- **Why keep:** `left_core_migration` explicitly defines camofox as a plugin toolset
  (`replaces_toolsets`: core `browser` = browser_exec; Camofox's tools = plugin `camofox`)
  and expects saved platform lists to name the plugin spelling — it is the post-left-core
  name. The config-check warning is transitional and disappears on a camofox-less core
  or once the plugin activates (it stays inactive with "this Hermes core still bundles
  the Camofox browser backend" while bundled).

## 18. Provider-name case split `custom:litellm` (root) vs `custom:LiteLLM` (58 profiles) — cosmetic

- **What:** root `model.provider` is `custom:litellm`, the 58 profiles use
  `custom:LiteLLM`; every `providers:` block is keyed lowercase `litellm:`. Resolution is
  case-insensitive (fleet runs fine; `config check` rc=0 both spellings).
- **Status:** harmless spelling drift from profile-creation history. Do not churn 59
  files for it; normalize opportunistically via the PROF-SWEEP byte-sync machinery if
  it ever runs again.

## 19. `telemetry.shared_metrics` off on 3 profiles (distiller, kanban-board-architect, plugin-ab) — accepted opt-outs, RECORDED 2026-10-24

- **What:** `enabled/send: false` on exactly these three (root + all others: true).
- **Why:** operator-usage telemetry deliberately off on the meta/gate lanes and the A/B
  probe profile (probe isolation is obvious for plugin-ab; the distiller/architect
  opt-outs predate 2026-10-24 records and are kept as deliberate judgment-seat opt-outs
  — flipped candidates only if the operator asks for uniform telemetry).


---

*Measurement provenance: re-measured 2026-10-24 by t_36eda488 pre-flight (qw_preflight.py / qw_docfacts.py in the card workspace); study baseline HERMES-PERF-PORTABILITY-STUDY.md §B11 (commit 757b729). Re-measured again 2026-10-24 by the R10 sweep (t_fab224e9: deprecated-key collectors from hermes_cli.doctor_config + nested-path divergence scan, raw output on the card). Rollback for any row: estate hourly git snapshot.*
