# METATRON-W7-VOICE-SLICE — design record for the minimum voice-profile + contribution-ledger slice

**Card:** W7-VOICE-SCOPE (t_843c15fe) · **Author:** sw-architect · **Date:** 2026-10-28
**Canonical decision:** `metatron-rewrite/docs/adr/0011-voice-profile-and-contribution-ledger.md` @ `b8ce4ba` (origin/main). This doc is the working design + sequencing record; where any wire shape is restated here it quotes the ADR — the ADR governs.
**Trigger:** operator finding, verbatim (butler clarify, 2026-10-28, W6 human-test session): *"i dont see any thing that would indicate the writing voice collection process."* Voice collection promoted to a Wave-7 workstream.
**Lineage:** ADR-0007 (D5 + rider) — fidelity in, evasion permanently out; ANTIREQ-BACKLOG C9 (ledger content locked) + OA-3 (surface: PM rec (b) = file + served UI pane); AR-014 (every stylometry pass ledgered, no default-on mutation); research seeds RS-1/RS-2 explicitly NOT consumed in v1.

---

## 1. What v1 is, in one paragraph

An explicit, user-owned voice corpus (`<state-dir>/voice/corpus/`, paste/imported from the operator's own writing, optionally copy-imported from his in-project human documents); one typed `collect_voice` command that produces an atomically-written, provenance-carrying voice profile (deterministic stats + provider-extracted style directives including the anti-trope/anti-formatting set, per ADR-0007 §IN-2); a single stylometry application point — DraftStage conditions its delegation prompt on a *fresh* profile and says so in evidence, ledger, and chip; and an unconditional, hash-chained, append-only contribution ledger (`contributions.jsonl` per state dir) with a server-served pane, covering agent publications, gate verdicts, human document acts, basis events, and all voice acts. **No code path in v1 mutates existing text for style — voice is applied only at generation time, inside an agent-authored draft, disclosed in three places.** No detector-adjacent anything (ADR-0007 standing red-flag rule carries verbatim).

## 2. The four deliverable questions, answered

### 2.1 Corpus — what feeds the collector
**Both families, explicit in both cases; derivation rejected.** (a) Imported writing is primary: the operator's writing from anywhere lands in `voice/corpus/*.md` through `voice_import` (editor paste door + CLI `--file|--stdin`). (b) In-project human documents join by **copy-import** ("use as voice sample" per document), never by mining revision history — mixed-authorship files (suggestion accepts, agent appends) make history-derived corpora a machine-prose poisoning risk. Bounds are typed and named both ways: `< MIN_CORPUS_WORDS (1000)` refuses with the honest count; `> COLLECT_CORPUS_CAP_WORDS (24k)` refuses with "split the import" — **no silent truncation**. The corpus survives `project_start` re-initialization (it is not a project artifact; I1).

### 2.2 Profile representation
`voice/profile.json` (schema `voice-profile/1`: `collected_at, model, corpus manifest [{name, sha256, words}], corpus_words, stats, directives[]`) + `voice/profile.md` (human-readable rendering, user-owned, I1). Atomic tmp+replace on success only; provider failure leaves no partial profile. **Staleness is derived, not stored**: corpus-manifest digests vs the profile's recorded manifest; stale → not applied, named everywhere.

### 2.3 Ledger surface
`contributions.jsonl` per state dir — append-only, seq'd, hash-chained (`prev_digest`/`digest`, chain test in CI — closes the hash-chain gap class at birth). Frozen entry: `{seq, ts, actor: human|agent|system, action, surface, target, summary, rationale?, prev_digest, digest}`; closed, mirror-guarded action enum (v1: `stage_run, artifact_published, gate_verdict, document_created, document_edited, revision_commit, project_start, voice_import, voice_collect, voice_applied`). Starts empty at landing — no backfill; pre-feature history stays queryable via `history`/`revisions`/git, and the pane's empty state says exactly that. This is OA-3 option (b); export disclosure (c) stays deferred.

### 2.4 Where stylometry is applied in the lifecycle
**One point: DraftStage.** Fresh profile → labeled voice block in the delegation prompt (the `instructions_from` provenance precedent); disclosed by the stage evidence line, a `voice_applied` ledger entry, and the served voice chip. No profile → byte-identical prompt, zero voice claims on any surface (served-truth law). Review/revise/cite/export voice work: non-goals, each with a falsifier in the ADR.

## 3. UI affordances (orientation-first layout; served-truth law)

Registry surface consumed by the client: `REQUEST voice_state {exists, stale, corpus:{files:[{name,words}],words}, profile:{collected_at,model,corpus_words}|null}` and `REQUEST contributions {limit?}` (default 50, cap 200, honest `omitted`).

| Surface | Placement | Renders | Honest posture |
|---|---|---|---|
| Voice chip | Zone A project bar (supersedes the t_79a369a8 static stopgap chip) | served `voice_state` verbatim: `not collected` / `ready · N-word corpus · collected <date>` / `stale — corpus changed since <date>` | no `voice_state` served → chip absent; client invents nothing (AR-020) |
| Voice panel | toolbar toggle beside the Provider panel (ADR-0009 chrome pattern) | corpus list, import form → `voice_import`, per-doc "use as voice sample", profile summary or honest empty, **Collect now** → `collect_voice` | buttons disable with named reasons only from served facts / typed refusals (no provider, below-min); two standing lines: files-on-disk note (I1) + "collecting sends your corpus to the configured model provider" |
| Contributions pane | Zone E side, under History | bounded recent entries, actor badges (human/agent/system), summary + target + rationale, omitted-count line | empty state names the ledger start; never claims coverage of pre-feature history |

Every affordance maps to a served fact or an existing registry command — the served-truth law is the review lens for the editor card. The panel consumes dark mode's theme tokens, therefore **must land after t_88d283f2 merges** (else it ships light-only and the QA sweep re-touches it).

## 4. Sequencing vs in-flight W7 (recommendation)

Queue reality (2026-10-28): dark mode t_88d283f2, phase-back-edge t_86bc6550, and the voice stopgap t_79a369a8 are all running branch-only on sw-dev-a, under the QA-env HOLD (operator session active); corpus-wiring t_06421201 and thesis-builder t_3713f88c are design cards beside this one. Recommendations:

1. **Merge order for the in-flight web chain:** dark mode → back-edge → stopgap chip. Dark mode is the operator's explicit ask, the biggest surface (CSS token set), and the base everything else should rebase over; back-edge and the chip are small additive riders.
2. **Corpus-wiring legs land before voice legs.** It closes a golden-path hole (fresh projects dead-end at `run research`) under a fresh operator ruling ("the point of the system was to do the research for the user…"); voice has no golden-path dependency and its visibility need is covered by the stopgap chip in the meantime.
3. **Voice legs land last in W7, internally ordered:** contributions-ledger backend (no editor collision; pure additive server work; the ledger must exist before voice acts can be ledgered from day one) → voice backend (gated on the ledger; both serialize on `runtime.py`) → editor surfaces (gated on both backends + dark-mode tokens) → REVIEW + VISUAL-QA → INTEGRATE + QA-env repin after the operator's session closes.
4. **Single-writer discipline:** `runtime.py` is the server hotspot (two sequential cards, not parallel branches); `editor.ts/main.ts/editor.css` the web hotspot (voice card queues behind the three in-flight cards). Every card rebases onto fresh origin/main before review.

## 5. Decomposition — six cards (parents = t_843c15fe)

| # | Card | Assignee | Gated on | Shape |
|---|---|---|---|---|
| V1 | W7-VOICE-LEDGER: contribution ledger backend (module + hooks + `contributions` request + CLI verb + chain/completeness tests) | sw-dev-b | — | server-only, additive; no editor files |
| V2 | W7-VOICE-COLLECT: voice corpus store + `voice_import`/`collect_voice` + `voice_state` + DraftStage conditioning + `voice` CLI group | sw-dev-b | V1 (runtime.py serialization + ledger-exists dependency) | server + stages; TEST-GUIDE S25 |
| V3 | W7-VOICE-EDITOR: Zone-A served voice chip + Voice panel + Contributions pane + stopgap-chip removal | sw-dev-a | V1, V2 (and queues behind dark mode/back-edge/stopgap merges) | frontend hotspots, TEST-GUIDE S23–S24 UI halves |
| V4 | REVIEW: ADR-0011 conformance + AR-014 no-silent-mutation + served-truth lenses on the integrated tip | sw-reviewer | V3 | branch-tip review, gauntlet |
| V5 | VISUAL-QA: both themes, chip states (not-collected/ready/stale), panel + pane batteries, golden-path regression | sw-qa | V3 (parallel with V4 per W6 pattern) | real-Chromium screenshots, same-sha gates |
| V6 | INTEGRATE: merge → main after V4+V5, supersede-stopgap check, QA-env repin after operator session closes, operator ping | sw-devops | V4, V5 | merge + repin |

TEST-GUIDE additions land with their features: S23 (voice collection from the browser), S24 (ledger battery), S25 (honest refusal battery) — full sketches in ADR-0011 Consequences.

**Forbidden zones (all six cards):** generated `frontend/app/dist/`, `node_modules/`, the QA env (`/local/qa/metatron`) and its qa-home during the operator's session, any litellm/config.yaml path, `.qa/` state dirs of other envs. Cards carry the frozen ADR §§2–5 contract inline; workers do not read this doc by default.

## 6. Open product decisions

**None blocking.** Every genuinely-open call in the card brief was settled inside the recorded decision space or fenced with a falsifier (ADR-0011 §Revisit): corpus source (explicit-only, falsifier on chore), stale-profile behavior (skip-with-naming, falsifier on complaint), interview mode (deferred, falsifier), voice scoring (requires operator adjudication before any metric exists), post-hoc passes (new ADR required). No blocked-card handback to the operator is needed for v1 to proceed.

---

## 7. W7-VOICE-ELICIT extension (2026-10-28) — guided-conversation elicitation, ADR-0014

**Card:** W7-VOICE-ELICIT (t_18f2eec9) · **Canonical decision:** `metatron-rewrite/docs/adr/0014-voice-elicitation-interview.md` @ `e2bb809` (origin/main). ADR-0011's *"No interview-based collection"* non-goal is amended (its falsifier fired on the operator's expansion request); every other ADR-0011 sentence stands.

