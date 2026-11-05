---
sidebar_position: 13
title: "Board Layers (Role × Board Composition)"
description: "Compose one role profile with many kanban boards — per-board memory, skills, SOUL context, and env, with boards isolated as devices"
---

# Board Layers — One Role, Many Boards

A [profile](../profiles.md) is one flat bundle of two things: **who** the agent is
(personality in `SOUL.md`, model/provider, toolsets, base skills) and **where** it works
(memory bank, session history, host facts and rules, board skills, bot tokens). If you run
the same role on more than one [kanban board](./kanban.md), only the *where* changes per
board — but because the profile is the only composition unit, the usual workaround is to
clone the profile per board. Clones drift, and every identity-level improvement has to be
applied N times.

**Board layers** split the two axes. You define a **role profile** once, keep per-board
context in the **board's own home directory**, and Hermes composes the pair at launch:

```
running agent = role × board
```

A board without layer files behaves exactly as before; nothing changes anywhere until you
add a `board.yaml` (see [Zero-change guarantee](#zero-change-guarantee)).

## The four layers

Composition is a pure launch-time computation over four layers, general → specific:

| # | Layer | Lives in | Can change |
|---|-------|----------|------------|
| 1 | **Role profile** | `~/.hermes/profiles/<role>/` | everything (today's behavior) |
| 2 | **Board base** | `board.yaml` root keys, `SOUL.md` fragment, `skills/`, `env/` | memory provider/bank, skills & toolset *deltas*, SOUL fragment/slots, env |
| 3 | **Board per-role overrides** | `board.yaml overrides.<role>` | anything board-side, **including model/provider — only here, and only with a `reason:`** |
| 4 | **Role `pin:`** | role `config.yaml boards.pin` | *erasure*: pinned keys ignore layers 2 and 3 entirely |

List-valued keys (`skills`, `toolsets`) merge as **delta-unions** — each board layer adds
and removes entries from the role's list; nothing silently replaces it. A full `replace:`
exists only at the `overrides.<role>` layer, only for toolsets (never skills), and must
carry a `reason:`. `pin:` outranks overrides by design: a board may extend a shipped role,
it may not rewrite its specialty.

## Board home layout

The board layer lives in the **existing** board directory, next to `board.json` and the
board DB — so a board is self-describing, and archiving a board archives its agents'
context with it:

```
<kanban home>/kanban/boards/<slug>/
├── board.json                  # existing board metadata (unchanged)
├── kanban.db                   # existing per-board DB (unchanged)
├── workspaces/                 # existing (unchanged)
│
│  ── added by board layers ──
├── board.yaml                  # REQUIRED marker of a layered board; the layer manifest
├── SOUL.md                     # board SOUL fragment, APPENDED to each bound role's SOUL
├── skills/                     # board skills, unioned into the role's skill index
├── env/
│   ├── manifest.yaml           # env layer: exported NAMES + sources (values live apart)
│   └── secrets.env             # optional 0600 values file (never rendered by tooling)
└── state/
    └── <role>/                 # per-(role, board) state home
        ├── state.db            #   session DB
        ├── sessions/           #   gateway session index
        ├── memories/           #   MEMORY.md, USER.md, provider storage
        └── logs/
```

`state/<role>/` is a state root, not a profile: `hermes profile list` deliberately never
adopts it. Each `(role, board)` pair has its own state root, so the "never point two agent
processes at the same profile" rule from the [profiles doc](../profiles.md) stays literally
true for every physical directory.

## board.yaml reference

```yaml
version: 1                     # required; unknown version = composition error

roles:                         # OPTIONAL allowlist of roles that may bind here.
  - assistant                  # Absent = any role may bind (open board).
  - researcher

memory:                        # OPTIONAL board base — the rarest override.
  provider: hindsight          #   swap the memory provider for bound roles
  bank: my-explicit-bank       #   explicit bank id; default is derived per pair (§State)

skills:                        # delta-union onto each bound role's skill list
  add:
    - ./skills/deploy-runbook  # path form: relative to the board home, must stay inside it
    - kubernetes-node-reboot-safety   # name form: resolved against role skills, then the hub
  remove: []                   # role skills to suppress on this board

toolsets:
  add: [kanban]
  remove: []

soul:
  fragment: ./SOUL.md          # appended to the role SOUL (default; rarely spelled out)
  slots:                       # fills for {{board.*}} slots declared in role SOULs
    hosts: |
      - build-01: 8x GPU, long jobs only
    rules: |
      - Always file receipts as board comments after a mutation.

env:
  manifest: ./env/manifest.yaml   # the only accepted form (see Env layer)

overrides:                     # per-role, most specific board-side layer
  researcher:
    model: openrouter/auto     # model may be touched ONLY here …
    reason: "board pays for its own research quota"   # … and ONLY with a reason
    skills:
      add: [./skills/webresearch]
  assistant:
    toolsets:
      replace: [default, kanban, gateway]   # toolset replace lives only at this layer
      reason: "this board's assistant is chat + board only"

meta:
  description: "Example project board"
  maintainers: [you@example.com]
```

Validation is strict by design: unknown top-level keys are a **schema error** (a typo like
`skils:` would silently drop every board skill otherwise), role names must be valid
profile names, and every path must resolve **inside** the board home — a board manifest can
never reach into a profile home or another board.

## SOUL fragments and `{{board.*}}` slots

The effective SOUL of a composed agent is the role's `SOUL.md` **plus** the board's
fragment appended. Instead of duplicating host facts and board law into N cloned SOULs, a
role SOUL declares holes and boards fill them:

```
My job is to keep work moving.

Board facts:
{{board.hosts}}

Board law:
{{board.rules}}
```

Rules that matter:

- Only `{{board.<name>}}` is special. Any other `{{ … }}` passes through verbatim — SOULs
  are prose, not templates.
- Slot values come only from `board.yaml soul.slots.<name>` and are substituted literally
  (never recursively rendered).
- **Unfilled slots are strict at launch.** A role with `{{board.hosts}}` bound to a board
  that doesn't define `hosts` fails the launch with a message naming the slot and the yaml
  key to add — a live system prompt with a hole where the host facts belong is silent
  corruption. `hermes profile effective` (dry-run) is deliberately tolerant and shows
  `[UNFILLED SLOT …]` inline so you can still inspect everything else.

## Env layer

The board env layer is a **manifest**, not a bare `.env`:

```yaml
# env/manifest.yaml
version: 1
vars:
  TELEGRAM_BOT_TOKEN                     # name only ⇒ value from env/secrets.env (0600)
  GITHUB_REPO: {value: acme/widget-co}   # non-secret literal, inline and reviewable
export: [TELEGRAM_BOT_TOKEN, GITHUB_REPO]  # ONLY these names overlay the agent env
```

- Only names listed under `export:` enter the agent environment; a values file can hold
  unrelated material for board scripts that never touches an agent.
- The board **wins** the names it exports (that is what "the board's bot token belongs to
  the board" means). A collision with the role's `.env` is surfaced as an error-level
  finding by `profile effective` and logged at launch.
- **Names-only rule:** no renderer, log line, or error message ever prints a value from the
  board env layer. `profile effective` reads the manifest, not the values file, so it is
  value-blind by construction. A manifest that exports provider-credential names
  (`OPENAI_API_KEY`, …) is flagged with a loud warning — model credentials belong to the
  role.

## State: memory, sessions, banks

Each `(role, board)` pair resolves to `<board>/state/<role>/` as its state root:
session DB, gateway session index, `MEMORY.md` / `USER.md`, and memory-provider storage all
relocate there. Memory providers need no configuration change — they re-bind every store
from the state root passed at launch.

The default memory-bank name is derived from the pair (e.g. `board-<slug>-<role>`), so two
different roles on one board never cross-write each other's memories. An explicit
`memory.bank` in `board.yaml` overrides the derivation, making a shared per-board bank a
deliberate, visible choice in `profile effective`.

## Launch paths

Composition works identically on all three ways an agent starts:

| Path | How the board is chosen |
|---|---|
| **Dispatcher workers** | Already receive `HERMES_KANBAN_BOARD` in their environment. If that board is layered, the worker composes itself at startup — no new configuration. Claim-time validation additionally refuses to dispatch to a role outside the board's `roles:` allowlist. |
| **Interactive / gateway** | `hermes --board <slug> …` pins the board for the session, or the role's `boards.default` supplies it. One `assistant`-style role can serve every board, each with its own bot token from the board env layer. |
| **Cron jobs** | A job may declare `board: <slug>`; the run composes that board. A cron run never inherits an ambient board. |

The pair is pinned for the lifetime of the process (or gateway conversation). An existing
session never re-reads `board.yaml` mid-conversation — re-pinning means a new session, the
same rule as switching profiles.

## Isolation: boards are independent devices

A board-pinned agent is hermetic **by mechanism, not by SOUL prose**:

- Kanban tools default to the pinned board and **refuse** any other `board=` value —
  refused in the shared client layer, before any DB connection opens. The refusal names
  the grant that would allow it. (Dispatcher workers already had this fence via their
  environment pin; board layers extend the same fence to interactive and cron launches.
  Delegated children inherit it.)
- Memory, sessions, skills, and env resolve only from the board home. There is no path
  from one board's state to another board's bank, credentials, or sessions.
- This is cooperative client-layer scoping, not OS confinement — the same honesty as the
  existing worker fence. It cannot stop arbitrary code with direct filesystem or SQLite
  access; hardening that surface is tracked separately upstream.

### `boards: all` — the meta-role opt-out

Genuine cross-board roles (fleet monitors, routers) opt out explicitly:

```yaml
# role config.yaml
boards:
  capability: all     # operator-granted, audited — never a default
```

Grant it with `hermes board grant-all <role>`, which records `granted_by`/`granted_at`
audit fields. A bare hand-edited `capability: all` without a grant record is warned about
by `profile effective`. A board can never grant it — boards don't mint their own
multi-board agents. Capability is orthogonal to `pin:`: a meta role may read every board
while keeping its own memory.

## Trust tooling: `hermes profile effective`

```
hermes profile effective --profile <role> --board <slug> [--json]
hermes profile effective --profile <role> --board none      # role alone, no layering
```

One command answers *"what would this agent actually be?"* — the composed SOUL with
per-section source provenance, the effective config with a `# from: <layer>` note on every
merged value (model overrides shown with their `reason:`), the merged skill list with
shadowed entries marked, the state root and bank name, the env **names** only, and the
fencing posture (`pinned` vs `boards: all`) including the exact refusal a cross-board call
would get. Exit codes: `0` clean, `1` warnings (extraneous slots, ungranted capability,
model override present), `2` composition errors.

## Zero-change guarantee

A board is layered **if and only if** its directory contains `board.yaml` (file-as-marker,
not a flag or env var). With no layered boards present:

- composition is the identity function — SOUL, config, skills, env, and state resolve
  exactly as before, byte-identically;
- the only added code on the launch path is one existence check;
- the only schema additions are the `boards:` key in role config and the new board files.

Single-board installs and plain multi-profile installs never observe a behavior difference.

## Roadmap

- **`hermes board adopt-profile <clone>`** — migration helper that folds an existing
  per-board profile clone into `role × board` (dry-run diff first): see
  [migration notes](./board-layers-migration.md).
- **Role specialization becomes cheap.** Once boards carry context, splitting `coder` into
  `python-coder` / `ts-coder` costs a SOUL and a toolset — not a full context clone.
- **Prose safety briefings retire.** Per-board "board discipline" paragraphs appended to
  cloned SOULs can be deleted once the same rules are enforced in code.
- **Board dashboards** (`hermes boards show <slug>`): bound roles, state sizes, last
  dispatch.
- **Rotate-with-board secrets**: bot tokens rotated with the board via the manifest's
  file source.

## See also

- [Quick-start: one role, two boards](./board-layers-quickstart.md)
- [Migrating cloned profiles](./board-layers-migration.md)
- [Profiles](../profiles.md) · [Kanban](./kanban.md) · [Memory](./memory.md) · [Skills](./skills.md) · [Cron](./cron.md)
