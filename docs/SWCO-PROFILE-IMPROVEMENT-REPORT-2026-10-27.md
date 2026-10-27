# software-co profile improvement report (SWCO-REVIEW-3)

**Card:** t_4364a4a2 · **Date:** 2026-10-27 · **Author:** default (orchestrator)
**Inputs:** SWCO-REVIEW-1 internal audit (t_29ccafb6, `SWCO-REVIEW-1-audit.md`, defects D1–D12) and SWCO-REVIEW-2 external research (t_6085f9c9, 7 files, index `SWCO-REVIEW-2-INDEX.md`), plus the 2026-10-22 profile proposal (`profile-proposal-2026-10-22.md`, incl. its §8 execution record).
**Status: REPORT ONLY. Nothing here has been applied.** No config, profile, skill, board, or card was changed. The operator picks what becomes an implementation card.

### Terms used here
- **Lane / profile / seat**: one sw-* Hermes profile. In Hermes a profile is a *template* that the dispatcher spawns per card. An idle profile costs no runtime; it costs config upkeep and adds a routing choice.
- **Hop**: one card-to-card handoff in a chain (e.g. dev → reviewer). Each hop is a queue and a context reset.
- **Two legs**: every recommendation cites (a) an internal finding from REVIEW-1 (`R1:`) and (b) an external finding from REVIEW-2 (`R2:`). Anything that lacked a leg was dropped or moved to §6 "not recommended".
- **Governed** (⚠): touches a surface covered by a GOVERNANCE.md rule. These need extra gating no matter their priority (§5).

### Extra checks I made for this report (read-only)
1. **D1 root cause confirmed in source.** `hermes_cli/kanban_db_dispatch.py:2687 _resolve_worker_cli_toolsets()` pins worker toolsets from `_get_platform_tools(cfg, "cli")`, which reads `platform_toolsets.cli` (`hermes_cli/tools_config.py:578`). Top-level `toolsets:` is never read for workers. `custom_toolsets` (pm-ro, arch-ro, review-rw, ux-rw) has **zero code references** outside tests, so those blocks do nothing. This matches the 10-22 proposal's §8 execution note, which already recorded `custom_toolsets` as inert.
2. **Granularity limit.** The smallest built-in toolset that contains `read_file` is `file` = {read_file, write_file, patch, search_files}. There is no read-only file toolset and no per-tool disable key. **Config alone cannot make a lane read-only while it can still read code.** Config *can* remove whole toolsets (terminal, browser, code_execution).
3. **Rework is low.** Software-co kanban.db (309 tasks): only 2 `changes_requested` events and about 4 true post-fix re-review cards (REVIEW-R2 on w6 branches; QA-005 rework t_c200ec71). Most "R2/R3/R4" titles are parallel review *waves*, not rework. So the audit shows no handoff ping-pong between roles.
4. **The failure limit is effectively 2, not 3.** The `gave_up` events on t_1678e983, t_6e194773, t_f7261f4b, t_7c89f6da and t_e3bc9d63 all show `"effective_limit": 2`. That makes D3 (owner-refused crashes) more costly than the audit stated.
5. **AGENTS.md coverage.** metatron has AGENTS.md/CLAUDE.md. **mprov, mprov-maint and mprov-testenv have none**, and the mprov family is software-co's biggest workload.

---

## 1. Per-profile improvement list

Baseline for all 9 (R1 §1): provider `custom:LiteLLM` (Orb), max_turns 200, no MCP servers, the same 14 disabled toolsets, the same 5 plugins. Because of D1, **all 9 run the same tool surface** (tool_names hash 9d10d4d5).

**On models:** REVIEW-1 has no per-model quality data (no rework rate, no review-defect rate split by model), and REVIEW-2 says model choice matters less than topology (MAST: system design, not model capability, drives failures). So **I recommend no model swaps.** The only model-adjacent items below are missing `fallback_model` entries, which add resilience rather than change the primary model.

