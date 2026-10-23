# METATRON anti-requirements backlog (W1-2)

> **GENERATED VIEW - do not hand-edit.** Canonical machine-readable register:
> `antireq/requirements.yaml` (schema owner: W1-2, card `t_630ef5d0`).
> Regenerate: `uv run python scripts/gen_antireq_doc.py` (canonical YAML, this path).
> The verbatim review registers live under `antireq/registers/`.
> This view is mirrored to the management repo at `metatron/ANTIREQ-BACKLOG.md`.

**Status:** v1.0 - 2026-10-23 - METATRON-W1-2 (`t_630ef5d0`).
Normative source: METATRON-ARCH-BRIEF.md (FINAL @ be48540) §2.3, §3.2, §6.1 W1-2, §7.1.

Operator Q7=c: **this backlog IS the filing** - no upstream issues, labels,
or PRs on the legacy repo, ever. D8: the 20 legacy audit issues and 6 dependabot PRs
are raw material only (no priority uplift).

## Ingest totals

- **83 register findings** ingested - R1-V1 master@811e335: 40; R2-V2 v2@b2c1a5b: 17;
  R3-GUI feature/gui-editor@838f88c: 26
- Severity mix: S1 4 / S2 19 / S3 40 / S4 20
- **26 anti-requirement classes (AR-001...AR-026)** + explicit dispositions;
  every finding maps to exactly one class or disposition
- Gate: **all S1/S2 findings carry a named ADR answer** - CI-enforced by
  `tests/test_antireq_register.py`

## Defect-class index

| AR | Defect class (the ban) | Worst sev | ADR answer | Test status | Phase |
|----|----------------------|-----------|------------|-------------|-------|
| AR-001 | No unauthenticated or externally-bound network surface by default | S1 | ADR-0003, ADR-0004 | phase-gated (P1 / W1-5 server shell) | P1 |
| AR-002 | Snapshots and restores must be capture-complete | S1 | ADR-0006 | phase-gated (P2 revisioning; seeded today by tests/test_repo_hygiene.py history guards) | P2 |
| AR-003 | Deletions are first-class history | S2 | ADR-0006 | phase-gated (P2 / ADR-0006 acceptance test) | P2 |
| AR-004 | One engine, one contract — no second orchestration path | S2 | ADR-0005 | phase-gated (P1 / W1-4 engine) | P1 |
| AR-005 | Single-writer discipline and crash-safe locks | S3 | ADR-0006 | phase-gated (P2) | P2 |
| AR-006 | Wired features only — advertised capability implies call site | S2 | ADR-0005 | seeded (W1-1 guard landed; real call-graph gate needs W1-4 engine code) | P1 |
| AR-007 | Stable identity — idempotency keyed on stable ids, never slug/title | S2 | ADR-0001 | phase-gated (P2 project model; P6 migration) | P2 |
| AR-008 | No cwd-trusted config; no import-time side effects | S1 | ADR-0003 | seeded (guard landed in W1-1; e2e lands P1 / W1-3) | P1 |
| AR-009 | Stream retries and per-attempt state are deterministic | S2 | ADR-0003 | phase-gated (P1 / W1-3) | P1 |
| AR-010 | Provider symmetry — two transports, one reasoning policy, credentials carried | S2 | ADR-0003 | phase-gated (P1 / W1-3) | P1 |
| AR-011 | Trust gate strictness — fetched records or it didn't happen | S3 | ADR-0008 | phase-gated (P3 trust layer) | P3 |
| AR-012 | Escape once, centrally, per output format | S2 | ADR-0003 | phase-gated (P4 export family) | P4 |
| AR-013 | Fail-loud guardrails — no stub-as-success, no swallow-all, no silent fallback | S2 | ADR-0005 | phase-gated (lint seeded P0; behavioral tests P1/P3) | P1 |
| AR-014 | No silent content mutation; every stylometry pass is ledgered | S3 | ADR-0007 | phase-gated (P4 voice layer) | P4 |
| AR-015 | Resource lifecycle is owned, not GC'd | S3 | - | phase-gated (P1+) | P1 |
| AR-016 | Unsafe composition sinks banned — argv lists, validated identifiers, safe extraction | S1 | ADR-0006 | phase-gated (P2 restore paths; identifier check P3 evidence layer) | P2 |
| AR-017 | Packaging integrity — runtime deps cannot live in dev extras | S3 | ADR-0003 | landed | P0 |
| AR-018 | Dependency hygiene — pins and dedicated bump commits | S4 | - | phase-gated (P0 CI extension — small hygiene card candidate) | P0 |
| AR-019 | Single-sourced truth — docs, enums and capabilities generated, never hand-mirrored | S4 | - | seeded | P1 |
| AR-020 | The client renders what the server serves | S3 | ADR-0004 | phase-gated (P5 front end) | P5 |
| AR-021 | Test infrastructure with teeth — suites must be able to fail | S2 | ADR-0003 | landed (extends each phase) | P0 |
| AR-022 | Public event/replay contract, generation-correct and subscriber-safe | S3 | ADR-0004 | phase-gated (P1 / W1-5 event spine) | P1 |
| AR-023 | No wedged state — every busy/in-flight flag recovers | S3 | - | phase-gated (P1 gateway shell / P5 front end) | P1 |
| AR-024 | Transient failure must not lose user-visible content | S3 | - | phase-gated (P5) | P5 |
| AR-025 | Advertise only what actually landed | S3 | ADR-0004 | phase-gated (P5) | P5 |
| AR-026 | Apply-once content semantics — accept/reject round-trips are exact | S2 | ADR-0004 | phase-gated (P5 front end) | P5 |

