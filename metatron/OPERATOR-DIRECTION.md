# Metatron — Operator Direction (locked decisions from intake Q&A)

Status: BINDING for all metatron architect/review/backlog cards.
Source: kanban t_cef0727b (METATRON-0-INTAKE), operator answers relayed
verbatim by swco-butler 2026-10-23 04:4xZ; PM-verified against verbatim
quotes and folded here as the standing record. Reviewers/architects do NOT
re-ask these; new questions go as card comments (butler relays).

## 1. Verbatim operator answers (Q1–Q8 from the intake question list)

| Q | Topic | Operator answer (verbatim) |
|---|---|---|
| Q1 | Scope: is `feature/gui-editor` a third source? | "I think a dedup and reasonable down select of features and plans is fine, but the end product will need some sort of front end." |
| Q2 | Keep-vs-rewrite: revisioning | "It doesn't need to be git but I want some sort of document revisioning system built in so it can be reverted by the user or the harness as needed." |
| Q3 | Fresh rewrite vs evolve master | "Yes I think a new code base, or perhaps rebasing metatron because I do like the name." |
| Q4 | Platform / users | "I think just single user, maybe in the future it could offer a one note like collaboration experience." |
| Q5 | Providers / distribution | "Yes opensource and self hostable are first class, we should also support other openai and anthropic compatible endpoints." |
| Q6 | Privacy / PyPI name | "Yes private only, and yes" (repo stays private; PyPI name `metatron` kept). |
| Q7 | Filing gate | "c" — feed findings straight into the rewrite backlog; NO upstream issue filing, NO label creation on the fork. |
| Q8 | Licensing | "Yes confirmed" — MIT + permanently open source stands for the redevelopment. |

## 2. Locked constraints (PM interpretation, confirmed consistent with verbatim)

1. **Greenfield rewrite.** New code base; the name `metatron` (and PyPI name)
   is retained. Note: Q3's "perhaps rebasing" reads as *rebranding* (likes the
   name), not a git operation — greenfield is operative.
2. **All three lines are source material** — `master` (v1), `v2`, and
   `feature/gui-editor` — subject to dedup/down-selection; no branch is
   sacred. v2's ADRs/lifecycle redesign are **input requirements to weigh**,
   not dead drafts and not binding constraints (Q1/Q2).
3. **Front end is a requirement** ("some sort of front end"); form is open —
   not necessarily the existing GUI. `feature/gui-editor` is prime candidate
   material (reviewed by METATRON-R3-GUI).
4. **Built-in document revisioning is required**, revertible by the user AND
   by the harness. Git-backed is NOT required — ADR-0002 (git-backed
   revisioning) is input, not constraint.
5. **Single-user first**; one-note-like collaboration is a *possible future*
   → multiplayer machinery (Hocuspocus et al.) is a YAGNI candidate; keep the
   substrate decoupled, don't build for it now.
6. **Open-source licensing + self-hostability are first class.** Provider
   stack must support OpenAI-compatible AND Anthropic-compatible endpoints
   (existing vLLM/Ollama posture carries over).
7. **Repo stays private during redevelopment**; PyPI name `metatron` kept;
   MIT + permanently-open-source commitment reconfirmed (commits
   2f34532/d096bbf lineage).
8. **No filing phase, ever.** Findings registers feed the rewrite backlog
   directly. No issues, no labels, no PRs, no branch/tag writes on
   biondogs/metatron. REVIEW-CHARTER §3's "operator-gated label creation"
   caveat is closed as moot by this decision.

## 3. Downstream card map (software-co board)

| Card | Lane | Status gate |
|---|---|---|
| t_cef0727b | METATRON-0-INTAKE (this record's source) | completes with this doc |
| t_ff37197e | R1-V1 review (master @ 811e335) | child of intake |
| t_712f7faa | R2-V2 review (v2 @ b2c1a5b) + v1→v2 delta | child of intake |
| t_b68a8d3b | R3-GUI review (feature/gui-editor @ 838f88c) | child of intake (added post-Q1) |
| t_668275f1 | DOC-1 heritage sweep | child of intake |
| t_77ba5a4b | ARCH-1 foundational rework + direction gate | needs all four above done |

Direction-gate discipline for ARCH-1: the eight answers above are LOCKED —
the operator gate on the brief should surface only what remains genuinely
open (e.g. stack choice, phase ordering, revisioning mechanism design).
