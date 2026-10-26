# ESTATE REVIEW — SYNTHESIS (2026-10-26)

Card t_bf623554 · merges `ESTATE-REVIEW-2026-10-26.md` (t_d325c0e0) + `PLUGIN-SURVEY-2026-10-26.md` (t_f5855ec3) into ONE ranked proposal list for operator pick.
**Nothing in this document has been executed.** Every adoption = a separate, operator-approved card. Public filings additionally require the operator final gate (distiller gate → OPERATOR GO → sha256-match → agent files byte-exact).

**Live re-verification (2026-10-26 11:00–11:15 EDT, this card):** the top 5 claims were re-checked before ranking:

| Claim | Live check | Result |
|---|---|---|
| Restart-kills-workers: `restart_drain_timeout: 0` meets drain-capped restarts; zombie reaps ongoing | `config.yaml:25` reads `restart_drain_timeout: 0`; gateway.log shows fresh reaps at 10:46, 10:51, 10:51 today | **CONFIRMED** (1,500 reap lines in full gateway.log) |
| Auto-decompose duplication risk live | `config.yaml:350–351`: `auto_decompose: true`, `per_tick: 5`; 39 decompose mentions in gateway.log | **CONFIRMED** |
| Carry stack 784 commits behind, PR branches ready | `git rev-list --count origin/main ^local/hotfixes-rebased-2026-10-25` = **784**; branches `862e87c2` and `a6c85c32` both exist | **CONFIRMED** |
| Single alert path, no alt sink | 3 scripts reference Telegram chat 8158007517; **0** webhook/smtp/mail references in `~/.hermes/scripts` | **CONFIRMED** |
| Zero log rotation | `~/.hermes/logs` = **55 MB** (tui_gateway_crash.log 23.6 MB, estate-sync.log 7.5 MB); no `/etc/logrotate.d/hermes` | **CONFIRMED** |

**Operator steer correction applied (dropped item):** estate-review item #10 ("R1 shared skill tree unexecuted, 176.6 MB / 25.3× duplication") **contradicts live state and is DROPPED**. Verified: **59/59 profiles** carry `skills.external_dirs: [~/.hermes/skills]` in config.yaml; per-profile skill trees now total **4.8 MB** (shared tree 64 MB — consistent with the t_6614dec5 / t_dfa26265 receipt of ~183 MB saved). The old finding was stale, not wrong-at-the-time.

