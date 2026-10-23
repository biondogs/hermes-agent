# METATRON-ARCH-BRIEF — Foundational redevelopment architecture brief

**Status:** DRAFT FOR OPERATOR DIRECTION — §7 decision gate open; brief is not final until D1–D8 are answered.
**Card:** t_77ba5a4b (METATRON-ARCH-1) · **Author:** sw-architect · **Date:** 2026-10-23
**Binding inputs:** `OPERATOR-DIRECTION.md` (@8d70770 — verbatim Q1–Q8 + 8 locked constraints) · `INVENTORY.md` · `REVIEW-CHARTER.md`
**Evidence base:** METATRON-CONTEXT.md (DOC-1 heritage sweep, t_668275f1) · findings registers + REVIEW-NOTES from R1-V1 (t_ff37197e, 40 findings, master@811e335), R2-V2 (t_712f7faa, 17 findings, v2@b2c1a5b), R3-GUI (t_b68a8d3b, 26 findings, feature/gui-editor@838f88c) · direct read-only spot-checks in /local/projects/metatron at the pinned refs (branch tips, `PHASE_ORDER` in workflow.py, `src/metatron/project/` tree, EDITOR-ARCHITECTURE.md non-negotiables — re-verified 2026-10-23).

Every preserve/discard claim below carries its reviewer-evidence citation. All 83 register findings were reconciled against the three REVIEW-NOTES before adoption; claims I could not ground in evidence are marked **[gated]** and routed to the operator gate (§7) rather than assumed.

---

## 1. The foundational concept, restated from evidence

Independent of any of the three implementations, this is what the repo's history says metatron *is* — stable from the first commit (`effc861`, 2026-06-05: *"initial scaffold for Metatron — AI agent harness for academic writing"*) to the last (`838f88c`, 2026-09-22).

### 1.1 The problem

Writing a scholarly document is a **recursive knowledge-transformation process** — plan, draft, review, revise, with universal back-edges — not a linear pipeline. v2's research corpus (*How Humans write.md*, ~1100 lines grounded in Flower & Hayes, Bereiter & Scardamalia, Kellogg, Sommers; commit 24593fd) names fixed-order pipeline thinking the repo's "largest architectural gap," and the repo's own three-way phase-model contradiction (12-linear in code / 10-cyclic in spec / 9 in changelog; METATRON-CONTEXT §3) proves it was never resolved in practice.

Existing AI writing tools fail this user in two documented ways:

1. **They fabricate.** research-lifecycle-v2.md §0.2 (v2 branch) documents 17–33% fabrication rates in comparable tools whose "verification" is source-*existence* checking only, and declares the fabrication ship-gate **retroactively blocking** — the operator's highest-certainty value in the entire corpus (METATRON-CONTEXT §4.1: "trust over fluency").
2. **They take the author's work hostage.** Cloud relays, proprietary blob storage, hidden provenance, no attribution of what the machine touched. The operator rejected category members on exactly these grounds (Liveblocks rejected as "contrary to the self-hosted vLLM setup"; ADR-0001 rejected DB-blob storage as "recreating the JSON-blob problem with better plumbing").

### 1.2 Metatron's answer (what it is)

A **self-hosted, open-source agent *harness* — not a chatbot** — that scaffolds a single human author through the research/writing lifecycle:

- orchestrates specialist agents (research, outline, draft, cite, review) around the lifecycle,
- **the user's own plain-text files are the product** ("dissertation is the product" — ux-replan doc, v2), portable and externally editable, deletable by `rm` (ADR-0001 decided force),
- **every change — human or agent — is attributed and revertible**, by the user and by the harness (checkpoints from the first commit 06f4627; operator Q2 verbatim: revertible "by the user or the harness as needed"),
- **citations must resolve to verified fetched records**; trust gates fluency,
- the human remains the author; machine contribution is disclosed (v2 voice-profile non-goal: *"not an authorship-detection evader"*), **[gated D5]**,
- the server is the single authority and clients observe-and-request (EDITOR-ARCHITECTURE §1.1: "WorkflowManager is the sole server-side authority; the Y doc is content, never state").

### 1.3 For whom

