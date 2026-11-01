# UPSTREAM ISSUE DRAFT — Board-scoped profile composition ("board layers")

> STATUS: **LOCAL DRAFT — DO NOT FILE.** This text has NOT passed the estate's gate chain
> (distiller gate) nor the operator final gate. Filing is forbidden until both are stamped on
> the filing card. Tracked refs were verified OPEN on 2026-11-01 (live GitHub API dedupe sweep);
> re-verify before any filing.

---

## Proposed title

Role × board profile composition: boards as a layer over profiles, not a reason to clone them

## Suggested labels / area

`area/profiles` (Multi-profile isolation, HERMES_HOME scoping), `area/kanban`

## Problem

A Hermes profile is one flat bundle of **identity** (SOUL, model/provider, toolsets) and
**context** (memory, session history, host facts/rules, skills, secrets). The kanban feature
made the *board* the natural unit of context — a multi-board setup needs per-board memory,
per-board skills, often a per-board messaging bot token — but the only composition unit Hermes
has is the profile. So users who run the same role on several boards end up **cloning the
profile per board**:

- N copies of near-identical roles (butlers, researchers, scribes) that differ mainly in memory
  bank, sometimes a couple of skills and a SOUL paragraph, almost never the model;
- every identity-level improvement (SOUL edit, toolset change, model swap) applied N times by hand;
- clones drift silently.

There is clear demand for per-board *knobs* already on the tracker, but it arrives fragmented —
one field at a time:

- **PR #64625** — board-local allowed-profiles policy vs a machine-level ceiling (PR #87741 closed
  as its duplicate)
- **Issue #141889** — per-board `orchestrator_profile` with board→global fallback
- **Issue #118116 / PR #136925** — per-board dispatch caps via `board.json`
- **PR #89217** — `doctor` diagnostics for profile composition
- **Issue #110080** — forbid direct SQLite writes to board state

Each solves a symptom of the same underlying gap: **the board is not a composition layer.**

## Proposal

Split the two axes explicitly and compose them at launch:

- **Role profile** — *who*: identity, model/provider, toolsets, base SOUL, base skills. Defined
  once; unchanged on disk (`~/.hermes/profiles/<name>/`).
- **Board layer** — *where*: memory, sessions, host facts/rules, skills, env/secrets. Lives in
  the **existing board directory** (`<kanban home>/kanban/boards/<slug>/`, next to `board.json`
  and the board DB), so a board stays self-describing and archiving a board archives its agents'
  context with it:

```
<board>/
  board.yaml          # layer manifest: roles allowlist, skills/toolset deltas, env manifest ref,
                      # per-role overrides (the only place model may be touched, explicitly)
  SOUL.md             # board fragment, APPENDED to the role SOUL; role SOULs may declare
                      # {{board.hosts}} / {{board.rules}} slots the board fills — kills
                      # duplicated host prose and giant SOULs
  skills/             # board skills, unioned into the role's skill index (on-demand, not injected)
  env/manifest.yaml   # env layer: exports a NAMES-only list; values never rendered by tooling
  state/<role>/       # per-(role, board) state home: state.db, sessions/, memories/ (MEMORY.md,
                      # USER.md, provider storage)
```

- Running agent = **role × board**, composed at launch, with precedence
  **role → board base → board per-role `overrides` → profile `pin:`** (pin = role-declared keys a
  board may never touch, e.g. a specialist that keeps its own memory bank).
- **All three launch paths**: dispatcher workers already receive `HERMES_KANBAN_BOARD`; interactive
  and cron executions gain `--board <slug>` / a `board:` job field; a single `butler` role can then
  serve every board, each with its own bot token from the board env layer.
- **Boards as isolated devices**: a board-pinned agent is hermetic — kanban tools default to the
  pinned board and refuse other `board=` values (extending the existing worker env-pin fence to
  interactive/cron), and memory/sessions/skills/env resolve only from the board home. Genuine
  cross-board agents opt out explicitly via an operator-granted `boards: all` capability, surfaced
  in dry-run output — never a default.
- **Trust tooling**: `hermes profile effective --profile <role> --board <slug>` renders the
  composed SOUL, config, skill list, env **names** (never values), and the source layer of each
  line — one command answers "what would this agent be". This subsumes the diagnostics proposed
  in PR #89217 and would render every existing and future per-board knob in one place.
- **Zero-change guarantee**: a board without `board.yaml` is unlayered; with no layered boards
  anywhere, behavior is byte-identical to today (additive `boards:` config key only).

## How it stays upstream-safe / what's out of scope

- No kanban schema changes; no new profile semantics for plain single-board installs.
- No confinement claims: fencing is cooperative client-layer scoping, the same honesty as the
  current worker fence (issue #110080's direct-SQLite hardening is complementary).
- State is per (role, board) — no shared-memory magic; the "one writer per home" rule from the
  profiles docs is preserved for every physical directory.
- Migration of existing per-board clones stays out of core (a helper can be a follow-up).

## Evidence / regression surface

Draft RFC with full schema (board.yaml, slot syntax + strict-at-launch/tolerant-at-dry-run
semantics), precedence algorithm (delta-union list keys; `pin:` over overrides), state-dir
derivations, fencing mechanism, and per-launch-path landing points (file:line against current
main) is written and being implemented behind tests whose centerpiece is the zero-change
byte-identity regression. Happy to adapt the proposal to maintainer feedback on naming and
schema before any PR.

## Relation to existing tracker items

Not a duplicate of any single item above; it is the unification they each reach toward. PR #64625's
board-local allowed-profiles policy maps to the manifest's `roles:` allowlist; #141889's
orchestrator slot and #118116's caps become ordinary fields of one precedence engine; #89217's
diagnostics become the general `profile effective` renderer; #110080 remains adjacent hardening.
