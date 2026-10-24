# Claude Code Wiring — 2026-10-24 (t_0f3b5c1e)

**Task:** CLAUDE-CODE-4-WIRING (wire Claude Code into pilot-winning profiles with usage governance)
**Inputs:** t_104ef76d (candidates) · t_b83974bc (limits + mitigation design) · t_93b6f033 (pilot verdicts) · operator rulings 2026-10-24 (shared-CLI/no per-profile OAuth; ~90/10 allocation flip)
**Artifacts:** `docs/receipts/claude-code-wiring-2026-10-24/` (pre/post-wire SOULs + diffs, wrapper v1/v2, caps, settings allowlists, alert script, ledger snapshot, smoke receipts).

---

## 1. Wired profiles (final list)

| Profile | Scope wired | Pilot evidence (t_93b6f033) |
|---|---|---|
| **sw-dev-a** | Substantial code cards (multi-file features/fixes, test scaffolds, METATRON-class) — implementation routes through the wrapper; profile reviews diffs, runs gates, commits | Complete gate-clean METATRON QA-001/002 fix in 2 bounded shots ($0.50; 141 tests, mypy strict, ruff) vs muse's 3–4-run crash track record |
| **g02-ops** | **Engineering fraction ONLY**: offline composition — PromQL/recording/alert rules, k8s/chart/config YAML, scripts, technical proposals | First-try correct kubelet-eviction mechanics (system-node-critical) vs the 8B model's false-premise round-1; $0.33/1 shot |

**Not wired:** sw-dev-b (pilot INCONCLUSIVE — equal quality on the FIX sublane; extend from lane A on observed need, not speculatively). Orchestrator/judgment/reviewer/butler seats and the `default` profile (its native anthropic binding is untouched by this program) — out of scope per the task constraint.

**Mechanism of wiring:** additive **SOUL.md doctrine sections only** ("Claude Code Lane", 2026-10-24). Neither profile's `config.yaml` changed — models (muse / qwen38-flash-fp8) remain the profiles' own brains and the fallback target; Claude Code is reached as a tool via the sanctioned wrapper, exactly per the operator's 2026-10-24 clarification (shared `~/.claude` credentials, one shared login, no per-profile OAuth). The `autonomous-ai-agents:claude-code` skill was copied into sw-dev-a's skill tree (g02-ops already had it) for print-mode reference.

## 2. Invocation path (what a wired profile actually runs)

```
~/.claude-board/cc-board.sh <profile> "$PWD" 10 0.50 /tmp/cc-receipt-<card>-<shot>.json '<prompt>'
```

`cc-board.sh` **v2** (lineage: t_b83974bc design → pilot v1 → this wiring) enforces, fail-closed:

