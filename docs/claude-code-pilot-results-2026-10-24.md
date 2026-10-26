> Status: superseded by hermes-estate/docs/OPERATIONS.md §2.2 (cc-board-usage-alert) — pilot receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# Claude Code Pilot Results — 2026-10-24 (t_93b6f033)

**Task:** CLAUDE-CODE-3-PILOT (budgeted trial of Claude Code print-mode on top candidate profiles)
**Inputs:** t_104ef76d (candidate ranking) · t_b83974bc (account limits + mitigation design)
**Per operator ruling 2026-10-24:** pilots invoked the already-authenticated standalone `claude` CLI (shared `~/.claude` credentials, JHU enterprise seat, `jbiondo2@jh.edu`) — no per-profile OAuth.
**Artifacts:** `docs/receipts/claude-code-pilot-2026-10-24/` (all receipts, ledger, wrapper, prompts, CC-produced files, diffs).

---

## 1. Executive summary

| Profile | Pilot task (type replayed) | CC result | Cost / turns / wall | Verdict |
|---|---|---|---|---|
| **sw-dev-a** (muse) | METATRON QA-001/002 fix card (t_e3bc9d63, todo — no duplicate-work risk) in isolated clone of `metatron-rewrite@w4/qa-ready` | Complete, correct, gate-clean diff; **independently verified**: 141 tests pass, mypy strict clean, ruff clean; tests have teeth (RED verified on unfixed tree for the mash analog; lock refusal + corrupt-log typed-exit asserted) | $0.50 metered over 2 bounded shots (+$0.19 on the misconfigured first shot); 3+7 effective turns; ~95 s of CC wall-clock | **WORTH WIRING IN** |
| **g02-ops** (qwen38-flash-fp8) | Capacity-trend guard proposal (t_7c1d2e12, original card text only, offline) | First-try correct kubelet-eviction mechanics — rejected the toleration premise that cost the current model a `changes_requested` round, landed on `system-node-critical` criticality; 12 alert rules incl. blind-spot guards + trend prediction; honest assumption-/caveat-flagging | $0.33 / 8 turns / 2 m 28 s, single shot | **WORTH WIRING IN** (engineering fraction only, as scoped by t_104ef76d) |
| **sw-dev-b** (muse) | mash#24 replay at exact base sha 36ef120 (muse's landed fix `a2391a8` is ground truth) | Valid minimal fix (1-line, call-site helper — both fix options were card-sanctioned), RED/GREEN teeth **independently reproduced** (35 passed w/ fix; 1 failed no-slash case w/o fix) | $0.10 / 9 turns / 34 s, single shot | **INCONCLUSIVE — NEED MORE DATA** (marginal; see §5) |

**Total pilot consumption: $0.93 against the $2.00/5 h board-lane cap from t_b83974bc** (7d cap $10.00; see ledger). Zero throttling/rate-limit signals at any point; operator interactive headroom untouched (≤ ~5% of even a conservatively-sized session window, on top of the 6%-at-probe-start baseline). No profile config was modified; all work happened in isolated clones/workdirs under the task scratch workspace.

> **OPERATOR UPDATE (2026-10-24, mid-pilot): budget allocation flipped.** The operator will use Claude Code personally only "very seldom" — the reserve split inverts: **the board/profile lane may use up to ~90% of the rolling window/budget; the operator keeps a thin ~10% reserve** for occasional personal use (supersedes t_b83974bc §7's operator-keeps-≥85-90% split). This did not gate the pilot (the $0.50/invocation and aggregate caps were never approached), but the wrapper's current $2/5 h + $10/7 d caps **encode the OLD conservative split and must be recomputed at wiring time** against the new allocation, anchored on real ledger consumption rather than the old percentage math.
>
> Separately: the operator is **open to upgrading to a higher-limit Anthropic plan** if the pilot shows Claude Code is a *real* capability upgrade (not marginal). This decision is deferred until after pilot verdicts — see §8.

---

## 2. Method

Shadow/replay pilots, not live dispatches: each candidate's representative *task type* (from t_104ef76d's workload evidence) was replayed against the real repo/state at the relevant sha, run through the shared CLI inside the t_b83974bc mitigation stack. The current-model baseline is the documented track record (crash/reclaim/rework rates from t_104ef76d), and for sw-dev-b additionally the *actual landed muse fix* for the identical defect at the identical base sha — a true A/B.

