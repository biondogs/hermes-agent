# HERMES-EMBEDDING-LEVERAGE-RESEARCH — 2026-10-27

**Card:** t_095daea6 (default board) · **Author:** research profile · **Mode:** read-only (no config/profile/Hindsight/litellm changes)
**Question:** Does the Hermes-estate (kanban/orchestration layer) benefit from dedicated embedding models (gargantua02's tournament winners `harrier-oss-v1-27b` fp8 / `embeddinggemma-2` Q8_0), or is there no real benefit at current scale?

## TL;DR verdict

| # | Area | Current state | Verdict |
|---|------|--------------|---------|
| 1 | Hindsight recall | **Already embeds** (bge-small-en-v1.5, 384-d, CPU) inside a 4-strategy hybrid pipeline | **Keep as-is.** Swapping to harrier-27b is a full re-embed for ~zero gain at 45k facts; reranker — not embedder — is the known CPU bottleneck |
| 2 | Skill retrieval | Model reads the full name+description index (73–119 skills) in the system prompt every turn; zero embedding code | **No benefit.** Retrieval isn't the failure mode; description quality is |
| 3 | Kanban dedup/similarity | Process-level dedup (G-08 law, `idempotency_key`, DEDUP-FIRST, nightly audit) | **Don't bother.** Past duplicates were orchestration races, not fuzzy-match misses; 1.3k cards is trivially small |
| 4 | Cross-bank/cross-board search | Per-profile bank-scoped Hindsight + grep over docs-of-record + session_search | **No shared index** — it would re-introduce the cross-env contamination class the operator's 2026-10-23 env-axis ruling deliberately retired. Optional cheap add: card-summar bank in the *existing* Hindsight server |
| — | System-1 | Decision-model program (approval/watchdog/title), verdict STAYS-BIG | Not an embedding consumer at all; nothing to plug in |

**Overall: no implementation card is warranted right now.** The estate already gets semantic search for free from Hindsight's built-in embedder; every other proposed use is below the volume/latency threshold where a dedicated embedder changes outcomes.

---

## Estate scale (real numbers, pulled 2026-10-27)

- **Kanban:** ~**1,304 cards** across 7 live boards (default 243, gargantua02 351, gaudi 384, software-co 250, skipjack 50, gargantua01 26, skipjack-prototype small); ~**3,156 comments**; ~1,940 task_runs; ~81K task_events. Source: live per-board SQLite counts.
- **Skills:** **73** curated skills visible on the research profile; **119** `SKILL.md` files in the default skills home (`/home/arch/.hermes/skills`). Any model's context comfortably holds the whole name+description catalog.
- **Hindsight:** **22 banks** on ga01:8888 (ApiKeyTenantExtension auth since 2026-10-26), ≈ **44.8k facts** total (`BANK-MAP.md` live counts): general group 40,523 (hermes 30,164 · laptop 6,053 · software-co 4,306), role/specialist 2,240, butler 1,200, per-environment 857. Median bank is a few hundred facts.

## 1. Hindsight / memory banks — already embedding; adequate; don't swap

**How it actually works (verified, not guessed).** The deployed recall pipeline runs **four parallel strategies — semantic (vector), BM25 keyword, entity/temporal/causal graph, time-range — merged by RRF, then cross-encoder reranked.** The server (`ghcr.io/vectorize-io/hindsight`, `/local/compose/aistack/docker-compose.yml` L218-261) sets only `HINDSIGHT_API_LLM_*` (ORB `qwen36-fast`, reasoning off, concurrency caps) and reranker tuning (`HINDSIGHT_API_RERANKER_LOCAL_BUCKET_BATCHING=true`, `LOCAL_MAX_CONCURRENT=8`). **No `HINDSIGHT_API_EMBEDDINGS_*` variable exists in the compose file (grep: 0 hits)** → upstream defaults apply: **`BAAI/bge-small-en-v1.5`** (local SentenceTransformers, CPU, 384-dim) + **`cross-encoder/ms-marco-MiniLM-L-6-v2`** reranker, both auto-downloaded. The standing note "Hindsight embeds via the ORB-routed qwen36-fast" is **wrong** — qwen36-fast is only the extraction/reflect LLM side; embeddings are local CPU.

**Would harrier-oss-v1-27b fp8 help?** No, at this scale:
- **Volume:** 44.8k facts, largest single bank 30k — bge-small-class CPU indexing and search is milliseconds-to-seconds territory. Query load is a handful of recalls per worker turn, not a throughput fleet.
- **Migration cost:** changing the embedder changes vector dimensions → per upstream docs, **existing vectors are lost and the whole bank must be re-embedded** across all 22 banks (API-key-gated bulk operation; blast radius = every profile's memory).
- **The actual bottleneck is elsewhere:** compose comments (L243-247, citing upstream `/developer/performance`) already identify the **CPU reranker** as the recall-path bottleneck — which is why bucket batching + concurrency 8 were set. A bigger embedder does not move that; it shifts latency from CPU (free) to an H200 holding **47.9 GiB/card** (`ASSEMBLY.md` §1.3 winner receipt) for traffic that doesn't justify it.
- **TEI is explicitly not the estate's embedding throughput lane** (`ASSEMBLY.md` §1.3 E1c: 11.3× slower, quality parity proves it's a candle-backend velocity problem).

**Honest caveat:** we have no A/B measurement of bge-small recall quality on our own corpus. If recall-miss complaints ever become a recurring pattern (they haven't surfaced on any board audit to date), the cheap test is a **small** upgrade (embeddinggemma-2 class via Hindsight's `litellm`/`tei` provider) exercised on a **fresh test bank**, never a dimension-change flip on populated banks. That's a future card only if a measurable complaint exists.

## 2. Skill retrieval — embeddings solve a problem the estate doesn't have

**Current mechanism (hermes source `/local/projects/wt/hermes-up-base/agent/`):** the full skill catalog (name + description, 73 entries on this profile) is injected into the system prompt; **the model itself chooses** and calls `skill_view`. `skills_index_delta.py` only diffs the catalog mid-session; `skill_commands.py` handles invocation scaffolding. A repo-wide grep for `embedding|cosine|vector|sentence-transformers` in the agent/skill paths returns **only prose comments** — zero retrieval code, embedding or keyword. (The only embedding-adjacent consumer in the client is `plugins/memory/__init__.py` warming numpy for the Hindsight plugin — server-side embedding again.)

**Assessment:** semantic skill search is a solution for catalogs too big to show the model (thousands of entries). At 73–119 skills, the model already sees everything every turn — a vector ANN over 119 descriptions cannot out-perform reading them. The recorded failure mode "wrong skill loaded / skill never found" traces to **ambiguous descriptions and name collisions**, which embedding similarity would *worsen* (nearest neighbors of near-synonyms are precisely the confusable pairs). Correct lever, no embedding: keep tightening description triggers (already the skill-authoring convention: "first 57 chars a self-contained trigger").

**Verdict: no benefit, don't bother.**

## 3. Kanban dedup / similarity detection — the duplicates were never semantic misses

**Current mechanism:** process-level, by design:
- G-08 **Dedup-Close Law** (`hermes-estate/docs/GOVERNANCE.md` L29): dedup hits close as KILLED-BY-DEDUP by default;
- butler **DEDUP-FIRST** list-before-create (SOULs);
- kernel `idempotency_key` on `kanban_create` (exact-key dedup);
- nightly board audits + `archive_gc`.

**Why embeddings don't move the needle:** the recorded duplicate incidents (the 2026-10-23 fleet incident behind G-08: same intake filed twice within one hour, both ran; the t_7cd02b4d archive) were **orchestration races — two writers creating the same card concurrently** — not "an existing similar card existed and nobody found it." An ANN similarity index does not fix a race; `idempotency_key` and single-intake-channel (G-02 butler-first) already target the actual cause. And the near-miss class embeddings would catch — "two differently-worded cards about the same work" — occurs at a rate of ~a handful per ~1,304 cards, each already caught by nightly audit. **At 1.3k cards, brute-force title comparison is sub-millisecond in any implementation; a model call is the current check and costs pennies.**

If a cheap guard were ever wanted it's **SQLite FTS5 on titles** (zero ML, zero service, already in every board DB's engine) — but current incident history doesn't even justify that.

