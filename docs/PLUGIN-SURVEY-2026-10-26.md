> Status: current. Referenced from hermes-estate/docs/OPERATIONS.md (2026-10-26).

# PLUGIN-SURVEY-2026-10-26 — Official + Community Hermes Plugins for Fleet Fit

Task: ESTATE-REVIEW-B (t_f5855ec3) · Research only, nothing installed · Survey date: 2026-10-26
Operator ask (verbatim): "...review any available official or community plugins as well to see if there are any that could benefit us."

Fleet context used for fit: 59-profile kanban fleet on one multiplexed gateway; Telegram-only chat (Slack creds-only by design); self-hosted LiteLLM gateway; Hindsight memory server; GPU/HPC ops (vLLM, Gaudi, K8s); heavy upstream PR/issue work. Pain points: worker crashes on gateway restart, triage duplicating cards, context compression, long-running jobs.

---

## TL;DR

1. **Version hygiene is clean.** 9 of 10 installed catalog plugins are at the current reviewed catalog pin. Only **langfuse** (declined for fees) has drifted: installed `c2a95963`, catalog now **v2.0.0 @ `e1f16143`**. Since it's declined, consider `hermes plugins remove langfuse` in a later housekeeping card rather than updating.
2. **Best-fit new candidates (shortlist of 8 below).** Top trial: **hermes-vcc** (zero-token, no-LLM compaction engine — directly addresses our compression-storm pain without an aux-model dependency), **memlock** (re-asserts pinned instructions after compaction), **planning-with-files** (crash-proof plans + context-rot re-injection), **advanced-delegation** (official — per-subagent model/profile routes for the fleet), **session-lens** (read-only fleet observability incl. compression-distress analytics), **bubblewrap** (official terminal sandbox), **disk-cleanup** (bundled, free — enable only), with **nerve** as a high-fit/high-caution watch.
3. **Two named pain points have no plugin cure.** Nothing in the official registry or community survey fixes *worker crashes on gateway restart* (that's core multiplexing-gateway persistence + dispatcher reclaim behavior) or *triage duplicating cards* (recommend process fix: `kanban_create(idempotency_key=...)` — no plugin found that dedupes cards).
4. **Trust model matters more than the list.** The official catalog (`plugin-catalog/` in hermes-agent, rendered at /docs/plugins) is human-merged, exact-SHA-pinned, security-scanned, with a `removed.yaml` blocklist — installs from raw GitHub URLs bypass all of that. Shortlist marks which candidates are catalog-reviewed vs. raw-community.
5. **Community ecosystem is bigger than it looks**: `topic:hermes-plugin` = **570 repos** on GitHub; the official registry itself has **hundreds of entries**. Curation (this doc) is the value, not discovery.

---

## 1. Where the plugin universe lives (with sources)

| Source | What it is | Key facts |
|---|---|---|
| **Plugin Catalog (official registry)** | `plugin-catalog/*.yaml` in the hermes-agent repo; one YAML per entry; published as JSON at https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json (generated 2026-10-26T09:14Z), browsable at https://hermes-agent.nousresearch.com/docs/plugins | Hundreds of entries; tiers official/verified/community; every entry pins an exact 40-hex SHA bumped only by reviewed PR; `removed.yaml` blocklist refuses installs; capability declarations (tools/hooks/middleware/env) mandatory. Sources: [plugin-catalog README](https://github.com/NousResearch/hermes-agent/tree/main/plugin-catalog), [docs: Plugin Catalog](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog) |
| **hermes-official-plugins** | Supported first-party plugins, Nous-maintained | [repo](https://github.com/NousResearch/hermes-official-plugins) · MIT · **504★** · 81 forks · last push **2026-10-26** (api.github.com/repos/NousResearch/hermes-official-plugins). 18 plugins: homeassistant, spotify, claude-subscription-directsdk, memory-wiki, blender, snyk, touchdesigner, accent-picker, langfuse, rea, xchat, **singularity**, agent-importers, mcp-serve, **bubblewrap**, meshy, **advanced-delegation**, camofox (+ elevenlabs-sfx) ([README](https://github.com/NousResearch/hermes-official-plugins#readme)) |
| **hermes-labs-plugins** | Nous-built but **unsupported** experimental plugins (community tier in catalog, "up for adoption") | [repo](https://github.com/NousResearch/hermes-labs-plugins) · MIT · **128★** · created 2026-10-21, last push **2026-10-26**. Full catalog = **4 plugins**: telegram-business, **inbox** (we run it; upstream PR #33 pending), workflow-record, github-copilot ([README](https://github.com/NousResearch/hermes-labs-plugins#readme)) |
| **Bundled (in-core, opt-in)** | Ship disabled in the repo; enable with `hermes plugins enable <name>` | disk-cleanup, security-guidance (25 rules, Apache-2.0 fork of Anthropic patterns), teams_pipeline, google_meet, image_gen backends, hermes-achievements, kanban/dashboard. Source: [docs: Built-in Plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/built-in-plugins) |
| **Official MCP integrations** | Native MCP client (`mcp_servers` in config.yaml; env-filtered stdio subprocesses, credential-stripped errors, sampling caps); portable "Agent Plugins v1" packages that pin MCP servers (blender, snyk, rea, meshy, touchdesigner, 0bull, aave-mcp); Nous Tool Gateway hosted connectors; `mcp-serve` official plugin (Hermes *as* an MCP server) | Sources: docs [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp), [Tool Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-gateway), official repo README |
| **Community directories** | [0xNyk/awesome-hermes-agent](https://github.com/0xNyk/awesome-hermes-agent) (**5,902★**, CC-BY-4.0, editorial maturity tags; ecosystem snapshot last reviewed 2026-07-16) + GitHub `topic:hermes-plugin` (**570 repos**) and keyword searches | Discord/forum public indices surfaced only via these mirrors |

Community discovery findings that are **not** Hermes plugins despite tagging (skip): iPolloWork (multi-engine agent workbench), internet-court-skill (web3 A2A commerce), agentscope-ai/ReMe + scope-recall-hermes + supermemory/mem0/honcho/Mnemosyne etc. (memory providers — we standardized on Hindsight; re-proposing a second memory backend is churn, not gain).

---

## 2. ALREADY HAVE — version deltas (installed pins vs catalog pins today)

Installed pins from `~/.hermes/plugins/.install-metadata.json` (all `pinned: true`); catalog pins from `plugin-catalog/<name>.yaml` on main, 2026-10-26.

| Plugin | Installed @ | Catalog @ | Catalog version | Delta |
|---|---|---|---|---|
| aux-ledger | `aee39a67` | `aee39a67` | 1.4.0 | current |
| error-ledger | `dd646070` | `dd646070` | 1.3.0 | current |
| wait-ledger | `c44b60aa` | `c44b60aa` | 1.0.0 | current |
| kanban-stream | `d6c3e802` | `d6c3e802` | 1.0.2 | current |
| inbox | `62dbc160` | `62dbc160` | – | current (our `/inbox` PR #33 is a separate upstream change, not in the pin yet) |
| custodian | `d5b4ebfd` | `d5b4ebfd` | 3.0.1 | current |
| degeneracy-guard | `ffc28d0a` | `ffc28d0a` | 1.3.0 | current (catalogued 2026-10-20, `requires_hermes >=0.22.2`; 1-week trial continues) |
| camofox | `190593f4` | `190593f4` | 1.0.0 | current |
| hindsight | `d952b6e6` | `d952b6e6` | 1.2.3 | current |
| **langfuse** | `c2a95963` | **`e1f16143`** | **2.0.0** | **behind** — declined for fees; recommend removal at next housekeeping instead of re-pin |

Already-tested per card (tool-slimmer, toolaria, skill-retrieval — A/B'd 10-23): no action; they don't appear as new installs.

---

## 3. SHORTLIST (8) — verdicts with reasons

Fit legend: 💥 = hits a named pain point. Security notes come from each entry's own catalog disclosure (catalog entries only install at a human-reviewed SHA; raw-GitHub candidates get no such review).

### S1. hermes-vcc — TRIAL 💥 (compression)
- **What:** Algorithmic **no-LLM** context-compaction engine: deterministic regex-extraction summaries instead of a summarizer-model call; zero-token, byte-reproducible, runs inside the built-in ContextCompressor; compacted turns stay searchable via session_search. Derived from pi-vcc (MIT).
- **Who/how healthy:** rain-sk, repo [agentbox-tech/hermes-vcc](https://github.com/agentbox-tech/hermes-vcc) — org repo, **1★**, created 2026-10-08, last push 2026-10-12, **no license file on the port repo** (upstream pi-vcc is MIT), v0.1.0.
- **License:** upstream MIT; port repo license file missing (flag before any adoption).
- **Security:** catalog disclosure: no network, no env vars, no secrets, no telemetry; registers no tools/hooks/middleware; only reads the turns the host passes for compaction; optional `debug: true` writes a metadata-only file. Minimal blast radius in the whole survey.
- **Fit:** our 10-23 compression storm was an aux summarizer-model failure (qwen38-flash-fp8 pin). vcc removes the summarizer call from the compression path entirely — removes that failure class and its token cost fleet-wide.
- **Verdict:** **Trial** on one long-context profile first (pin `d08eb0ad`). Caveats: v0.1.0, 1★, license gap — quality-of-summary must be eyeballed (regex extraction is lossy by design, but lossiness is deterministic and inspectable).
- Source: [catalog yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/hermes-vcc.yaml), [catalog page](https://hermes-agent.nousresearch.com/docs/plugins/hermes-vcc)

### S2. memlock — TRIAL 💥 (compression: instruction drift)
- **What:** Re-asserts pinned standing instructions after context compaction ("pin anchors, detect drift, rehydrate before the model forgets"); audit-then-rehydrate default, cites the instruction-instability/Context-Rot literature.
- **Who:** Sahil-SS9, [hermes-memlock](https://github.com/Sahil-SS9/hermes-memlock) — **18★** MIT, last push 2026-09-17.
- **Security (disclosure):** hooks pre_llm_call/on_session_*; `memlock_setup.py` edits config.yaml + `.claude/settings.json` (with backups) only when run manually; **`scope=global` pins apply to every session sharing the same HERMES_HOME** — per-profile pinning mandatory in our multiplexed layout.
- **Fit:** post-compaction instruction loss is a recurring worker-quality failure in our fleet (agents forgetting their card contract after compression). Small, focused, complements (not replaces) the compressor.
- **Verdict:** **Trial** at catalog pin `123b9fd2`, per-profile pins only.
- Source: [catalog yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/memlock.yaml), [catalog page](https://hermes-agent.nousresearch.com/docs/plugins/memlock)

### S3. planning-with-files — TRIAL (community, NOT catalog-reviewed) 💥 (long-running jobs + compression + crash recovery)
- **What:** Persistent file-based planning for long-running agent tasks: crash-proof markdown plans, session recovery after /clear and compaction, per-turn re-injection against context rot, deterministic completion gate. Hermes surface via its `hermes-plugin`/`hermes-skill` tagging; installs from npm/skills, 60+ agents supported.
- **Who:** OthmanAdi, [planning-with-files](https://github.com/OthmanAdi/planning-with-files) — claims **27,664★**, MIT, created 2026-01-03, last push **2026-10-24** (very active). Star count not independently verified; treat as reported.
- **Security:** no Hermes-catalog review/scanner coverage (raw community); Python/npm supply chain must be pinned and reviewed per our trust rules; writes markdown plan files into the workspace.
- **Fit:** addresses three of our four pains with the boring-artifact approach (files + re-injection + completion gate) that matches our kanban discipline; biggest-maintained option found for long-running-job durability.
- **Verdict:** **Trial** on one heavy-workflow profile, vendored/pinned commit (never floating npm), after a read of the Hermes integration surface. Skip if the synthesis card wants catalog-only adoption.
- Source: [repo](https://github.com/OthmanAdi/planning-with-files) (via GitHub `topic:hermes-plugin` search, stars/pins per api.github.com 2026-10-26)

### S4. advanced-delegation — TRIAL (official) 💥 (fleet leverage)
- **What:** Two extra `delegate_task` routing modes: **model routes** (agent picks a named route — fast/deep/local — per subagent) and **profile routes** (run a subagent as one of our 59 profiles with its model, credentials, skills, SOUL.md; only route names + one-liners reach the model). `hermes delegation config` + `/delegation`.
- **Who:** NousResearch, official repo (504★, MIT, pushed 2026-10-26). v1.0.0 @ `e404b681`.
- **Gate:** requires Hermes **≥0.22.5** (pluggable delegation providers) — verify fleet core version before proposing.
- **Security (disclosure):** no deps, no own network/model calls; writes only `delegation.*` config; a model route's optional `api_key` lands in **config.yaml plaintext** (use `provider:` routes to keep keys in .env/auth.json); listing a profile exposes that profile's credentials/SOUL to callers — route allowlist is an access-control decision.
- **Fit:** turns our sprawled 59 profiles into first-class delegation targets; directly complements kanban fan-out (orchestrator picks the specialist profile per subtask).
- **Verdict:** **Trial** after core-version check; decide the credential-exposure policy before enabling profile routes.
- Source: [catalog yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/advanced-delegation.yaml), [plugin README](https://github.com/NousResearch/hermes-official-plugins/tree/main/advanced-delegation)

### S5. session-lens — TRIAL with scrutiny (read-only ops) 💥 (compression distress + long-running job visibility + cost)
- **What:** Read-only observability (Desktop/dashboard): per-session cost-and-why with full trace, recurring tool-failure detection, **all-profiles fleet view**, provider quotas/balances, model comparison with cheaper-route evidence, and an ops view covering gateway health and **context-compression distress (fallback streaks, ineffective passes, cooldowns)** plus per-cron run-health scoreboards.
- **Who:** abualnassr, [hermes-session-lens](https://github.com/abualnassr/hermes-session-lens) — 3★, MIT, v0.53.2, last push 2026-10-13.
- **Security (disclosure):** reads every profile's state.db + logs + cron/gateway state + config.yaml + .env (key names and the values of keys its adapters use); calls each configured vendor's usage/balance endpoint with Hermes' own resolvers (which may renew Codex/Nous/xAI logins; Anthropic Haiku probe off by default); sends **no session content** anywhere; writes no Hermes state.
- **Fit:** closest single tool to our fleet-ops cockpit gap (compression telemetry is explicitly its surface; aux-ledger covers the aux-call ledger, this covers per-session/cron distress). Self-hosted LiteLLM may leave vendor-quota panels inert — harmless.
- **Verdict:** **Trial** at pin `69bc2b18`, read-only by construction, but code-review the `.env`-value access path first (highest secrets surface among the trials).
- Source: [catalog yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/session-lens.yaml), [catalog page](https://hermes-agent.nousresearch.com/docs/plugins/session-lens)

### S6. bubblewrap — TRIAL (official) (security hardening for worker terminals)
- **What:** Linux terminal backend: every `terminal`/`execute_code` command runs in its own bwrap sandbox at host paths — read-only root, per-profile writable workdir (restricted/workspace/network modes), home dot-entries (credential stores always) + Hermes home hidden, private /tmp + /proc, agent/docker sockets masked, per-command mem/CPU/pid limits.
- **Who:** NousResearch, official (v1.2.1 @ `da8d3240`, requires ≥0.22.2).
- **Security (disclosure):** no deps, no network of its own; drives `bwrap`/`prlimit` binaries; default `network` profile shares host network; **file tools (read_file/write_file/patch/search_files) still run on host** — it confines shell, not everything; dangerous-command prompts retained.
- **Fit:** 59 profiles share one host; caps blast radius of a runaway/compromised worker shell and stops cross-profile credential reads via env. Alternative: **singularity** (official, v1.0.0 @ `d46aced3`) for HPC-node workers where Apptainer is the native runtime and full containment (incl. skipped dangerous-command prompts) is wanted — watch-list it for GPU/HPC nodes.
- **Verdict:** **Trial** per-profile (`terminal.backend: bubblewrap`) on worker profiles; keep file-tool limitation in the risk note.
- Sources: [bubblewrap yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/bubblewrap.yaml), [singularity yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/singularity.yaml)

### S7. disk-cleanup — TRIAL (bundled; enable-only, zero install)
- **What:** Bundled opt-in plugin: auto-tracks ephemeral files (`test_*`, `tmp_*`, cron outputs, stale chrome profiles) and cleans on session end with age thresholds + audit log; `/disk-cleanup` command. Never touches project trees, kanban/, or top-level state dirs.
- **Fit:** 59 profiles × scratch workspaces + our known temp-file churn; free win with documented protection rules. Source: [docs: Built-in Plugins → disk-cleanup](https://hermes-agent.nousresearch.com/docs/user-guide/features/built-in-plugins)
- **Verdict:** **Trial** = `hermes plugins enable disk-cleanup` on default profile first. (Also noted: bundled **security-guidance** — 25 dangerous-pattern rules on writes — is a plausible fleet-wide enable for our PR-heavy work; watch-list, it warns on every hit so decide noise tolerance first.)

### S8. nerve — WATCH (high fit, real caveats) 💥
- **What:** "Supervisory nervous system": typed System-One decisions, evidence-backed **Kanban supervision**, context governance/rehydration, token-budget trajectory control, durable SSH workers. The only surveyed item that aims at kanban-worker supervision + durability directly.
- **Who:** keeltrace, [hermes-nerve](https://github.com/keeltrace/hermes-nerve) — **46★** MIT, v0.3.1, pushed 2026-10-25 (very active).
- **Security (disclosure):** default Reflex backend is **hosted Jev** — every turn's user prompt (≤12k chars) + redacted tool previews leave the box to OpenRouter-Decisions/TypeSafe spending your credits; Laya/OpenJev backends can be run local/self-hosted; hooks across 9 lifecycle points incl. transform_tool_result.
- **Why watch, not trial:** the egress default violates our data-minimization posture, and the local-backend mode needs eval effort (extra local model) we haven't budgeted; hooks breadth is large. Re-visit if (a) we want kanban supervision beyond kanban-stream + custodian, or (b) local OpenJev matures.
- Source: [catalog yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/nerve.yaml)

---

## 4. Watch list (not shortlisted — reasons)

| Plugin | What / source | Why watch, not trial |
|---|---|---|
| **hermes-trove** | DAG SQLite context engine, "never loses a message" ([yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/hermes-trove.yaml), 2★, MIT, v1.1.4) | Replaces the context engine wholesale; stores **full raw transcripts with secret redaction OFF by default**; reads private AIAgent attributes. Powerful but maximalist — revisit only if vcc+memlock prove compaction is still the bottleneck |
| **hermes-workflows** | JSON-DAG background runner w/ gates, fingerprint-resume ([yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/hermes-workflows.yaml), jacobhausler, 2★, MIT, v1.3.6, pushed 10-26, 27 open issues) | Fits long-running jobs, but its own disclosure flags risk: `gate.wait.until_argv` runs agent-authored argv **outside Hermes' approval gate**; run.done wakes instruct the session to auto-dispatch follow-up PRs. Needs serious governance review; overlaps our kanban dispatcher |
| **long-conversations** | Handoff briefs across session boundaries ([yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/long-conversations.yaml), 0★, **no license**, 10-12 push) | Right idea (compression continuity), too green + licenseless; also overlaps memlock + our handoff discipline |
| **rtk-hermes** | pre_tool_call shell-output rewriting via RTK, claims 60-90% token cuts ([repo](https://github.com/ogallotti/rtk-hermes), 298★ MIT) | **Stale: last push 2026-05-04**; not catalog-listed; same lane as tool-slimmer (which we A/B'd) — would need re-benchmark vs prior results |
| **token-optimizer** | "Find the ghost tokens… survive compaction" ([repo](https://github.com/alexgreensh/token-optimizer), claims 2,714★, pushed 10-25) | Cross-agent analyzer, Hermes binding via community topic only; unverified scope; could duplicate session-lens value — re-check after session-lens trial |
| **singularity** | Official Apptainer/Singularity terminal backend ([yaml](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/singularity.yaml)) | HPC-node-appropriate sibling of bubblewrap; pick one backend per host class. Skills + credential files bind-mounted RO; dangerous-command prompts skipped inside sandbox |
| **hermes-hookdeck** | Webhook reliability layer: queue, dedupe, **in-flight event recovery at boot/crash** ([awesome entry](https://github.com/hookdeck/hermes-hookdeck)) | Solves "survive restart" for webhook-driven flows; our traffic is Telegram+kanban+cron, so low overlap today |
| **memory-wiki** | Official dashboard/Desktop tab over local session history ([repo README](https://github.com/NousResearch/hermes-official-plugins#readme)) | Read-only, writes nothing, but mostly a Desktop/curiosity surface; session_search + agenttrace-type CLIs cover audits |
| **cronalytics / cronwatch / cron-status-alert** | cron cost/health analytics & failure alerts ([awesome list](https://github.com/0xNyk/awesome-hermes-agent)) | Overlap: inbox already surfaces failed cron runs; custodian runs cron-health 4×/day |
| **snyk** (official) | SAST/deps/container scan via Snyk MCP ([README](https://github.com/NousResearch/hermes-official-plugins#readme)) | Fits PR-heavy work only if we accept a Snyk account + Snyk egress; same fee/vendor objection pattern as langfuse — operator call |

## 5. Skips (named, so nobody re-surveys)

- **langfuse** — declined (fees). Not re-proposed; pin behind → remove at housekeeping. (Docs note: profiles that had it auto-migrate to the catalog plugin — [built-in-plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/built-in-plugins).)
- **labs: telegram-business / workflow-record / github-copilot** — no Telegram-Business accounts, browser-workflow recording not a fleet need (camofox covers browsing), no Copilot subs.
- **Platform bridges** (zalo, feishu, xchat, homeassistant, WhatsApp/Discord/voice bridges, evey suite, xurl-adjacent social packs) — Telegram-only by design; Slack stays creds-only.
- **Memory providers** (trove-class aside; mem0, supermemory, honcho, Mnemosyne, Lians, ReMe, scope-recall, chronicle, clawmem, causal-memory, hexus, penfield…) — Hindsight is our settled backend; second memory layer = context bloat + split truth.
- **Model providers / x402-crypto rails** (abstract, zerosignal, ClawRouter, gondola, agentcash, aave, 0bull, payguard, hurmoz…) — self-hosted LiteLLM; no crypto-spend surface wanted.
- **icarus-plugin** (158★ MIT) — interesting self-memory/fine-tune angle but stale (last push 2026-05-17).
- **Desktop/TUI cosmetics** (accent-picker, codex-skin, blinkenbar, achievements, TackMark, novnc/computer-use viewers…) — headless fleet.
- **agent-importers, mcp-serve, blender, meshy, touchdesigner, rea, elevenlabs-sfx, google_meet, teams_pipeline** — no workflow match.

## 6. Honest gaps & process notes

1. **Gateway-restart worker deaths:** no plugin fixes this; it is core multiplexing-gateway persistence + dispatcher reclaim territory ([docs: multiplexing gateway](https://hermes-agent.nousresearch.com/docs/developer-guide/multiplexing-gateway), [kanban](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban)). Keep it as an estate/core issue; the nearest plugin mitigations are nerve (durable SSH workers, watch) and planning-with-files (worker can rebuild state from its plan file).
2. **Triage duplicate cards:** nothing surveyed dedupes kanban cards. Recommendation for synthesis: process-level fix — triage prompts must pass `idempotency_key` to `kanban_create` (board kernel already supports it and returns the existing id) + nightly audit already detects duplicates.
3. **Method caveat:** registry JSON is 1.28 MB of single-line JSON; entry *names* were verified via the rendered catalog directory and per-entry YAMLs, and community coverage via the curated awesome-list + GitHub searches (`topic:hermes-plugin` = 570 repos, keyword search = 2,273). A tiny tail of registry entries d–z may exist that neither the directory render (paged to ~"c…") nor the searches surfaced; the awesome-list + catalog-page searches covered our pain-point vocabulary (kanban/compression/resume/delegation/dedup) across the rendered pages.
4. **Adoption gate reminder (LITELLM-law-adjacent discipline):** every TRIAL above = separate operator-approved card, install at catalog pin (`hermes plugins install <name>`), keep the pinned-true hold mechanism from t_3d7caa12. Raw-GitHub trials (S3) additionally require pinned-commit vendoring + a code read, since they bypass catalog review.

*Prepared by @research on 2026-10-26 for task t_f5855ec3. Star counts/push dates via api.github.com on 2026-10-26; catalog pins from hermes-agent@main on 2026-10-26; awesome-hermes-agent ecosystem status page itself last reviewed 2026-07-16 (community maturity tags may lag).*