**Shape in one line:** the interview is a **second door into the same explicit corpus** — an LLM-run, fixed 12-slot curriculum (declared probes → prose prompts → rewrite-provocation drills → register probe + litmus) whose human prose turns enter `voice/corpus/` at **user-confirmed finish** (one file per session, interview provenance), whose declared answers enter a separate low-weight `declared` stream merged additively at `collect_voice` (`voice-profile/2` + `declared_directives`/`conflicts`, samples-win-on-conflict), and whose mechanics are 3 commands + 1 request on the one registry with durable resume, a 12-exchange provider-call budget, and typed refusals throughout. `collect_voice`, staleness, the single DraftStage conditioning point, and the no-post-hoc-mutation law are untouched. Ledger action enum grows 10 → 11 (`voice_interview`) + `voice_import` entries with `surface="voice:interview"`.

**Landing order (extends §4.3's queue; elicit lands STRICTLY AFTER the substrate it extends):** ledger backend (t_fe756fb6, DONE) → voice backend (t_28aee972, running) → editor (t_71d35d27) → **E1 elicit backend (sw-dev-b; runtime.py serializes behind t_28aee972)** → **E2 elicit editor affordance (sw-dev-a; queues behind V3)** → E-REVIEW (sw-reviewer) ∥ E-VISUAL-QA (sw-qa) → E-INTEGRATE (sw-devops), sequencing against the substrate INTEGRATE (t_374a3847) at merge time. TEST-GUIDE additions: S26 (interview session arc, browser) + S27 (honest refusal/budget battery).

**Open product decisions:** none blocked back — the two candidate calls settle inside ADR-0011's recorded decision space: interview length cap = 12 exchanges (cost-honesty constants precedent), elicited-prose corpus entry = confirm-at-finish (explicit-door law I1). Both carry one-line falsifier flips in ADR-0014 §Revisit.