A single researcher/writer (the origin: an ABD-stage graduate student — the corpus cites CGS attrition data deliberately) working locally against **self-chosen LLM endpoints** — private vLLM/Ollama (the "direct-ga01:8001/v1" posture, commit 0a30617), OpenAI-compatible cloud APIs, and Anthropic-compatible endpoints (operator Q5; note master's provider defaults were Anthropic-*named* while shipping no native Anthropic transport — R1 inventory flag; both transports are now first-class requirements).

Single-user first (operator Q4; in-repo anticipation 48468e5: "no feature gets built that only a second human would use"). A one-notebook-like collaborative future is explicitly *possible* and explicitly *not now*.

### 1.4 Core invariants (implementation-independent — these survive every rewrite)

| # | Invariant | Evidence |
|---|---|---|
| I1 | **User-owned artifacts.** The document is the user's plain-text files in a project directory; portable, externally editable, no content trapped in app-internal storage. | ADR-0001 (v2); operator intent evidence §4.3; Q2 revisioning language |
| I2 | **Attributed, revertible change history.** Every document change records actor (human vs agent), surface, and rationale; history is append-only; both user and harness can revert to any point; human and agent changes never silently merge. | First commit's human-in-loop checkpoints; ADR-0002 trailer protocol; operator Q2 verbatim |
| I3 | **Trust over fluency.** A claim must trace to a verified, fetched source before its text ships; existence-only checking is the documented failure mode of the category. Provenance disclosure is a feature, not a leak. | research-lifecycle-v2 §0.2 ("retroactively blocking"); ROADMAP ship-gate notice (R2 §5 called it "the single highest-value sentence in the v2 corpus") |
| I4 | **The human is the author.** The tool scaffolds knowledge-transformation, not knowledge-telling; agent-drafted text is ledgered as such. | roadmap-v2 pillar 3; ux-replan principle 3; voice-profile non-goal (value reversal of the June Scribbr module) |
| I5 | **Self-hosting as identity.** Nothing about the core loop transits or depends on third-party relays; providers are endpoints on the user's own terms. | textual-serve "nothing transits third-party relays" (PR #80); Liveblocks rejection; operator Q5 |
| I6 | **One authority, typed contracts.** Exactly one engine owns lifecycle state and document truth; every other surface (CLI, web UI, test harness) observes events and requests transitions. Agent output lands as *reviewable suggestions*, not silent writes, wherever feasible. | EDITOR-ARCHITECTURE §1.1; R1's top arch finding (4 orchestration paths) is the negative result; suggestion-set model (R3 §2.1) |
| I7 | **No silent failure.** Every stage/stage-adjacent operation returns a typed status; error text can never masquerade as success output; anything persisted must be able to state what it did *not* capture. CI must be able to signal red on every branch. | R1 verdict (six silent-wrong-output S1/S2 findings + V1-021); R1-002 (checkpoints lying is "the killer"); GUI-004 exit-0 mask; CI-blindness recurrence #2 |
| I8 | **YAGNI with teeth.** No feature that only a second user (or a hypothetical future) would use. Multiplayer machinery, presence, speculative subsystems — out until a real user needs them. | 48468e5 rule; eedf06 gateway cut; operator Q4 |

### 1.5 Non-goals (scope fences — most scope creeps through silence, so make them explicit)

- **Not a chatbot / general assistant.** Surfaces exist to move a document through a lifecycle.
- **Not multi-user.** No accounts, no presence, no per-user permissions, no CRDT in v1's storage core. **[gated D7]**
- **Not a hosted SaaS.** No relay, no telemetry dependency, no server fleet. One user, one machine, one process (plus a browser tab).
- **Not an citations-launderer.** No "make this sound undetectable" posture. **[gated D5]**
- **Not a research search engine.** Connectors exist to feed the trust gate, not to be a product themselves (OpenAlex/Unpaywall/Retraction-Watch were already down-selected in v2's own honest ⬜ annotations).

---

## 2. Adjudication of the source lines

All three lines are source material (operator Q1). None is a fork candidate: master carries structural accidental complexity at the orchestration root (R1); v2 is 49 commits stale with a live S1 (tar CVE, V2-001) plus an *introduced* S1 (import-time `.env` cwd-trust, V2-002) — R2's verdict "components catalog + negative-results list" is adopted; gui-editor has zero CI runs ever and test infrastructure that cannot fail (R3). **Disposition: harvest concepts and named components; do not inherit any branch's wiring or lineage.**

### 2.1 What SURVIVES conceptually (cross-checked against the registers)

**From v1 (master@811e335) — R1 §3, register-checked:**

| Concept | Evidence check | Carries as |
|---|---|---|
| LLM client *shape*: single handcrafted OpenAI-protocol client, streaming + tool-call accumulation, transient/retry classification curated for local vLLM/Ollama | Sound per R1, **except** retry-state corruption (V1-008) and asymmetric reasoning-content handling (V1-033) — both are rewrite requirements, not inheritances | Provider-layer design input; fix V1-008/033 class |
| `message_normalize.py` provider-shape validation for OpenAI AND Anthropic formats | Register-clean; directly satisfies operator Q5's two-transport requirement as the shared pre-flight | Near-verbatim harvest candidate |
| Workflow phase state machine + atomic persistence (tmp-file+replace) + typed event bus (workflow.py/events.py/console.py — "the best code in the tree" per R1) | Register-clean at concept level; V1-002 (checkpoint capture lies) and V1-026 (parallel context mutation) are the defects to design out via typed snapshots and single-writer discipline | Core design input; see D3 for the phase *model* choice |
| 10-stage domain topology (research/outline/draft/cite/review/synthesize/finalize/analyze/evaluate/RAG) as a lifecycle vocabulary | "Genuinely good paper-writing topology; the wiring is broken, the concepts are not" (R1 §3); the 4-silent-no-op finding (V1-003/004/005) indicts wiring, not topology | Stage catalog input to D3 |
| Citation stack *shape*: parallel existence-verification against arxiv/crossref/pubmed/semanticscholar, per-source classes, fault-isolation, bibtex import/export | Keep shape; V1-023 (false-verify on 50%-match) and V1-009 (greedy regex) must be designed out; existence-only checking is insufficient for I3 anyway (feeds D6) | Component + trust-gate input |
| SQLite-only RAG (sqlite-vec, no external vector DB) + in-memory test store | Matches I5/I8 exactly; V1-010 (hash-seed poisoning), V1-031 (discarded doc IDs), V1-018 (zero-vector fallback), V1-015 (identifier interpolation) are the fix list | Harvest with fixes |
| Research clients (`tools/research.py`): per-API classes, unified Paper dataclass, partial-fault isolation | Register-clean; add rate limiting (V1-030) | Near-verbatim harvest candidate |
| Config precedence env > file > defaults, single settings object | Register-clean; but pydantic `env_file` + v2's load_dotenv S1 (V2-002) define the security boundary: **no cwd-upward env capture, ever** | Pattern harvest |
| Console UX (command shell + live status; "the operator liked it" per R1) | Register-clean | CLI-parity design input |

**From v2 (b2c1a5b) — R2 §2/§7, register-checked:**

| Concept | Evidence check | Carries as |
|---|---|---|
| ADR-0001: project = directory, `sections/NN-<slug>.md` files, per-project RAG/session scoping | Verified FIXED with leak-canary isolation tests (R2 §2.1); margin defects V2-006 (lock TOCTOU), V2-010 (identity churn), V2-016 (session isolation gap) are the fix list | **Adopted as target model (satisfies I1)** |
| ADR-0002 *semantics*: section-granular history, actor/surface/rationale trailers, append-only rollback, Noop degradation, crash recovery | RevisionStore core verified good ("excellent rewrite seed"); wiring unfinished (V2-005), deletions dropped (V2-003), checkpoint hybridization (V2-012) are the negative results | **Semantics adopted verbatim (satisfies I2); substrate = D4** |
| EditSync: external edits detected and committed as `human` actor | Proven-pattern with a provenance test the ADR demanded; V2-007 concurrency gap is the fix | Harvest |
| The cyclic-lifecycle doctrine + Plan/Draft/Review surfaces + synthesis-matrix artifact + claim–source alignment ship gate (roadmap-v2 / research-lifecycle-v2) | Never coded (the repo's biggest unimplemented idea); doc spot-checks honest per R2 §5 | **Adopted as the doctrine; scale is D3** (full 10-phase cyclic vs compact cyclic) |
| TUI fixes (focus model, help overlay, error visibility) | Verified fixed then self-contradicted in-branch docs (V2-014) — keep the lessons, not the docs | UX lessons for any future TUI |
| Connector honesty matrix (✅/🔶/⬜ per feature) | R2 §5 spot-checked: no overstated ✅ found | Backlog triage method |

**From feature/gui-editor (838f88c) — R3 §2/§3, register-checked:**

| Concept | Evidence check | Carries as |
|---|---|---|
| Gateway WS protocol: hello → replay-then-live envelopes (seq/replay), command/request/resolve types, one-at-a-time `busy`, 4401 auth close | "Genuinely good design" (R3 §2.1); defects are at the *edges* (GUI-005/010/014) not in the shape | **Adopted as the front-end contract** |
| "WorkflowManager sole authority; document is content, never state"; clients request, never mutate | The one place it was violated (client-mirrored PHASE_ORDER in workflow.ts) is precisely where pain appeared (R3 §3) | **Adopted as I6; the anti-pattern goes in the ADRs** |
| Suggestion-set model (id/original/proposed/rationale/status/resolvedBy) with content-mutation ≠ state-transition split | "Reviewer-shaped, ready to carry into the rewrite" (R3 §2.1) | **Adopted (instantiate's I6's "reviewable suggestions")** |
| Edit-op vocabulary seam (block.insert/appendDelta/replace/remove, suggestions.set/resolve) from Candidate-B ODR — "Python never speaks the Yjs sync protocol" | "The single most reusable artifact on this branch"; transport is incidental, the typed vocabulary is the seam (R3 §2.1) | **Adopted as the editor seam** |
| Degradation principle (collab unreachable → commands still flow) + stream batching (150ms/512B) + token separation (control token never in browser) + token-redacting loggers | Principles sound; break-sites GUI-005/006/009, token bugs GUI-003 are implementation | Design rules |
| AgentEvent as the single UI-visible signal spine | GUI-018 lesson: the contract needs *public* replay/cursor/unsubscribe the moment a network surface attaches | **Event spine requirement (I6/I7)** |

### 2.2 What is DISCARDED (with reasons)

**v1 structural discards (R1 §4 — the root accidental-complexity list):**

1. **All four orchestration paths** (root `Orchestrator`, `PipelineOrchestrator`, `OrchestratorAgent`, `ExecutionEngine`) → one execution engine with ONE pipeline model. R1's single largest finding; non-negotiable.
2. **The AgentContext grab-bag** (history/metadata/output aliases, ctx_keys shadowing, post-construction context override — V1-005/007/021 root causes) → typed per-stage request/result contracts.
3. **Dead subsystems, ~2k LOC**: curator, profiles, skill_system, context_compress, security module (zero call sites — V1-016/gh#51), viz. Nothing production-reachable; re-derive from actual phase needs if ever.
4. **Duplicate LLM wrappers** (llm_factory, llm_client, type-routing sugar, OpenAIChat alias) → one client interface.
5. **Three duplicate exporters** (docx/pdf/latex, ~90% shared, inconsistent cited-papers styling — V1-014 class) → one template-driven export system with **centralized per-format escaping** (the #54/#55/#56/V1-029 injection class gets fixed once, in one place, not per-format per-release).
6. **The REST server** (unauthenticated 0.0.0.0 + compose port publishing — V1-001 S1, gh#42) → replaced by a single-process local server with token auth, loopback bind default (gui-editor's token posture, minus its GUI-003 bug class via same-origin single token).
7. **Alias/back-compat shims and stubs-as-features** (LiteLLM renames, run/run_async dispatch stack, subagent_process fake success — V1-012) → nothing carries.
8. **Scribbr humanizer default-on** (V1-022: unseeded rewriting of academic text by default) → **[gated D5]**; I4's evidence points to removal.

**v2 discards (R2 §3/§7):** the branch *wiring* (cli-local persistence hooks, dual workspace models, V2-009 process-global session mutation), import-time `load_dotenv()` (V2-002, its introduced S1 — standing ban in the new codebase), the 49-commits-stale lineage itself, checkpoint-verb hybridization (V2-012), in-branch dependency churn (V2-015), self-contradicting docs (V2-014).

**gui-editor discards (R3 §2.2):** the **3-service substrate** (Vite+Hocuspocus+gateway; 3 ports/3 tokens/3 processes for one user — fails the branch's own "does the single human benefit?" test), **Yjs/CRDT as required document core** (revisioning doesn't need it; R3: "keep CRDT as a future collab backend behind the control-op seam" — **[gated D7]**), **awareness/presence machinery** (GUI-011 races; demo-grade value), **two-token browser auth with query-string tokens** (GUI-003's entire bug class), per-connection DirectConnection caches + per-room op queues (exist only because agents used a second door), **client-side PHASE_ORDER hand-mirror** (the concrete anti-pattern: the client renders the phase model the server serves), the O(n²) event feed (GUI-015).

**Repo-wide process discards (recurrence registry, METATRON-CONTEXT §2):** CI that can't fail (exit-0 masks, push-only jobs, never-run branches — GUI-004/#82/recurrence #2 becomes a P0 exit criterion), ad-hoc per-format escaping patches, doc-drift (no more hand-parallel claims; the phase model, counts, and stack names become single-sourced), the 4-identity git mess and untracked automation debris (greenfield repo hygiene from commit one).

### 2.3 Negative-results register → rewrite requirements

The three registers (83 findings) become the new repo's acceptance-test anti-catalog: every S1/S2 is encoded as "this must be impossible in the new design" (typed statuses, no stub-as-success, capture-completeness assertions, `.env` cwd-trust ban, deletion-aware history). This is operator Q7=c's direct feed into the backlog; triage of the 20 old audit issues is **[gated D8]**.

---

## 3. Target architecture (first principles)

The shape below is invariant across the §4 stack options; component *bindings* (frameworks, editor kit) follow the stack decision. Items marked **[D\*]** firm up after the gate.

### 3.1 Layer map

```
┌── Surfaces: CLI (Typer console)  ·  Web UI (browser editor + event feed)  [D2]
│     └── both speak: typed command vocabulary + typed event stream (AgentEvent spine w/ PUBLIC replay/cursor/unsubscribe — GUI-018 lesson)
├── Gateway: single process, token auth, loopback default, same-origin single token
│     hello → replay-then-live envelopes · one-command-at-a-time busy · 4401 on auth failure
├── Lifecycle engine (sole authority): cyclic phase state machine [D3], typed per-stage
│     request/result contracts, single-writer, append-only state log, atomic persistence
│     "one engine, one pipeline model" — the R1 verdict made structural
├── Domain stages (lifecycle vocabulary, from v1's topology + v2's doctrine):
│     research · synthesize · plan/outline · draft · review · revise · cite · export
│     agents produce SUGGESTION SETS / reviewable deltas, never silent document writes [I6]
├── Project & revisioning: directory-per-project · sections as MD files ·
│     RevisionStore (actor/surface/rationale trailers, append-only, deletions included) [D4]
│     · change reconciliation (EditSync semantics) · revert verbs for user AND harness [I2]
├── Trust layer: citation resolution (fetched-record or it didn't happen) ·
│     claim–source alignment verifier · AI-contribution ledger [D6 sequencing] [I3/I4]
├── Evidence layer: research connectors (rate-limited, fault-isolated) · SQLite-only RAG
│     (deterministic IDs, no silent zero-vectors, parameterized identifiers)
├── Provider layer: native OpenAI-compatible transport + native Anthropic Messages transport,
│     message_normalize as shared pre-flight, streaming with correct retry state,
│     reasoning-content policy, config precedence env>file>defaults, NO cwd-upward .env capture
└── Storage: user's files (I1) + .metatron/ internal state + revision history [D4 substrate]
```

### 3.2 Load-bearing design rules (ADR seeds)

1. **One engine.** If a second orchestration path appears, the design has failed (R1-003/004/005/012/021 are the receipts).
2. **Typed status on everything that can fail.** A stage returns success-with-evidence, failure-with-cause, or explicitly-named-skip. Unpersisted/uncaptured state is itself a typed status. (I7 — V1-002 is the killer precedent.)
3. **Document mutations flow through the suggestion model** — accept/reject is content; approve/revise/rewind is state; the two never gate each other (R3's split invariant).
4. **The client renders what the server serves** — no phase models, no status enums mirrored in front-end code (workflow.ts anti-pattern).
5. **No import-time side effects** — no env loading, no schema creation, no network (V2-002 + V1-025 class ban).
6. **Escape once, centrally, per output format** — the #54/#55/#56/#40/V1-029 injection class is one subsystem's responsibility, covered by one property test suite.
7. **Every subsystem must be reachable or deleted.** Integration graph is part of CI: dead code that nothing calls fails the build (kills V1-016-class "shipped but unwired").
8. **CI red-ability is a release gate**, on every branch (fixes recurrence #1/#2 at the root: e2e assertions sanitized at a harness seam once, suites that can't fail are rejected at review).

### 3.3 What is deliberately NOT yet decided here

Stack (D1), front-end form (D2), phase-model granularity (D3), revision substrate (D4), humanizer stance (D5), trust-gate sequencing (D6), collab substrate scope (D7), backlog triage (D8). These are operator forks — see §7. Downstream cards decompose from the *approved* state of this brief only.

---

## 4. Stack options (≥2 credible, per card)

### Option A — **Conservative-reuse (RECOMMENDED): Python-first monorepo, single-process web app**

- **Backend:** Python 3.12+, `uv` packaging, PyPI distribution under the reserved name `metatron`. Framework: FastAPI app serving (a) the WS gateway (harvested gui-editor protocol) and (b) the built SPA as static files — **one process, one port, one token, loopback by default**. Typer CLI for console parity stays in-process against the same engine.
- **Front end:** the gui-editor *concept* minus its substrate: BlockNote/React editor (build verified GREEN by R3 against locked versions: BlockNote 0.54.2, React 19, TS 5.9, vite 7 — and its MPL-2.0 license is already cleared by the permanent-OSS decision d096bbf/2f34532), run **non-collaboratively**: the editor's document model syncs through the command/edit-op seam to the server-side revision store. No Yjs, no Hocuspocus, no presence.
- **Harvest ratio (concept → new code):** message_normalize, research clients, sqlite-vec RAG, citation stack shape, RevisionStore semantics + EditSync, gateway protocol, suggestion model, edit-op vocabulary, console UX — the highest-value proven components from all three lines are Python or protocol-level assets. Python matches the LLM/agent tooling ecosystem and the operator's vLLM posture.
- **Risks / cons:** two languages in one repo (mitigated: pnpm workspace + CI gate like gui-editor's, but actually run); Python packaging errors already bit once (GUI-016: runtime imports in dev extra) → packaging tests are a P1 exit criterion; FastAPI/uvicorn must be *runtime* dependencies. BlockNote is a moving target (0.x) → version pinning policy from day one.

### Option B — **Clean-slate: TypeScript-first full-stack (Node/Bun)**

- Everything re-implemented in TS: agent orchestration, providers (raw OpenAI/Anthropic REST), revision store, editor, gateway in one language; agent execution in the same process family as the UI.
- **Pros:** one language across harness + editor; kills the two-language CI split; CRDT-collab would be native *if ever needed*; no Python packaging surface.
- **Cons:** discards the proven Python harvest precisely where it's strongest — RevisionStore (tested actor-attribution semantics), sqlite-vec RAG, research clients, citation machinery — re-implementing ~all of it against different libraries with no tests carried over; the LLM tooling/agent ecosystem is thinner in TS; higher greenfield risk on the *hard* part (trust gate, revisioning correctness) to save effort on the *easy* part (one build system). Violates the evidence: the repo's durable asset is its Python component catalog.

### Recommendation

**Option A.** Every credible evaluator of the evidence (R1's priority pyramid, R2's "components catalog" verdict, R3's "keep the seam, drop the substrate") converges on the same shape: keep the Python component harvest, keep the typed protocol seams, drop the multi-process substrate. Option B is on the table because the card requires it to be — but its only structural advantage (single language) is bought by discarding the highest-probably-correct assets in the building. **[gated D1]**

---

## 5. Migration & continuity considerations

1. **Old repo:** stays read-only, private, at pinned refs (master 811e335 / v2 b2c1a5b / gui-editor 838f88c). No writes ever (Q7=c). PR #69's remains unmerged deliberately — the branch is a catalog, not a candidate.
2. **New repo:** fresh private repo during redevelopment, named `metatron` (Q3/Q6); MIT + permanent-OSS carried; single wired git identity from commit one (fixes the 4-identity mess); `.gitignore` the internal state dir; **CI mandatory on all branches from the first commit** (the "broken for 8 merges" lesson).
3. **Data continuity:** one known deployment (the operator's own JSON-blob workspaces in `~/.metatron/`). A migration command (P6) converts legacy workspaces → project directories, keyed on the stable legacy **paper id**, NOT title slugs (V2-004's negative result: slug-keyed skip logic masks same-title papers). v2's `project/migrate.py` is the reference implementation but is itself the defect's origin — rewrite, don't port.
4. **PyPI:** name `metatron` retained (Q6). No releases during redevelopment; the name squats safely (history shows prior releases under it).
5. **Doc continuity:** single source of truth per claim. The phase model, agent roster, test counts, and stack names each live in exactly one machine-checkable place (e.g., generated README sections) — the doc-drift registry (three incompatible phase models, 1389-vs-1710, LiteLLM-in-AGENTS.md) is the standing warning. ADRs are written for every D1–D8 outcome and every §3.2 rule broken in practice.
6. **Skills continuity (people, not code):** the constants — human-in-the-loop from commit one, checkpoints, self-host providers — carry into team conventions; the variables (stack names, counts, phase lists) are never hand-asserted in docs again.

---

## 6. Phase breakdown (long horizon: phases → candidate workstreams; task-level decomposition happens in later card waves, AFTER the §7 gate)

**P0 — Groundwork & guardrails** *(the anti-recurrence phase; nothing else starts without it)*
WS: new repo scaffold (uv, package layout, pnpm workspace) · CI skeleton with red-ability gate on all branches + packaging test (no dev-extra-only runtime deps — GUI-016 class) · licensing/MIT + governance docs · ADR skeleton + doc single-sourcing rules · backlog ingestion: registers → tagged anti-requirements/test ideas.
*Exit:* CI signals red on a deliberately broken commit; a trivial provider call round-trips through packaging.

**P1 — Core substrate**
WS: provider layer (native OpenAI-compat + native Anthropic Messages via message_normalize pre-flight; streaming with correct retry state — V1-008 class fix; reasoning-content policy — V1-033 class fix) · typed stage-result contract · the single lifecycle engine (state machine skeleton sized per D3) · typed event spine with public replay/cursor/unsubscribe · config system (precedence + no-cwd-capture ban as a tested invariant) · local server shell with token auth/loopback default.
*Exit:* a two-stage toy workflow runs end-to-end with each surface (CLI + WS) observing the same event stream; every failure mode returns typed statuses.

**P2 — Project & revisioning** *(I1 + I2 made real)*
WS: project model (directory, sections-as-files, registry, per-project scoping with leak-canary tests per the v2 pattern) · RevisionStore per D4 (trailers, append-only, **deletions captured** — V2-003) · change reconciliation (EditSync semantics: external edits → `human` actor) · revert verbs (user + harness) · lock/crash recovery (V2-006/007 class designed out) · migration design draft.
*Exit:* the ADR-0002 provenance test passes in the new stack: external edit + agent pass ⇒ two attributed changes, distinct actors — and the V1-002 "checkpoint lies about what it captured" scenario is impossible (capture-completeness asserted).

**P3 — Research & the trust layer** *(I3: the gate that was never funded)*
WS: research connectors harvested + rate-limited (V1-030) + escalated identifier/escaping discipline (V1-015/V1-029 classes) · citation resolution to *fetched records* (strict matching — V1-023 designed out) · claim–source alignment verifier + fabrication checks (D6 sequence) · AI-contribution ledger · SQLite RAG with deterministic IDs, no zero-vector fallbacks, seeded-hash ban (V1-010/018/031).
*Exit:* a seeded claim set with one fabricated citation fails the gate loudly; a clean set passes with evidence links.

**P4 — Writing lifecycle & agents**
WS: lifecycle stages on the P1 engine (research→plan→draft→review→revise→cite→export, back-edges per D3) · drafting agents emit **suggestion sets**, not writes · voice profile (interview → drafting style; ledgered — I4, D5 posture) · single template-driven exporter family with centralized per-format escaping + Unicode (V1-014/024 class) · synthesis/argument-structure tooling per the v2 corpus (down-selected per D8).
*Exit:* full paper arc runs with every agent output reviewable and every exported artifact escaping-clean under property tests.

**P5 — Front end**
WS: gateway (harvested protocol: hello/replay-then-live, busy, 4401) · browser editor (per D1/D2 substrate; suggestion review UI; checkpoint/rail surface **rendered from server-served phase model**) · event feed with bounded rendering (GUI-015 class) · dev-operability (token gen/redacting loggers/pidfile+tree-kill scripts — gui-editor's small good parts) · console/CLI parity.
*Exit:* a draft streams into the correct section (GUI-001 class impossible by construction: no client-side section guessing — server computes placement), accept/reject round-trips through the revision store, a fresh `pnpm build && pnpm test` + Python suite all run and can fail in CI.

**P6 — Hardening, migration, release**
WS: backlog burn-down (all carried S1/S2-class anti-requirements verified as tests) · workspace migration from v1 JSON blobs (legacy-paper-id keyed; V2-004 lesson) · docker/self-host packaging (self-built image that CI actually builds — #82 lesson) · docs (user/developer/AGENTS generated sections) · release engineering (first public PyPI cut under `metatron`, version tags — the repo never had tags; do not repeat that).
*Exit:* end-to-end acceptance from bare clone → paper → revert → export; operator demo.

Dependencies: P0 → P1 → {P2, P3} → P4 → P5 → P6 (P2 and P3 parallelizable across dev lanes).

---

## 7. OPERATOR DIRECTION GATE — decision list

Per OPERATOR-DIRECTION §3, the eight locked answers are NOT re-asked. Everything below is a genuine remaining fork, each with my recommendation and its falsifier. Answers here scale directly into the phase plan and the ADR set; D1/D2 gate the wave-1 card breakdown itself.

| # | Fork | Options ( recommendation first ) | Why | What it changes |
|---|---|---|---|---|
| **D1** | **Stack** | **(a) Option A: Python-first, harvest-forward, single-process web app** · (b) Option B: TS clean-slate · (c) other | §4 | All of P0–P6's bindings |
| **D2** | **Front-end form for first usable release** | **(a) Browser editor primary + CLI parity; no TUI in v1** · (b) TUI first, browser later · (c) both minimal | The 2-month arrow of your own intent evidence (TUI→shell→Console→serve→editor) ends at the editor; the TUI repeatedly broke in daily use (TUI-ISSUES audit) | P5 lane scope |
| **D3** | **Phase-model granularity** | **(a) Compact cyclic: ~7 states (research→plan→draft→review→revise→cite→export) with typed back-edges + Plan/Draft/Review surfaces** · (b) full v2 10-phase cyclic model · (c) keep a linear rail | The 12-linear model is evidence-broken (3 contradictory models, back-edges never coded); full 10-phase was never validated at any size; (a) gets the doctrine right at shippable cost | Lifecycle engine size; rail UX; D3 is revisitable at any phase boundary |
| **D4** | **Revision-store substrate** | **(a) Embedded shaded git repo (`GIT_DIR=.metatron/history`, v2's RevisionStore semantics: actor trailers, append-only, Noop-degrade — deletions fixed)** · (b) purpose-built SQLite/content-addressed snapshot journal | (a) is the only *proven* implementation (v2 tests) and git earns diffing for free while staying invisible ("no git knowledge needed" README promise); (b) matches the SQLite-only posture but must re-derive diff/attribution correctness from zero. Your Q2 only excludes *requiring* git — (a) uses it internally, never exposes it | P2 workstream; I2 mechanics |
| **D5** | **Scribbr humanizer / evasion stance** (fold of DOC-1 Q2 + R1's ethics flag) | **(a) Do not inherit; voice-profile + contribution ledger only (the July reversal as permanent)** · (b) retain as an explicit opt-in "humanize" tool, always ledgered | The v2 corpus's non-goal is the clearest values line in the history; default-on silent rewriting (V1-022) is its exact opposite | P4 agent roster; ethics section of docs; product positioning |
| **D6** | **Trust-gate sequencing** | **(a) Claim–source alignment + fabrication checks ship as a first-class gate in P3, before expansive drafting features — the "retroactively blocking" stance honored** · (b) existence-only checks first, full alignment later | Unfunded-but-declared was the old repo's biggest honesty gap (the gate existed only as prose for 3 months); (a) is costlier early | P3 size; P4 ordering |
| **D7** | **Collab substrate scope** (fold of R3's posted Q2) | **(a) Confirm: no Yjs/Hocuspocus in rewrite v1 — keep the edit-op seam + event contract so collab can be added later without surgery** · (b) keep the collab substrate live | All three reviewers independently read single-user-first as substrate-out; (a) is also strictly cheaper | P5 surface count; future-collab cost |
| **D8** | **Backlog triage + corpus authority** (fold of DOC-1 Q1/Q3/Q4) | **(a) Confirm: the 20 open audit issues + 6 dependabot PRs are backlog-raw-material only (nobody fixes them on v1) — flag any that actually bit you for priority; (b) confirm the v2 research corpus (How Humans write / roadmap-v2) remains the design doctrine to cite, down-selected per-feature; (c) v2/PR#69's status: superseded-as-branch, harvested-as-ideas (my read — confirm)** | Sets doctrine authority + tells P3/P4 triage which defects had real-world bite | P3/P4 priorities |

**Open-question register (non-blocking, answered anytime):** O-1 (from R3): want an empirical JS/TS test run of the never-CI'd gui-editor suites via sw-qa before its harvest ratio is trusted? Default: no — the register already documents why collab-suite green wouldn't be trusted (GUI-004/017). O-2 (from DOC-1): anything from the dead-line harvest table you want reconsidered (canvas, OpenWiki, multi-platform) — default: stay dead.

---

## 8. Revisit triggers (falsifiers — every ADR that follows from this brief names one)

- Revisit D1 (stack) if the Python harvest proves non-portable in P1 (>30% rework on two consecutive harvest attempts) — that falsifies Option A's premise.
- Revisit D3 (compact cyclic) if P4 shows real writing sessions needing the synthesis-matrix/global-revision-gating machinery as first-class states — that falsifies "compact suffices."
- Revisit D4 (git substrate) if restore-attribution or lock-recovery correctness fights the git substrate more than once — that falsifies "invisible git" and promotes option (b).
- Revisit D7 (no CRDT) the day a second human actually joins a document — that's the trigger the substrate seam exists for.
- Revisit the whole single-process posture if the browser editor needs sub-50ms streaming and the in-process path can't deliver — measured, not assumed.

---

*Prepared by sw-architect, card t_77ba5a4b. Post-gate, this brief finalizes (§7 answers folded in as ADRs), the phase plan converts to implementation cards for sw-dev-a/sw-dev-b, and sw-reviewer gets the ADR set as its adversarial checklist.*
