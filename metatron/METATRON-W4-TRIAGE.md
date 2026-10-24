# METATRON-W4-TRIAGE — Wave-4 candidate menu + recommended cut

**Card:** t_7dd9e899 (software-co board) · **Author:** sw-pm · **Date:** 2026-10-24
**Purpose:** ranked triage of all pending Metatron work so the owner (swco-butler) can fan out Wave-4 build cards next cycle.
**Code base:** `biondogs/metatron-rewrite` main tip `265f24e` (the card's `7eba526` is the W3-FE merge point inside the wave-3 exit series: `7eba526 → f5f1592 → dacb545 → 265f24e`; the receipts at the tip are the authoritative wave-4 input record).
**Evidence read for this triage:** three findings registers (`antireq/registers/*.yaml`), `antireq/requirements.yaml` (26 AR classes + dispositions + research seeds), `METATRON-ARCH-BRIEF.md` §6 phase plan + §7.1 locked decisions, `docs/w2-integration-receipt.md`, `docs/w3-integration-receipt.md` §"Gaps this exit hands to wave-4", `docs/w3-research-rag-receipt.md` §7, `docs/w3-frontend-hardening-receipt.md`, live `src/metatron/stages/` (only `research.py` + `draft.py` exist — confirms review/revise/cite/export unshipped).

## 0. Input reconciliation (before ranking)

1. **"43-finding register" in the card body is a miscount.** The registers hold **83** findings — R1-V1: 40 (2 S1/12 S2/20 S3/6 S4), R2-V2: 17 (2/3/7/5), R3-GUI: 26 (0/4/13/9). The brief (§2.3), `antireq/README.md`, and `requirements.yaml` meta all independently state 83. No action needed; every future card should cite 83.
2. **All 83 findings are dispositioned.** 26 AR classes carry them; the S1/S2 all have landed ADR answers with landed tests **except three still-open AR classes**: **AR-012** (centralized escape, phase-gated P4 export family), **AR-007** (stable-id idempotency — test half open), **AR-006** (dead-code half seeded, call-graph gate open). Those three are the only register-origin S2 residue.
3. **The rest of the pending work is wave-handoff gaps**, not findings: the W3-INT exit names 8 gaps; W3-RAG names 6; W2 carried `state.log` hash-chain integrity twice now. The AI-contribution ledger (brief §6 P3 line) has **no AR and no code** and was explicitly carried "for the PM to place" — it is placed here (C9).
4. **Phase scoreboard:** P0 ✅ (CI teeth receipted 3 waves running) · P1 ✅ · P2 ✅ minus hash-chain + stable-id tests · P3 ✅ minus AI-contribution ledger, minus live-network proof, minus substrate sign-off · P4 ~30% (research+draft shipped; review/revise/cite/export unshipped; voice layer untouched) · P5 ✅-ish (W2-P5 + W3-FE: DOM probes, reconnect class removed at product root, engine pin, load gate — healthy) · P6 0% (all of it is Wave-5+).

## 1. Candidate menu (ranked by user-visible risk/value)

Ordering per card rule: S1/S2-class findings first → things the human QA tester would trip per invariants I1–I8 → durability/persistence gaps → enhancements.

| # | Candidate | Class | AR/gap origin | Lane | OWNER-ASK |
|---|---|---|---|---|---|
| C1 | Export family + export stage | S2 finding residue | AR-012, brief §3.2-rule-6 | sw-dev-a | — |
| C2 | Review + revise stages | QA arc-trip | brief P4, I6 | sw-dev-b | — |
| C3 | Cite stage + full-arc E2E closeout | QA arc-trip | brief P4, I3 | sw-dev-b | — |
| C4 | Research connectors wired behind the stage + contact config surface | I3 realism | W3-RAG §7.2/§7.5, AR-006-half pattern | sw-dev-a | — |
| C5 | Live-network connector smoke (opt-in, out of CI) | I3 trust | W3-INT gap 3, W3-RAG §7.1 | sw-dev-b | **OA-4** |
| C6 | `state.log` hash-chained integrity + compaction | Durability | W2 §Known-gaps, carried 2× | sw-dev-b | — |
| C7 | Stable-identity idempotency tests | S2 finding residue | AR-007 | sw-dev-a (fold → H) | — |
| C8 | AR-006 call-graph dead-code gate + register closeout (AR-018, AR-020, local-build docs) | S2 finding residue + hygiene | AR-006/018/020, W3-INT gap 8 | sw-dev-a (fold → H) | — |
| C9 | AI-contribution ledger | I3/I4 invariant gap | brief §6 P3 line, no AR | sw-ux after design | **OA-3** |
| C10 | sqlite-vec substrate decision → implementation | Substrate gate | W3-RAG §2 deviation, W3-INT gap 2 | sw-dev-a/b post-decision | **OA-1** |
| C11 | Real embedder replacing `HashEmbeddingModel` | Substrate gate | W3-INT gap 4, W3-RAG §7.3 | sw-dev-a/b post-decision | **OA-2** |
| C12 | Voice profile v1 slice (+ AR-014 ledgered passes) | Enhancement | P4, ADR-0007 rider | sw-dev-b + sw-ux | — (owner ranking call, see §3) |
| C13 | RS-1 humanizer/style-transfer eval (research, no product code) | Enhancement research | RS-1 seeded | sw-architect | — |
| C14 | Legacy-workspace migration design draft (paper-id keyed) | P6 prep | brief §5.3, V2-004 class | sw-architect | — |
| C15 | P6 proper: docker self-host packaging, generated docs, first PyPI cut | Release | brief §6 P6 | sw-devops/sw-docs | — |

### Candidate scopes

**C1 — Export family + export stage.** One template-driven exporter (docx/pdf/latex/odt down-select) with *centralized per-format escaping* — the #54/#55/#56/#40/V1-029 injection class gets fixed once, in one place, and dies under one property-test suite (AR-012's named test). Ships `export` as the final EDGE_TABLE stage over existing artifacts; a DOM-probed trigger in the browser UI. This is I1's promise made real ("the document is the product — portable"): today the paper cannot leave the tool. Affected: P4/P6, new `export/` package, lifecycle stage slot, front-end one control. **Lane sw-dev-a.** No owner input needed — format down-select is an implementer call under the brief's "one template-driven family" constraint.

**C2 — Review + revise stages.** Ship the two middle stages of the 7-state machine with agents emitting **suggestion sets, never writes** (I6/§3.2-rule-3), review findings as attributed, resolvable items reusing the frozen suggestion contract (AR-026 apply-once semantics). W3's exit E2E traversed review/revise with *named waivers*; when these ship, those waivers retire and the `EVIDENCE_GAP`-recycle digest-pop path must keep holding (W3-INT gap 1's explicit watch item). This is the #1 QA trip: a full-arc walkthrough visibly stops here. **Lane sw-dev-b** (owns the arc since W3-P4).