## The anti-requirements

### AR-001 - No unauthenticated or externally-bound network surface by default

The server binds loopback by default, requires a token for any non-loopback bind, refuses to start without one, and compares tokens in constant time. An unauthenticated 0.0.0.0 server with published ports must be unreachable by construction, not by configuration advice.

- **Sources:** V1-001
- **Worst severity:** S1
- **Answer:** ADR-0003 (one process, one port, one token, loopback default); brief §3.1 gateway layer; ADR-0004 seam rules
- **Test:** bind-default-refusal — default host is 127.0.0.1; non-loopback bind without token exits non-zero; token compare is constant-time (structural check)
- **Test status:** phase-gated (P1 / W1-5 server shell) - **Phase:** P1

### AR-002 - Snapshots and restores must be capture-complete

A checkpoint captures the full project tree including subdirectories and restore reconstructs full tree state (overlay-restore is banned). Anything persisted must be able to state what it did NOT capture — a typed capture-completeness assertion, never a silent partial backup wearing the name of a full one (V1-002: "checkpoints lying is the killer").

- **Sources:** V1-002
- **Worst severity:** S1
- **Answer:** ADR-0006 (restore reconstructs full tree state including deletions; capture-completeness property test named in its Consequences)
- **Test:** capture-completeness-property — nested dirs + deletions round-trip through checkpoint/restore; incomplete capture returns typed partial status
- **Test status:** phase-gated (P2 revisioning; seeded today by tests/test_repo_hygiene.py history guards) - **Phase:** P2

### AR-003 - Deletions are first-class history

Every tracked-file deletion reaches the revision history as an attributed change and is restorable. History that silently drops rm diverges from the worktree and voids the append-only provenance promise.

- **Sources:** V2-003
- **Worst severity:** S2
- **Answer:** ADR-0006 (deletions-captured is a stated acceptance test, not a hope)
- **Test:** deletion-reaches-history — outline, rm a section, history shows a deletion revision; store status drains to clean; restore revives the file
- **Test status:** phase-gated (P2 / ADR-0006 acceptance test) - **Phase:** P2

### AR-004 - One engine, one contract — no second orchestration path