**Overlap merges applied (steer #3):** compression hardening = **hermes-vcc + memlock** (one item); crash recovery = **planning-with-files** folded into the restart-workers item as its plugin stopgap; cost/observability = **one** of session-lens vs. local jsonl ledger — recommend the **local ledger**, session-lens listed only as the alternative inside that item.

---

## RANKED PROPOSALS (12) — for operator pick

Plain English: what it fixes · effort (S/M/L) · risk · recommended next action.

**1. Stop restarts from killing in-flight workers (zombie flood + lost run progress).**
Every gateway restart orphans running workers — 236 reaped in 42 h, three more today by 10:51 — and each lost run costs a 174–223 K-context session. Live cause: `restart_drain_timeout: 0` while bounces already run drain-then-restart.
*Effort M · Risk med.* **Next:** one card — set `restart_drain_timeout: 300`, keep the F27 drain-gate hotfix armed at every restart (not just sanctioned bounces), and file an upstream RFE for worker checkpoint/resume-on-drain (draft + operator gate). Plugin stopgap in the same card: trial **planning-with-files** (pinned commit, code-read first — it is NOT catalog-reviewed) on one heavy lane so workers can rebuild state from plan files after a kill. *(No plugin fixes the core bug — survey §6.1.)*

**2. Make triage auto-decompose idempotent (duplication is live, 2 incidents already).**
Five decompose events in 42 h with `auto_decompose: true`; duplicated children double-execute side effects and burn worker sessions. No plugin dedupes cards.
*Effort S–M · Risk low.* **Next:** one card — decompose marker per card + `idempotency_key` on every spawned child (kernel already returns the existing id); optionally scope auto_decompose to operator-prose intake boards. Upstream RFE candidate (draft + gate).

**3. Upstream the 4 candidate carries — shrink the carry stack 11→7.**
Stack verified 784 commits behind origin/main; 0 retire candidates; PR branches already prepared for bfdea091 (`862e87c2` suggested-session-rows) and 1ec1dce4 (`a6c85c32` one-shot source labels); fa69c0e5 (compression degradation mode) needs a branch authored; 7ee59473 rides upstream #143206.
*Effort M · Risk low.* **Next:** these are **public filings — draft + operator final gate for every PR, never auto-file** (OPERATOR GO + sha256 match before any submit). One card per PR, or one orchestration card with per-PR children.

**4. Close the update-script test-net gaps before the next `hermes update` breaks a carry.**
3 of 11 carries (drain gate, compression guard, prompt diet) have no post-cherry-pick regression check; same-day re-runs force-overwrite the carried branch; a bare `hermes update` bypasses the script with no dispatch pause.
*Effort S · Risk low.* **Next:** one script-only card — add 5 missing test files, `STACK_N == 11` assert, date-unique branch (`%F-%H%M`), bare-update guard, write-back to a fresh `local/hotfixes-rebased-<date>`.

**5. Add a gateway dead-man switch + one alternate alert sink.**
All 24 cron jobs alert only to Telegram chat 8158007517 (verified: zero webhook/smtp references in scripts); nothing checks heartbeat-file age, so a silently dead gateway alerts exactly nobody.
*Effort S · Risk low.* **Next:** one card — no-agent heartbeat-age cron (proven alert-only pattern), plus one alternate sink (second chat or gh issue on a private repo) on the 5 most critical jobs only.

**6. Rotate logs before they eat the disk (and mirror them).**
55 MB unbounded (tui_gateway_crash.log 23.6 MB); no logrotate config exists; estate mirrors exclude `logs/` — so after any incident the forensic evidence is the one thing not backed up.
*Effort S · Risk low.* **Next:** one card — logrotate entry (weekly, rotate 8, compress), include rotated logs in the nightly mirror, prune per-card logs >14 d.

**7. Finish DR: wire the second mirror and prove a full-boot restore.**
Restore proven only to config-check boot, never gateway+dispatcher boot; the second mirror target (garg02 / local RAID / second GH namespace) has been awaiting an operator pick since 10-24.
*Effort M · Risk low.* **Next:** operator picks the mirror target, then one card wires it; schedule a quarterly full-stack restore drill through gateway boot + one smoke card on a scratch machine.

**8. Add a main-lane token/cost ledger — recommend the LOCAL jsonl ledger, not session-lens.**
The estate's biggest cost driver (5.06–5.09 M input tokens/session on the heaviest lane) is entirely unmeasured; every cost decision flies on one-off studies. **Pick ONE approach:** recommended = homegrown per-call jsonl ledger keyed by profile/board/run + nightly rollup cron (zero new trust surface, 50 lines, respects the Langfuse-declined canon). Alternative inside the same card: trial **session-lens** (`69bc2b18`) if richer dashboards are wanted — but it has the highest secrets surface of the survey (.env values + vendor endpoint calls, mostly inert on self-hosted LiteLLM), so it needs a code-read of its key-value path first.
*Effort M · Risk low.* **Next:** one card, local ledger; session-lens only if operator prefers dashboards over trust-minimization.

**9. Harden compression with two small plugin trials: hermes-vcc + memlock.**
The 10-23 storm class was an aux-summarizer model failure. **hermes-vcc** (catalog pin `d08eb0ad`) removes the summarizer call entirely — zero-token deterministic compaction, minimal blast radius (caveats: v0.1.0, 1★, port-repo license gap to flag). **memlock** (catalog pin `123b9fd2`) re-asserts pinned instructions after compaction — addresses post-compression contract drift.
*Effort S each · Risk low.* **Next:** two separate operator-approval cards (one per plugin, catalog pin, per-profile scope for memlock — never global scope on a shared HERMES_HOME), trial on one long-context profile each.

**10. Teach the nightly audit to flag stale cards (reclaim=0 blindspot).**
4–9-day-idle cards sit in running/scheduled with zero reclaims while the structural audit passes HEALTHY — it checks structure, not age.
*Effort S · Risk low.* **Next:** one card — age-drift check in the nightly audit (running >24 h without heartbeat, blocked/scheduled >3 d idle) + an operator reopen-or-retire pass on the four named cards (t_05987520, t_6a6ca54c, t_91935e10, t_6e194773).

**11. Sandbox worker terminals with bubblewrap (official).**
59 profiles share one host; a runaway or compromised worker shell can read other profiles' credentials via env. **bubblewrap** (official, v1.2.1 @ `da8d3240`) confines each terminal/execute_code call (read-only root, per-profile writable dir, private /tmp, masked sockets). Caveat: file tools still run on host — it confines shell, not everything.
*Effort S–M · Risk low-med.* **Next:** one operator-approval card — enable `terminal.backend: bubblewrap` per-profile on worker profiles first; **singularity** stays watch-listed for HPC nodes (one backend per host class).

**12. Housekeeping bundle (fast, low-drama).**
(a) Doc-of-record re-stamp: profile census, cron table, session-gc row, `protect_first_n` key name, store sizes; (b) config debris: langfuse marker, anthropic context_window override in a litellm-only tree, committed `.pyc` + `__pycache__/` gitignore, claude-opus-5-5 references in gateway.log explained or documented; (c) `hermes plugins remove langfuse` (declined for fees, pin behind — removal, not re-pin); (d) `hermes plugins enable disk-cleanup` on the default profile (bundled, free, documented protection rules).
*Effort S · Risk low.* **Next:** one card, four sub-items, receipts per sub-item.

---

### Dropped / not proposed
- **R1 shared skill tree** — dropped: live-verified already done (59/59 profiles on `external_dirs`, receipt 183 MB saved). Residual is nil.
- **Canon items** — not re-proposed: Slack xoxb/listeners, Telegram mouse_tracking, Langfuse (fees), secret-redaction-on, LITELLM-YAML LAW changes, skill-evo GEPA cron.
- **nerve, hermes-trove, hermes-workflows, long-conversations**, and the rest of the survey watch list stay watch-listed (see PLUGIN-SURVEY §4); nothing else from the survey's skip list is revived.

*Inputs: ESTATE-REVIEW-2026-10-26.md (t_d325c0e0, commit be2832a) · PLUGIN-SURVEY-2026-10-26.md (t_f5855ec3). All top-5 claims re-verified live 2026-10-26 by t_bf623554. Operator picks via the decision prompt; nothing executed.*