- **Model/effort allowlist:** haiku-5-5 / sonnet-5-5 only; effort ≤ medium; opus/fable and max-effort are operator-exclusive.
- **Per-shot ceilings:** `--max-turns ≤ 10`, `--max-budget-usd ≤ 0.50` (CLI's own verified-working meter), one-shot print mode, `--no-session-persistence`, per-task workdir.
- **Permissions via `--settings` allowlist** (per-profile files `~/.claude-board/settings-<profile>.json`): grants Read/Write/Edit/Glob/Grep plus a repo-toolchain Bash allowlist; denies git push, rm, sudo, network (curl/wget/ssh), kubectl/helm/docker/systemctl, other-agent CLIs, credential-file reads, and WebFetch/WebSearch. **No `--dangerously-skip-permissions` anywhere in the shipped mechanism** (pilot lesson L1 retired). If no allowlist exists for the profile, the wrapper refuses rather than run ungranted. g02-ops's allowlist additionally denies `az` and grants no cluster tools — cluster mutation and GO-gated actions cannot route through Claude Code even by accident.
- **Every run ledgered** to `~/.claude-board/ledger.jsonl` under flock, including failed runs (they still meter — pilot lesson L4).

Exit codes are the fallback contract: `0` ok (check receipt `subtype`; `error_max_turns` → bounded continue-shot, max 4 per card) · `41` refused bad args/model/effort/no-allowlist · `42` board-lane or per-profile rolling cap hit · `43` run failed (non-limit) · `44` quota wall active · `45` Anthropic usage-limit-class failure.

## 3. Governance: caps, shared-pool coordination, operator protection

### Caps (recomputed per the operator's flipped allocation, 2026-10-24)

Old pilot-era caps ($2/5h + $10/7d) encoded the conservative operator-keeps-≥85% split. The operator now allows the **board lane up to ~90% of the rolling window** and keeps a **thin non-negotiable ~10% reserve**. Confirmed anchor (t_b83974bc): the 5-hour session window's conservative API-equivalent floor is ~$20; Anthropic publishes no absolute numbers, so the guarantee is built against the floor. All caps live in **`~/.claude-board/caps.json`** — the single tuning point:

| Cap | Value | Derivation |
|---|---|---|
| Board lane 5h | **$18.00** | 90% × $20 conservative window floor. Even if the true window is the smallest plausible size, the operator keeps ≥ $2 (≥10%); if it is larger (estimates run to $40+), the reserve is proportionally bigger. |
| Board lane 7d | **$65.00** | 90% × an assumed ~$72 conservative weekly floor (~3.6× the session floor; weekly size is unobservable member-side — assumption stated, not measured). Also stays under the ~$91/wk "average active developer" org-analytics visibility line at full burn. |
| Per-profile 5h | **$12.00** | 2/3 of the lane cap — no single wired profile can monopolize the lane. |
| Per shot | 10 turns / $0.50 | unchanged from pilot. |

Fail-closed: a missing or unparseable caps.json drops the wrapper to the conservative pilot-era values ($2/$10/$1.50), never to uncapped. Measured demand context: the entire pilot cost $0.93; a FIX card ~$0.10; a two-fix METATRON card ~$0.50. The caps are a structural ceiling and demand-signal detector, not a throttle expected to bind.

### Shared-pool coordination (all wired profiles + the operator hit ONE Anthropic meter)

- **Pre-run:** every invocation checks the shared ledger's rolling 5h/7d sums (board-wide and per-profile) under flock, and refuses *before* calling Claude when a cap is hit — exhaustion is discovered Hermes-side, never by contesting the operator inside Anthropic's window.
- **Quota wall (new in v2):** when a run fails with a usage-limit-class error, the wrapper writes `~/.claude-board/quota-wall.json` (30-min default cooldown from caps.json) and exits 45. Every subsequent invocation from **any** wired profile is refused (`exit 44`) until the wall expires — one profile's discovery of account exhaustion protects all of them, instead of each independently re-burning attempts into a wall.
- **Observability:** refusal/wall events log to `events.jsonl`; cron job `cc-board-usage-alert` (kanban-board-architect profile, every 30 min, no-agent) delivers 50/80/100%-of-cap crossing alerts and quota-wall/cap-refusal notices (delivery currently `local` — visible in the architect profile's cron/gateway log and estate audits; wiring a Telegram notifier is a trivial follow-up if the operator wants push alerts).

### Operator-protection guarantee (the exact mechanism, per the task receipt requirement)

The board lane can never spend more than **$18 in any rolling 5-hour window and $65 in any rolling 7-day period, summed across every wired profile** — enforced fail-closed by the wrapper's pre-run ledger check, which is the *only* sanctioned path to the shared credential. The caps are set at 90% of the most conservative estimate of the account's window, so the operator's own interactive `claude` use retains at least $2 (≥10%) of even a worst-case-sized window — and typically far more. On any cap hit, quota wall, or Anthropic limit error, wired profiles fall back to their own gateway models and the board keeps moving; the operator's access can be *degraded only by Anthropic-side limits the board did not cause*, never silently starved by board usage. Credential-lifetime operations (`claude auth login/logout/setup-token`) remain operator-only — profiles are read-only w.r.t. credentials by doctrine and by the allowlists' deny rules.

## 4. Fallback behavior (per profile, baked into SOUL doctrine)

Wrapper exit 42/44/45, or any run failure with no usable result → the profile drops Claude Code **for that card**, does the work with its normal tools/model (muse / qwen38-flash-fp8 as configured), and notes the fallback on the card. Never retries quota-class errors, never blocks or fails a card on Claude Code unavailability. `--fallback-model` inside Anthropic is explicitly NOT used (limits are shared across models — it cannot rescue a quota wall; t_b83974bc §3).

## 5. Smoke-test evidence (all executed 2026-10-24, receipts in `receipts/…/smoke/`)

| # | Test | Result |
|---|---|---|
| Gov-sim suite | cap refusals (board + per-profile), shot ceilings, model allowlist, quota-wall pre-run refusal, limit-classification → wall write → second profile refused by first's wall, caps-missing fail-closed, alert dry-run | **All pass** — exits 42/42/41/44/45→44/42, events logged, alert fired on wall event (simulated via sandboxed `CC_BOARD_DIR` + PATH-shim; zero cost, no real Anthropic impact) |
| S1 happy path, wrapper, sw-dev-a allowlist | real `claude` run, haiku, fix a RED repo to GREEN | exited 0, $0.0031, `subtype: success`, clean diff, **zero permission-denial noise** — `--settings` allowlist fully replaces bypass mode |
| S2 happy path, wrapper, g02-ops, sonnet default | compose PrometheusRule + proposal | exited 0, $0.0617, correct rules/mechanisms |
| E2E session, **sw-dev-a profile itself** | real hermes session following its new SOUL doctrine end-to-end | invoked wrapper once via its own terminal, $0.0029 haiku, RED→GREEN verified, diff reviewed, reported exit/subtype/cost — **independent re-verification passed** |
| E2E session, **g02-ops profile itself** | same, composition task | $0.0030, correct artifact, self-verified then independently verified |
| E2E fallback session, **sw-dev-a profile itself** | sandboxed board dir with exhausted caps → wrapper refused (exit 42) | profile applied the fallback law: no retry, fixed the code itself with its own model, verified GREEN — fallback + non-regression proven live |
| Non-regression | `hermes config check` both profiles; both E2E sessions exercised normal tools around the CC lane | both clean; profiles' non-CC behavior unchanged (config.yaml untouched by design) |

Real Anthropic-side 429/usage-limit events cannot be safely forced without burning real quota and drawing org attention — the classification path (S5) was validated with a PATH-shimmed fake `claude` emitting a real-format usage-limit error, which is the honest maximum simulation. The wrapper's rc≠0-with-receipt path (pilot lesson L4) was already proven live in the pilot.

## 6. Rollback instructions (revert a profile to pre-wiring state)

Everything is additive and reversible; rollback is a SOUL edit plus (optionally) infra removal. Byte-exact pre-wire snapshots with sha256 are in `receipts/claude-code-wiring-2026-10-24/`:

1. **Unwire a profile (behavior):** `cp receipts/claude-code-wiring-2026-10-24/SOUL.<profile>.prewire.md /home/arch/.hermes/profiles/<profile>/SOUL.md`. (Diffs are pure section additions — deleting the "Claude Code Lane" section achieves the same.)
2. **Kill the lane entirely (all profiles):** additionally `hermes cron remove <cc-board-usage-alert id>` (kanban-board-architect cron), and either empty the caps in `~/.claude-board/caps.json` (wrapper fail-closes to conservative) or `chmod -x ~/.claude-board/cc-board.sh` (invocations then fail → SOUL fallback law handles it gracefully on any in-flight card).
3. **Nothing else to revert:** profile config.yaml, models, fallbacks, skills (beyond the copied reference skill), and the shared `~/.claude` credential were never modified. No repo/worktree state was touched by wiring.

## 7. Deferred decision surfaced to the operator

The pilot showed a genuine (not marginal) capability upgrade on 2 of 3 lanes. **If ledger data shows wired profiles sustainably hitting the $18/5h (90%) ceiling in practice — genuine demand signal, not speculation — the natural next step is the operator's open option of a higher-limit Anthropic plan.** Do not assume it until the ledger shows the pressure; current measured demand ($0.93 pilot + $0.07 wiring smokes ≈ $1.01 total) sits at ~6% of one 5-hour cap. Governance reminder stands: this usage is attributed to the operator's JHU identity in admin analytics; the caps keep the lane visually boring by design.

---

*Wired 2026-10-24 ~14:40 EDT by kanban-board-architect (t_0f3b5c1e). This closes the Claude Code exploration program (t_104ef76d → t_b83974bc → t_93b6f033 → t_0f3b5c1e); any further expansion (sw-dev-b, other profiles) requires a fresh operator ask.*
