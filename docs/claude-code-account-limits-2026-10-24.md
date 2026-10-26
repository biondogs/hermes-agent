> Status: superseded by hermes-estate/docs/OPERATIONS.md §2.2 — receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# Claude Code Account Limits & Multi-Profile Sharing Mechanics — 2026-10-24

Task: t_b83974bc (CLAUDE-CODE-2-LIMITS) · Assignee: kanban-board-architect · Host: ga01
Scope: account-mechanics research feeding the Claude Code board-profile pilot. Per the operator ruling of 2026-10-24 (mid-run clarification): **no per-profile OAuth logins** — all wired profiles shell out to the single already-authenticated standalone `claude` CLI on ga01 via terminal/print-mode. The default profile's native Hermes anthropic provider binding is out of scope.

---

## 1. Executive summary

| Verdict | Answer |
|---|---|
| Plan tier | **Claude Enterprise** (Johns Hopkins University org), **not** the Pro-tier account our stale memory claimed. `subscriptionType: "enterprise"`, login method "Claude Enterprise account", org-managed remote settings active. |
| Rolling limit mechanics | An included-usage **5-hour session window is actively metered** (observed "6% used, Resets 2:09pm (America/New_York)" on 2026-10-24). A weekly window almost certainly also applies (see §4 caveats). Limits are per-member/per-account, shared across Claude chat, Claude Code, Cowork, and **across all sessions and machines**. |
| Shared vs independent pool | **One shared pool, by construction and by policy.** One credential (operator ruling) → trivially one pool. Even under hypothetical multi-login, Anthropic meters usage per member account, never per OAuth session. There is no way to "multiply" quota with more logins. |
| Concurrent shared-CLI invocation | **Empirically SAFE at the process level for print mode**: two simultaneous `claude -p` one-shots completed cleanly (exit 0, correct outputs, `~/.claude/.credentials.json` untouched, no lock contention). `~/.claude/.credentials.lock` (flock target) serializes credential access. |
| Safe shareable headroom | **~$2.00 API-equivalent per rolling 5-hour window, and ~$10/week, for the board lane** — thousands of bounded haiku one-shots or roughly 5–15 bounded sonnet-5.5 tasks per window — while reserving ≥75% of the session window for the operator's own interactive use. Caps are enforced Hermes-side in the CLI's own cost meter (verified working on OAuth auth). |
| Biggest non-quota risk | **Governance, not lockout.** This is a university enterprise account; JHU admin analytics, spend reports, audit logs, and the compliance API attribute every token to `jbiondo2@jh.edu`. Board-lane usage is personally attributed to the operator and visible to JHU admins (who are already actively pushing managed settings — the org telemetry policy arrived 2026-10-24). |

---

## 2. Verified account facts (live probes, 2026-10-24 ~17:30–18:10 EDT)

From `claude --version` / `claude auth status` / `claude doctor` / interactive `/status`, `/usage` on ga01:

- CLI: Claude Code **2.1.310** (native install, `/home/arch/.local/bin/claude`).
- `loggedIn: true`, authMethod `claude.ai`, apiProvider `firstParty`, **`subscriptionType: "enterprise"`**.
- Email `jbiondo2@jh.edu`, org **Johns Hopkins University** (`cb80f992-99ae-48ce-9a15-c5d21e608d73`).
- `/status`: "Login method: **Claude Enterprise account**"; default model Opus 5.5; setting sources include "Enterprise managed settings (remote)"; "Auto mode server: Enabled".
- Org policy (`~/.claude/policy-limits.json`, fetched live): `allow_remote_control: false`, `allow_quick_web_setup: false`, `require_trusted_devices: allowed`. Remote-control (claude.ai/mobile steering) is blocked by JHU policy.
- Org pushed remote-managed telemetry settings on 2026-10-24 (~13:34 UTC-mtime) demanding `OTEL_EXPORTER_OTLP_ENDPOINT=https://jhemmslmotelext.johnshopkins.edu:4318`; the operator has that endpoint **firewall-blocked** (t_ff5e3742) and `~/.claude/settings.json` sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `OTEL_SDK_DISABLED=true`.
- Model catalog (org-scoped, `~/.claude/cache/model-catalog/…-cc.json`): **12 models** — opus-5-5, opus-5, opus-4-8, opus-4-7, opus-4-6, sonnet-5-5, sonnet-5, sonnet-4-6, haiku-5-5, haiku-4-5, fable-5, fable-5-1. (The "~14 models" memory note was approximately right; 12 confirmed now.) Opus max effort carries a "3.5× or more usage" warning in the catalog itself.

