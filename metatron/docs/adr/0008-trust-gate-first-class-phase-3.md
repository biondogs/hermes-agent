# ADR-0008: The trust gate is first-class — claim–source alignment ships in Phase 3, before expansive drafting

**Status:** Accepted (operator decision D6, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction) · sw-architect (formulation) · Card: METATRON-ARCH-1 (t_77ba5a4b)
**Related:** invariant I3 (trust over fluency); R2's verdict that the alignment ship-gate line is "the single highest-value sentence in the v2 corpus."

## Context

The v2 research corpus (research-lifecycle-v2 §0.2) documents 17–33% fabrication rates in comparable AI writing tools whose "verification" is source-*existence* checking only, and declares the fabrication ship-gate **retroactively blocking** — the operator's highest-certainty value. The old repo's biggest honesty gap: the gate existed only as prose for three months, never funded, never coded. R1 additionally showed the existing verification is not even trustworthy at existence-checking: V1-023 (false-verify on a 50% partial match) and V1-009 (greedy citation regex matching).

## Decision

**Claim–source alignment verification plus fabrication checks ship as a first-class, tested gate in redevelopment Phase 3 — before expansive drafting features (Phase 4).**

- Citations resolve to **verified fetched records** only; a claim must trace to its source before its text ships (I3). Existence-only checking is classified as insufficient *and* incorrect (V1-023 is the receipt).
- Strict matching discipline: no partial-threshold "verified" results — V1-023 designed out.
- Gate failures block loudly with typed status (I7); nothing downstream of a failed gate can present the text as verified.
- Seeded false-citation and fabricated-claim fixtures exist from the gate's first commit; P3's exit test is: a seeded claim set with one fabricated citation fails loudly, a clean set passes with evidence links.

## Alternatives rejected

- **Existence-only checks first, full alignment later** — recreates the old repo's unfunded-gate gap under a new name; "retroactively blocking" means the gate cannot be a future-phase feature, or the product ships in the exact failure mode the corpus documents.

## Consequences

- P3 is larger and arrives before drafting value is visible; drafting (P4) consumes alignment outputs rather than duplicating them.
- Fabrication checks on *model output* (not just citations) are part of the gate's P3 scope.
- The gate is a permanent release gate thereafter — no phase may ship text around it.

## Revisit when (falsifier)

The gate itself is never revisited. Only its *mechanisms* are: if the P3 verifier proves too slow or too weak for P4 volumes, the verifier implementation is replaced — never deferred behind drafting features.