### sw-pm — qwen38-flash-fp8 / medium · 28 done · 14.7 run-h (≈10 h of it watch polling)
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| PM-1 | **Re-enable `upstream-issue-watch-poll`** on sw-pm. | D2: the skill is disabled, yet sw-pm owns live watch t_9af16d80. Its state.db shows "Skill … is disabled" errors after the 10-26 22:20 sweep. | Per-role skills are how procedural knowledge reaches a role (Agent Skills, progressive disclosure, tool-mcp §g). MAST: specification/system-design faults are ~44% of failures, and a lane missing its own procedure is exactly that. |
| PM-2 | **Make watch polling cheaper.** Move the 15-min t_b2d3c1c0 sweep's "anything changed?" check into a non-LLM script (cron/wake-driver) that wakes the card only when something changed. Keep the LLM for the response. | D5: 297 scheduled wake runs (~10 h of qwen38 runtime, about 2/3 of sw-pm's run-hours). It is also the board's only rate-limited run. | Deterministic checks belong to the "last word", not prompts (Claude Code best practices, tool-mcp §f). Anthropic effort scaling: simple checks deserve a small budget. MAST's top failure mode is step repetition (15.7%). |
| PM-3 | **Make the declared tool surface match the real job, then enforce it** via `platform_toolsets.cli`. sw-pm really does filing ops through `gh` (terminal 495 calls/24 h), so the "pm-ro" declaration is wrong, not just unenforced. Recommended: keep file+terminal+web+vision+kanban+skills+memory+session_search+todo, and **drop browser and code_execution**. | D1: declared pm-ro, effective = full surface. Its usage shows terminal/write are core work (mprov filing t_31f2b588, t_086a4982). | Lethal trifecta (Willison): don't combine untrusted web content, credentials and an outbound channel in one agent unless needed. OpenAI: give a role only the tools it needs, since tool overlap causes misselection. |
| PM-4 | Add a `fallback_model`: an *existing* alias different from its primary qwen38-flash-fp8 (e.g. muse, which the dev lanes already use). | D10: no fallback on sw-pm; D3/D5 show it is the lane with crash clusters and the rate-limit hit. | LangChain: production agents need durable execution/resume. MAST FC3: premature termination is 6.2%. |

### sw-architect — glm53 (1M) / high · 10 done · 3.4 run-h
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| AR-1 | **Enforce "advise, don't act"** with `platform_toolsets.cli` = file, web, vision, kanban, skills, memory, session_search, todo. **Drop terminal, browser and code_execution.** Route mechanical write work (rebase/push) to a dev lane. Caveat: `file` still contains write_file/patch (check 2). | D1: arch-ro declared, but terminal 54 / write_file 6 / patch 3 calls in 24 h. Rebase/push t_833943dd ran on this lane. | Cognition (Apr 2026): multi-agent works when "writes stay single-threaded and additional agents contribute intelligence rather than actions". Microsoft: advisory participants are read-only. |
| AR-2 | **Prune the unused `spike` and `plan`** from the lane's skill pack, or move them to a card's `skills:` list when needed. | D8: neither was loaded in 30 d. The lane loaded `sdlc-review` once and nothing else. | Anthropic context engineering: "smallest possible set of high-signal tokens". Agent Skills level-1 descriptions are loaded into every session. |
| AR-3 | Add a `fallback_model`. | D10. | Same as PM-4. |

### sw-dev-a / sw-dev-b — muse (262k) / medium · 44 / 40 done · 17.4 / 16.7 run-h (the hot pair)
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| DEV-1 | **Enable the `degeneracy-guard` plugin on sw-dev-b** (twin parity). | D10: on dev-a, pm and docs but not dev-b. dev-a hit 200/200 iterations on t_7096b003 (Orb E2E deadlock). | MAST top mode: step repetition, 15.7%. METR: long-task failures are dominated by repeating failed actions. |
| DEV-2 | **Give the twins one shared skill pack** (same template, different lane name). Union the core; move card-family skills (mprov-*, metatron-*) to the card's `skills:` field instead of baking them into one twin. Notably, `kanban-fix-with-gate-receipts` is only on dev-a. | R1 §1: dev-a has 4 own skills, dev-b 8. Four of dev-b's own skills were never loaded (D8). Twins get different procedures depending on which lane the dispatcher picks. | OpenAI: "role = template variable, not seat"; use one flexible base prompt. LangChain: skills/router give role separation without more agents. |
| DEV-3 | **Every card closes on an executable check plus an attached receipt** (test/typecheck/smoke command output). Make it a card-template field (see X4); the dev lanes are the first adopters. | dev-a's own `kanban-fix-with-gate-receipts` already does this for fix cards. Reviewer R2 rounds show post-fix verification is being done by hand. | Tool-mcp top pattern #1 ("every done is a check, never a claim"). Meta TestGen-LLM/ACH: accept only measured improvements. |
| DEV-4 | **Fail-first tests on bug cards** (write the reproducing test, then fix). Cheap: one line in the card template. | t_6e194773 and t_1678e983 each crashed ×3; QA-005 needed a rework round (t_c200ec71). Regressions are caught downstream instead of pinned by tests. | Claude Code best-practices canonical prompt ("write a failing test that reproduces it, then fix it"); tool-mcp pattern #7. |

*No model change, no toolset change for the dev pair.* They are the legitimate writers, and research supports parallel writers **on separate cards** (Cognition/Microsoft). The 10-23 cap hit (8 each) came from wave bursts and is a capacity question (§2.3), not a profile defect.