## 3. Limit mechanics — what a seat actually gets

Current Anthropic plan architecture (docs, 2026): Enterprise comes in two flavors —

1. **Usage-based Enterprise seat** (the current model all legacy seats migrate to at contract renewal): seat fee covers access only; **every token bills the org at standard API rates**; no per-seat usage limits; org/group/individual **monthly dollar spend limits** with a fixed monthly reset (00:00 UTC on the 1st).
2. **Legacy seat-based Enterprise** (Standard = 1.25× a Pro session window, Premium = 6.25×): per-member **rolling 5-hour session window + weekly window**; past the wall, usage credits (off by default) bill monthly at API rates. Weekly resets happen at a per-account fixed time.

**What we observed on this seat:** `/usage` renders a **session-window meter in percent with a wall-clock reset time** ("6% used, Resets 2:09pm") — that is included-allowance metering, which only exists when a seat carries token windows. It also showed the session cost stats panel ($0.0000 cost, token counters per session).

**What we could NOT resolve end-user-side** (needs the org admin console, which only JHU admins can see):
- Whether this seat is legacy seat-based (Standard/Premium) or the new usage-based seat. The observed % meter leans seat-based, but Anthropic does not expose seat flavor to members.
- Whether a weekly window applies and when it resets. `/usage` rendered only the session line, and live refresh is blocked (§5), so no weekly data was obtainable.
- Absolute window size in tokens. Anthropic deliberately publishes no absolute token numbers for seat windows; percentages *are* the interface.

**Design assumption to carry forward (fail-safe):** treat the account as if (a) a 5h session window AND a weekly window both exist and are shared, and (b) any usage past a wall **may bill JHU at API rates**. Designing to a dollar meter (§7) makes the distinction non-critical: the same caps protect both cases.