Exactly one execution engine owns lifecycle state and stage dispatch (7-state cyclic machine, ADR-0005). One execution contract per agent; a stage whose agent lacks the contract fails loudly, never falls through to a stub. Stage I/O is declared slots (typed request/result), metadata is stage-local by default; parallel stages get isolated contexts merged deterministically. All surfaces (CLI, WS, tests) speak the same engine.

- **Sources:** V1-003, V1-004, V1-005, V1-007, V1-013, V1-017, V1-026, V1-038, GUI-001, V2-012
- **Worst severity:** S2
- **Answer:** ADR-0005 (one engine, one pipeline model; all surfaces observe events and request transitions); brief §3.2 rules 1 and 3; §2.2 v1 structural discards 1-2
- **Test:** single-engine-graph — CI fails if a second orchestrator-shaped class appears; slot-binding test per stage (review stage receives the draft slot); metadata-leak test (stage N never sees stage M's knobs); deterministic-ordering test under parallel stages
- **Test status:** phase-gated (P1 / W1-4 engine) - **Phase:** P1

### AR-005 - Single-writer discipline and crash-safe locks

All revision-store mutations (commit, reconcile, rollback) hold the project lock; lock acquisition is atomic (O_EXCL/fcntl); a malformed lock is treated as stale, never raised through every subsequent command; persistence failures after expensive work are caught at the promised boundary and surface as typed status, never as a lost-output traceback.

- **Sources:** V2-006, V2-007, V2-008
- **Worst severity:** S3
- **Answer:** ADR-0006 (crash recovery + lockless-read designed out); brief §3.2 rule 2 (typed status on everything that can fail)
- **Test:** lock-brick-test (malformed lock recovers automatically); concurrent-read-during-write attribution test (two actors, no interleaved commit); disk-failure-after-generation test (content preserved, typed failure)
- **Test status:** phase-gated (P2) - **Phase:** P2

### AR-006 - Wired features only — advertised capability implies call site

A stated commit/feature policy must be realized by wired call sites, not by docs — "every agent pass commits" means every agent path persists. Dead code that nothing calls fails the build. Partial-fault evidence work is rate-limited and fault-isolated, never globally blocking.

- **Sources:** V1-016, V1-021, V2-005, V1-030
- **Worst severity:** S2
- **Answer:** invariant I7 + ADR-0005 error-as-status; brief §3.2 rules 2 and 7 (reachability gate — W1-1 seeded tests/test_repo_hygiene.py import-coverage guard); §2.2 "shipped but unwired" kill; P2 provenance acceptance test
- **Test:** dead-code-graph gate (extends seeded import-coverage guard, P1+); ADR-0002 provenance test extended to every agent surface (full pipeline run shows every pass in history); per-host token-bucket limiter test
- **Test status:** seeded (W1-1 guard landed; real call-graph gate needs W1-4 engine code) - **Phase:** P1

### AR-007 - Stable identity — idempotency keyed on stable ids, never slug/title

Migration and dedup decisions key on the stable legacy paper id / project id, never on title slugs; a missing project_id in an existing config is a hard load error (regeneration only at first creation); ids are uuid4-class, never timestamp-hash.

- **Sources:** V2-004, V2-010, V1-036
- **Worst severity:** S2
- **Answer:** brief §5.3 (migration keyed on legacy paper id — V2-004's negative result); ADR-0001 identity-decoupled-from-name semantics
- **Test:** same-title-migration test (two papers, one fails mid-flight, re-run retries it, not skipped); config-load test (missing project_id raises load error); id-uniqueness collision test
- **Test status:** phase-gated (P2 project model; P6 migration) - **Phase:** P2

### AR-008 - No cwd-trusted config; no import-time side effects

No import-time env loading, schema creation, or network. No cwd-upward .env discovery EVER; cwd-discovered config may not influence network endpoints, proxies, CA bundles, or token-file resolution without explicit user opt-in. Config precedence env > explicit-file > defaults, paths resolved against the project/home root, never CWD.

- **Sources:** V2-002, V1-025
- **Worst severity:** S1
- **Answer:** ADR-0003 config posture (no cwd-upward .env capture, ever — §2.1 config harvest boundary); brief §3.2 rule 5 (V2-002 + V1-025 class ban); W1-1 mechanism — tests/test_repo_hygiene.py dotenv import-time capture guard (landed at scaffold); P1 config invariant per §6.1 W1-3
- **Test:** dotenv-import-guard (landed); cwd-trust e2e — run CLI inside a directory containing a hostile .env (HTTPS_PROXY / SSL_CERT_FILE / LLM_API_BASE) and assert effective network config is unchanged; no-home-write-on-import test
- **Test status:** seeded (guard landed in W1-1; e2e lands P1 / W1-3) - **Phase:** P1

### AR-009 - Stream retries and per-attempt state are deterministic

Every streamed accumulation is per-attempt local; a retry starts from zero state; a result is committed only after a fully successful stream. Partial prefixes and concatenated tool-call JSON can never reach the caller.

- **Sources:** V1-008
- **Worst severity:** S2
- **Answer:** ADR-0003 provider layer (per-attempt accumulators — §2.1 fix V1-008 class; §6.1 W1-3 scope)
- **Test:** stream-retry-reset test — injected mid-stream transport drop with retry yields exactly-once content and parseable tool calls
- **Test status:** phase-gated (P1 / W1-3) - **Phase:** P1

### AR-010 - Provider symmetry — two transports, one reasoning policy, credentials carried

Native OpenAI-compatible AND native Anthropic Messages transports behind one client interface with message_normalize as shared pre-flight; provider credentials/endpoint survive model overrides; reasoning content is never silently substituted for content nor silently dropped — the policy is uniform across complete/stream shapes; one client lifecycle per provider factory (no unclosed clients, no misleading TLS warnings, no CWD-relative certs).

- **Sources:** V1-006, V1-019, V1-033, V2-011, V2-013
- **Worst severity:** S2
- **Answer:** operator constraint 6 / Q5 codified by ADR-0003 (two first-class transports); brief §2.1 message_normalize harvest; §6.1 W1-3
- **Test:** contract tests of REAL agents against the typed complete() signature (no MagicMock sinks — V1-035 method); model-override credential carry-through test; reasoning-content matrix test (3 call shapes x reasoning present/absent)
- **Test status:** phase-gated (P1 / W1-3) - **Phase:** P1

### AR-011 - Trust gate strictness — fetched records or it didn't happen

Citation verification resolves to fetched records with strict matching (year/author corroboration); no partial-overlap threshold can return "verified"; claim-support is a separate explicitly-partial signal; existence-only checking is classified insufficient. Gate failures block loudly with typed status; seeded fabrication fixtures exist from the gate's first commit.

- **Sources:** V1-023
- **Worst severity:** S3
- **Answer:** ADR-0008 (first-class gate in P3; seeded false-citation fixtures; V1-023 designed out)
- **Test:** seeded-fabrication-fails-loudly (P3 exit test verbatim from ADR-0008/§6); 50-percent-overlap-wrong-paper fixture must NOT verify
- **Test status:** phase-gated (P3 trust layer) - **Phase:** P3

### AR-012 - Escape once, centrally, per output format

One template-driven export family owns all per-format escaping and injection defense (bibtex keys and fields, LaTeX/DOCX/PDF escaping), covered by one property-test suite; exporters are stateless or explicitly reset; Unicode coverage (registered fonts) is a test, not a hope; structured citation parsing is per-entry correct (no greedy cross-entry matches); structured metadata rides machine-readable sidecars, not separator-fragile prose.

- **Sources:** V1-009, V1-014, V1-024, V1-029, V2-017
- **Worst severity:** S2
- **Answer:** ADR-0003 (single template-driven export family inside the Python-first monorepo — the harvest-forward decision that makes centralization affordable) + brief §3.2 rule 6 (the #54/#55/#56/#40/V1-029 injection class is fixed once, in one place); P4 single exporter family
- **Test:** per-format escaping property suite (injection + round-trip properties, multi-entry bibtex fixtures, CJK/extended-Unicode export, two-table export isolation)
- **Test status:** phase-gated (P4 export family) - **Phase:** P4

### AR-013 - Fail-loud guardrails — no stub-as-success, no swallow-all, no silent fallback

Stubs are named and never wired as success; fabricated success output is banned; exception-swallowing fallbacks (except-Exception-pass, best-effort that silently drops) may not mask scope loss, credential loss, or work loss — a fallback fires only with a typed degraded status the user is told about; embedding/vector failures raise or mark partial, never poison stores with zeros; retrieval ids are deterministic across processes (no PYTHONHASHSEED dependence) and stable ids are honored by stores.

- **Sources:** V1-010, V1-011, V1-012, V1-018, V1-031, V1-032, V2-009
- **Worst severity:** S2
- **Answer:** invariant I7 codified across ADR-0005/0006/0008 typed-status requirements; brief §3.2 rule 2 (typed status; unpersisted/uncaptured state is itself a typed status; V1-002 killer precedent); §2.2 discard 7 (stubs-as-features carry nothing)
- **Test:** cross-process-embedding-determinism test; re-ingest idempotence test; advertised-backend-unregistered test; swallowed-fallback lint rule (bare except-pass without typed status rejected; CI grep guard over src)
- **Test status:** phase-gated (lint seeded P0; behavioral tests P1/P3) - **Phase:** P1

### AR-014 - No silent content mutation; every stylometry pass is ledgered

No default-on rewriting of user or agent text. Every style/stylometry pass writes an attributed contribution-ledger entry (I4) — silent passes are banned by test, per the ADR-0007 standing rule that no voice feature's validation may target a detector's output.

- **Sources:** V1-022
- **Worst severity:** S3
- **Answer:** ADR-0007 (D5 rider; the V1-022 anti-pattern is banned by test)
- **Test:** ledger-completeness test — any pass that mutates document text produces a ledger entry with actor+rationale; no default-on mutation path reachable from default config
- **Test status:** phase-gated (P4 voice layer) - **Phase:** P4

### AR-015 - Resource lifecycle is owned, not GC'd

Engines/clients/stores are context managers; the pipeline owns and closes stage resources; connections close in finally paths; no import-time home-directory writes.

- **Sources:** V1-020
- **Worst severity:** S3
- **Answer:** brief §2.1 "engines are context managers"; §3.2 rule 5 for the import-time class
- **Test:** resource-leak gate — test session run with warnings-as-errors fails on unclosed sqlite/httpx handles
- **Test status:** phase-gated (P1+) - **Phase:** P1

### AR-016 - Unsafe composition sinks banned — argv lists, validated identifiers, safe extraction

No command strings interpolated with paths (argv lists only); store identifiers validated strictly at the boundary (alnum/underscore/hyphen); archive extraction uses component-wise containment (is_relative_to / commonpath) or the stdlib data filter with no prefix-startswith fallbacks; requires-python floors exclude known-vulnerable interpreters.

- **Sources:** V1-015, V1-027, V1-028, V2-001
- **Worst severity:** S1
- **Answer:** ADR-0006 (the revision substrate owns extraction/restore safely — the tar CVE class lives only where ad-hoc archives exist); brief §2.2 (never port v2 checkpoints/profiles tar paths); §3.1 evidence layer (parameterized identifiers)
- **Test:** identifier-validation unit tests; traversal-archive fixture rejected with typed error on every extract path (property test over member shapes); no-shell structural check (no shell=True, no string command builds)
- **Test status:** phase-gated (P2 restore paths; identifier check P3 evidence layer) - **Phase:** P2

### AR-017 - Packaging integrity — runtime deps cannot live in dev extras

Every shipped entry point imports successfully in a clean venv installed from core dependencies only; production images install from the lockfile, never dev extras; runtime/dev dependency sets are disjoint.

- **Sources:** GUI-016, V1-037
- **Worst severity:** S3
- **Answer:** ADR-0003 Consequences (Python packaging tests are a P1 exit criterion); W1-1 mechanism — scripts/ci.sh clean-venv wheel smoke (LANDED)
- **Test:** wheel-clean-venv-import-smoke (landed in W1-1 CI); lockfile-respected image build test (P6 packaging)
- **Test status:** landed - **Phase:** P0

### AR-018 - Dependency hygiene — pins and dedicated bump commits

Interop-critical version sets are exact-pinned with the upgrade-together rule restated in the manifest; lockfiles change only in dedicated bump commits, never as side effects of feature branches; deliberate lockfile policy from commit one.

- **Sources:** V2-015, GUI-021
- **Worst severity:** S4
- **Answer:** brief §4 Option-A risk register (version-pinning policy from day one); W1-1 pinning practice (TS 5.9.3 pinned, packageManager pinned)
- **Test:** lockfile-drift CI check (uv.lock / pnpm-lock diff allowed only when the matching manifest changed in the same commit, else fail with pointer to bump-commit policy)
- **Test status:** phase-gated (P0 CI extension — small hygiene card candidate) - **Phase:** P0

### AR-019 - Single-sourced truth — docs, enums and capabilities generated, never hand-mirrored

Phase model, agent roster, test counts, stack names each live in exactly one machine-checkable place; docs assert nothing a generator does not emit; shipped config cannot name capabilities (providers, models, transports) absent from the capability registry (config-capability drift fails CI); client code contains no mirrored server enums.

- **Sources:** V1-039, V1-040, V2-014, GUI-024
- **Worst severity:** S4
- **Answer:** brief §5.5 (doc single-sourcing; the three-phase-model registry is the standing warning); W1-1 mechanism — docs/doc-single-sourcing.md + tests/test_single_sourcing.py (LANDED)
- **Test:** single-sourcing guards (landed; extended per generator as the ADR-0005 engine lands — scaffold README stage-list prose converts to generated once the engine exists); config-validation-against-capability-registry test (P1)
- **Test status:** seeded - **Phase:** P1

### AR-020 - The client renders what the server serves

No phase models, status enums, or placement logic mirrored in front-end code; the server computes section placement/targeting from command arguments — no client-side guessing; command replies carry their labels (protocol completeness).

- **Sources:** GUI-012, GUI-025
- **Worst severity:** S3
- **Answer:** ADR-0004 (the client renders what the server serves; workflow.ts anti-pattern named in the ADR); brief §3.2 rule 4
- **Test:** no-mirror structural check (front-end source grep for phase/status enum literals fails CI); server-placement test (draft targets resolve from args, first-command case included); editor-app unit suite exists (getTokens/diff/rail logic — GUI-025 lead list)
- **Test status:** phase-gated (P5 front end) - **Phase:** P5

### AR-021 - Test infrastructure with teeth — suites must be able to fail

CI runs on every branch and can signal red at every layer (proven by canary); no process.exit(0)/force-exit masks in test hooks; test scripts build-before-test so fresh clones pass or fail truthfully; every advertised UI affordance and dev-script promise has at least one behavior-asserting test (shape-only assertions over behavior-critical seams are rejected at review); test harnesses pin ALL home-derived paths so tests cannot touch real user state.

- **Sources:** GUI-004, GUI-013, GUI-017, V1-035, V2-016
- **Worst severity:** S2
- **Answer:** ADR-0003 Consequences (CI gate runs both suites on every branch and must be able to signal red — exit-0 masks are a P0-rejected defect class); brief §3.2 rule 8 (CI red-ability is a release gate on every branch — recurrence #1/#2 root-fix); W1-1 CI-with-teeth (LANDED: canary cycle receipts green/red/red/red/green) + tests/test_repo_hygiene.py no-masks guard (LANDED)
- **Test:** canary-cycle receipt (landed, docs/ci-teeth-receipt.md); exit-0-mask structural guard (landed); build-before-test script pattern check; one-fixture-pins-all-homes harness rule (P1 harness)
- **Test status:** landed (extends each phase) - **Phase:** P0

### AR-022 - Public event/replay contract, generation-correct and subscriber-safe

The event spine exposes PUBLIC replay/cursor/unsubscribe from day one (no surface reaches into bus internals); replayed envelopes carry the artifact generation published with the event (correlate by id, never phase-to- latest lookup); per-handler exception isolation with error events; bounded client-side rendering for unbounded streams.

- **Sources:** V1-034, GUI-010, GUI-015, GUI-018
- **Worst severity:** S3
- **Answer:** ADR-0004 (AgentEvent contract with public replay/cursor/unsubscribe — GUI-018 lesson); §2.1 gui-editor event-spine requirement (I6/I7)
- **Test:** replay-generation test (redraft then reconnect — older checkpoint frame carries its own suggestion ids); poison-subscriber isolation test; public-API-only structural check (no private-attribute access on the bus from surfaces); bounded-feed render test
- **Test status:** phase-gated (P1 / W1-5 event spine) - **Phase:** P1

### AR-023 - No wedged state — every busy/in-flight flag recovers

Whole-operation try/finally around busy/lock flags; disconnects, timeouts and malformed transport responses clear in-flight client and server state on reconnect; degraded paths follow the documented degradation, never assert/crash; no blocking sleeps inline in command latency paths.

- **Sources:** GUI-005, GUI-009, GUI-014
- **Worst severity:** S3
- **Answer:** brief §2.1 gui-editor degradation principle (principle sound, break-sites fixed); §3.2 rule 2 (typed status on every failure incl. transport)
- **Test:** exception-mid-command busy-recovery test; disconnect-mid-command and disconnect-mid-resolve client-recovery tests; degraded-mode (no doc ops) still-emits-typed-CHECKPOINT test
- **Test status:** phase-gated (P1 gateway shell / P5 front end) - **Phase:** P1

### AR-024 - Transient failure must not lose user-visible content

Stream chunks that fail to deliver are re-queued, not discarded; partial loss surfaces as typed degraded status naming what was not captured; final flush retries before declaring loss.

- **Sources:** GUI-006
- **Worst severity:** S3
- **Answer:** brief §2.1 degradation principle + I7 (anything persisted must state what it did not capture)
- **Test:** control-outage-mid-stream test — doc and result-event content identical after a 1s outage; lossy case returns typed partial status
- **Test status:** phase-gated (P5) - **Phase:** P5

### AR-025 - Advertise only what actually landed

Suggestion ids, checkpoints, and success envelopes are set only on verified success; a failed run leaves no actionable phantom artifact; envelopes referencing artifacts are transactional with the artifact's existence.

- **Sources:** GUI-007, GUI-008
- **Worst severity:** S3
- **Answer:** §3.2 rule 2 (typed status; error prose never presents as success) + ADR-0004 content/state split (suggestion existence is content truth, gate-consistent with the checkpoint state event)
- **Test:** failed-run-no-suggestion test; suggestion-id-in-envelope always resolves in doc (property test over outage injections)
- **Test status:** phase-gated (P5) - **Phase:** P5

### AR-026 - Apply-once content semantics — accept/reject round-trips are exact

Applying a suggestion replaces the ENTIRE target block content (no first-child assumptions); accept of a streamed multi-flush block yields exactly the proposed text; content round-trips are length- and content-exact under multi-child fragments.

- **Sources:** GUI-002
- **Worst severity:** S2
- **Answer:** ADR-0004 (edit-op vocabulary seam — block.replace full-replacement semantics preserved from the harvested op vocabulary); brief §2.1 suggestion-set model adopted
- **Test:** multi-child accept test (>=2 stream flushes, accept yields content == proposed, no duplicated tails) — the exact regression GUI-002's suite missed
- **Test status:** phase-gated (P5 front end) - **Phase:** P5

## Dispositions (answered by construction, not by a carried test)

- **GUI-003, GUI-011, GUI-019, GUI-020, GUI-022, GUI-023, GUI-026** - not-carried (`ADR-0003, ADR-0004`).

Defect classes native to the discarded gui-editor substrate. Two-token query-string browser auth + localStorage slot routing (GUI-003) — ADR-0003's same-origin single token removes the class by construction. Presence/ awareness machinery races and inline linger (GUI-011, GUI-022) — ADR-0004 cuts presence from v1 entirely. Collab-server token compare (GUI-019) — no collab server exists; AR-001 covers the surviving auth surface. CWD-relative dev token file, hand-assembled tokenized dev URLs, and webridge URL derivation in a 3-service dev topology (GUI-020, GUI-023, GUI-026) — brief §2.2 discards the substrate and §2.2 repo-wide discards kill CWD-relative resolution; the surviving cwd-trust PRINCIPLE is carried in AR-008, and P5 harvests only the dev-operability good parts (pidfile + tree-kill, token gen/redacting loggers) per §6.1.

## Raw material (D8 - no uplift)

**Legacy audit issues.** biondogs/metatron open issues — verified count 20 via read-only gh @ 2026-10-23.

Policy: D8 — backlog raw material only; no upstream issues/labels ever (Q7=c); no uplift over register findings.

All 20 are re-verified and mapped into register entries by R1 REVIEW-NOTES §2, and thus ride this register — #33 to AR-016; #34 to AR-004/AR-013; #35 to AR-021; #37 and #38 to AR-013; #39 to AR-012; #41 to AR-012; #42 to AR-001; #43 to AR-010; #45 to AR-013; #46 to AR-004; #47 to AR-007; #49 to AR-013; #50 to AR-012; #51 to AR-006; #53 to AR-006; #57 to AR-004. Fixed-issue regression guards ride AR-012 (#28/#40/#54/#55/#56) and AR-016 (#28).

**Dependabot PRs.** biondogs/metatron open dependabot PRs — verified count 6 (#71 #67 #65 #63 #61 #29) @ 2026-10-23; PR #69 excluded (superseded-as-branch per D8).

Policy: D8 — raw material only. Disposition: consume during P0/P1 dependency setup under AR-018's lockfile policy; none gets its own card

## Research seeds (D5 rider - seeded, not executed)

- **RS-1 - Evaluate open humanizer / style-transfer models as candidate voice-stylometry passes** (seeded-not-executed; research list from P0 onward; product integration P4).

Survey and evaluate current open humanizer/style-transfer models as candidate passes of the voice profile. Any adopted model must pass the SAME corpus-fidelity validation (similarity to the author's own corpus), never a detector benchmark (ADR-0007 line — the reference target decides the category). All passes ledgered.

**Seed:** §7.1 D5 rider (operator — "there are actually a number of new humanizer models we could add [to] the research list")

- **RS-2 - Voice LoRA fine-tune plan on the voice-collector corpus** (seeded-not-executed; post-v1 (planning may be carded when P4 opens)).

Planning track only — define the fine-tune plan (dataset = voice-collector corpus; native-in-voice generation instead of post-processing; evaluation = corpus fidelity under the ADR-0007 red-flag rule). Post-v1 scope per brief §6.1 wave-2 preview.

**Seed:** §7.1 D5 rider (operator — "we could also plan to make a LoRA from the voice collector")

---
*Generated from `requirements.yaml` v1.0 (t_630ef5d0). Coverage invariants are
CI-enforced: findings mapped exactly once, no unknown ids, severity consistency,
and every S1/S2 ADR-answered (see tests/test_antireq_register.py).*