### sw-reviewer — glm53 (1M) / high · 24 done · 8.2 run-h · 0 blocks
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| RV-1 | **Audit, then enforce, reviewer independence.** First run a cheap read-only query: where did the 38 write_file calls in 24 h land? If they are review artifacts (findings registers), that is good practice and stays. If any landed in the worktree under review, the reviewer is co-authoring → move the reviewer to a read-only worktree checkout and keep findings as attachments. | D1: review-rw declared "no write", yet write_file 38 / browser_exec 31 in 24 h. | Claude Code: "a fresh reviewer does help, because it hasn't seen your reasoning". Self-review is weak (Huang et al. 2310.01798; self-preference bias 2404.13076). Filesystem-artifact handoffs are good (Anthropic). |
| RV-2 | **Add a scanner step to the review ladder** (Semgrep CLI / Guardian-style skill, run on the diff, output attached). The scanner is the judge; the LLM triages. This replaces the "security ladder in SOUL prose" with a tool. | No sw-* profile has an MCP or a security-scan skill (R1 §1). The security ladder from proposal rec #4 lives only in SOUL text. Security work does show up (SEC-REMODEL t_2450bd52, wave-0 credential fixes). | Tool-mcp §d: security is moving to "agent-inline guardrails … validated by re-running the scanner". Note: the `semgrep/mcp` server was archived 2025-10-28, so use the CLI or Guardian, not that MCP. |
| RV-3 | **Delete or adopt `github-code-review`.** Either fold its useful steps into `sdlc-review` (loaded 23×) or remove it. | D8: never loaded. | Context budget (Anthropic). Avoid overlapping tools/skills that invite misselection (OpenAI). |
| RV-4 | Add a `fallback_model`. | D10. The reviewer is the single verification gate, and its 3 crashes (t_e3bc9d63) stalled it. | Microsoft maker-checker: needs an iteration cap and an escalation path, and a dead checker is a stalled pipeline. |

### sw-qa — muse / medium · 6 done · 2.6 run-h
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| QA-1 | **Keep Playwright via CLI + skill; do not add a Playwright MCP.** Codify the current practice: remove the stale dogfood-first wording and make `metatron-visual-qa-gate` the lane's named procedure. | D7: 0 browser_* calls. The lane drives self-provisioned Playwright 1.64.1 via terminal (t_e8ca03e4). | Playwright MCP README: for coding agents, prefer "CLI + SKILLS" as more token-efficient; MCP is for exploratory/long-running loops. |
| QA-2 | **Add a deterministic pixel-diff step** (baseline screenshot vs new, threshold), with vision_analyze as the second opinion rather than the judge. | The AUTONOMOUS-VISUAL-QA gate uses vision_analyze (9 calls), so the visual verdict is an LLM judgment. | Tool-mcp §a/pattern #6: "deterministic visual gates" and a "non-LLM oracle in the loop" (Chromatic/Percy pattern). |
| QA-3 | See §2.2 for the verifier-seat consolidation option (QA + reviewer). | Light load: 6 cards and 2.6 run-h in 30 d. | Sizing synthesis: merge reviewer+QA into one fresh-context verifier. |

### sw-devops — muse / medium · 6 done · 1.4 run-h
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| DO-1 | **Re-enable `upstream-issue-watch-poll`.** | D2: disabled, yet the lane owns live watch t_6bc4ac45 (UPSTREAM-WATCH-V2). | Same as PM-1. |
| DO-2 | **Enable `github-pr-workflow`** on sw-devops, or stop routing INTEGRATE cards to it (see §2.2 on the overlap with dev-b). | D9: INTEGRATE cards t_6d23461f and t_ddadae10 ran with that skill disabled. | Skills deliver role procedures (Agent Skills). Merge-queue/draft-PR patterns are the standard integrate procedure (tool-mcp §f). |
| DO-3 | **Integrate like a merge queue:** re-run the required checks against the *merged* result before landing, and record the receipt. | Today's W6 chain is serial through sw-devops (t_ddadae10 → t_38b6a5c5 / t_a8b44a04). Bottleneck per R1 §4. | GitHub merge-queue docs: "ensuring the branch is never broken by incompatible changes". This is the standard way to handle many agent PRs without thrash. |
| DO-4 | Prune the never-loaded own skills (docker-ci-parity-masks, metatron-qa-env-ops, tailscale-pinned-qa-relay) **only after** confirming no card family needs them. Otherwise move them to card `skills:`. | D8. | Context budget (Anthropic). |

### sw-docs — muse / medium · 16 done · 4.3 run-h · 6 blocks (all distiller waits)
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| DC-1 | **Write and maintain AGENTS.md for the mprov repos** (mprov, mprov-maint, mprov-testenv), with build/test/PR commands the agents can run. metatron already has one. | Check 5: none of the three mprov repos has AGENTS.md/CLAUDE.md, yet mprov is the board's largest card family (fix wave 10-23, filing ops, docs retrofits). | agents.md (60k+ projects): agents "execute relevant programmatic checks". Tool-mcp pattern #5. |
| DC-2 | **Distiller pre-clearance for docs cards** (see X3). | D4: all 6 sw-docs blocks are distiller-gate waits. | Little's law: every hop is a queue (sizing synthesis). |

