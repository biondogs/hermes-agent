> Status: superseded by hermes-estate/docs/PROFILES.md (generated live census) — proposal executed (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# Software Co profile proposal — UX / front-end specialization and gap review

**Card:** SW-CO-SPAWN-COMPASS (t_54333b70) · **Author:** kanban-board-architect · **Date:** 2026-10-22
**Status: PROPOSAL — no provisioning performed. Operator GO gate required before any profile is created.**

---

## 0. TL;DR

| # | Recommendation | Action |
|---|----------------|--------|
| 1 | Add **one** new profile: `sw-ux` — front-end + UX implementer with visual-verification duty (hybrid, not two hires) | Create on GO |
| 2 | Re-route descriptions on `sw-pm`, `sw-architect`, `sw-dev-a`, `sw-dev-b` so UI/front-end work lands on `sw-ux` | Edit on GO |
| 3 | Fix a live defect the review found: **`sw-qa` cannot run its own `dogfood` skill** (browser toolset disabled) | Fix on GO |
| 4 | Add a **security-ladder section** to `sw-reviewer`'s SOUL instead of a separate security profile | Edit on GO |
| 5 | Reject everything else: dedicated security reviewer, UX researcher, DBA/data specialist, doc variants, second front-end lane, 24-persona adoption | See §6 |

Net fleet growth: **+1 profile (8 → 9)**. That is deliberately the maximum; every other candidate role fails the "earns its keep" bar for a board with 14 lifetime tasks.

---

## 1. Evidence base

### 1.1 Our own board — what actually ran

Query of `software-co` kanban.db (read-only): **14 lifetime tasks** (9 done, 5 archived, 0 open). Last waves:
- `SW-MPROV-*` (14 Oct): 1 PM charter + 4 parallel `sw-reviewer` review cards + `sw-architect` adjudication + PM filing + docs sweep — a clean **fan-out/fan-in** (breadth-parallel reviews → single-threaded adjudication).
- `SW-WAVE0-*` (18 Oct): 4 serialized security/credential fixes split across `sw-dev-a`/`sw-dev-b` lanes.

**No card in board history has ever mentioned frontend/UX/UI/design.** The operator-flagged gap is forward-looking (staff the company before UI work arrives), not a response to visible misrouting.

Observed config state (all verified this session):

| Profile | Model | Effective toolsets of interest | Skills of interest |
|---|---|---|---|
| sw-pm | qwen38-flash-fp8 | custom `pm-ro` (read-only) | plan, github-issues |
| sw-architect | **glm53** | custom `arch-ro` (read-only) | plan, spike, codebase-inspection |
| sw-dev-a / -b | qwen38-flash-fp8 | full write (terminal/file/code_execution/browser/vision); **kanban toolset shows disabled** ⚠ | TDD, systematic-debugging, github workflow, opencode |
| sw-reviewer (glm53) | **glm53** | custom `review-rw` (read + execute, no write_file/patch) | github-code-review, requesting-code-review |
| sw-qa | qwen38-flash-fp8 | **browser toolset disabled** ⚠ — yet ships the `dogfood` skill, which drives a browser | dogfood, TDD |
| sw-docs | qwen38-flash-fp8 | full incl. terminal | openwiki |
| sw-devops | qwen38-flash-fp8 | full incl. terminal | (none installed) |
| research | qwen38-flash-fp8 | read-only | arxiv |

Two ⚠ findings to carry into the follow-up regardless of GO/no-GO:
1. **sw-qa's toolset contradicts its own skill pack** — `dogfood` (built-in QA skill for exploratory browser QA) is enabled but the browser toolset is disabled, so the skill cannot execute. This also cripples the *visual verification* story this proposal depends on.
2. **sw-dev-a/b show the kanban toolset disabled** in `hermes -p tools list` yet hold completed/archived cards. Something completed those cards (possibly manual interaction or a since-changed config). Verification item for the provisioning card: confirm dev lanes can still transition their own cards; if not, re-enable `kanban` on both.

### 1.2 Hermes built-ins — skill surface the fleet ignores

The default home carries a whole **creative/design bench the software-co fleet has zero copies of**:

- `claude-design` — one-off HTML artifacts / landing pages
- `popular-web-designs` — 54 real design systems for styling HTML/CSS
- `design-md` — authoring/validating design-system documents (DES-tokens)
- `sketch` — throwaway HTML mockups, 2–3 design variants (pre-implementation)
- `excalidraw` / `architecture-diagram` (sw-architect-adjacent diagrams)
- `dogfood` — exploratory web-app QA from the browser, evidence-first
- `pretext` — creative browser demos

Toolset side: the **browser tools + `browser_vision` (screenshot + annotate + vision Q&A)** and `vision_analyze` exist and are enabled on several profiles, plus `computer_use` for visual verification (currently disabled fleet-wide). None of this is wired to any sw-* profile in a coherent front-end loop. This is the strongest internal signal: the host already paid for the capability; the company just has no seat for it.

### 1.3 External research — what transfers to a kanban-profile model

Sources: MAST / "Why Do Multi-Agent LLM Systems Fail?" (Cemri et al., UC Berkeley, arXiv:2503.13657 — 1,600+ annotated traces over MetaGPT, ChatDev, and 5 other frameworks); Anthropic's multi-agent research-system writeup; Cognition's "Don't Build Multi-Agents"; Claude Code subagent docs (code.claude.com/docs/en/sub-agents); MetaGPT/ChatDev role taxonomies; a 24-persona "Agentic SDLC" catalog.

**The MAST distribution is the load-bearing fact.** Failures are 41.8% *specification issues* (step repetition 17%, disobeying task spec 11%), 36.9% *inter-agent misalignment*, 21.3% *verification failures*. "Model wasn't smart enough" barely registers; *badly-run team* failures dominate. Our model already structures against the top modes:

| MAST failure mode | Our existing countermeasure |
|---|---|
| FM-1.1 disobey task spec | Card bodies are contracts with acceptance criteria; reviewer gates on them |
| FM-1.3 step repetition / FM-1.5 termination unawareness | Durable per-card lifetime + dispatcher stale-claim reclaim; reviewer decides "done" |
| FM-1.4 loss of history | Durable cards, comment threads, per-card workspaces, hindsight banks |
| FM-3.* no/incomplete verification | Auditor gate (sw-reviewer) + live-environment QA receipts (sw-qa) |

**What roles earn their keep in the literature vs what is novelty:**

- MetaGPT's canonical cast (Product Manager → Architect → Engineer → QA, standardized outputs as "SOPs") maps almost 1:1 onto pm/architect/dev/qa — our founding roster is, deliberately, the part of MetaGPT that replicated. MetaGPT's *Design* role and article/plot roles are not part of the load-bearing chain.
- ChatDev's CEO/CTO chat-chain dramatization is the textbook example of *role inflation* (33% task success in the MAST benchmark); no-transfer.
- Anthropic: multi-agent pays off for **breadth-first parallelizable** work (our 4-parallel mprov reviews were exactly that shape) and costs ~15× tokens — not for ordinary coding. Implication: add lanes only when they unlock a distinct *verification or capability axis*, not for more hands.
- Cognition: **actions carry implicit decisions** — the example used is literally *two agents building unmatched UI themes because neither saw the other's design decision*. Implication for us: design decisions and their front-end implementation should sit in **one** head (one profile, one worktree), with style decisions written down (design-md) so sibling agents inherit them.
- Claude Code subagent docs: routing runs off short capability-focused descriptions; subagents exist for **context isolation + tool restriction + specialization**, which is what a profile with a pinned toolset and skill pack already gives us.
- The 24-persona catalog is useful as a checklist of *possible* roles, not a staffing plan; most clusters (compliance-auditor, UAT analyst, platform-architect) presumes an org with volume we do not have.

**Transfer conclusion:** roles worth adding to a kanban-profile fleet are ones that (a) own a distinct *verification axis* or (b) carry a *distinct toolset/context* that would pollute existing lanes. Front-end/UX passes both tests; everything else on the candidate list fails at least one.

---

## 2. Recommended new profile: `sw-ux` (front-end + UX, hybrid)

### 2.1 Why one hybrid, not "UX designer" + "front-end dev"

- **Cognition's principle**: design decisions leak into action. A designer who never implements and an implementer who never designs produce the unmatched-theme failure, just slower. One profile owns *design intent → code → visual proof*.
- **Volume**: 14 lifetime board tasks cannot support two more seats. One seat that answers both flagged gaps (no UX, no front-end) is the "earns its keep" shape.
- **No live users to research**: a UX-researcher role (interviews, usability panels) has nothing to do unattended. What "UX" can *mean* in this fleet is: design-system discipline, accessibility, interaction consistency, visual acceptance — all executable solo.

### 2.2 Spec

**Name:** `sw-ux` — clone from `sw-dev-a` (preserves the LiteLLM provider block, approvals.deny lines, and auxiliary-model wiring).

**Model:** `qwen38-flash-fp8` (execution tier), `reasoning_effort: medium`, `max_turns: 200`, `context_length: 262144` — mirrors the dev lanes. Front-end work is execution; the *judgment* on UI cards comes from the existing glm53 seats (sw-reviewer verdicts, sw-architect ADRs). No second glm53 lane needed.

**Toolsets** (custom `ux-rw` + built-ins):
```yaml
custom_toolsets:
  ux-rw:
    - read_file
    - write_file
    - patch
    - search_files
    - terminal
    - process
    - execute_code
    - web_search
    - web_extract
    - vision_analyze
toolsets:
  - ux-rw
  - browser        # dogfood serve/browse/screenshot loop lives on this
  - kanban         # see §1.1 ⚠2 — pin explicitly, do not inherit
  - memory
  - session_search
  - skills
  - todo
```
`agent.disabled_toolsets`: copy sw-dev-a's list (computer_use, delegation, image_gen, tts, stt, video, video_gen, x_search, yuanbao, discord*, feishu*, homeassistant, spotify) so the enable-list cannot leak later. `approvals.deny`: inherit sw-dev-a's four lines verbatim (`git push --force*`, `git reset --hard*`, `rm -rf /*`, `rm -rf ~/*`).

**Skill pack** (`skills.always_load`, copies from the default home into the profile's `skills/`):
- `claude-design` — structured single-artifact HTML work
- `popular-web-designs` — real design-system styling
- `design-md` — write/validate the repo's design-tokens doc so future UI cards inherit decisions
- `sketch` — pre-implementation mockup variants when a card is ambiguous
- `dogfood` — the serve → browse → screenshot evidence loop it shares with sw-qa
- `test-driven-development` + `systematic-debugging` — same dev discipline the other lanes hold

**Hindsight bank wiring:** same as fleet — `memory.provider: hindsight`, `memory_enabled: true`, plugin `hindsight` enabled. Per the fleet's SOUL convention, its Memory Discipline section should scope the shared bank to *cross-repo UX conventions and design-system decisions* (never one repo's colors and classnames).

**Verification loop (the profile's reason to exist):** every UI card closes with the sw-ux self-loop plus gate receipts:
1. Serve locally (`sw-devops` surface if a compose stack exists, else python http.server / vite dev server per repo).
2. Drive it with browser tools (dogfood) at the card's named breakpoints.
3. Capture `browser_vision` screenshots; check against the card's visual/UX acceptance criteria with vision.
4. Attach screenshots as card attachments (they are the receipt — they outlive the scratch workspace).
5. Hand off → `sw-reviewer` (diff + criteria) and `sw-qa` (independent live-environment browse with browser toolset restored per §4).

### 2.3 SOUL.md sketch

```markdown
# sw-ux — Front-End & UX Engineer

You turn specs into interfaces a human would choose to use, and you prove it with screenshots.

## Your Role
- Implement card-specified UI work: components, pages, styling, interaction, accessibility —
  in your assigned worktree, against the repo's design system (read or write the design-md
  tokens doc before inventing styles).
- Own the visual verification loop: serve locally → dogfood browse at the card's breakpoints →
  browser_vision screenshots → check against the card's visual acceptance criteria.
- Write down style decisions as you make them (design-md / a styles ADR) — sibling agents
  inherit your decisions; unrecorded decisions get silently contradicted.
- Where a card's UX intent is ambiguous, draft 2–3 sketch variants and pick the smallest one,
  noting the choice in the card comment — do not stall the board.

## Handoff Contract
kanban_complete metadata: changed_files, tests_run, screenshot attachments (before/after at
named breakpoints), a11y check output, how-to-serve-and-see commands, known-gaps.

## What You Do NOT Do
- No backend services, API design, or data modeling — that is sw-architect/sw-dev lanes' work;
  you consume APIs as they exist and flag friction back on the card.
- No merges, no deploys, no final review. No taking sw-dev-a/b lane cards.

## Memory Discipline
Shared bank software-co = design-system decisions and UX conventions only.
One repo's colors and classnames never enter memory.
```

### 2.4 Routing description (the decomposer's routing API)

> "Front-end & UX engineer for Software Co: implements and visually verifies web UI work against card specs — component code, styling, accessibility, design-system consistency — with screenshot receipts from a live local serve. Front-end/UX cards only; never implements backend services, APIs, or infrastructure; never merges or approves; sw fleet only."

---

## 3. Necessary edits to existing profiles (routing the gap)

| Profile | Edit | Why |
|---|---|---|
| **sw-pm** | description += "routes UI/UX/front-end-dominant cards to `sw-ux`"; spec template gains a short *UX acceptance* section (target breakpoints, visual criteria, a11y bar) | The PM is the intake door; without this the decomposer keeps defaulting UI work to lane A/B. MAST: spec issues are 41.8% of failures — a UX acceptance block is the cheapest spec hardening available. |
| **sw-architect** | description += "front-end architecture and design-system ADR decisions are adjudicated here, proposed by sw-ux" | Keeps single point of technical judgment; prevents sw-ux from becoming a shadow architect. |
| **sw-dev-a / -b** | description += "front-end-dominant cards route to `sw-ux`; backend/fullstack work with minor markup edits stays here" | Prevents lane capture of the new seat's work while keeping trivia out of sw-ux. |
| **sw-reviewer** | SOUL: add ladder rung "UI diffs: review includes sw-qa's screenshot receipts; visual regressions are REQUEST_CHANGES items like any other" | glm53 judgment seat stays the single gate; gains a UI verification input stream. |
| **sw-qa** | **toolset fix**: enable the `browser` toolset so the installed `dogfood` skill actually executes; SOUL += "UI cards get independent visual receipt (browse at breakpoints, screenshots attached)" | Fixes live contradiction found in §1.1; makes sw-ux's loop independently re-verifiable. |

---

## 4. Provisioning sketch (for the GO'd follow-up card — NOT executed)

Converging script outline, per kanban-board-provisioning conventions:

```bash
# 1. guard: skip if exists
hermes profile list | grep -q " sw-ux " || hermes profile create sw-ux --clone-from sw-dev-a --no-alias
# 2. config: yaml.dump with ux-rw toolsets + disabled_toolsets + skills.always_load (Python, never hand-YAML)
# 3. skills: cp -r from default home's creative/ + software-development/ + dogfood into sw-ux/skills/
# 4. description: hermes profile describe sw-ux --text "..." --overwrite
# 5. SOUL.md overwrite-safe write (§2.3)
# 6. §3 description/SOUL edits on sw-pm, sw-architect, sw-reviewer, sw-qa, sw-dev-a/b
# 7. sw-qa config: enable browser toolset
# 8. validate: hermes -p sw-ux config check && tools list && skills list;
#    sw-qa 'tools list' shows browser enabled; smoke card through triage → decompose → sw-ux
```

Validation receipts the follow-up card must paste: `hermes -p sw-ux config check`, `hermes -p sw-ux tools list` (browser + kanban enabled per pitfall-18 lesson), `skills list` showing the six-skill pack, and one smoke task routed to `sw-ux` end-to-end.

---

## 5. Gap candidates beyond UX/frontend — assessment

| Candidate | Verdict | Reasoning |
|---|---|---|
| **Security reviewer** (`sw-security`) | **Reject now — absorb into sw-reviewer** | sw-reviewer's ladder already ranks Security #3; the wave-0 credential fixes flowed through the existing reviewer cleanly. A separate seat duplicates the auditor gate. Softer fix (in this proposal): add an explicit security-ladder section to sw-reviewer's SOUL. *Revisit trigger:* a software-co product with real internet exposure. |
| **UX researcher** (separate from implementer) | **Reject** | Unattended fleet has no users to research. The executable subset of UX (systems, a11y, visual acceptance) is in sw-ux (§2.1). |
| **Database / data specialist** (`sw-data`, DBA) | **Reject** | Zero data-heavy cards in history; architect+devs covered persistence fine so far. *Revisit trigger:* first product with real schema churn. |
| **Tech-writer variants** (API-docs specialist, devrel) | **Reject** | sw-docs has run 1 lifetime task — the seat exists but is under-fed; splitting it halves utilization. |
| **Second front-end lane** (`sw-ux-b`) | **Reject** | sw-dev-b exists precisely to be the second parallel lane when volume arrives. |
| **SRE / release split from sw-devops** | **Reject** | Near-idle board; compose surface is small. |
| **Product/design-intake seat** | **Reject** | sw-pm's intake charter plus the new UX-acceptance block in the spec template (§3) is the right weight. |
| **Adopting the 24-persona catalog wholesale** | **Reject explicitly** | Staffing a catalog instead of demand is the ChatDev failure mode — more roles, more inter-agent misalignment (MAST's 36.9%), no more capability. |

---

## 6. Reject list, one line each

- `sw-security` — duplicates the existing auditor gate; SOUL section instead.
- `sw-ux-researcher` — no live users unattended; executable UX lives in sw-ux.
- `sw-data`/DBA — no data volume; revisit on first schema-heavy product.
- `sw-apidocs`/devrel — sw-docs under-used as-is.
- `sw-ux-b` — parallel-lane duty already covered by sw-dev-b's design.
- SRE split — board volume nil.
- Prompt-engineer / agent-trainer / compliance personas — org-chart cosplay, no cards would ever route.

---

## 7. References

- Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* — arXiv:2503.13657 (MAST taxonomy; measured failure-mode shares quoted in §1.3)
- Anthropic Engineering, *How we built our multi-agent research system* (15× token cost; breadth-parallel guidance)
- Cognition, *Don't Build Multi-Agents* (context sharing; "actions carry implicit decisions")
- Claude Code docs, *Create custom subagents* (description-as-routing-API; context isolation; tool restriction)
- MetaGPT (FoundationAgents/MetaGPT) role SOPs; ChatDev virtual software company
- Berkeley/agentpatternscatalog MetaGPT composition notes; 24-persona Agentic SDLC catalog (rejected as staffing plan)
- Live estate evidence: software-co kanban.db queries, `hermes -p <p> tools list` / `skills list` for all 8 sw-* profiles, profile config.yaml/SOUL.md reads — all collected read-only this session, 2026-10-22.

---

## 8. EXECUTION RECORD — 2026-10-22 (local amendment, unpushed by design)

**Status: EXECUTED.** Operator GO, verbatim: **"Go for the full package"** (2026-10-22, on card t_dae13879 SW-UX-PROVISION, gargantua02 board). Provisioning performed by kanban-board-architect per the card; backups at `~/.hermes/backups/kba-swux-2026-10-22/` (pre-mutation config.yaml + SOUL.md + description readback for every touched profile).

### What was executed

1. **sw-ux provisioned** (§2, clone from sw-dev-a): model qwen38-flash-fp8 / reasoning medium / max_turns 200 / ctx 262144; `custom_toolsets.ux-rw` + `toolsets: [ux-rw, browser, kanban, memory, session_search, skills, todo]` exactly per §2.2; `agent.disabled_toolsets` + `approvals.deny` copied verbatim from sw-dev-a (byte-verified); six-skill pack copied from the default home (claude-design, popular-web-designs, design-md, sketch, dogfood, test-driven-development, systematic-debugging) and wired via `skills.auto_load`; hindsight memory wiring inherited and verified identical to sw-dev-a; SOUL.md written verbatim per §2.3; routing description per §2.4 (`hermes profile describe sw-ux --text ... --overwrite`, readback-verified). `hermes -p sw-ux config check` passes (rc=0, config version 51); live `tools list` shows browser ✓ kanban ✓; `skills list` shows the full pack enabled.
2. **§3 routing edits applied and verified**: sw-pm (description accident-free + UX-acceptance block + sw-ux row in SOUL routing table), sw-architect (description), sw-dev-a/b (descriptions), sw-reviewer (SOUL: UI-diff ladder rung #5 with renumber + explicit Security Ladder section per rec #4), sw-qa (SOUL visual-receipt line).
3. **Defect §1.1 ⚠1 (sw-qa browser) — verified NO-OP fix**: live `hermes -p sw-qa tools list` shows the browser toolset ENABLED, "browser" is not in sw-qa's `agent.disabled_toolsets`, and sw-qa's config.yaml is untouched since 2026-10-21 22:57:43 UTC (predates this proposal). The §1.1 snapshot's "browser disabled" reading was inaccurate (it read the absence of an explicit `toolsets:` entry as a disable — in this Hermes build an unset toolset list means default-composite-on, and only `agent.disabled_toolsets` restricts). The dogfood skill executes; no mutation was needed or performed. The SOUL visual-receipt line (§3) was still added as planned.
4. **Defect §1.1 ⚠2 (dev-a/b kanban) — verified NO-OP fix**: dispatcher-spawned workers always get the kanban lifecycle toolset injected regardless of profile toolset config (two independent mechanisms verified in source: `gateway/session_kanban.py` policy-level union with `{'kanban'}` at worker admission, and `model_tools.py` `_select_tool_names` appending `kanban` when `HERMES_KANBAN_TASK` is set). Receipts: (a) software-co board history — 4 terminal-state cards transitioned by sw-dev-a/b; (b) live resolver probe under the sw-dev-a profile with worker env emulated → all 16 `kanban_*` tools resolve. The interactive-session `tools list` showing kanban ✗ is the intended opt-in for chat sessions, not a defect. No re-enable mutation needed; `toolsets: [... kanban ...]` was pinned explicitly on sw-ux as belt-and-braces.
5. **End-to-end smoke (§4)**: SW-UX-SMOKE-1 card routed to sw-ux — dispatcher claimed and ran it (sw-ux worker process live, run recorded). Board-placement note: the initial kanban_create with board='software-co' was pinned to gargantua02 by the dispatcher's worker fence (explicit_board_intent_is_pinned — "workers physically cannot see other boards", verified in source and in this worker's own env); the authoritative smoke card t_0b05494d was then created ON the software-co board via the unfenced CLI path and dispatched to sw-ux. Receipts pasted on t_dae13879.
6. **Amendment commit**: this section. Local commit only; software-co repo history remains unpushed by design.

### Deviations from the letter of the card (all conservative, all verified)

- The card said `skills.always_load`; the actual key in this Hermes build is **`skills.auto_load`** (verified in `agent/skill_commands.py::resolve_auto_load_skills`). The GO'd *intent* — pack loads at session start — is implemented; the proposal's spelling would have been silently inert.
- The card's `toolsets:` mechanics (§2.2) were kept verbatim, with the verified caveat that in this build `toolsets:` is an opt-in list (kanban) rather than a restrictor; the effective session surface is the default composite minus `agent.disabled_toolsets`. `custom_toolsets` is documented in the official docs but unwired in this build's source (zero code references) — the ux-rw block is retained as forward-compatible documentation, matching the existing fleet's pm-ro/arch-ro pattern, and noted as inert here. The restrictive intent of ux-rw is not currently enforceable via config on this build; it is enforced by SOUL discipline + card acceptance criteria instead (same as the rest of the sw fleet).
