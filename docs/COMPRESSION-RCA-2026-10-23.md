> Status: superseded by hermes-estate/docs/OPERATIONS.md §8 (compression posture) + ER2-C leg — RCA kept as record (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# COMPRESSION-RCA — the 2026-10-23 compression storm (PERF-PORT R3 b/c/d)

- **Task:** kanban t_2cc1a7b3 (research), follow-on to the R3 measurement pass (t_99611d63) and plan `HERMES-PERF-PORTABILITY-STUDY.md` @ 757b729 (operator GO 2026-10-24).
- **Scope:** read-only root cause of the 10-23 storm (49× ~90s `InternalServerError` compression calls on `qwen38-flash-fp8`, 66% failing), plus **proposals (NOT applied)** for (c) a degradation mode that avoids retry storms and (d) per-lane `compression.threshold` changes with numbers. Config edits are handed back to the architect lane. Zero configs touched, zero restarts, zero public writes by this card.
- **Clocks:** all epoch-derived times below are **UTC**. Log-file timestamps (`agent.log`, `errors.log`, `agent.log.1`) were verified clock-UTC by cross-matching three events against `calls.jsonl` epoch timestamps (±2s). Directory-name stamps (`aux-sync-20261023_195137`) are **America/New_York** (fleet tz per commit 6b49f67).

---

## 1. Executive summary

**Root cause: a pre-pin config, not a fallback bug and not an orb outage.** Every Hermes config on the fleet — root `/home/arch/.hermes/config.yaml` and every profile — explicitly pinned `auxiliary.compression.model: qwen38-flash-fp8`. That model is the fleet's *main workhorse*: reasoning-enabled by default, it answers compression prompts with ~1:1-length summaries (observed output ≈ input, 14–18k tokens), which take >90 s to decode. On 10-23, one deployment path behind the orb LiteLLM proxy was killing long generations at ~90 s with HTTP 500; the root orchestrator session's compression calls kept landing there. Hermes retried each event up to 3× at ~90 s each, the context stayed over-threshold after total failures, and the next turn re-triggered — a self-sustaining retry storm for 18h33m.

The `_summary_model_fallen_back` path was **not involved** (zero fallback log lines across storm-window logs; and on profiles the main model is *not* `qwen38-flash-fp8`, so a fallback-to-main could not have produced these calls). There is **no feasibility-fallback routing** in the tree. It **can recur** through specific open vectors (§6), the sharpest being: root's main model *is* `qwen38-flash-fp8`, and the compression fallback-to-main path retries main **immediately, no cooldown** — so any future `qwen36-fast` compression outage re-routes compression straight back into the exact storm shape.

The storm ended via a two-wave aux re-pin: root `compression`→`qwen36-fast` between 23:25–23:44Z on 10-23, fleet-wide aux byte-sync backed up at `aux-sync-20261023_195137` (19:51 EDT = 23:51Z), then — after probe t_7cb89ed9 (10-24 02:12Z) revealed `qwen36-fast` was really capped at 131,072 on gh201 — the deployment + catalog raise to 262,144 (t_d5916d8a / t_87165309, 10-24 03:32–03:52 EDT). Since then: zero `qwen38-flash-fp8` compression calls in any profile log on 10-24; root compressions run 5–23 s.

---

## 2. Storm anatomy (verified numbers)

Primary source: `/home/arch/.hermes/plugin-data/aux-ledger/calls.jsonl` (aux-ledger plugin ledger; first record is 10-23 04:52Z — the storm may predate the ledger by an unknown margin; §7.4 of the R3 measurement pass, t_99611d63, separately measured 55 compression calls >60 s in 10-22/23 log data, consistent with this window being a subset).

- **Window:** first attempt starts 10-23 **04:52:30Z**, last bad call chain completes 10-23 **23:25:05Z** → **18 h 33 m**.
- **Victim:** a single session — `20261008_201220_1cc05163`, the **root/default-profile gateway orchestrator session** (HERMES_HOME `/home/arch/.hermes`, Telegram-linked operator chat, `gateway.run` auto-decomposition across boards, 87k-message session started 10-08). All 74 storm ledger rows carry this `session_id`, `aux_task=compression`, `model=qwen38-flash-fp8`, `provider=litellm` (orb.arch.jhu.edu).
- **Traffic:** **74 compression API calls** in **≈30 events** (attempt chains; event cadence ≈ every 37 min). **49 failed** (66%): `error_type=InternalServerError`, durations 84.7–92.9 s (mode 90.0–90.1 s), `usage=null` (killed before completion).
- **5 events exhausted all 3 attempts and compressed nothing** (session stayed above threshold): chains ending 04:57:01Z, 20:39:43Z, 21:14:20Z, 22:06:17Z, 23:18:33Z.
- **"Successes" inside the storm are diagnostic gold:**
  - ~15 retry-at-1/2 "successes" at **0.05–3.4 s** with *identical* usage to the attempt that just failed (e.g. 14,585 in / 16,123 out at both 90 s-fail and 0.148 s-"success") → served from a proxy-side response cache: the bad deployment had already *computed* the summary before its response was killed.
  - 5 full successes at **87.0 / 103.5 / 116.0 / 204.6 / 229.3 s** (prompts 39,974–55,296 tokens) → the ~90 s kill was **not a uniform proxy timeout**: same session, same provider entry, successes and failures interleaving (e.g. 87 s success at 14:4xZ, 90 s fail at 14:4xZ minutes later; 126.3 s success from swco-butler at 13:54Z vs 90 s kill in root at 13:57Z). Best-supported explanation: **orb load-balances `qwen38-flash-fp8` across multiple deployments and at least one path kills ~90 s+ generations with 500** (consistent with the 10-22 21:16–21:40Z prelude in `errors.log:2470,2555`: `502 Server Error … nginx/1.27.4` and `Hosted_vllmException … Cannot connect to host <upstream>:8001` on the same provider). Component attribution inside orb is **medium confidence** — orb runs off this host; no orb-side logs here.
- **Output shape:** on every completed `qwen38-flash-fp8` compression call, **output ≈ input (ratio 1.0–1.15, 14–18k tokens out)** — the model ignored the 20 %-budget summary prompt and (pre-pin config had no `reasoning_effort: none`) burned reasoning tokens on top (e.g. 340 reasoning tokens on a partial run). This is why *only compression* saw the >90 s tail: main-lane chat on the same model finishes under 90 s and never met the ceiling.
- **Cost:** ≈ **74 min** of failed wall-clock GPU generation (49×90 s) + ≈14 min slow successes ≈ **87 min** of compression time in one session over 18.5 h. Rough inference: ~49×15k ≈ **0.7 M output tokens generated-then-discarded** (estimate from cached-success usage figures; ledger usage on failures is null). Operator-visible latency was capped by the gateway hygiene 10 s turn-hold (compression runs as a watermark-fenced background worker; abandoned holds don't block turns) — but the storm kept *failing* to compress while burning capacity every ~37 min.
- **Prelude (10-22):** the same root session had approval-lane hard-fails on orb (`Connection error`, 502, `:8001` unreachable, `errors.log` 2470–2571, 10-22 21:16–21:40Z) — the deployment pathology predates the compression storm by a day.

## 3. Fleet exposure (not just root)

- **Root/default profile:** the storm above. Current config confirms the fix: `auxiliary.compression.model: qwen36-fast`, `reasoning_effort: none`, `context_length: 262144` (+ `providers.litellm.models.qwen36-fast.context_length: 262144, max_tokens: 32768`, the t_87165309 catalog repin).
- **Profiles (slow-success, no failure ledger):** compression telemetry on `qwen38-flash-fp8` at **31–126 s** per call with `effective_threshold 196608` (= built-in default 0.75 × 262,144 — profiles carry *no* compression tuning block). Confirmed on **10-23**: `swco-butler` (10 events, 31.6–126.3 s), `sw-dev-a` (5), `sw-dev-b` (2), `sw-reviewer` (2), `g02-butler` (1). Same misconfiguration in telemetry on surrounding late-Oct days: `sw-ux`, `sw-architect`, `sj-ops`, `gaudi-deployer`, `gaudi-benchrunner`, `gaudi-liaison`. No profile recorded a *failed* 90 s compression — they hit the healthy deployment or short summaries; p99 (12–24 s turn-blocking per R3 pass, to 126 s here) was the tax.
- **state.db numbers** (from the R3 measurement pass t_99611d63, which had DB access; this card left `state.db` locked/untouched): 13 sessions / 5 profiles affected; `sw-architect` lane worst at ~5.09 M tokens/session; between-compression dwell 174–223 K tokens.

## 4. Why compression routed to `qwen38-flash-fp8`

Verdict: **pre-pin config** — option (2) of the task's three candidates.

| Candidate | Verdict | Evidence |
|---|---|---|
| `_summary_model_fallen_back` fallback path | **Ruled out** | Zero `Falling back to main model due to` / `Summary model '…' failed` lines in `root-agent.log`, `agent.log`, `errors.log` (all cover the storm window; current files start 10-22). Structurally impossible on profiles too: fallback-to-main uses each profile's *main* model (e.g. kanban-worker main = `muse` ≠ `qwen38-flash-fp8`), but profile compression telemetry on the bad model persisted for days with no fallback lines. |
| Feasibility fallback | **Ruled out** | No feasibility-probe routing exists in the tree; `agent/auxiliary_client.py::call_llm(task=…)` resolves `auxiliary.<task>.*` from config first; tests (`tests/agent/test_compression_aux_fallback_route.py`) document config-first, fallback-on-error semantics. |
| **Pre-pin config** | **Confirmed** | Pre-rollout backups `config-backups/aux-sync-20261023_195137/*.config.yaml` (fleet) and the R3 pass's verification show **every profile's** `auxiliary.compression.model: qwen38-flash-fp8`; root's `providers.litellm` entry (the provider the storm calls used, `provider=litellm` in the ledger) lists `model: qwen38-flash-fp8` as the provider default with no per-task override pre-pin. No `reasoning_effort: none`, no timeout override on the compression block anywhere. The model choice itself was the fleet-wide aux consolidation onto the workhorse model (visible as `custom:qwen38-flash-fp8` / `litellm` in the 10-23 backups). |

**Amplifiers that turned one bad routing into a storm:**
1. **5×90 s kill, then retry ×3.** The kills were HTTP 500s, *not* client timeouts, so the current tree's protections (`_COMPRESSION_TIMEOUT_FLOOR_SECONDS = 300.0`; `_TIMEOUT_NO_RETRY_TASKS = {compression, session_search}` — no same-provider retry on *full-budget timeout*) never engaged. 5xx retried through the provider retry loop (`agent.api_max_retries: 3`) at 90 s a pop. (Medium confidence on exact deployed retry code on 10-23: `running-commit.txt` records only the *current* commit `c6b760932c`, and `gateway.log` has rotated away 10-23; the 90 s×3 shape is directly visible in the ledger.)
2. **Cooldown never armed.** After 2 failed attempts, attempt 3 typically "succeeded" from the proxy cache (0.05–3.4 s) — a *success* — so the compression-failure timeout-cooldown ladder (60→300→900 s, arms on timeout-failure class) never escalated.
3. **Threshold re-trigger.** The 5 events that failed all attempts left the context above threshold → the next turn re-triggered compression. Event cadence ≈ every 37 min for 18.5 h.
4. **No output cap.** `_call_summary_llm` deliberately omits `max_tokens` (Anthropic/NIM truncation caveat, `context_compressor.py:3690-3698`), so an unconstrained model could spend 90+ s generating a 16k-token "summary" — the very thing the kill ceiling punished.

**Resolution timeline (all UTC unless noted):**
- 10-22 21:16–21:40Z — prelude: approval-lane orb 502/`:8001` hard-fails, same session.
- 10-23 04:52:30Z → 23:25:05Z — storm (74 calls / 49 fails).
- 10-23 ~12:1xZ — approval/vision lane already on `qwen36-fast` in the ledger (earlier wave); **compression stayed bad**.
- 10-23 19:24Z — approval-lane model switch recorded in ledger (session pickup of wave-1 pins).
- 10-23 23:25–23:44Z — root `auxiliary.compression` → `qwen36-fast` (last bad chain ends 23:25:05Z; first `qwen36-fast` context-resolution warnings 23:44:45Z / 23:46:45Z `errors.log:5278,5286`).
- 10-23 19:51 EDT (23:51Z) — fleet aux-sync backups (`aux-sync-20261023_195137`), profile pins written; picked up at each profile's next session (profile logs show 0 bad compression calls from 10-24 00:00Z).
- 10-24 02:12Z — probe t_7cb89ed9: `qwen36-fast` *effective* window is 131,072 (gh201 `--max-model-len 131072`), so root's session threshold auto-lowered to 131,072 (repeated `errors.log` warnings; root telemetry shows mixed 131,072 / 222,822 effective thresholds through 10-24 early hours).
- 10-24 03:32–03:52 EDT (07:32–07:52Z) — t_d5916d8a + t_87165309: orb container 131,072→**262,144** (verified by 262,200-token probe), root + 52 profiles catalog repin, provider `request_timeout_seconds` 30→120. First `qwen36-fast` compression had already run 10-24 02:08:06Z (17.98 s).
- Post-fix steady state: root compressions 4.9–23.1 s (micro ~5–8 s, full ~15–23 s), `effective_threshold 222,822`, zero bad-model calls (root + all 59 profiles).

## 5. Was the current code base a factor?

Partially, but it isn't the cause. At current commit `c6b760932c` the tree already contains: the 300 s compression timeout floor, timeout-no-retry for compression, a gateway-hygiene failure-streak cooldown (`gateway/session_state.py:76-90`), and a fail-closed in-context input bound (`gateway/run_turn.py:119`). **None engage on a 5xx kill at 90 s**: they cover timeouts, hygiene loops, and pre-API overflow, not "server returns 500 after doing the work." The gap this incident exposes is §7 (c).

## 6. Recurrence risk — audit of the current state

**Closed:** fleet compression pins — root read directly (`qwen36-fast` + `reasoning_effort: none`); `swco-butler` read directly; fleet-wide verified by the R3 pass + 0 bad-model compression calls in all profile logs on 10-24; the QW-card inventory tripwire (t_36eda488, in flight, `qw_inventory.py` incl. `compression_pins` counter) asserts the canon going forward.

**Open vectors (ranked):**
1. **HIGH — fallback-to-main lands on the storm model.** Root (and 21 other profiles; per-lane model census from the R3 pass t_99611d63) have main = `qwen38-flash-fp8`. `context_compressor.py:3795-3803`: the compression fallback-to-main path fires *with no cooldown, immediate retry* whenever the aux model 4xx/5xx/aborts. A `qwen36-fast` outage today re-creates the storm verbatim on those 22 lanes. The QW3 tripwire detects the symptom after the fact; nothing prevents the routing.
2. **MEDIUM — orb's bad deployment path is unaddressed.** Nothing in the estate fixes the ~90 s killer (orb is outside this host; the 10-22 prelude errors are estate-visible proof it existed ≥1 day). Any future long-generation lane (vision on big inputs still pins `qwen38-flash-fp8` on root; 14 profiles have compression on muse — unknown generation profile) can rediscover it.
3. **MEDIUM — config pickup lag.** Pins bind at session start; long-lived sessions keep routing on the old model for hours after a fleet write (butler ran `qwen38-flash-fp8` compressions up to 22:09Z on 10-23, ~4 h after wave-1). A pin-rollout without a bounce leaves a storm-shaped window; "config says X" ≠ "traffic says X".
4. **LOW-MED — catalog-default trap.** t_7cb89ed9 proved deployment caps can silently contradict catalog context_length (qwen36-fast: native 262,144, deployed 131,072). Any new aux slug pinned without a needle-probe inherits a wrong window until the auto-lower warning fires.
5. **LOW — 5×90 s kill class.** Orb off-host; no estate-side change removes vector 2. Tripwire + degradation mode are the estate-side mitigation.

## 7. Proposals — NOT applied; architect lane owns config/code edits

### (c) Degradation mode that avoids retry storms

Design goal: **a compression-lane outage should cost one bounded attempt + one fallback try, then degrade quietly — never a 90 s×3 hammer every 37 min.**

- **C1 — Fallback pin + storm-model blacklist** (config + small code). Add `auxiliary.compression.fallback_model: qwen38` (reasoning none; ledger shows qwen38 at 0.45–0.9 s on small calls, healthy through the storm window) and have `_fallback_to_main_for_compression` consult a `degraded_models` list (seed: `qwen38-flash-fp8`): if main ∈ degraded, skip main and go straight to the degraded path. Closes vector 1. Config sketch:
  ```yaml
  auxiliary:
    compression:
      model: qwen36-fast        # current, correct
      fallback_model: qwen38    # proposed (config key: new)
  agent:
    compression_degraded_models: [qwen38-flash-fp8]   # proposed key (code: new)
  ```
- **C2 — Fail-fast compression (5xx = timeout parity).** Extend the existing `_TIMEOUT_NO_RETRY_TASKS` semantics (full-budget timeout ⇒ no same-provider retry, go to fallback) to **5xx on compression**: one attempt per provider per event. Storm math: 49 failed calls × 90 s ≈ 74 min becomes ≈ 6 events × 90 s + fallback ≈ 12 min at worst. No new constants needed conceptually; `agent.api_max_retries: 3` currently gives 3× — the per-task no-retry set is the right scalpel (dropping `api_max_retries` fleet-wide would also blunt main-lane resilience; not recommended).
- **C3 — Degraded-mode latch (the core "degradation mode").** State machine on the existing `hygiene_failure_streak` home (`gateway/session_state.py:76-90`): when **≥2 compression events fully fail within 20 min**, latch the lane degraded for that session until a probe succeeds:
  1. Stop full-summary attempts; use the existing degraded static marker + `micro_compact` path (already exists — `context_compressor` "falls back to a degraded static marker").
  2. Raise the session's effective threshold to **0.92** (fewer re-triggers; bounded, not infinite: 0.92 × 262,144 = 241,172 still < 262,144 hard stop; the fail-closed in-context bound `bound_model_input_without_hygiene` remains the backstop).
  3. Probe every 15 min with a 512-token throwaway call to `qwen36-fast` (~1–7 s observed) → on success, unlatch and restore.
  4. Emit the `aux_model_fallback` telemetry metric already named in code (`metrics: aux_model_fallback task=compression … model=<…>`) → QW3 tripwire (t_36eda488) alerts on `task=compression model=qwen38-flash-fp8` and would extend to `latch=degraded`.
- **C4 — Bounded summary output (litellm/custom only).** Pass `max_tokens = 2 × summary_budget` when the provider is litellm/custom (keep the no-cap rule for Anthropic/NIM per the code comment at `context_compressor.py:3690-3698`). Post-fix `qwen36-fast` summaries run 2–18k tokens; a ~32k cap (also `providers.litellm.models.qwen36-fast.max_tokens: 32768` already pin) bounds worst-case decode ≈ 200 s < 300 s timeout floor. Cuts the tail *and* the token waste (1.0–1.15 output/input ratio is the thing that met the 90 s ceiling).
- **C5 — Streaming summary calls.** `_call_summary_llm` currently sets `stream=False`; the aux client supports streaming with a no-progress watchdog (`_AUX_STREAM_NO_PROGRESS_TIMEOUT = 60.0`). Streaming turns "silent death at 90 s" into "fails at 60 s of true silence, keeps flowing otherwise" — fail-fast on real stalls, immune to absolute idle ceilings.
- **C6 — Orb-side (operator infra, outside estate).** Identify/quarantine the `qwen38-flash-fp8` deployment path that 500s at ~90 s (alternating success/failure on identical traffic + 0.05 s cached replays pin it to deployment-level, not router-global, config); set an explicit router `request_timeout` above legitimate compression duration; surface per-deployment error counters. Until fixed, C1–C3 are the estate-side shield.
- **C7 — Rollout verification protocol (process).** After any aux-pin change, acceptance = **traffic check**, not file check: aux-ledger query `task=compression AND model NOT IN (allowed_set)` over trailing 6 h must return 0 rows (the ledger exists precisely for this; the butler's 4-hour lag post-write is the cautionary receipt). Fold into the aux-sync runbook + QW inventory.

### (d) Per-lane `compression.threshold` changes, with numbers

Baseline facts measured here: default threshold (profiles, no compression block) = **0.75** → trigger **196,608** (telemetry `effective_threshold: 196608` on `swco-butler`, `sw-architect`); root explicit **0.85** → **222,822**; healthy event cost 12–24 s (`qwen36-fast`, this pass + t_9961d… R3 pass); profiles carry **no** tuning block (root-only tuning, R3 pass B11).

| Lane | ctx | Current effective trigger | Proposal | New trigger | Expected effect (measured dwell basis) |
|---|---|---|---|---|---|
| Heavy dev/eng lanes: `sw-dev-a/b`, `sw-architect`, `kanban-board-architect`, `sw-reviewer`, `sw-qa`, `sw-ux`, `research`, `kanban-worker` | 262,144 | 196,608 (implicit 0.75) | **explicit block: `threshold: 0.85`, `target_ratio: 0.2`, `protect_last_n: 20`, `micro_compact: true`, `keep_first_n: 3`, `verify` off-defaults mirrored from root** | 222,822 | Inter-event token distance +26,214: **−29 % events** at 66 K-token deep-reclaim dwell (architect-class); **−80 % events** for threshold-hugging butler-class hovers (floor ~190 K → interval 6.6 K→32.8 K). At 12–24 s/event and the R3 pass's ~10 events/8 h on butler lanes, order **20–40 min/day fleet-wide turn-blocking time saved**, and a proportionally smaller failure surface (fewer events × storm exposure). |
| Root orchestrator (`/home/arch/.hermes`) | 262,144 | 222,822 (explicit 0.85) | **keep 0.85**; hold 0.88 (230,687, −7 % events) in reserve | — | Root was the storm victim; threshold was not its problem (routing was). Do not raise it while C1–C3 are unshipped. |
| Butlers (chat-dominated: `g01/g02/swco/sj/gaudi-butler`) | 262,144 | 196,608 | **keep 0.75** for now; if adopting the explicit block, 0.80 (209,715) max | 196,608 | Chat turns are small and frequent; their events are cheap (micro 5–8 s). The big win for them is the explicit block's `target_ratio`/`micro_compact`, not threshold. |
| 1 M-window lanes (glm-5.x / claude main) | 1,000,000 | config 0.85 → 850,000, **silently clamped to 262,144** by the aux model's window | **no threshold change possible/needed until the aux model's window ≥ 1 M**; document the clamp; re-probe aux window before believing any 1 M-lane number | 262,144 (de-facto) | Editing 0.85 on these lanes is a no-op today — avoid the false sense of tuning. |

Guardrails for any threshold increase: keep ≥10 % window headroom below the hard stop at the *trigger* (0.90 × 262,144 = 235,930 → 26,214-token ≈ 10 % floor; **do not exceed 0.90 while the aux compression window is 262,144**, or the compression prompt itself crowds the aux model's context — the pre-pin era's "Context size has been exceeded" class). Stagger: apply the explicit block to one pilot lane (sw-dev-a), verify with aux-ledger event counts + `effective_threshold` telemetry for ≥3 days, then fan out — the PROF-SWEEP-OPT byte-sync machinery (59 configs, commit 4b1349e) is the distribution vehicle and its checklist should gain one line: "compression block".

**Savings arithmetic (honest form):** each avoided event ≈ 12–24 s of turn-blocking compression + ~1 aux call of ~200–350k tokens of API throughput; the storm-class insurance is the larger number — at 74 calls / 49 failures, halving event frequency halves exposure to a repeat of this incident. The proposals do not change healthy compression *duration*; they change its *frequency* and its *failure cost*.

## 8. What would falsify the root cause

- Orb logs for 10-23 showing the 500s originated in LiteLLM router logic (not a deployment) would refine vector 2 but not the config root cause.
- Evidence of a different session in the storm would falsify "single session" — none exists in the ledger (74/74 rows same session), and profile logs show only slow-success events.
- The ledger's first row sitting exactly at storm start leaves an unmeasured pre-10-23-04:52 tail; the 55-slow-calls figure from log data bounds it (the storm did not materially start earlier than ~10-22 evening, when the prelude errors appear).

## 9. Evidence index

- `/home/arch/.hermes/plugin-data/aux-ledger/calls.jsonl` — storm traffic (74 rows 10-23; fix-era rows 10-24).
- `/home/arch/.hermes/logs/root-agent.log` + `errors.log` (10-22 →) — compression telemetry (`aux_model`, `effective_threshold`, durations), auto-lower warnings (23:44:45Z / 23:46:45Z `errors.log:5278,5286`), prelude 502/`:8001` errors (10-22 21:1xZ).
- `/home/arch/.hermes/config-backups/aux-sync-20261023_195137/*.config.yaml` — pre-pin fleet configs (all `compression.model: qwen38-flash-fp8`); `…/aux-ctx-262k-20261024_0332/` — pre-262K configs.
- `/home/arch/.hermes/config.yaml` — current root pins (compression `qwen36-fast`, `reasoning_effort: none`, `context_length: 262144`; `providers.litellm` @ :412-430 = the orb entry the storm used).
- `/home/arch/.hermes/hermes-agent/agent/{context_compressor.py, auxiliary_client.py}` — fallback/timeout/stream/max-token semantics; `gateway/{session_state.py, run_turn.py}` — hygiene streak + fail-closed bound; `tests/agent/test_compression_aux_fallback_route.py` — fallback semantics; `tests/agent/test_compression_background_worker.py` — turn-hold background worker.
- Kanban receipts: t_99611d63 (R3 measurement), t_d5916d8a, t_87165309 (262K rollout), t_7cb89ed9 (131K probe, reflog 80), t_36eda488 (QW inventory, in flight).
- `/local/projects/software-co/.git/logs/HEAD` — fleet rollout commits (PROF-SWEEP-OPT 4b1349e; qwen36-fast probe e1f9993; 262K pins).
- Gaps noted: `gateway.log` covers 10-24 02:32Z onward only (10-23 rotated away); `state.db` left locked (read via t_99611d63); orb-side logs not on this host.

*Prepared read-only by research (kanban t_2cc1a7b3), 2026-10-24. No configs edited, no services restarted, no public writes. Handback: (c)+(d) config/code deltas above → architect lane.*