**Verdict: no benefit, don't bother.**

## 4. Cross-bank / cross-board "where was X decided" search — the shared index is ruled out; the cheap variant is optional

**Current state:** three layers: (a) `hindsight_recall` — semantic+hybrid but **bank-scoped by design**; (b) `session_search` for verbatim transcripts; (c) **docs-of-record grep** (GOVERNANCE.md registry indexes the law texts; BANK-MAP, KANBAN-SYSTEM-AS-BUILT, per-topic docs under `software-co/docs/`). Recurring operator asks ("find the bot-battles campaign", "find the muse incident") are history-lookup queries, answered today by grep + targeted recall, and the GOVERNANCE §5 alias map exists precisely to resolve shorthand asks without search.

**The decisive constraint is governance, not tech:** a single shared embedding index over all banks would re-create exactly the defect class the operator's 2026-10-23 **env-axis cutover** retired by construction (`BANK-MAP.md` §2: a Gargantua02 watcher recalling Habana/HPU lore as if it applied — measured contamination across 3 shared pools, then deleted). Butler-bank isolation (t_fd8ca6f0) says the same for butler memory. **Any proposal to federate banks into one searchable space needs an operator ruling first; this research will not recommend fighting that ruling.**

**What remains genuinely open (low priority):** the *card corpus* (not banks) is fair game — kanban cards are not bank-contaminated. Options ranked by cost:
1. **Free:** a standing grep/FTS recipe over the 7 board DBs (titles+bodies+comments; 4.5k rows total — any scan is instant). A skill, not a service.
2. **Cheap:** a dedicated `board-doc` Hindsight bank fed with card title+completion-summary retains; queries ride the **existing** hybrid+rerank pipeline — no new serving, no new embedder, no dimension change. Bounded value: completion summaries are already surfaced to downstream workers via parent handoffs.
3. **Not recommended:** a bespoke vector index over cards+observations+docs — new moving part, new staleness problem, at volumes where #1 answers the same question in one command.