**Known mechanics that matter for wiring (documented behavior, confirmed where noted):**
- Limits are **per member**, per account — identical for every session, machine, and profile invoking under `jbiondo2@jh.edu`. Switching models does **not** restore access once a wall is hit (limits shared across models), so "fallback to haiku on quota error" is not a mitigation; fallback must leave Anthropic entirely.
- The 5-hour window is rolling per account; heavy agentic sessions deplete it multiplicatively (Opus ≈ several× Sonnet per turn; effort `max` ≈ 3.5×+ usage per the model catalog's own warning).
- `--max-budget-usd` **works on OAuth subscription auth** (verified: probe accepted, ran, reported `total_cost_usd`). This is the per-invocation enforcement primitive. Minimum viable value ≈ $0.05 (system-prompt cache creation).
- `claude -p` reports exact per-call consumption via `--output-format json` (`total_cost_usd`, input/output/cache tokens, turns, duration) — verified. This is the metering primitive for a Hermes-side ledger.

## 4. Shared vs independent pool — verdict and evidence

**Verdict: one pool. Always one pool.**

- By construction (operator ruling): exactly one credential (`~/.claude/.credentials.json`, mode 0600, shared OS user `arch` on ga01). Every profile, plus the operator's interactive sessions, hit Anthropic as the same member account.
- By policy: Anthropic meters seat/team/enterprise usage **per member account** — "usage limits are per member, not applied to the team as a whole"; on usage-based enterprise, one member's usage doesn't reduce others' because nothing is allocated in the first place. Multiple OAuth grants for the same account would not create independent pools; they'd just be multiple doors into the same meter. (The original multi-OAuth research question is moot per the operator ruling, and would have been moot anyway.)
- Corollary: **the operator's interactive `claude` use and board-lane use are indistinguishable to Anthropic.** The only entity that can reserve headroom for the operator is *us*, Hermes-side. That is the entire point of §7.

## 5. Usage visibility — what the operator can actually see

- Interactive `/usage` shows the session-window percent and reset time, **but live refresh currently fails** ("Showing last-known usage as of Nm ago (could not refresh)"; retry also failed). Cause: almost certainly the operator's own `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` hardening (it disables secondary-service calls, which is how the telemetry quarantine is enforced app-side). Egress to Anthropic's API itself is fine (model calls work).
- Consequence for the pilot: **do not design Any alerting/dashboards on in-CLI `/usage`.** The only reliable, real-time source of consumption truth for the board lane is a Hermes-side ledger fed by `--output-format json` cost receipts (§7). The operator can temporarily lift the env var to get a fresh in-CLI reading when desired.
- The Freshest reading captured for the record: **6% of the session window used as of 2026-10-24 late afternoon** (operator's setup + research probes combined were this small).

## 6. Process-level concurrency safety of the shared CLI (empirical)

Files at stake (single shared OS user):
- `~/.claude/.credentials.json` — OAuth tokens (access + **rotating single-use refresh token**). Any clobber here logs *everyone* out.
- `~/.claude/.credentials.lock` — zero-byte flock target; serializes credential reads/refreshes across processes.
- `~/.claude/history.jsonl`, `~/.claude/projects/…`, `~/.claude/sessions/` — per-directory session state; `~/.claude/cc-socks/…` per-PID auto-mode sockets.

**Probe (2026-10-24, full detail in §9):** two simultaneous `claude -p` one-shots (haiku, `--max-turns 1 --no-session-persistence`, separate working dirs, launched the same second) → both returned correct distinct outputs, exit 0, no stderr, ~2 s wall, `.credentials.json` mtime unchanged, `claude auth status` still `loggedIn: true` afterwards. No lock contention, no state corruption.

Residual risks and why they're acceptable / how to keep them closed:
- **Token-refresh race:** if the access token expires while N processes run, one refreshes (rotating refresh token!) under the `.credentials.lock` and the others must pick up the new token. We did not force-expiry-test this path (too invasive); the lock file exists precisely for it and basic concurrency is proven. Mitigation: keep invocations short (one-shot `-p`), and **profiles must never run `claude auth login`/`logout`/`setup-token`** — credential-lifetime operations stay operator-only.
- **Same-directory sessions:** `--continue`/session resume is per-directory; two profiles resuming in one dir would interleave. Mitigation: every wired profile gets its own workdir (kanban workspaces already are per-task) and one-shots use `--no-session-persistence`.
- **Interactive mode from profiles:** do not. The org telemetry-approval and workspace-trust dialogs make interactive mode stateful and human-gated (both were observed mid-run), and concurrent interactive sessions share history/session state needlessly. Print mode skips all dialogs — that is the sanctioned surface.
- `--bare` is **not usable here**: it requires `ANTHROPIC_API_KEY`/keychain and never reads OAuth — flag it so nobody "optimizes" the wrapper into broken auth.

## 7. Safe concurrency / volume model & operator-protection guarantee

### Measured economics of a bounded one-shot (haiku, effort low, max-turns 1, fresh dir)

`--output-format json` receipt: `input 2 · cache_write 3,794 · cache_read 13,391 · output 4` tokens, `total_cost_usd $0.00089`, 1.0 s. The dominant cost is the ~17k-token system prompt+tools, mostly on cached-read rates. The CLI's dollar meter is the right unit — it already encodes model weights and cache discounts the way Anthropic's allowance metering does.

**Working cost model (estimates anchored on the haiku measurement and published model ratios; label as estimates, they are planning figures):**

| Work unit | Typical cost (API-equiv, meter-reported) |
|---|---|
| Bounded haiku one-shot (classify, summarize, small edit) | ~$0.001–0.01 |
| Bounded sonnet-5.5 small task (≤5 turns, Read/Edit only) | ~$0.05–0.30 |
| sonnet-5.5 medium agentic task (10–20 turns, tools) | ~$0.50–3 |
| opus-5-5 medium agentic task | ~$3–15 (several× sonnet; plus 3.5× more on effort=max — catalog's own warning) |

**Scenario modeling against the rolling session window.** Absolute window size is unpublished; observable data: operator's light setup+interactive use ≈ 6% of one session window on 2026-10-24. Community-consensus magnitude for a Pro-class 5h window is on the order of $15–30 API-equivalent (a Standard enterprise seat ≈ 1.25× that, ≈ $20–40; Premium ≈ 6.25×). Design to the conservative end.

| Scenario | Board-lane draw / 5h window | Share of a conservative ($20-equiv) window | Lockout risk to operator |
|---|---|---|---|
| 1 profile, light (haiku one-shots, ≤50/day spread out) | ≤ $0.05 | ~0.25% | none |
| 3 profiles, light (each ≤30 haiku one-shots + 2 bounded sonnet tasks/day) | ≤ $2.00 | ~10% | none — operator keeps ≥90% |
| 1 profile, heavy (opus/sonnet agentic sessions, no caps) | $10–50+ | 50–250%+ | **severe — starves operator same-window and trips weekly wall** |

**The headroom number for the receipt:** with the caps below, the board lane can sustainably consume **~$2.00 API-equivalent per rolling 5-hour window and ~$10/week** without ever meaningfully denting the operator's interactive capacity (≤ ~10–15% of even a conservatively-sized session window; thousands of haiku one-shots or ~5–15 bounded sonnet tasks per window).

### Operator-protection guarantee (to be enforced by the pilot's wrapper)

1. **Board-lane caps (fail-closed, Hermes-side ledger):** ≤ **$2.00 per rolling 5h window** and ≤ **$10.00 per rolling 7 days** summed across ALL wired profiles. When either cap is hit, the wrapper refuses to invoke claude (`exit: budget-exhausted`) and the calling profile falls back to its own configured model. Never bypassed silently; a cap breach is surfaced on the card as a block, not a starvation.
2. **Model/effort allowlist:** haiku-5-5 and sonnet-5-5 only; effort ≤ medium; `--max-turns ≤ 10`; `--max-budget-usd 0.50` per invocation ($5 floor never approached); opus/fable/max-effort are operator-exclusive.
3. **One-shot discipline:** `-p` only, `--no-session-persistence`, per-task workdir (kanban workspace), narrowed `--allowedTools`, never interactive mode, never auth subcommands.
4. **Shared ledger (the coordination mechanism):** one OS user → one ledger file (e.g. `~/.claude-board/ledger.jsonl`, flock-guarded). Wrapper: read ledger → check 5h/7d rolling sums → run `claude -p --output-format json` → append `{ts, profile, cost_usd, tokens, model}` from the receipt. All profiles coordinate through this single file, so they discover exhaustion *before* Anthropic tells them — the operator never competes with a surprise. Ledger doubles as the usage dashboard: `tail`/sum gives real-time headroom, and a trivial cron alert can ping the operator at 50/80/100% of board-lane cap. (This is *necessary* because in-CLI `/usage` refresh is disabled by the operator's own telemetry hardening — §5.)
5. **Fallback semantics:** on quota/limit-class errors (Claude Code reports usage-limit errors distinctly from overload), do **not** retry Claude and do **not** use `--fallback-model` within Anthropic (limits are shared across models — switching cannot restore access). Fall back to the profile's own gateway model and finish the task there; note the degradation on the card.
6. **Credential safety:** credential-lifetime operations (`auth login/logout`, `setup-token`, config edits under `~/.claude/`) are operator-only; profiles' claude usage is read-only w.r.t. credentials.

### Governance ceiling (independent of quota)

Even when quota-safe, board-lane consumption is **attributed to the operator's JHU identity** in org analytics/spend exports (daily refresh, 90-day windows, spend-concentration rankings, audit logs, compliance API). Recommended posture: keep the board lane visually boring (the caps above do this — $10/week is far below the "$13/active-day average developer" figure Anthropic publishes), and if the program ever scales past a pilot, the operator should loop in JHU Claude admins rather than let a spend-concentration report do it for them. Also note: JHU is *actively* managing this deployment (managed-settings push + required telemetry collector, both arrived 2026-10-24), so assume admin attention exists.

## 8. Feasible mitigations, ranked

1. **Hermes-side budget ledger + wrapper (build in pilot)** — the only mechanism that can reserve operator headroom and coordinate profiles; also the only real-time dashboard available given `/usage` refresh is off. Cheap: one script + one jsonl file.
2. **Per-invocation caps** — `--max-turns`, verified-working `--max-budget-usd`, `--effort low/medium`, model allowlist. Zero infrastructure.
3. **Fallback-to-own-model on budget/quota exhaustion** — profile completes work on qwen36-fast et al.; board never hard-fails a card because of Anthropic limits.
4. **Threshold alerts off the ledger** (50/80/100% of board cap) — cron or existing notifier; seconds of work once the ledger exists.
5. **Not feasible / rejected:** per-profile OAuth "quota multiplication" (moot + impossible); API-key billing isolation (would change the operator's personal setup and bypass the enterprise seat — out of scope); `--bare` mode (incompatible with OAuth); in-CLI `/usage`-based dashboards (refresh disabled app-side by the operator's telemetry hardening).

## 9. Evidence log (commands run on ga01, 2026-10-24)

- `claude --version` → 2.1.310 · `claude auth status` → loggedIn, claude.ai OAuth, firstParty, enterprise, jbiondo2@jh.edu, JHU org id cb80f992-99ae-48ce-9a15-c5d21e608d73.
- `claude doctor` → org policy loaded from api.anthropic.com; remote control disabled by org policy; auto-updates disabled by env.
- Interactive `/status`, `/usage` (tmux, home dir) → "Claude Enterprise account"; session window "6% used, Resets 2:09pm (America/New_York)"; refresh failed, retry failed.
- `~/.claude/policy-limits.json` → org restrictions (remote_control/quick_web_setup disallowed, trusted devices allowed).
- Model catalog parse → 12 models (list in §2).
- **Concurrency probe:** two same-second `claude -p 'Reply with exactly: ALPHA-1|BRAVO-2' --model haiku --max-turns 1 --no-session-persistence --effort low` in two dirs → both exit 0, correct outputs, empty stderr, 2 s wall; `.credentials.json` mtime unchanged; `claude auth status` post-run still loggedIn/enterprise.
- **Metering probe:** `claude -p ... --output-format json` → total_cost_usd 0.00089491; tokens in 2 / cache-create 3,794 / cache-read 13,391 / out 4; num_turns 1; 1016 ms.
- **Budget-cap probe:** `--max-budget-usd 0.10` accepted on OAuth auth, ran clean (`total_cost_usd 0.00095291`, result delivered).
- Docs consulted (2026-10-24): Anthropic help — "What is the Enterprise plan?", "Claude Enterprise consumption guide", "How do usage and length limits work?", "Manage usage credits for Team and seat-based Enterprise plans"; Spillway Ops explainers (usage-limits & spend-limits, Sept 2026 data, incl. Sept 14 2026 weekly-limit change −17% vs promo).

## 10. Open items for the pilot / follow-ups

- Seat flavor (usage-based vs legacy seat-based) and weekly reset time: only visible in JHU admin console — ask operator to glance at Members page seat types, or accept the fail-safe assumption in §3 (caps make it moot).
- Exact window size: unresolvable (Anthropic unpublished) — percentages + dollar ledger are the working interface.
- Forced token-expiry refresh race: untested (invasive); `.credentials.lock` presumed sufficient; revisit only if a multi-process logout is ever observed.
- The 6%-used reading predates the research probes; refresh `/usage` after temporarily lifting `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` if a fresh baseline is wanted.

**Bottom line for the pilot design:** wire profiles to the shared CLI through a flock-guarded, ledger-checked, dollar-capped wrapper (`claude -p` one-shots, haiku/sonnet, `--max-turns ≤10`, `--max-budget-usd ≤0.50`, own-model fallback), and the operator's interactive use is structurally protected — the board lane can never spend more than ~10–15% of a session window or ~$10/week, and it coordinates itself instead of racing the operator to an invisible wall.