**C3 — Cite stage + full-arc E2E closeout.** Cite consumes `verified_claims`/`sources` slots through the trust gate to produce the bibliography/inline-cite pass (fetched-record-or-it-didn't-happen, AR-011 already landed — this composes it, doesn't re-build it). Then the wave-defining E2E: **zero named waivers anywhere** — one paper traverses research→gate→draft→review→revise→cite→export with every agent output reviewable. Depends on C2 (same files, `tests/test_w3_integration.py` + contracts) and wants C1 landed to assert the true final arc. **Lane sw-dev-b, after C2.**

**C4 — Research connectors behind the lifecycle stage + operator contact config.** W3 shipped connectors + SQLite RAG + entailment and proved gate-consumability through the frozen slot contract, but `ResearchStage` doesn't call the connectors yet (verified: `stages/research.py` has no `evidence` import) and `config/settings.py` has no contact-header surface, so polite-pool hosts are used anonymously. Wire the real retrieval surface into the stage, add the settings surface, extend the typed refusal when no contact is configured. QA trip: "research" currently runs entirely through the provider path — I3's trust story is only as real as fetched records. **Lane sw-dev-a.**

**C5 — Live-network connector smoke.** Everything about the connectors has ever spoken to `MockTransport`; the parsed shapes have never met a real api.crossref.org/arXiv/Unpaywall payload. Opt-in, out-of-CI, operator-supplied contact header, small failure-shape triage follow-up budget. Gated on **OA-4** (approval + the contact identity). **Lane sw-dev-b, after C4.**