### sw-ux — qwen38-flash-fp8 / medium · 5 done · 2.3 run-h · real browser user
| # | Suggestion | R1 evidence | R2 support |
|---|---|---|---|
| UX-1 | **Verify `skills.auto_load` for kanban workers** with a one-card probe (does the session contain the 7 design skills?). If it is inert, put the design skills on UI cards via the card `skills:` field (the path `session_kanban` actually honours). | D6: kanban sessions build skills from `task.skills`. sw-ux made 0 skill_view calls in 30 d, so the design pack may never reach context. | Agent Skills progressive disclosure. The 10-22 proposal's whole case for sw-ux was this skill pack (Cognition "actions carry implicit decisions" → write design decisions down via design-md). |
| UX-2 | Add a `fallback_model`. | D10. | Same as PM-4. |
| UX-3 | Add sw-ux to `board.json`'s roster text so routing descriptions match reality. | D11: board.json still lists the old 8-lane chain. | MAST FC1 (spec/system design ~44%). Routing runs off descriptions (Claude Code subagent docs, cited in the 10-22 proposal). |

---

## 2. Do we need more or different profiles?

### 2.1 Is 9 the right count?
**Short answer: keep 9 profiles for now, add none, and cut hops per card instead of cutting seats.** One consolidation (§2.2a) is worth piloting.

Why I partly disagree with REVIEW-2's "9 → 3–5":
- The sizing research assumed "a handful to a few dozen cards per week". REVIEW-1 measured **0–74 done per day**, with dev-a, dev-b and distiller each hitting the cap of 8 on 10-23. At that load the dev pair is a capacity need, not role cosplay.
- In Hermes, **an idle profile has no runtime cost.** Profiles are templates spawned per card. The research's cost model (Brooks n², always-on coordination channels, "idle seat = fixed coordination cost") applies to *hops per card* and *routing ambiguity*, not to the number of templates in the directory.
- The research's own shrink triggers are mostly **not firing**. Handoff rework and ping-pong are low (check 3: 2 changes_requested, about 4 post-fix re-reviews in 309 tasks). No lane shows tool misselection, and there is no handoff loop. The one trigger that does fire is **idle/light seats**: qa 2.6 h, ux 2.3 h, devops 1.4 h, architect 3.4 h over 30 d.

What the research *does* show clearly, and what this report adopts: **writes single-threaded per card, one fresh-context verifier, read-only fan-out only for breadth work, fix topology rather than prompts** (MAST +15.6pp from topology vs +5–9pp from prompts; DeepMind 2512.08296 17.2× vs 4.4× error amplification). The board already follows the write rule (dev lanes on separate cards). The real gap is that **"read-only" and "no-write" roles are not enforced** (D1), so the topology on paper is not the topology that runs.

### 2.2 Redundant or overlapping profiles

| Overlap | Evidence (R1) | Research (R2) | Recommendation |
|---|---|---|---|
| **(a) sw-reviewer + sw-qa** (both verify) | QA 6 cards / 2.6 h; reviewer 24 / 8.2 h, 0 blocks; UI review rung #5 already consumes QA screenshots. | Sizing synthesis "Keep separate: one verifier seat (reviewer + QA)". Microsoft maker-checker. MAST: explicit verifiers fail less. | **Option, pilot first:** route "verify" as one stage (reviewer runs code review + QA receipt) for non-UI cards, and keep sw-qa for UI/visual cards only. Keep both profiles; change routing. Don't delete sw-qa: it holds the Playwright toolchain and visual gate. |
| **(b) sw-dev-b (landing lane) + sw-devops (INTEGRATE)** | dev-b runs metatron INTEGRATE/landing (t_5979a91c, t_77913927…); sw-devops also runs INTEGRATE (t_6d23461f, t_ddadae10), without github-pr-workflow. | Team Topologies: a platform role exists to *reduce* others' load and has no standing queue. Sizing: "devops → on-demand". | **Pick one integrate owner.** Recommended: INTEGRATE stays with dev-b (it has the skill pack and volume). sw-devops keeps environment/QA-env/watch work (t_e5161c67, t_3f878612) as an on-demand platform lane. |
| **(c) sw-architect + sw-pm** (both "read-and-advise" on paper) | In practice they differ: PM is a filing/write lane (terminal 495), architect does ADRs/adjudication (10 cards). Different models (qwen38 vs glm53/high). | Sizing: "merge architect+PM". OpenAI: split on measured failure only. | **Do not merge.** The research premise (both read-only advisers) is false here: sw-pm writes. What overlaps is "decomposition/triage", which also overlaps swco-butler and default. Clarify that in descriptions, no structural change. |
| **(d) sw-docs into dev** | sw-docs' load is standalone policy/impact retrofits (t_b19bbdd2, t_f21df19d…), not docs trailing a dev's code change. | Sizing: "docs → into the dev that wrote the code (single writer)". | **Do not merge.** The research rule covers code-adjacent docs. Apply it there only: code-adjacent docs ride the dev card (card template, X4). Standalone writing stays on sw-docs. |
| **(e) sw-ux vs dev lanes** | 5 cards, a real browser user (64 browser_exec). | Cognition: keep design intent and its implementation in one head. 10-22 proposal (same evidence). | **Keep.** It is the one lane with a distinct toolset (browser loop) and skill pack, which is the research's own legitimate split trigger. |