- **Wrapper/ledger:** `~/.claude-board/cc-board.sh` + `ledger.jsonl` (committed copy in receipts dir) — flock-guarded, checks $2/5 h + $10/7 d rolling caps before every invocation, model allowlist (`claude-sonnet-5-5`/`claude-haiku-5-5` only), effort ≤ medium, `--max-turns 10`, `--max-budget-usd 0.50`, `--no-session-persistence`, per-run `--output-format json` receipt appended to the ledger.
- **Runs sequential,** never parallel, per the shared-pool caution.
- **Independent verification:** test suites, type/lint gates, and RED-on-base proofs were re-executed by the pilot operator (kanban-board-architect), not trusted from CC's self-reports.

### Per-invocation log (board ledger)

| # | profile | subtype | turns | cost | wall | note |
|---|---|---|---|---|---|---|
| 0 | k-b-architect | success | 1 | ~$0.001 (est., backfilled) | — | model-id smoke probe |
| 1 | sw-dev-a | success | 16† | $0.1891 | 53 s | design-only: print-mode permission denials (§6 L1) |
| 2 | sw-dev-a | error_max_turns | 11 | $0.1927 | 50 s | real edits landed, hit the 10-turn cap mid-loop |
| 3 | sw-dev-a | success | 7 | $0.1199 | 41 s | bounded continue-shot → complete, gate-clean |
| 4 | g02-ops | success | 8 | $0.3328 | 2 m 28 s | single-shot complete |
| 5 | sw-dev-b | success | 9 | $0.0988 | 34 s | single-shot complete |

† Receipt `num_turns` can exceed the `--max-turns` bound (sub-agent/tool accounting); the cap itself held — run 2 terminated at max-turns.

---

## 3. sw-dev-a — METATRON lane (candidate #1): **WORTH WIRING IN**

**Replayed task type:** the METATRON lane's code-fix card family — specifically todo card t_e3bc9d63 (QA-001: dual-writer state-log prevention via advisory flock + typed `state-dir-locked` refusal; QA-002: typed one-line `StateLogCorrupt` at the CLI door). Chosen because the QA-ready predecessor card (t_6e194773) is the lane's worst track-record exemplar. Honest caveat carried from t_104ef76d: that card's three "crashes" were ~2 s gateway-admission refusals (infra, inherited by any model), so the pilot targeted the lane's *code-loop* fragility (multi-step fix-over-tests-over-gates on METATRON, where the W2-P5 editor card took `crashed×3 → completed`) rather than the infra fault.

**Outcome.** Shot 1 (after the permission fix) implemented the lock correctly (`StateDirLock` hold/probe flock semantics, typed refusal message byte-exact, serve-lifetime hold, release-on-close paths) and was cut off by the 10-turn cap with tests unwritten. The bounded continue-shot finished the work: added teeth-tests, fixed its own ruff E501, diagnosed why its first corrupt-log test failed (single garbage line = torn tail, not corruption — a correct domain deduction) and fixed it. Final: 5 source files +70/−5, new `tests/test_state_dir_lock.py`.

**Independent verification (this pilot's receipts, not CC's):** `pytest tests/test_state_dir_lock.py tests/test_cli_parity.py tests/test_lifecycle_engine.py tests/test_runtime_commands.py tests/test_server_shell.py` → **141 passed**; `mypy --strict src/metatron tests/test_state_dir_lock.py` → **clean (52 files)**; `ruff check` → clean; `ruff format --check` → only a pre-existing markdown code-block nit, untouched by CC. The one honest gap in CC's own report (claimed format-clean) is pre-existing, not introduced.

| | muse track record (t_104ef76d) | Claude Code pilot |
|---|---|---|
| Runs to land METATRON-class code cards | multiple (W2-P5: 4 runs; lane crash rate 11%, 7 crashes/63) | 2 bounded shots, 0 crashes, 0 protocol violations |
| Review cycles | 2 on the lane | not exercised (fix matches the card's own spec; no reviewer ran) |
| Gates | mixed | clean first pass |
| Cost | n/a (gateway model) | $0.50 total |

**Residual risk for the verdict:** no e2e `metatron serve`-process test was written (CC flagged this itself) and no reviewer seat compared the diff against a design of its own. The mechanism quality, however, is unambiguous.

---

## 4. g02-ops — ops-engineering fraction (candidate #3): **WORTH WIRING IN** (asscoped)

**Replayed task type:** the capacity-trend guard card (t_7c1d2e12) — PromQL/alerting-rules + node-protection artifact + snapshot script composition. This is the lane's changes_requested-rework exemplar: the current qwen38-flash-fp8 (8B) lane produced a **false-premise artifact in round 1** (proposed a node-exporter *NoSchedule toleration*, which kubelet eviction ignores — the reviewer's changes_requested proved it a verified no-op), needed live-cluster receipts to correct it, and separately shows `finish_reason='length'` truncations and protocol violations in logs.

