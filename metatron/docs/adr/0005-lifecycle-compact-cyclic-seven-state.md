# ADR-0005: Lifecycle model — one engine, compact cyclic seven-state machine with typed back-edges

**Status:** Accepted (operator decision D3, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction) · sw-architect (formulation) · Card: METATRON-ARCH-1 (t_77ba5a4b)

## Context

The old repo never resolved its lifecycle model: three contradictory phase models coexisted (12-linear in code, 10-cyclic in the v2 spec, 9 in the changelog — METATRON-CONTEXT §3), and back-edges were never actually implemented. The v2 research corpus (*How Humans write*, grounded in Flower & Hayes, Bereiter & Scardamalia, Kellogg, Sommers) names fixed-order pipeline thinking the repo's "largest architectural gap": scholarly writing is a recursive knowledge-transformation process. R1's top architectural finding — four overlapping orchestration paths with silent-success conventions — means the rewrite gets exactly one execution engine, and its pipeline model must be chosen deliberately.

## Decision

**Compact cyclic model: 7 states — research → plan → draft → review → revise → cite → export — with typed back-edges and Plan/Draft/Review surfaces.**

- **Typed back-edges:** every non-sequential transition carries an explicit trigger and rationale, recorded in the append-only state log; there is no implicit "jump" — a rewind is a first-class, attributed event (feeds I2's history).
- **One engine, one pipeline model** (brief §3.2 rule 1): the state machine is the sole lifecycle authority; every surface observes events and requests transitions.
- v1's 10-stage topology is the vocabulary donor: synthesize / analyze / evaluate / RAG survive as sub-operations, reports, or services *within* states (e.g. synthesize as a plan-state operation per the v2 synthesis-matrix doctrine), not first-class states.
- The rail/progress UI renders the model **the server serves** (ADR-0004's rule).

## Alternatives rejected

- **Full v2 10-phase cyclic model** — the doctrine is right but the scale was never validated at any size (it existed only as prose for three months). Adopting it unvalidated repeats the old repo's unfunded-spec pattern at the engine's root.
- **Keep a linear rail** — evidence-broken (the three-model contradiction and the corpus's own verdict).

## Consequences

- The engine stays bounded: 7 states × typed edges is small enough to exhaustively test (every edge, every failure mode = typed status per I7).
- Migration docs map legacy stage names → new states for continuity.
- D3 is explicitly revisitable at phase boundaries without a rewrite: states are data, not distributed hard-coding.

## Revisit when (falsifier)

If P4 shows real writing sessions needing synthesis-matrix or global-revision-gating machinery as first-class states — i.e., the compact model forces contorted sub-operation modeling — promote to the full cyclic model. That promotion is an ADR amendment, not an architecture failure.
