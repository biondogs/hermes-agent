# ADR-0006: Revision-store substrate — embedded shaded git implementing v2's RevisionStore semantics

**Status:** Accepted (operator decision D4, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction) · sw-architect (formulation) · Card: METATRON-ARCH-1 (t_77ba5a4b)
**Related:** ADR-0002 (legacy, v2 branch — the semantics this adopts); invariant I2.

## Context

The operator requires built-in document revisioning, revertible **by the user AND by the harness**, and explicitly does NOT require git to be the exposed mechanism (intake Q2; ADR-0002 is input, not constraint). I2 requires: every change attributed (actor human/agent, surface, rationale), append-only history, both-user-and-harness revert to any point, and — from R2's negative results — **deletions must reach history** (V2-003: v2 silently dropped them) and the ADR's commit policy must actually be wired (V2-005: only outline+draft ever persisted). The v2 RevisionStore is the only implementation whose attribution semantics have passing tests; R2 called its core "excellent rewrite seed." V1-002 (checkpoint capture silently skipping subdirectories, restore as overlay-only) is the standing anti-example for capture completeness.

## Decision

**An embedded, shaded git repository at `.metatron/history` (`GIT_DIR`) as the storage substrate, implementing v2's RevisionStore semantics verbatim:**

- section-granular commits with actor/surface/rationale trailers;
- append-only history; rollback implemented as reverting commits, never rewriting them;
- **deletions captured** (the V2-003 fix is a stated acceptance test, not a hope);
- Noop degradation and crash recovery per ADR-0002;
- EditSync semantics: external edits detected and committed as `human` actor (V2-007 concurrency gap designed out);
- git is **invisible**: never a user-facing requirement, never a command a user must know ("no git knowledge needed" — the legacy README promise, now actually honored because revisioning is API-level).

## Alternatives rejected

- **Purpose-built SQLite/content-addressed snapshot journal** — matches the SQLite-only posture but must re-derive diffing and attribution correctness from zero, with no carried tests, for the one subsystem where correctness is hardest to verify (I2).
- **User-facing git repo** — violates the operator's "not required to be git-backed" framing and the portability promise (I1); makes an implementation detail a compatibility obligation.

## Consequences

- The Python git binding choice (dulwich vs pygit2/libgit2 vs shelling to system git) is a P2 implementation card, decided on: no import-time side effects (V2-002 class ban), recoverability from a corrupted object store, and packaging on the PyPI wheel.
- Restore reconstructs **full tree state including deletions** — overlay-only restore is the V1-002 anti-pattern and is covered by a capture-completeness property test.
- All revision state lives under `.metatron/history` (internal state, ignored by the user's own tooling); there is never a second user-facing repo.

## Revisit when (falsifier)

If restore-attribution or lock-recovery correctness fights the git substrate more than once, "invisible git" is falsified → promote the SQLite snapshot journal (option b). One fight is an implementation bug; two is a substrate verdict.