**Pilot:** given only the ORIGINAL card text (no round-1 feedback), offline. The prompt's item 5 asked it to reason from kubelet's actual eviction behavior.

**Outcome.** First-try, single-shot: it explicitly reasoned "kubelet eviction is node-local, not the scheduler; tolerations, PDBs, affinity don't bind it; a plain DS is evicted and stays down," and landed on **`priorityClassName: system-node-critical`** — the same mechanism class the real lane only reached in round 2 with live kubelet logs in hand. Delivered: recording rules, 12 alerts (warn 80%, crit 85%, 83% eviction-imminent, 24 h predict_linear-to-85%, DiskPressure live, Evicted-pods, `absent()` blind-spot guards for both metric sources, snapshot-staleness, exporter-down), a snapshot-cron script, a PROPOSAL.md with per-rule rationale and the structural trade-off paragraph (move containerd root off /mnt/models > raising evictionHard), and a candid "not verified / assumptions" section (kubelet version-sensitivity of critical-pod handling, instance/job names, port coexistence).

**Comparison vs ground-truth v2 (the lane's round-2 artifacts, snapshot in the receipts dir):** same correct mechanism class and the same priorityClassName; CC's rule set is a superset of the lane's 6 rules. One packaging nit: CC proposed a new *static pod* exporter rather than patching the existing helm DS values (ground truth's cleaner, cluster-verified path); CC itself flagged the kubelet-version verification gap. For a review-only artifact lane this is a quality delta, not a correctness failure — and offline composition without cluster access was a pilot constraint, not a wiring constraint.

**Scope caveat unchanged:** GO-gated Azure mutations derive no benefit; wire the engineering fraction only.

---

## 5. sw-dev-b — mprov FIX sublane (candidate #2): **INCONCLUSIVE — NEED MORE DATA**

**Replayed task type:** mash#24 at its exact base sha (36ef120), where sw-dev-b's landed fix (`a2391a8`, PR #52) is literal ground truth. This sublane is where sw-dev-b performed *well* historically — the lane's failure mode (13% reclaims; the METATRON-W1-3 changes_requested loop) lives in longer cards, not small FIX cards.

**Outcome.** Single-shot, $0.10: verified the defect reproduces, chose the card-sanctioned option 2 (join with leading slash via `rstrip('/')` at the call site — 1-line diff vs muse's 4-line connect-time normalization; both were explicitly allowed, "minimum footprint wins" favors CC's), wrote a teeth test. **Independently reproduced:** full suite 35 passed with the fix; stash-the-fix → the no-slash case fails (RED); restore → green. Root-cause paragraph is precise (only BMC plugin appended `power/` without a leading slash; connect-time normalization would cover future blind joins but touches 3 sites).

**Why inconclusive for wiring:** both models solved this class cleanly — the pilot found **no quality gap to close** on the FIX sublane. CC's advantage here is economics/latency ($0.10, 34 s, 1 shot), not correctness. sw-dev-b's actual struggle pattern (long multi-step cards ending in reclaims/rework) was not exercised by an ethical small replay. **Recommendation:** don't wire on this evidence alone; lane-A's result plausibly transfers (same lane, same model, same workload family), so if sw-dev-a wiring proves out in practice, extend to sw-dev-b on observed need rather than speculative wiring — consistent with t_104ef76d's "infer lane B from lane A" fallback.

---

## 6. Wrapper/engineering lessons for the wiring task (t_0f3b5c1e) — found by burning real budget