**Verdict: marginal; recommend #1 (a documented grep/FTS recipe), skip #2 until the ask actually recurs enough to measure.**

## System-1 clarification (from the operator's framing)

"System1" per the gargantua02 ledger is the **approval/watchdog/title decision-model** program — its tournament verdict is **STAYS-BIG** (no small candidate reached ≥99% agreement on the frozen CAP-2A corpus; `ASSEMBLY.md` §4 table). It is a classification/decision consumer, not a retrieval consumer: **there is no embedding-model integration point in System-1**, and the estate's own decision lanes (butler intake, dispatcher guards, watchdog gates) run on the big-model path exactly as the ledger prescribes. The two embedding assets (harrier-27b fp8 GPU / embeddinggemma-2 CPU) exist to serve gargantua02's own fleet workloads; **the Hermes-estate is not a workload that needs them.**

## Recommendation

1. **Do nothing now** — no implementation card. All four candidate areas are either already embedded (Hindsight), below volume (skills, dedup), or governance-blocked with cheaper equivalents available (cross-search).
2. **One cheap hygiene follow-up (optional, operator's call):** document the cross-board card-search grep/FTS5 recipe as a small skill so "find where X was decided" is one command. Pure documentation; no model, no service.
3. **Trigger-based revisit conditions (write them down so we don't re-research):**
   - Hindsight recall misses become a recurring, cited pattern on board audits → A/B a *small* embedder on a fresh test bank via Hindsight's `litellm`/`tei` provider; never a dimension flip on populated banks without a re-embed plan.
   - Skill catalog grows past ~300 entries per profile → reconsider retrieval-assisted skill selection.
   - Card volume passes ~10k with a measured fuzzy-duplicate miss rate → reconsider FTS5/ANN dedup guard.
   - Operator explicitly wants federated cross-bank recall → needs_input ruling against the env-axis canon before any build.

## Sources (all verified this run unless noted)

- `/local/compose/aistack/docker-compose.yml` L218-261 — Hindsight env (LLM=ORB qwen36-fast, reranker tuning, auth ext); **no EMBEDDINGS_* override** (grep 0 hits).
- Hindsight upstream recall architecture + default models (bge-small-en-v1.5 / ms-marco-MiniLM-L-6-v2) + dimension-change re-embed warning — verified in first attempt against upstream docs (checkpoint receipt, card t_095daea6 comment 2026-10-27).
- `/local/projects/gargantua02/rnd/ASSEMBLY.md` §1.3 (harrier fp8 winner, 47.9 GiB/card, TEI E1c loss), §2.2, §4 table (System-1 STAYS-BIG, embeddinggemma-2 conditional).
- `software-co/docs/BANK-MAP.md` — 22 banks, per-bank live fact counts, env-axis contamination table §2, butler isolation.
- `hermes-estate/docs/GOVERNANCE.md` G-02/G-08/G-09 rows.
- `~/.hermes/skills/devops/hindsight-bank-admin/SKILL.md`, `hermes-kanban-crossboard-ops/SKILL.md` — current admin/cross-board workflows.
- `/local/projects/wt/hermes-up-base/agent/` (skills_index_delta, skill_commands), `plugins/memory/__init__.py` — zero embedding retrieval code (grep-verified; prose-comment hits only).
- Live per-board SQLite counts (cards/comments/runs/events) — first-attempt checkpoint, spot-consistent this run.
