# ADR-0004: Front-end form — browser editor primary, CLI parity, no collab substrate in v1

**Status:** Accepted (operator decisions D2 + D7, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction) · sw-architect (formulation) · Card: METATRON-ARCH-1 (t_77ba5a4b)

## Context

A front end is an operator requirement (intake Q2: "some sort of front end"), form open. The intent evidence's two-month arrow (TUI → shell → Console → serve → editor, June→Sept 2026) ends at the browser editor; the TUI repeatedly broke in daily use (TUI-ISSUES audit; V2-014 shows fixes contradicted by their own docs). Single-user first is locked (intake Q4; commit 48468e5: "no feature gets built that only a second human would use"). R3's verdict on gui-editor: the protocol and *seams* are the reusable assets; the 3-service substrate (Vite + Hocuspocus + gateway: 3 processes, 3 ports, 3 tokens for one human) fails the single-human test, and Yjs-as-core is unnecessary for single-user revisioning.

## Decision (D2)

**Browser editor primary + CLI parity for the first usable release. No TUI in v1.**

- The browser editor is the primary surface; the Typer console (harvested v1 console UX) provides parity for terminal workflows against the *same* engine.
- TUI lessons (focus model, help overlay, error visibility from v2) are recorded, not implemented.

## Decision (D7)

**No Yjs/Hocuspocus/CRDT in v1 — not in storage, not in transport.** The editor runs BlockNote non-collaboratively; its document model syncs through the command/edit-op seam to the server-side revision store. We **preserve the seams that make collab addable later without surgery**:

1. the edit-op vocabulary (block.insert / appendDelta / replace / remove; suggestions.set / suggestions.resolve) — "Python never speaks the Yjs sync protocol";
2. the AgentEvent contract, with **public replay/cursor/unsubscribe** from day one (GUI-018 lesson — the moment any network surface attaches, clients need resumable subscriptions);
3. the "WorkflowManager is the sole authority; the document is content, never state" split, and "the client renders what the server serves" (no client-mirrored phase models — the workflow.ts anti-pattern).

## Alternatives rejected

- **TUI-first / TUI-and-browser** — contradicts the operator's own usage arrow and re-funds the surface that repeatedly broke.
- **Keep the collab substrate live** — a YAGNI violation (I8): presence/awareness machinery, per-room op queues, and two-token browser auth exist only for a second human who does not exist. R3 showed its defect load (GUI-003 token class, GUI-011 races) lands precisely on this machinery.

## Consequences

- Future collab = a new transport adapter behind the frozen edit-op seam, not a rewrite.
- Drafts land where the *server* computes placement (GUI-001 class — stale client `active_section` — impossible by construction).
- Front-end cards start only after the P1 event-spine contract is frozen (brief §6.1).
- The editor's suggestion-review UI carries the suggestion-set model (id/original/proposed/rationale/status/resolvedBy) from R3.

## Revisit when (falsifier)

- **D7:** the day a second human actually joins a document — the seam exists precisely for that trigger; collab then gets its own ADR.
- **D2:** if browser-editor streaming cannot hold acceptable perceived latency in-process, measure first (brief §8): that falsifies the single-process posture, not the editor choice itself.