**C6 — `state.log` hash-chained integrity + compaction.** The only durability gap carried twice (W2 → W3 → here). Replay already re-validates forgeries structurally; what's missing is the hash chain (tamper-evidence between records) and log compaction, both explicitly P2 revision-store scope per `docs/lifecycle-contract.md` §7 and dispositioned out of W3-RAG for lane-ownership reasons. I7 (no silent failure — anything persisted must state what it did not capture). **Lane sw-dev-b** (the P2/lane-b substrate), independent of the arc cards — schedule when that lane is free.

**C7 — Stable-identity tests (AR-007).** Idempotency keyed on stable ids, never slug/title — the V2-004 forever-D class. Project model shipped; the pin-test half of the AR never landed. ~small, mechanical. Folds into C8's card.
**C8 — Hygiene closeout.** AR-006's full call-graph dead-code gate (CI teeth on "advertised capability implies call site"), AR-018 dependency-pin policy check, AR-020 register-status closeout (the W3 DOM probes already prove the served-model rule in the lifecycle pane — update the register honestly or name what's missing), and receipting the local-p5 "build first" caveat into contributor docs (W3-INT gap 8). One small card, all mechanical. **Lane sw-dev-a.**

**C9 — AI-contribution ledger.** Brief §6 P3 line, untouched, no AR, explicitly handed to the PM — placed here. Content is *not* open: every agent-attributed revision, gate verdict, and (per ADR-0007) every stylometry pass must be ledgered — that's I3/I4. The genuinely open question is the **surface** → OA-3. Suggested decomposition when unblocked: sw-architect ADR (half-page) → sw-dev-a backend → sw-ux surface with the standard UX acceptance block. Not in the recommended cut this wave (see §3 rationale) — but it is invariant-bearing, so it belongs high in Wave-5.
**C10 — sqlite-vec substrate.** W3 deliberately bound the SQLite-only posture *without* the sqlite-vec extension binary; the deviation is named in `src/metatron/evidence/__init__.py` and the swap point is isolated in `SQLiteRetrievalStore`. Owner sign-off pending since W3 (W3-INT gap 2): if the ADR-0003 posture is literal-posture, ratify and close; if it's a binding substrate choice, schedule the swap. Blocked on **OA-1**.
**C11 — Real embedder.** `HashEmbeddingModel` is an honest, guard-railed placeholder: term-overlap ranking, never semantic retrieval. A QA tester (or the operator) asking "find passages about X" will feel this immediately — worse, it *looks* like RAG. Either ratify-for-v1 (with docs honesty per AR-025) or pick a self-hostable local embedder. Blocked on **OA-2**.
**C12 — Voice profile v1 slice (P4, ADR-0007).** Interview → drafting-style profile; anti-trope/anti-obvious-AI-formatting passes; **all stylometry ledgered (AR-014 lands here or never)**. Standing red-flag rule applies: anything whose metric touches a detector's output escalates to the operator before shipping. Big scope; see §3 for why it's recommended *after* the arc closes.
**C13 — RS-1 humanizer/style-transfer model evaluation.** Seeded research (D5 rider). Feeds C12; evaluation must be corpus-fidelity, never detector-benchmark. Research card, no product code.
**C14 — Migration design draft (P6 prep, cheap to start).** One known deployment (operator's JSON-blob `~/.metatron/`); keyed on legacy paper id (V2-004: never slug). Design-only draft de-risks the P6 migration command; v2's `migrate.py` is the anti-reference.
**C15 — P6 proper.** Self-built docker image CI actually builds (#82 lesson), generated docs sections, first `metatron` PyPI cut + version tags (the repo never had tags). Wave-5+; do not dilute Wave-4 with it.

## 2. OWNER-ASK list (genuinely open design decisions for the Operator)

Exactly four. Everything else in this doc is decidable from locked direction (OPERATOR-DIRECTION Q1–Q8, ADR-0003–0008, D1–D8).

- **OA-1 — sqlite-vec substrate (carried since W3).** Ratify the no-binary SQLite deviation (posture, swap point already isolated), or schedule the upgrade-swap as a build card. *PM recommendation: ratify for v1; the isolation already honors the posture.*
- **OA-2 — Embedder choice.** Keep `HashEmbeddingModel` as the honest v1 default (term-overlap, labeled as such), or name a self-hostable local embedder now. *PM recommendation: decide together with OA-1; if retrieval quality is meant to be demo'd to the QA tester this wave, decide now.*
- **OA-3 — AI-contribution ledger surface.** Content is locked by I3/I4 + ADR-0007 (agent contributions, gate verdicts, every stylometry pass); the open call is presentation: (a) plain-text ledger file in the project dir only, (b) file + server-served UI pane, (c) (b) + a disclosure section in exports. *PM recommendation: (b) now, (c) when C1's export family matures.*
- **OA-4 — Live-network smoke approval + contact header.** Do we let an opt-in test suite call Crossref/arXiv/Unpaywall for real (out of the CI lane), and under what contact identity/header do the connectors introduce themselves? Required before C5 can run; polite-pool hosts stay anonymously slow until then.

## 3. Recommended Wave-4 cut — "close the real arc, ship the exit door, pay the durability debt"

Six build cards + one conditional + the standing wave-exit pattern. Coherent slice: after Wave 4 a full paper traverses all seven states with zero waivers and leaves the tool as files; the two longest-carried correctness debts are gone; CI honesty closes the last structural AR.

| Card | Scope (from §1) | Lane | Depends on | Priority tiebreak |
|---|---|---|---|---|
| **W4-1** | C4 — connectors behind `ResearchStage` + contact config surface | sw-dev-a | — | 3 |
| **W4-2** | C1 — export family + centralized escape + export stage | sw-dev-a | — | 4 |
| **W4-3** | C2 — review + revise stages (suggestion sets, waiver retirement) | sw-dev-b | — | 5 |
| **W4-4** | C3 — cite stage + zero-waiver full-arc E2E | sw-dev-b | W4-3, W4-2 | 2 |
| **W4-5** | C6 — state.log hash-chain + compaction | sw-dev-b | — | 1 |
| **W4-6** | C7+C8 — hygiene closeout: AR-006 call-graph gate, AR-007 pins, AR-018/020, build-caveat docs | sw-dev-a | — | 1 |
| **W4-7** *(conditional)* | C5 — live-network smoke | sw-dev-b | W4-1 + **OA-4** | 1 |
| W4-INT | Integration exit per the W1-6/W2-INT/W3-INT pattern (step-0 re-verify, union register resolution, battery, canary, wave E2E made permanent) | both lanes | all shipped above | — |

**Dependency order.** Lane a runs W4-1 → W4-2 → W4-6 (all independent; same-lane serialization is the dispatcher's). Lane b runs W4-3 → W4-4; W4-5 and W4-7 fill lane-b gaps at lower priority. The only hard edges are W4-4→{W4-3, W4-2} and W4-7→W4-1.

**Deliberately NOT in the cut (and why):** C9 ledger (blocked on OA-3 and wants an ADR first — queue it Wave-5 with priority-1 after the arc closes), C10/C11 substrate (blocked on OA-1/OA-2 — both asks are one-line answers, send them now so Wave-5 can plan), C12 voice profile (large P4 rider; cutting it into Wave 4 would dilute the arc close and drag AR-014 in half-finished; it is the natural Wave-5 centerpiece — this is a ranking call the owner may overrule), C13–C15 (Wave-5/P6 territory; C14 may start as a design-only side card any time).

**Known merge hotspot (flag, don't pile on):** `antireq/requirements.yaml` + `antireq/BACKLOG.md` conflicted at both W2-INT and W3-INT merges and every candidate here touches them (test_status landings). The union-resolution + regen-in-same-commit discipline from the W3-INT merge ledger is the proven recipe — carry it into every W4 card body. Secondary hotspot: `src/metatron/lifecycle/contracts.py` `FailureCause` (W3-INT unioned it once already; W4-3/W4-4 add members — keep deterministic-causes-before-entailment precedence).

**Spec-compliance note for card filing:** W4-2's front-end trigger is command-driven and DOM-probe-coverable in-lane; no dedicated sw-ux card is needed this wave (frontend receipts show the layer healthy). If OA-3 answers (b)/(c), C9 spawns the first sw-ux card of the rewrite with the standard UX acceptance block.

---
*Prepared by sw-pm, card t_7dd9e899. No code changes, no GitHub writes performed. Next cycle: owner fans out W4-1…W4-6 (+W4-7 on OA-4) as build cards with these scopes; OA-1…OA-4 relayed to the Operator via butler.*