1. **Print mode denies Edit/Write/Bash without a permission grant.** A naive `claude -p` produces a *read-only* run: CC read the code and designed a correct fix but every write was refused ("you haven't granted it yet") — $0.19 spent for a design doc. The wrapper now defaults to `--dangerously-skip-permissions` (print mode skips its interactive dialog). **Wiring should instead pin a per-profile `permissions.allow` settings allowlist** (Read/Write/Edit/Bash-scoped/Glob/Grep) so bypass mode is never the shipped mechanism.
2. **Model ids need the `claude-` prefix** (`claude-sonnet-5-5`, not the catalog's short `sonnet-5-5`) — otherwise `[claude-code:unrecognized_model]`, rc=1.
3. **`--max-turns 10` does not fit a two-fix code card.** A realistic METATRON-class card needs ~15–25 loop turns, i.e. **a bounded multi-shot continue pattern** (each shot ≤10 turns, ≤$0.50, state in the workdir — exactly how the pilot finished). num_turns in the receipt can exceed the cap value (accounting artifact); subtype is the ground truth (`error_max_turns`).
4. **Failed runs still spend money and the ledger must capture them.** Wrapper v1 skipped ledger-append when rc≠0, silently undercounting the lane by $0.19 (the error_max_turns run exits rc=1 with a fully-metered receipt). Fixed: receipts are ledgered whenever a meterable receipt exists; the cap check therefore always sees true spend.
5. **Cost model validation vs t_b83974bc estimates:** measured $0.10–0.33 per bounded sonnet-5-5 shot (8–10 loop turns, medium effort) — at/under the low end of the $0.05–0.30 "small task" estimate; ~$0.19–0.33 per 10-turn shot on a real mid-size codebase. The $2/5 h cap therefore buys ~6–15 sonnet shots per window, matching the "5–15 bounded sonnet tasks" planning figure. A FIX-class card costs ~$0.10; a two-fix METATRON card ~$0.50 across 2 shots.

## 7. Usage & safety summary (receipt requirement)

- **Pilot total: $0.9343** (ledger: `docs/receipts/claude-code-pilot-2026-10-24/board-ledger.jsonl`) vs caps **$2.00/5 h / $10.00/7 d** → 47% of the 5 h window cap consumed by the *entire three-profile pilot*. Within ceiling; no ceiling threatened at any point (pre-run cap checks rejected nothing because spend never approached the wall).
- **Zero account-wide throttling signals:** no rate-limit errors, no usage-limit-class errors, all receipts `service_tier: standard`, creds intact (`claude auth status` enterprise/logged-in throughout).
- **Operator impact: none observable** — pilot share of even a conservative session window is single-digit percent; probes never ran concurrently with operator sessions, and every invocation was hard-bounded by the CLI's own verified-working budget meter.
- All pilot work in isolated clones; no real repo, board DB, or profile config mutated. The real t_e3bc9d63 card remains todo for sw-dev-a, untouched.

## 8. Recommendation to t_0f3b5c1e (wiring)

1. **Wire sw-dev-a first** (METATRON + mprov FIX lanes) through the wrapper pattern with: multi-shot continue discipline, per-invocation `--max-turns 10`/`--max-budget-usd 0.50`, fallback-to-own-model on cap refusal/quota errors, and a permissions allowlist instead of bypass mode (lesson L1/L3).
2. **Wire g02-ops's engineering fraction** (chart-port/script/alerting composition) with the same guard rails; explicitly exclude GO-gated mutation lanes from any routing hint.
3. **Do not wire sw-dev-b yet**; revisit on observed lane-B rework after lane-A wiring has production data.
4. Ship the ledger as the coordination+dashboard mechanism exactly as piloted (it now counts failed runs), with the 50/80/100% cap alerts from t_b83974bc §7-4 still to be added at wiring time.
5. **Recompute the caps per the operator's flipped allocation (2026-10-24):** board lane up to ~90% of the rolling window, operator thin reserve ~10%. The pilot's measured economics ($0.10/FIX-card shot, ~$0.19–0.33 per 10-turn shot, ~$0.50/two-fix METATRON card) give the anchor: at the old $2/5 h cap the lane already buys 6–15 sonnet shots/window; at a ~90% allocation it scales several-fold before a plan discussion is even relevant.
6. **Flag to the operator — live option, deferred decision:** pilot verdicts show a genuine (not marginal) capability upgrade on 2 of 3 lanes — first-try correctness on failure modes where current models burned real review/rework/crash cycles. If wired production usage starts bumping against even the enlarged allocation, the operator has signaled openness to a higher-limit Anthropic plan. Do NOT assume it or design around higher limits yet; surface it as the natural next step only if ledger data shows sustained cap pressure.
7. Governance reminder stands: this spend is attributed to the operator's JHU identity in admin analytics; board lanes sized to whatever allocation the operator declares stay visually boring by design.

---
*Pilot executed 2026-10-24 13:53–14:10 EDT by kanban-board-architect (t_93b6f033), workspace scratch, all verification re-run independently. Feeds t_0f3b5c1e (CLAUDE-CODE-4-WIRING).*