### 2.3 Is any SDLC function missing?
The bar comes from the 10-22 proposal's MAST/Cognition caution: add a seat only if it owns a **distinct verification axis** or a **distinct toolset/context**, and only on measured demand.

| Candidate | Verdict | Justification against the "don't over-specialize" caution |
|---|---|---|
| **Security reviewer** (`sw-security`) | **No new profile; add a tool step instead** (RV-2, X5). | The research's security pattern is *a scanner as the judge, inline in the coding loop*, not a seat. A separate security agent would add a hop and an inter-agent misalignment channel (MAST FC2 ~32%) without adding a judge. One caveat favours separation: the lethal trifecta. If a lane ever reads untrusted external content (public PRs/issues) *and* holds credentials, separate those capabilities, but by toolset, not by a new role (X1). |
| **Release management** | **No.** | Already covered by dev-b landing + DO-3 merge-queue discipline + the G-06 public-filing gate. A release seat would add a hop to the serial chain R1 §4 names as the bottleneck. |
| **Data/analytics** | **No.** | No data/analytics card family exists in board history (R1 §2). The 10-22 revisit trigger ("first product with real schema churn") has not fired. |
| **Distiller (formalize, don't add)** | **Recognize it as part of the roster.** | D12: distiller has **62 done** on this board, more than any sw-* lane, and it is the main block source (D4). It is a de facto 10th seat that the roster, board.json and routing text don't mention. Formalizing adds no agent. It makes the real topology visible, which is the MAST FC1 fix. |
| **Ephemeral read-only fan-out** | **Use per card, never a seat.** | Research: breadth-first read work is the one place multi-agent clearly wins (Anthropic +90.2%). The board already did this well (the 4-parallel mprov review waves). The `delegation` toolset is disabled on all 9 (R1 §1), so in-card fan-out is impossible today. **Do not enable it fleet-wide**; at most enable it on sw-reviewer/sw-architect for audit-wave cards, as an experiment. |

**Net:** 9 profiles, 0 added, 0 deleted. Two routing consolidations (verify stage; single integrate owner) and one roster formalization (distiller).

---

## 3. Fleet-wide / cross-cutting improvements

| ID | Improvement | R1 evidence | R2 support |
|---|---|---|---|
| **X1** ⚠ | **Make toolset scoping real.** Write `platform_toolsets.cli` for every sw-* lane (whole toolsets, per §1 rows), and delete or annotate the inert `custom_toolsets`/top-level `toolsets` blocks so the config stops claiming restrictions it doesn't enforce. **Phase 2 (optional, higher effort):** a local carry that either wires `custom_toolsets` or adds a per-tool disable, plus an upstream issue. That is the only way to get a truly read-only lane that can still read files. | D1 (high): identical tool hash on all 9; read-only lanes write. Source confirmed (check 1/2). | Cognition single-threaded writes; Microsoft read-only participants; lethal trifecta; OpenAI scoped tools. MAST: topology fixes beat prompt fixes. Today the role boundaries are SOUL prose, i.e. prompt-level. |
| **X2** ⚠ | **Stop "Kanban owner refused: Gateway disconnected" from burning the failure budget.** Classify it as transient (no failure count, retry after the gateway is back). Short-term alternative: the bounce script drains/pauses so in-flight claims don't hit it. | D3: 20/21 crashes. Check 4: effective failure limit is **2**, so one bounce can make a healthy card give up (5 cards hit `gave_up`). | LangChain: "durable execution/resume" is a baseline production cost. MAST FC3 premature termination 6.2%. |
| **X3** ⚠ | **Distiller pre-clearance instead of block-and-wait.** When a card will need publication text (mprov PR/issue), create the distiller review as a **parallel child at decomposition**, fed the draft as soon as it exists, rather than the dev blocking at the end. Optionally batch drafts per wave. | D4: ~40/59 blocks are distiller waits (median 0.07 h, p90 0.9 h, max 23 h). The cost is churn (block/unblock runs), not wall time. dev-a ~14, dev-b ~16, docs 6. | Little's law: each hop is a queue; reduce hops on the critical path (sizing synthesis). Microsoft handoff anti-pattern. |
| **X4** | **Card template v2.** Add these fields: (1) `acceptance_check:` (the command whose output is the receipt); (2) `skills:` for the card family (fixes UX-1 / DEV-2 delivery); (3) `route:` "lean" (dev → verify) vs "full" (pm → architect → dev → verify → docs), with lean as the default for fix cards; (4) "code-adjacent docs ride this card"; (5) fail-first test line for bug cards. | D6/D8 (skills not reaching context); check 3 (low rework, so the full chain isn't earning its hops on small cards); R1 §4 serial chains. | MAST FC1 spec ~44% (bounded specs are the strongest mitigation); Anthropic "objective, output format, tools, boundaries" per subtask; tool-mcp pattern #1; Anthropic effort scaling (don't run the full pipeline on small cards). |
| **X5** | **Shared security-scan skill** (Semgrep CLI on the diff + secret scan, receipt attached), used by dev lanes pre-handoff and by the reviewer ladder (RV-2). | No scanner anywhere in the fleet (no MCP on all 9). Security cards do arrive (SEC-REMODEL, wave-0). | Tool-mcp §d (scanner-validated, inline, hooks+skills); Claude Code security-review README's prompt-injection caveat: run it on trusted diffs only. |
| **X6** ⚠ | **Skill-pack hygiene pass.** Remove skills never loaded on any lane in 30 d, and move card-family skills to card `skills:`. The 7 "common" skills are never loaded on any lane; decide per skill whether it is a real dependency (e.g. `secret-provisioning-no-leak` is a safety reference, so keep it) or noise. | D8 (long list of never-loaded skills, including "all common skills"). | Anthropic: context is a budget ("context rot"); level-1 skill descriptions cost tokens every session. |
| **X7** | **Consistency sweep:** degeneracy-guard on all write lanes (DEV-1), `fallback_model` on all 9 (PM-4/AR-3/RV-4/UX-2), twin parity (DEV-2). | D10. | MAST step repetition (top mode); LangChain durability. |
| **X8** | **Add the research's "shrink signals" to the nightly board audit** so future sizing decisions are measured: per-lane cards/week and run-h, `changes_requested` + re-review rate per boundary, ping-pong count (card returning to a prior lane), and distiller-wait share. | REVIEW-1 had to compute these by hand. Check 3 shows they are cheap to query. | Sizing synthesis "signals to watch": idle seats, handoff rework, card bouncing, coordination tax. OpenAI/Microsoft: split or merge only on a measured trigger. |
| **X9** ⚠ | **Board hygiene:** fix t_9251b9bc's stale `block_kind`, t_0f8768f4's archived parent, and t_3b7a2143's archived-with-active-run; refresh board.json roster text (+ux, +distiller). | D11, D12. | MAST FC1 (system description must match the running system). |
| **X10** ⚠ | **gh capability walls on sw-pm**: decide whether sw-pm should hold `read:project` and repo-delete rights. **Operator decision, not a recommendation.** The research has no finding either way, so this item lacks its R2 leg. It is listed only so it isn't lost. | D9: t_2beff046, t_cf23a633. | — (no R2 leg; least-privilege/lethal-trifecta arguably argues *against* adding scope) |

**Shared MCPs:** I recommend **none for now.** R2 explicitly favours CLI + skills over schema-heavy MCPs for coding agents (Playwright README; context budget), and the specific security MCP named in the brief (`semgrep/mcp`) is archived. R1 shows zero MCP use and no failure caused by its absence. A shared code-review MCP/bot (CodeRabbit/Greptile/Copilot) has only vendor-published precision data (tool-mcp §b caveats), and RV-1/RV-2 address the independence and security gaps more cheaply.

---

## 4. Prioritized action list

Sorted cheapest-highest-value first. Effort/risk = L/M/H. ⚠ = governed (see §5). "Owner lane" is the lane that would execute if GO'd. Per G-04, any profile/board config change runs on `kanban-board-architect`.

| Rank | ID | Action | Effort | Risk | Expected impact | Owner lane |
|---|---|---|---|---|---|---|
| 1 | PM-1 + DO-1 ⚠ | Re-enable `upstream-issue-watch-poll` on sw-pm and sw-devops | L | L | Two live watches stop erroring. Restores the watch function | kanban-board-architect |
| 2 | DEV-1 ⚠ | degeneracy-guard on sw-dev-b | L | L | Twin parity; guards against the top MAST failure mode on a hot lane | kanban-board-architect |
| 3 | UX-1 | One-card probe: does auto_load reach kanban sessions? | L | L | Settles whether the sw-ux skill pack works at all (affects X4 design) | sw-ux (probe) + kba |
| 4 | RV-1 (audit half) | Read-only query: where did reviewer's write_file calls land? | L | L | Decides whether reviewer independence is already broken | default/kba (read-only) |
| 5 | X9 + UX-3 ⚠ | Board hygiene + board.json roster refresh (+ux, +distiller) | L | L | Removes three stuck-state cards; routing text matches reality | kanban-board-architect |
| 6 | X8 | Add shrink signals to the nightly board-audit template | L | L | Future sizing decisions become measured, not argued | kanban-board-architect |
| 7 | X1 phase 1 ⚠ | Write `platform_toolsets.cli` per lane (whole-toolset scoping); annotate the inert blocks | M | M | Turns the role boundaries from prose into config. Biggest structural fix in the report. Risk: removing a toolset a lane actually uses (canary first, per G-30) | kanban-board-architect |
| 8 | X7 ⚠ | fallback_model on all 9 lanes | L | L–M | Fewer stalls when a primary alias fails. Uses existing aliases only (no LiteLLM change) | kanban-board-architect |
| 9 | X4 | Card template v2 (acceptance_check, skills, route lean/full, docs-ride, fail-first) | M | L | Attacks MAST FC1 (~44%) directly. Cuts hops on small cards. Fixes skill delivery | swco-butler/sw-pm template + kba |
| 10 | X3 ⚠ | Distiller pre-clearance as a parallel child at decomposition | M | M | Removes most of ~40/59 blocks and their run churn on dev/docs lanes | kanban-board-architect (skill/template) + distiller |
| 11 | DO-2 / §2.2b ⚠ | One integrate owner (dev-b); devops becomes the platform/env lane | L | M | Removes duplicate INTEGRATE path; fixes skill gap D9 | kanban-board-architect (descriptions) |
| 12 | DEV-2 + X6 ⚠ | Twin skill-pack unification + skill hygiene pass | M | M | Smaller context per session; same procedures whichever twin runs. Risk: pruning a rarely-needed skill | kanban-board-architect |
| 13 | AR-1 / PM-3 ⚠ | Lane-specific scoping (architect drops terminal/browser/code_exec; pm drops browser/code_exec) | L (after X1) | M | Architect becomes advise-only. Write work routes to devs | kanban-board-architect |
| 14 | RV-2 + X5 | Shared security-scan skill (Semgrep CLI + secret scan) in dev pre-handoff and review ladder | M | L | First scanner in the fleet; security judged by a tool, not prose | sw-devops (build skill) → kba (install) |
| 15 | DC-1 | AGENTS.md for mprov, mprov-maint, mprov-testenv | M | L | Agents get runnable build/test/PR commands on the busiest repo family | sw-docs |
| 16 | QA-1 / QA-2 | Codify Playwright-CLI practice; add deterministic pixel-diff gate | M | L | Visual verdicts get a non-LLM judge | sw-qa |
| 17 | DO-3 | Merge-queue-style integrate (re-run checks on merged result) | M | L | Fewer broken-main incidents in wave chains | sw-dev-b / sw-devops |
| 18 | §2.2a | Pilot "verify" stage: reviewer covers QA receipt on non-UI cards | M | M | One less hop on non-UI cards. Keeps fresh-context verification | swco-butler routing + kba |
| 19 | PM-2 | Non-LLM change-detector for the 15-min filing sweep | M | L | Cuts ~10 h/30 d of LLM polling and the rate-limit exposure | sw-devops (script) + kba (cron) |
| 20 | X2 ⚠ | Owner-refused = transient (carry + upstream issue), or bounce-drain fix | H | M | Ends the crash class (20/21) and false `gave_up` at effective limit 2 | kanban-board-architect (carry) |
| 21 | X1 phase 2 ⚠ | Carry: wire `custom_toolsets` / per-tool disable, plus upstream issue | H | M | True read-only lanes that can still read code | kanban-board-architect (carry) |
| — | X10 ⚠ | sw-pm gh token scope | — | — | Operator decision only (no R2 leg) | operator |

**Suggested first bundle** (one fleet-change card, all low effort/low risk): ranks 1, 2, 5, 8. **Suggested second card:** rank 7 (X1 phase 1) with canary seats, since it is the structural fix the rest depends on.

---

## 5. Governed-surface flags

**Nothing in this report touches `/local/compose/aistack/litellm/config.yaml`.** The fallback_model items (X7) reference *existing* LiteLLM aliases from profile config only. If an implementer finds a needed alias missing, that becomes a **G-01 LITELLM-YAML LAW** matter: `kanban_block(needs_input)`, operator request + two confirmations. Never add it as a side effect. **G-33** applies if any implementing card pushes the software-co or estate repo while a dirty protected delta exists.

| Item(s) | Governed surface | Rule(s) | Extra gating needed |
|---|---|---|---|
| PM-1, DO-1, DEV-1, DEV-2, X1, X6, X7, AR-1, PM-3, UX-1 fix, DO-2 | Another profile's `config.yaml` / skills tree, ≥2 profiles | **G-04** (meta-work → kanban-board-architect), **G-30** (fleet-change checklist: pre-tag, whole-file diff, canary seats, atomic apply under lock, census, rollback exercised, canon-sync) | Route to kba; `change_checklist` metadata required. **Preserve every `approvals.deny` line verbatim**, especially the G-01 `*aistack/litellm/config.yaml*` entry present on all 60 configs. The 2026-10-25 deny-list wipe came from exactly this kind of sweep (t_2fa0d71d). |
| X1 (any approach) | Approvals/deny posture | **G-01** (deny entry), **G-32** (only root is `single_query_mode: approve`; all others `deny`) | Toolset scoping must not be done by widening or editing approvals. Do **not** use approvals as a substitute for toolset scoping. Any approvals change elsewhere = drift. |
| X2, X1 phase 2 | Hermes source (local carry) | **G-26** (update path; every carry needs an upstream issue/PR + watch), **G-04**; **G-10** (gateway bounce to activate; sanctioned script only) | Operator GO for a new carry; upstream issue draft goes through **G-06/G-07** if filed publicly. |
| X3 | Distiller pre-publication gate | **G-06** (public-filing chain; mprov exempt from the *operator* gate but the distiller/agent gate stays), skill `kanban-distiller-gate` | X3 changes *when* the distiller runs, never *whether*. Any change must keep distiller VERDICT + sha256 on the exact bytes. Public (non-mprov) filings keep operator FINAL GO. |
| X9, UX-3, X8 | Board state / board.json / audit template | **G-04**, **G-03** (explicit `board=` on every kanban call) | Route to kba. |
| X10 | Credentials / token scope | **G-20** (never change keys/scopes on assumption; ask operator), **G-05** (platform credentials canon) | Operator decision only. |
| PM-2 | New cron / wake driver | **G-14** (every parked card needs a wake driver; don't break the existing driver), **G-05** (cron `deliver: telegram`, never `all`) | Keep `fleet-wake-driver.py` semantics intact. |
| §2.2 consolidations (if ever escalated to deleting a profile) | Profile deletion, banks | **G-00** (nothing permanent until operator declares), **G-12** (tombstone + tarball), **G-13** (bank deletes operator-GO'd) | Not recommended now; listed for completeness. |
| DC-1 (if AGENTS.md lands in a public repo) | Public commit | **G-06**, **G-07** (no internal specifics in public text) | mprov is exempt from the operator gate per G-06; G-07 wording discipline still applies. |

---

## 6. Considered and not recommended (missing a leg or contradicted)

- **Model swaps on any lane.** No R1 quality-by-model data, and R2 says topology dominates. Revisit after X8 produces per-lane rework data.
- **9 → 3–5 seat consolidation now.** R2's volume assumption doesn't match R1's measured load, and R2's own shrink triggers (rework, ping-pong, misselection) don't fire in R1/check 3. Only the light-seat trigger fires, and in Hermes light seats are nearly free. Revisit with X8 data.
- **New security / release / data profiles.** See §2.3.
- **Shared review/memory/Playwright MCPs.** No R1 failure motivates them; R2 prefers CLI + skills for coding agents.
- **Enabling `delegation` fleet-wide.** R2 supports read-only fan-out, but parallel write fan-out is the documented failure (Cognition). Any trial must be lane-limited.

## 7. Sources
- Internal: `/home/arch/.hermes/kanban/attachments/t_29ccafb6/SWCO-REVIEW-1-audit.md` (D1–D12, §1–§4).
- External: `/home/arch/.hermes/kanban/attachments/t_6085f9c9/` — `SWCO-REVIEW-2-INDEX.md`, `TEAM_SIZING_SYNTHESIS.md`, `multi-agent-role-consolidation-research.md`, `failure-modes-report.md`, `agentic-coding-team-tool-mcp-patterns-report.md`, `agent_scaling_evidence.md`, `multi-agent-frameworks-report.md` (per-claim URLs and verification tags live there).
- Prior decision record: `docs/profile-proposal-2026-10-22.md` (incl. §8 execution notes on inert `custom_toolsets` and `skills.auto_load`).
- Rules: `/home/arch/hermes-estate/docs/GOVERNANCE.md` (G-00…G-33).
- Read-only checks this card: `hermes-agent/hermes_cli/kanban_db_dispatch.py:2687`, `hermes_cli/tools_config.py:578`, `toolsets.TOOLSETS`; software-co `kanban.db` task_events (`changes_requested`, `gave_up` payloads); repo-root AGENTS.md scan of `/local/projects/*`.
