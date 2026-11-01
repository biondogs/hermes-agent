# RFC: Board-Scoped Profile Composition ("Board Layers")

Status:        Proposed (estate-approved core design; this RFC refines it into an implementable contract)
Authors:       sw-architect (design); operator (concept + rulings)
Date:          2026-11-01
Source truth:   NousResearch/hermes-agent @ `c627ec84` (shallow clone, read-only; file:line refs are
                valid for that commit)
Docs truth:     https://hermes-agent.nousresearch.com/docs — pages cited inline; divergences in §19
Companion:      `docs/BOARD-LAYERS-UPSTREAM-ISSUE-DRAFT.md` (local draft, NOT filed)

---

## 1. Problem

A Hermes profile today is one flat bundle. The profile home directory
(`docs/user-guide/profiles`, _profiles doc_: "a separate Hermes home directory … its own `config.yaml`,
`.env`, `SOUL.md`, memories, sessions, skills, cron jobs, and state database") conflates two axes:

- **Who the agent is** — identity: SOUL personality, model/provider, toolsets.
- **Where the agent works** — context: memory bank, session history, host facts/rules, skills, secrets/env.

On any estate that runs more than one kanban board, context varies **per board** while identity varies
per **role**. Because the only composition unit is the flat profile, every role gets cloned per board:
N near-identical butlers, N research/ops/scribe copies. An estate survey (59 profiles) found that what
reliably differs between a role's per-board clones is:

1. the **memory bank** (always),
2. **skills** and small **SOUL** deltas (often),
3. the **bot token / env** (for board-owned messaging bots),

and almost never the **model**. Clones drift, and every drift is fixed by hand. A rename, a toolset
change, or a SOUL improvement must be applied N times.

The kanban ecosystem inside hermes-agent has already started recognizing the board as a first-class
"place": boards have their own directories, DBs, workspaces and in-flight upstream proposals add
per-board policy knobs (§14). What is missing is a single composition model that says: an agent is a
**role × board** pair.

## 2. Goals and non-goals

### Goals

1. Define a **role profile** once; compose it with any **board layer** at launch.
2. All per-board state — memory, sessions, skills, env/secrets, SOUL board-prose — lives **in the
   board's existing home directory**, so a board is self-describing and archiving a board archives
   its agents' context with it.
3. Boards behave as **isolated devices**: a board-pinned agent cannot see another board's memory,
   credentials, sessions or kanban state, by mechanism rather than by SOUL prose.
4. Works identically on all three launch paths: **dispatcher workers**, **interactive/gateway
   sessions**, **cron jobs**.
5. **Zero-change guarantee**: with no board layer present, hermes behaves byte-identically to today.
6. A **trust/dry-run tool** (`hermes profile effective`) renders exactly what a composition produces,
   with provenance per line.
7. Upstream-safe: nothing estate-specific; gene is "role × board", not any particular estate.

### Non-goals (scope fences)

- **No change to the kanban data model** (tasks, runs, boards schema). Board layers add files *around*
  the existing board dir; they do not touch `board.json` semantics or the DB schema.
- **No multi-role shared memory.** State is per board **per role**. Cross-role memory sharing remains
  what it is today (external memory providers if desired).
- **No live migration.** Layering a board that already has cloned profiles does not merge or move
  their state automatically. A migration *helper* is roadmap (§15), not core.
- **No sandboxing/confinement claims.** As `agent/delegation_context.py` puts it for workers today:
  "cooperative runtime scoping, not confinement of code with direct SQLite access." Board fencing is
  enforced at every hermes client surface; it cannot stop arbitrary code with filesystem access run
  by the agent from reading another board's directory. (Upstream issue #110080 tracks the related
  hardening of direct SQLite writes.)
- **No per-board tool implementation.** Board env may configure existing tools (tokens, endpoint
  URLs); boards do not define new tools.
- **Not relitigating** the operator-approved core (role×board split, precedence order, board home =
  kanban board dir, boards-as-devices, `boards: all` opt-out). This RFC refines mechanism.

## 3. Concepts

| Term | Definition |
|---|---|
| **Role profile** | Today's profile, minus the assumption that it is per-board: identity + model/provider + toolsets + base SOUL + base skills. Physically unchanged: `~/.hermes/profiles/<name>/`. |
| **Board** | An existing kanban board: slug + home directory (`<kanban home>/kanban/boards/<slug>/`; see §4). |
| **Board layer** | The set of per-board files in the board home that compose onto a role: `board.yaml`, `SOUL.md` fragment, `skills/`, `env/`, `state/<role>/`. |
| **Composition** | The launch-time computation `effective(role, board) → EffectiveProfile` (§9). Pure function of on-disk state; no daemon. |
| **Layered board** | A board whose home contains a valid `board.yaml`. Only layered boards change behavior (§12). |
| **Unbound role** | A role with no board binding in the current launch. Behaves exactly as today. |
| **Meta role** | A role granted `boards: all` capability — may address any board. Operator-granted, never default (§10). |

An **agent execution** is always identified by the pair `(role, board|none)`. The pair is pinned for
the lifetime of the process/session (workers, cron runs) or of the gateway conversation (interactive).

## 4. Board home — physical layout

The board home is the **existing** board directory (`hermes_cli/kanban_db.py:485-498`:

```text
<kanban home>/kanban/boards/<slug>/
├── board.json                  # existing: metadata (name, created_by, archived tombstone)
├── kanban.db                   # existing: per-board DB ("default" keeps legacy <root>/kanban.db)
├── workspaces/                 # existing: per-board scratch workspaces
├── attachments/                # existing: per-board attachments
├── logs/                       # existing
│
│  ── added by this RFC ──
├── board.yaml                  # REQUIRED marker of a layered board; the layer manifest (§5)
├── SOUL.md                     # board SOUL fragment, APPENDED to the role SOUL (§6)
├── skills/                     # board skills, unioned into skills index, loaded on demand (§5.3)
├── env/
│   ├── manifest.yaml           # env layer manifest: NAMES + sources (§7)
│   └── secrets.env             # optional 0600 values file
└── state/
    └── <role>/                 # per-role, per-board state home (§8)
        ├── state.db            # session DB (SQLite + FTS5 structure, same as profile state.db)
        ├── sessions/           # gateway routing index / transcripts
        ├── memories/
        │   ├── MEMORY.md       # per-board built-in agent memory
        │   ├── USER.md         # per-board user profile notes
        │   └── <provider>/     # provider-owned storage (e.g. hindsight/), rooted here
        └── logs/
```

**Rules**

- `board_dir()` already normalizes slugs (`_BOARD_SLUG_RE`, kanban_db.py:374-398) and refuses
  traversal; adding files there inherits that safety.
- Directory `state/<role>/` is **not** a profile: it deliberately carries none of the profile identity
  markers (`hermes_constants.py:399`: `config.yaml`, `.env`, `SOUL.md`, `profile.yaml`, `auth.json`,
  `state.db` at a home *root* identify a profile). A state dir root has `state.db` — to keep
  `profile list` and `-p` from adopting board state dirs as profiles, the composer MUST ensure state
  dirs are only ever consumed via the EffectiveProfile, and the marker scan in `hermes_constants`
  should learn to skip roots under a board home (`*/kanban/boards/*/state/*`) — see card 3 (§16).
- Everything under `state/` is archival with the board: `hermes kanban boards archive` moves the
  board dir wholesale today; context follows automatically. No new archive path needed.
- The board env layer and state are owned by the board creator/maintainer (human or butler), the same
  trust domain as `board.json` and the DB itself.

## 5. board.yaml — the layer manifest

### 5.1 Schema (normative)

```yaml
# <board>/board.yaml
version: 1                     # required; only 1 defined. Unknown version = composition error.

# Which roles may bind to this board. Absent = any role may bind (open board).
# Listing roles explicitly is recommended; it is the board-side of the pairing contract.
roles:
  - butler
  - researcher
  - reviewer

# Default settings for every bound role (the "board base" layer).
memory:
  provider: hindsight          # OPTIONAL. Overrides role's memory provider for bound roles.
                               # Rare: most roles keep their provider and only get a different BANK.
  bank: board-software-co-researcher   # OPTIONAL explicit bank/tenant id; default is derived (§8.3).

skills:                        # list-valued; see §9.3 for semantics
  add:                         # names (resolved against role skills, then hub) or relative paths
    - ./skills/jira-runbook    # path form: relative to the board home
    - kubernetes-node-reboot-safety      # name form
  remove: []                   # role skills to suppress for this board

toolsets:                      # list-valued; see §9.3
  add: [kanban]                # e.g. give every bound role the interactive kanban toolset
  remove: []

soul:
  fragment: ./SOUL.md          # default; rarely needs spelling out
  slots:                       # fill values for {{board.*}} slots declared in role SOULs (§6)
    hosts: |
      - gaudi (training): 8x GPU, …
    rules: |
      - Always file receipts as board comments after a mutation.

env:
  manifest: ./env/manifest.yaml   # default; the ONLY accepted form (§7)

# Per-role overrides — MOST specific board-side layer. May touch model/provider ONLY here,
# and only explicitly. Anything put here that could have been in the base is a schema warning.
overrides:
  researcher:
    model: openrouter/auto      # explicit model touch — allowed but flagged in `profile effective`
    skills:
      add: [./skills/webresearch]
  butler:
    toolsets:
      replace: [default, kanban, gateway]   # full replace allowed ONLY at this layer (§9.3)

# Governance / documentation
meta:
  description: "Board for the example estate's software-co work"
  maintainers: [operator@example]          # free-form
```

### 5.2 Validation rules (enforced at load; card 1)

- Unknown top-level keys: **schema error** (fail closed, actionable message naming the key and the
  likely intent). Board.yaml is machine-read; silent-ignore hides typos (`skils:` losing all board
  skills) until an incident.
- Unknown keys inside `overrides.<role>`: error, except a reserved `x-*` escape hatch for
  forward-compat tooling.
- `roles:` entries and `overrides:` keys must be valid profile names (`normalize_profile_name`).
- Paths (`skills.add` path form, `soul.fragment`, `env.manifest`) resolve relative to the board home
  and MUST stay inside it (`..` escape = schema error) — a board manifest must not reach into
  profile homes or other boards.
- `overrides.<role>.model|provider` require a sibling comment key `reason:` (free text) — enforced in
  the schema so every explicit model touch carries an auditable why, rendered by `profile effective`.

### 5.3 Board skills

Board `skills/` mirrors the profile skills layout (`<category>/<name>/SKILL.md`). Board skills are
**unioned into the role's skill index** (index + offer surfaces + autocomplete), never injected;
progressive disclosure is unchanged (`docs/user-guide/features/skills`). Resolution order for a name
collision role-vs-board: **role wins** — a board may extend a role's knowledge, not silently rewrite
it; `profile effective` lists the shadowed board skill. (A role that wants the board version in a
specific case declares the pin `skills` or the board uses `overrides.<role>.skills.remove` on the
role skill name.)

Curation of board skills is heavyweight work, so it stays **human/butler-authored** — the curator
keeps its hands off board `skills/` exactly as it does bundled/hub skills today.

## 6. SOUL composition and slots

### 6.1 Fragment append

Effective SOUL = role `SOUL.md` **+** `\n\n` **+** board `SOUL.md` fragment (when the board layer
defines one and the role has not pinned `soul`). The fragment carries the "where" prose: board
mission, hosts, conventions, board-specific law. This is the mechanism that lets ~N per-board
SOUL-cloned paragraphs move out of role SOULs into board homes once (§15, roadmap).

Injection point: `agent/prompt_builder.py:1512 load_soul_md()` calls
`build_context_files_prompt` (prompt_builder.py:1720-1745) and `agent/system_prompt.py:554-555`.
The composed chain replaces the single `(home)/SOUL.md` read; all existing downstream handling is
untouched (scanning `_scan_context_content`, `strip_legacy_protocol`, truncation, distribution
manifest checks).

### 6.2 Slot syntax

Role SOULs may declare holes the board fills:

```
{{board.hosts}}     # multi-line block
{{board.rules}}
```

Normative rules:

- **Namespace**: only `{{board.<slot>}}` is special. Any other `{{ … }}` is passed through
  verbatim (SOULs are prose; templates like `{{Myshortcode}}` keep working). `{{board.` with no
  matching `}}` on the same line is passed through verbatim too (prose safety).
- **Sources**: slot values come from `board.yaml soul.slots.<name>` (text) — one source, no ifs.
  Board `SOUL.md` fragments do NOT define slots (a fragment is already board-local; it doesn't need
  indirection).
- **Slot values are raw text**, substituted literally, never recursively rendered (no injection
  chain).
- Whitespace: the entire slot token (including surrounding whitespace up to line boundaries' inner
  edge) is replaced by the value; blank line before/after a block value are normalized so a
  filled slot reads like authored prose.

### 6.3 Unknown / unfilled slot behavior (decided)

- **At launch (dispatcher worker, gateway session, cron run): strict.** A role SOUL containing
  `{{board.X}}` composed with a board that doesn't define `X` → **composition error**; the launch
  fails with a message naming the slot, the board, and the yaml key to add. Rationale: a live system
  prompt with a literal `{{board.hosts}}` or — worse — an empty gap where the host facts should be
  is silent corruption; failing the launch surfaces it at the only moment a human is watching.
  Same for a slot-bearing role SOUL composed with **no** board (slot with no source).
  Escape hatch: `HERMES_BOARD_SLOTS=loose` env (documented as testing-only) renders unfilled slots
  as empty + logs a warning.
- **In `hermes profile effective` (dry-run): tolerant.** Unfilled slots render as
  `[UNFILLED SLOT {{board.X}} — define soul.slots.X in <board>/board.yaml]` inline so the whole
  composition can still be inspected. Dry-run's job is visibility; gating it would hide the buggy
  layer that needs seeing.
- **Extraneous slots** (board defines a slot no bound role uses): warning in `profile effective`,
  not an error — boards serve roles whose SOULs evolve.

## 7. Env layer — manifest ref, not bare .env (decided)

**Format**: a manifest (`env/manifest.yaml`) naming the variables + their sources, plus value files.

```yaml
# <board>/env/manifest.yaml
version: 1
vars:
  TELEGRAM_BOT_TOKEN            # name only ⇒ value read from env/secrets.env (0600, git-ignored)
  GITHUB_REPO: {value: software-co/software-co}        # non-secret literal inline
  JIRA_URL: {value: "https://jira.example.internal"}   # non-secret literal inline
  VAULT_KV: {secret: file, path: ./env/secrets.env}    # explicit form (same default)
export: [TELEGRAM_BOT_TOKEN, JIRA_URL]   # the ONLY names overlaid onto the agent environment
```

**Why manifest-ref over plain .env (D3):**

1. **Names-only rendering for free.** The trust tool must print "which env names does this board
   inject" without ever touching values. A manifest is the names list; a bare .env has to be parsed
   and redacted, and every redaction path is a leak waiting to happen.
2. **Explicit export scope.** Only `export:` names are overlaid — a values file can hold unrelated
   secret material the board keeps for its own scripts without it ever entering an agent env.
3. **Non-secrets stay reviewable.** URLs and repo names are inline, diffable, scannable; secrets stay
   in the separate 0600 file.

Precedence: board env is overlaid **above** the role `.env` for its exported names. The board owns
the names it exports (that's what "the board's bot token belongs to the board" means); the role keeps
model/provider credentials untouched (a board manifest exporting model credentials is a governance
violation, and `profile effective` flags `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/other
credential-sounding names in `export:` with a loud warning). Collision between role `.env` and an
exported board name: board wins at launch (logged warning), and `profile effective` prints the
collision as an ERROR-level finding — surface in dry-run, availability at launch (D3).

Loader hook: `hermes_cli/env_loader.py` gains the board manifest as an additional source layer after
profile scope resolution (the same machinery multiplexing uses to overlay routed-profile scopes;
see `cron/scheduler_script.py:476-482` for the routed-profile precedent).

**Names-only rule (absolute):** no renderer, log line, dry-run, error message, or `profile effective`
section ever prints a value from the board env layer or secrets file. Violations are P0s.

## 8. State layout and derivation

### 8.1 The board state home

Each `(role, board)` pair gets `<board>/state/<role>/` — a home-shaped **state root**: `state.db`,
`sessions/`, `memories/` (incl. `MEMORY.md`, `USER.md`, provider storage), `logs/`. See §4 tree.

Two-agent-write hazard (profiles doc: "Never point two agent processes at the same profile — both
write memory automatically") is preserved: distinct (role, board) pairs have distinct state roots;
the same pair run twice concurrently is the same pre-existing hazard as running one profile twice,
with the same remedy (don't).

### 8.2 Bound state consumers

| Consumer | Today | Layered (unpinned) |
|---|---|---|
| Session DB (`state.db`) | `<HERMES_HOME>/state.db` via `hermes_state_dbfile` | `<board>/state/<role>/state.db` |
| Built-in memory (`MEMORY.md`, `USER.md`) | `<HERMES_HOME>/MEMORY.md` | `<board>/state/<role>/memories/MEMORY.md` |
| Memory providers (hindsight, honcho, …) | `initialize(hermes_home=<profile home>)` | `initialize(hermes_home=<board>/state/<role>)` |
| Gateway session index | `<HERMES_HOME>/sessions/` | `<board>/state/<role>/sessions/` |

The provider path requires **no provider changes**: `agent/memory_provider.py:121-128` already
mandates "bind every store, path, client, bank or tenant from `initialize()`'s `hermes_home`".
Passing a different `hermes_home` re-binds everything — the multiplexing contract (same file,
:84-103) was built for exactly this shape of per-agent-instance storage.

### 8.3 Derived names

- **Hindsight bank** (when the provider is hindsight and no explicit `memory.bank`):
  `board-<slug>` is tempting but wrong — two roles on one board would share a bank and cross-write
  role memories. Default is **`board-<slug>-<role>`**, i.e. bank = f(board, role) = f(state dir).
  Explicit `memory.bank` in board.yaml overrides (one shared-bank-per-board is then a *deliberate*
  configuration, visible in `profile effective`).
- **MEMORY.md / USER.md / state.db** never gain suffixed names; the directory distinguishes them.
- **Session DB identity**: `hermes_state` derives per-home storage from the DB path; pointing it at
  the board state root relocates the whole session surface. No schema change; the DB is simply
  younger (born when the board gets layered).
- Providers without a "bank/tenant" concept (e.g. builtin) need nothing: their storage is files
  under `hermes_home`, which is the state root.

### 8.4 What `pin:` may cover (decided)

Role `config.yaml`:

```yaml
boards:
  default: software-co     # OPTIONAL: default board binding for interactive launches
  pin:                     # role-layer keys that boards may NEVER touch
    - memory               # keep role's provider + bank + MEMORY.md/USER.md + provider storage
    - sessions             # keep role's state.db / session history
    - skills               # ignore board skills entirely
    - soul                 # no fragment append, no slot rendering
    - env                  # ignore board env layer
    - model                # board base/overrides cannot touch model (always honored — see D5)
    - toolsets             # board base/overrides cannot touch toolsets
  capability: all          # META-ROLES ONLY, operator-granted (§10)
```

- `pin:` accepts the closed list above or `["*"]` (fully unlayerable role: composition still pins the
  board for kanban fencing, but no other layer applies). Unknown entries = config error at load.
- `pin: [model, toolsets]` are **redundant safety**: the schema already forbids model/toolset in the
  board *base* (§5.1) — pinning them additionally blocks the explicit `overrides.<role>` route.
  Allowed for belt-and-braces on critical roles.
- NOT pinnable: `kanban` (the board binding itself — the pair is the point), and `nothing else`.

## 9. Precedence algorithm (normative)

### 9.1 The four layers

General → specific:

```
1. role profile                config.yaml, SOUL.md, skills/, .env, state
2. board base                  board.yaml root-level keys, SOUL fragment, slots, env, skills/
3. board overrides.<role>      per-role section of board.yaml
4. role pin:                   erasure (post-process), not a value source
```

### 9.2 Composition procedure

```
effective(role R, board B|none):
  role_cfg    = load_profile_config(R)                       # today's path, untouched
  if B is none or B is not layered (no board.yaml):
      return EffectiveProfile(role_cfg)                      # §12 zero-change guarantee — identity
  validate board.yaml (§5.2); roles: allowlist check
  pinned      = set(role_cfg.boards.pin) or ({"*"} if pin == ["*"]) 
  layers      = [board_base(B), board_overrides(B, R)]
  for each composable key class K in {scalar-config, skills, toolsets, soul, env, memory, state}:
      if K ∈ pinned:            value = role_value; provenance = "role:pinned"
      else:                     value = merge(role_value, [layer.value(K) for layer in layers])
  composed_soul = role_soul (+ fragment), slots rendered §6.3
  return EffectiveProfile with per-field provenance
```

### 9.3 Key-class merge semantics (decided)

- **Scalar config keys** (model, provider, memory.provider…): specific layer wins; the base layer's
  *scalar* set is restricted to `memory.*` only (model/provider/toolsets live in `overrides.<role>`
  or nowhere — §5.1). So in practice the only cross-board scalar divergence a base may introduce is
  the memory provider, which is context, correctly placed.
- **List-valued keys — `skills` and `toolsets`: DELTA-UNION, not replace.**
  Each layer expresses `add` / `remove` deltas applied in order (base then overrides): 
  `value = (role ∪ base.add − base.remove ∪ override.add − override.remove)`.
  - Rationale for union: the whole point of the survey finding ("skills often differ, model never")
    is that board skills are *additive knowledge*; a replace default turns every board.yaml into an
    unknowable restatement of the role's full skill list (today's clone-drift problem, rebuilt).
  - `replace:` exists **only** at the `overrides.<role>` layer (a named role on a named board can be
    told "exactly these toolsets"), requires the same `reason:` sibling as model overrides, and is
    refused for `skills` (skills replace is how a board silently lobotomizes a role; remove-by-name
    is sufficient).
- **Repeat application**: deltas are idempotent and order-stable; duplicate `add` entries dedupe.

### 9.4 `overrides:` vs `pin:` — pin wins (confirmed)

**Confirmation**: pinned keys ignore board base AND overrides entirely. Rationale:

1. **Authorship domains.** A role (with its pin list) is authored/maintained by whoever ships the
   role; a board.yaml by whoever runs the board. Letting a board override a pin means the board
   operator silently edits the shipped specialty — rebuildable clone drift with extra steps.
2. **The specialist case is real.** A `researcher` role whose value IS its curated memory bank
   (pinned) composed onto N boards keeps one evolving expertise; a `butler` with no pins gets N
   context sets. Both wanted; pin is the switch, and pin only has meaning if it outranks overrides.
3. **Precedence listed in the operator core already places pin last/hardest** — this section
   confirms rather than relitigates.

Falsify/revisit (D5): revisit if a case emerges where a board must diverge a pinned key for one
role — the answer there is a *new role* (role specialization, §15), which is the mechanism this RFC
prefers over per-board mutation of shipped roles.

`pin` vs `capability: all` are orthogonal: capability is about *which boards* an agent may address
(§10); pin is about *what a board may change in the role*.

## 10. Kanban-tool fencing and `boards: all`

### 10.1 Enforcement point: the shared client layer (decided)

Both agent-side surfaces route through the same layer today — the kanban docs state it outright
("Both surfaces route through the same `kanban_db` layer, so reads see a consistent view"), and the
source confirms it: model tools `tools/kanban_tools.py:314-318` call
`kbc.connect(board=board)`, whose path resolution is `hermes_cli/kanban_db.py:540-566 _board_path`
with explicit-intent override at :503-537. Fencing is therefore enforced **in the client/resolution
layer, not per-tool**:

- New check inside `_explicit_board_slug`/`_board_path` (or a wrapper `resolve_board_for_agent`):
  when the executing agent is board-pinned (EffectiveProfile.board_pin set, or dispatcher env pin —
  `explicit_board_intent_is_pinned()`, `agent/delegation_context.py:76-93` already covers workers
  and descendants) **and** the effective profile lacks `boards: all`, any resolved board ≠ pin →
  `PermissionError("board-pinned agent: refusing cross-board operation <board>; grant
  boards:all to <role> for multi-board access")` — refused **before** any connection opens.
- Dispatcher workers keep their env-pin fence unchanged (`HERMES_KANBAN_DB/BOARD/WORKSPACES_ROOT`,
  `kanban_db_dispatch.py:2845-2851`); the new check extends the same refusal to interactive and
  cron executions, which today have no pin beyond `get_current_board()`'s soft chain.
- Descendants (delegate children, spawned processes) inherit the pin exactly as they inherit
  `DELEGATED_CHILD_ENV_MARKER` + `HERMES_KANBAN_DB` today (`delegation_context.scrub_kanban_env`,
  :122-141): identity keys scrubbed, **board/location retained**. The lineage fence composes.

Tool-layer (per-tool schema denial) was rejected: the tools share one client, so a schema-level
ripple through 14 kanban_* tools adds surface for no isolation, and the CLI (`hermes kanban --board`)
needs the same refusal anyway — one choke point beats two.

### 10.2 `boards: all` declaration and validation

- Declared in the **role** config.yaml: `boards: {capability: all}`.
- **Granted only via an explicit operator command** — `hermes board grant-all <role>` — which writes
  the key (plus `granted_by`/`granted_at` audit fields). Hand-editing works (it's a yaml key) but
  `profile effective` distinguishes `capability: all (operator-granted 2026-11-01T…)` from
  `capability: all (no grant record)` and warns on the latter. It is **never** a default, and
  board.yaml **cannot** grant it (a board cannot mint its own multi-board agents).
- Validation at composition: capability requires the role to exist; `capability: all` **implies**
  `pin: ["*"]` is NOT implied — a meta agent may keep its own memory while reading many boards
  (e.g. an ops floor-walker that audits every board with one memory). Surfaced in:
  `hermes profile effective` output (always), gateway session banner (dry-run line:
  `role=butler board=software-co fencing=pinned` or `fencing=all-boards`), and the refusal message
  when hit.
- Roles used by dispatcher workers on ordinary cards should never need it; it exists for genuine
  meta roles (fleet monitors, cross-board routers).

## 11. Launch paths — where each hook lands

All file:line refs at upstream commit `c627ec84`.

| Path | Hook site | What lands |
|---|---|---|
| **Core composer** (new) | NEW `hermes_cli/board_layer.py` + `agent/effective_profile.py` | `resolve_board(slug)`, board.yaml schema/validator, `compose(role, board) -> EffectiveProfile`, slot renderer, provenance model. Pure stdlib+hermes_yaml; no I/O beyond board home + profile read. |
| **CLI/gateway entry** | `hermes_cli/profiles.py:2387 resolve_profile_env` + the `-p`/`--board` arg parsing in `hermes_cli/_parser.py` | New global flag `--board <slug>` (gateway/chat/cron subcommands). After profile resolution, compose BEFORE any consumer reads config/SOUL; stash EffectiveProfile on a ContextVar (`hermes_constants` pattern: `set_hermes_home_override`-style). No composition when no `--board`, no profile `boards.default`, and no layered `HERMES_KANBAN_BOARD`. |
| **Workers — dispatcher** | `hermes_cli/kanban_db_dispatch.py:2754-2869 _default_spawn` | **Zero new env vars.** Worker already receives `HERMES_KANBAN_DB/BOARD/WORKSPACES_ROOT` (:2845-2851) and `HERMES_PROFILE` (:2854); the child CLI sees a layered `HERMES_KANBAN_BOARD` and composes in its own process start. Dispatcher change is limited to validation at claim time (fail fast if assignee not in board `roles:` allowlist — currently surfaces only in the worker's error). |
| **Workers — child startup** | `hermes_cli` entry (post-`-p`, pre-config-load) | Trigger composer when `HERMES_KANBAN_BOARD` names a layered board: composed profile used for config/SOUL/skills/env/state. Identity gates unchanged (`kanban_worker_client.py:177` uses the pinned pair — free correctness: the fenced pair IS the composed pair). |
| **Interactive/gateway sessions** | `hermes_cli/gateway.py:3086-3088` (per-profile scope), `gateway/session_kanban.py:163` (worker env), `hermes_cli/web_server_profiles.py:278-320` (await-safe profile scope) | The gateway learns to route an inbound platform bot → `(role, board)`: bot token lookup in board env layer (board exports `TELEGRAM_BOT_TOKEN` for role `butler`); session construction composes. Session-tagging carries the board so `/resume`, `/new` keep the pin. |
| **Config load** | `hermes_cli/config` (`load_config`) | Effective config = role config + merged layer values (§9). Only composer callers pass a composed dict; today's callers untouched. |
| **SOUL** | `agent/prompt_builder.py:1512-1560 load_soul_md`, `:1720-1745 build_context_files_prompt`, `agent/system_prompt.py:554-555` | Role SOUL + fragment chain + slot rendering (strict §6.3); `home_override` threading unchanged. |
| **Skills** | `agent/skill_utils.py` index build (SKILLS_DIR override precedent: `hermes_cli/web_server_profiles.py:266-273`) | Index source list becomes `[role skills] + [board skills]` (role wins collisions §5.3). `HERMES_KANBAN_TASK/BOARD` already drive the `environments: [kanban]` relevance gate (`skill_utils.py:117-133`) — unchanged. |
| **Env** | `hermes_cli/env_loader.py` (+ `:682-685`, `:1094`) | Board env manifest source, exported names only (§7), ordered above role `.env`. |
| **Memory/state** | `agent/memory_provider.py:121-128 initialize(hermes_home)`; `hermes_state_dbfile` session-DB path resolution | Pass state root (§8) unless `pin: memory`/`sessions`. Providers need no changes (contract §8.2). |
| **Cron** | `cron/jobs.py` (job spec: new optional `board:` field), `cron/scheduler.py:2507` context build, worker env per `cron/scheduler_script.py:476-482` | Job may declare `board:`; the scheduler enters board scope for the run (pins `HERMES_KANBAN_BOARD` + composed EffectiveProfile), mirroring routed-profile scope handling. `tests/cron/test_cron_kanban_env_isolation.py` asserts cron does NOT inherit ambient kanban env today — extended with "declared board ⇒ pinned composition only". |
| **Kanban fencing** | `hermes_cli/kanban_db.py:503-566`, `agent/delegation_context.py:76-93` | §10. |
| **Trust tool** | new subcommand under `hermes profile` | `hermes profile effective` (§13). |

## 12. Zero-change guarantee (upstream safety)

1. **No layered board ⇒ identity composition.** The composer's first branch (§9.2) returns the
   role profile as loaded today. Regression test (card 1): fixture profiles, with and without
   `--board`, byte-compare effective SOUL/config/skill-list/env names.
2. **Layered board marker is a file.** Slugs without `board.yaml` are unlayered regardless of
   `HERMES_KANBAN_BOARD`. Upstream installs with zero multi-board usage never see a code path
   difference beyond one `Path.exists()` in the entry hook.
3. **Schema is additive.** `boards:` in role config and `board.yaml` are new keys; unknown keys in
   existing locations behave as before. (board.yaml is strict separately — §5.2 — but it only
   exists where the operator opted into layering.)
4. **Nothing estate-specific in core.** All names in this RFC ("butler", "researcher", estate
   examples) are examples; core knows only `role`, `board`, layer keys.
5. **No config.yaml mid-conversation mutation** (profiles-doc hard rule): composition happens at
   launch/construction; an existing session's pinned effective profile never re-reads board.yaml
   mid-conversation. Re-pinning requires a new session, same as today's profile switching.

## 13. Trust tooling: `hermes profile effective`

```
hermes profile effective --profile <role> [--board <slug>] [--json]
```

Renders the composed truth (Phase 1 requirement; card 2):

- **SOUL**: full composed text with inline fill provenance
  (`[role: ~/.hermes/profiles/r/SOUL.md]`, `[board: <board>/SOUL.md]`, unfilled slots §6.3).
- **Config**: effective config.yaml with per-line `# from: <layer>` provenance; model overrides
  shown with their `reason:`.
- **Skills**: role + board lists, shadowed entries marked, pin effects visible.
- **Env**: exported board names ONLY (values never, §7) + collision findings.
- **Memory/state**: resolved state root, provider, bank name, pin status.
- **Fencing**: `board=software-co pinned` / `boards: all (operator-granted …)` + the refusal a
  real cross-board call would get.
- **Exit code**: 0 clean; 1 warnings (extraneous slots, ungranted capability, model-override
  present); 2 composition errors (unknown keys, unfilled slots at strict sites, bad pins).

This is also the **convergence tool** for upstream (§14): one command answers "what would this
agent be".

## 14. Related upstream issues and positioning

Upstream tracker state swept 2026-11-01 (live GitHub API, dedupe verdict: **no duplicate of the
unified concept**). Demand exists but arrives fragmented — every item below is a single *field*
solution to the same underlying need:

| Ref | State | What it adds | Fragment of this RFC |
|---|---|---|---|
| PR #64625 | OPEN | board-local allowed-profiles policy vs machine ceiling (absorbed dup PR #87741) | board→role pairing (`roles:` allowlist, §5.1) |
| Issue #141889 | OPEN FR | per-board `orchestrator_profile`, board→global fallback | one slot of the precedence story (§9.1) |
| Issue #118116 + PR #136925 | OPEN | per-board dispatch caps via board.json | another board.json knob fragment |
| PR #89217 | OPEN | `doctor` profile-composition diagnostics | observability, no board axis (§13 builds the general form) |
| Issue #110080 | OPEN | forbid direct SQLite board-state writes | adjacent hardening of the fence boundary (§10, non-goal note §2) |
| Label `area/profiles` ("Multi-profile isolation, HERMES_HOME scoping") | — | maintainers already think in this frame | landing zone for the filing |

**Positioning**: the differentiator of this RFC is **unification**. Upstream keeps shipping
per-field exceptions — caps here, an orchestrator slot there, allowed-profiles over there —
because the composition model doesn't exist. One precedence/composition engine (§9) subsumes the
field set, and `hermes profile effective` (§13) is the convergence tool that makes every past and
future per-board knob inspectable in one place. The upstream draft (companion file) presents the
fragment set above as the motivation, not the competition.

## 15. Roadmap (post-Phase-1)

1. **Role specialization over clone-reduction.** With boards carrying context, role *granularity*
   can finally go the other way: `coder` → `python-coder`/`ts-coder`, tuned `researcher-a/b`,
   per-voice scribes — because a new role costs a SOUL + toolset, not a full context clone. Roles
   compose with every board automatically.
2. **Migration helper: `hermes board adopt-profile <clone> → <role> × <board>`.** Dry-run diff:
   what state moves (memory/sessions → board state root), what merges (skills union vs shadowing),
   what's discarded (clone's divergent config — the drift that motivated all this). Conflict
   policy: board wins for state presence, role wins for identity, everything else reported
   for human decision. Operator-driven, one clone at a time.
3. **SOUL prose deletion.** Once fencing is enforced in code (§10), the per-board "Board
   Discipline" prose blocks appended to N cloned SOULs (53 on the reference estate) delete —
   the fragment + mechanism replace prose-enforced convention. (Generic upstream story: enforced
   isolation replaces SOUL-paragraph safety briefings; estate numbers stay out of the filing.)
4. **Board dashboards**: `boards show <slug>` lists bound roles, state sizes, last-dispatched pair.
5. **Board-scoped secrets rotation**: rotate-with-board (bot tokens) via the manifest's file
   source without touching profile `.env`s.
6. **Cross-board federation (explicit non-goal today)**: read-only board references for meta
   roles — revisit only after #110080-class hardening lands upstream.

## 16. Implement-card decomposition check

Planned cards reviewed against this RFC (confirmation + adjustments; orchestrator to re-shape):

- **1-LOADER** (exists: t_c5ef283e) — CONFIRM, with scope notes: board-home discovery MUST reuse
  `hermes_cli/kanban_db.board_dir`/`_normalize_board_slug` (no second slug grammar); strict
  board.yaml validation per §5.2; zero-change gate = absence of board.yaml (not absence of env
  var); composer API returns EffectiveProfile with provenance per field (cards 2-4 consume the
  same object, never re-merge).
- **2-EFFECTIVE** — CONFIRM + emphasize: per-line source layering is the deliverable (§13), env
  names-only enforced by the renderer's structure (it reads the manifest, not the values file),
  exit-code contract 0/1/2, and the "what refusal would a cross-board call get" line. Can be built
  against the 1-LOADER composer API with stubbed state resolution.
- **3-STATE** — CONFIRM + add: per-(role,board) state root layout §8; `initialize(hermes_home=…)`
  re-binding is the ONLY provider touch (verify per installed provider contract, esp. hindsight
  bank default `board-<slug>-<role>`); session-DB relocation via `hermes_state_dbfile` resolution;
  profile-marker scan must skip board state roots (`hermes_constants.py:399` + `named_profile_is_live`
  consumers).
- **4-WIRING** — CONFIRM + split internally by launch path with different sized diffs:
  dispatcher ≈ validation-only (claim-time roles-allowlist check; child composes itself);
  gateway = largest (bot-token→board routing, session pin tagging, banner surfacing);
  cron = `board:` job field + scope entry; fencing = `kanban_db.py`/`delegation_context.py` choke
  point + `boards:all` grant command. Note adjacency: upstream issue #110080 (direct SQLite
  hardening) is complementary, not in-scope.
- **5-TEST** — CONFIRM + enumerate the guarantee tests that must exist: zero-board byte-identity;
  layered-board composition snapshots; pin-vs-override matrix (all 8 pin keys × base/override);
  strict-vs-dry-run slot behavior; list-key delta math incl. `replace` at overrides; fencing
  refusals per launch path (worker already fenced — regression; interactive/cron new); env
  names-only (grep the renderer's tests for value strings); cron declared-board pin
  (extend `tests/cron/test_cron_kanban_env_isolation.py`).

Sequencing stands: 1 → 2 ∥ 3 → 4 → 5 (4 needs 1+3; 5 accumulates).

## 17. Open questions

1. **Hindsight bank identifiers**: confirm the provider accepts `board-<slug>-<role>`-shaped bank
   names (hyphens, length) or needs a separator convention (D6 risk). Verify in card 3 tests, not
   by assumption. *(Open until card 3.)*
2. **Gateway bot→board routing surface**: which config declares "this Telegram bot id → board X"?
   Candidates: board env manifest (self-describing; chosen provisionally, §11) vs gateway platform
   config. Decide in card 4 spike; the answer must not add a per-board profile.
3. **`overrides.<role>` and the `roles:` allowlist**: should listing a role ONLY in `overrides`
   imply binding, or must every overridable role also appear in `roles:`? Provisional: `roles:` is
   the pairing contract; overrides for unlisted roles = schema warning (not error) because base-only
   boards may omit `roles:` entirely (open board). *(Decide in card 1 review.)*
4. **Default board layering**: `default` board keeps legacy `<root>/kanban.db` and its board dir
   holds metadata only (kanban_db.py:485-490). Can the default board be layered? Provisional: yes —
   `board_dir("default")` exists — but `profile effective --board default` must be tested
   explicitly in card 1. *(Low risk.)*
5. **Distribution profiles × boards**: a role installed from a git distribution
   (`hermes profile install`) with its own `SOUL.md` ownership rules (prompt_builder.py:1544-1555)
   — do fragment appends coexist with `distribution_owned` SOUL? Provisional yes (append is
   composition, not file mutation), but the blocking-scan interaction needs a card-1 test fixture.
6. **Timeline pin stability**: kanban board dirs move on archive (`_archived/` + tombstone) — a
   pinned-but-archived board mid-session should degrade to refuse-new-calls rather than crash the
   live session. *Card 4 detail.*
7. **Env exporting provider credentials** (§7 warning heuristic): exact name list and whether the
   warning should be an error. *Card 2 review.*

## 18. ADR-style decision log

**D1 — Board home = existing kanban board dir** (operator-approved; reflected not decided).
Context: any new location invents a second archive/lifecycle/permission story. Decision: layer files
live beside `board.json`/`kanban.db` (§4). Consequences: archive covers context; dir permissions
inherit; no new env-config location. Alternatives rejected: `<profile>/boards/` (re-fragments
per-profile state, defeats butler-serves-all-boards), `<root>/board-layers/<slug>/` (duplicate
lifecycle). Revisit when: kanban ever allows out-of-root board dirs (env-pinned DBs today support
it; layered files would follow the dir, fine) — no known pressure.

**D2 — Composition is per-subsystem resolution, not a merged physical home dir.**
Context: HERMES_HOME is a real directory whose identity markers make it a profile
(hermes_constants.py:399); config/`state.db`/skills/env all hang off it. A merged symlink-farm
"home" would be adopted by `profile list`, confuses distribution scan, secret_scope, and doctor.
Decision: `EffectiveProfile` carries explicit resolved paths per subsystem (§11); nothing tries to
be a fake home. Alternatives rejected: overlay symlink dir (identity leakage), copy-on-write
profile snapshot (state forks, two-writer hazard, drift). Revisit when: hermes gains a native
multi-home indirection that carries provenance (PR #89217's diagnostics may push that way).

**D3 — Env layer = manifest ref + separate values file; exported names only; board wins its names.**
Context: §7. Alternatives rejected: bare `.env` in board home (redaction-based names-only rendering;
no export scoping; non-secrets polluted). Consequences: tiny schema to validate; renderer is
structurally value-blind. Revisit when: a provider requires env names computed at runtime.

**D4 — Slots: strict at launch, tolerant in dry-run; single `{{board.*}}` namespace; no recursive
rendering.** Context: §6.3. Alternatives rejected: silent-empty (live-prompt corruption), global
template language (SOULs are prose; scope creep). Revisit when: a second slot namespace demands it
(`{{role.*}}`?) — none foreseen.

**D5 — `pin:` outranks board `overrides:`; pin closed-list = memory, sessions, skills, soul, env,
model, toolsets (`*` allowed).** Context: §9.4 (authorship domains; specialist memory). Alternatives
rejected: overrides can defeat pin (board edits shipped specialty — clone drift rebuilt), pin as
advisory (meaningless). Falsified when: a concrete case appears where one board must diverge one
pinned key of one role AND a new specialized role is worse — then revisit precedence, not the list.

**D6 — State root per (role, board): `state/<role>/`; providers re-bind via `hermes_home`; hindsight
bank default `board-<slug>-<role>`.** Context: §8. Two roles, one board, one bank would cross-write
role memories — bank names the pair. Alternatives rejected: per-board only bank (cross-role
contamination), per-role-profile state under role home with bank-per-board (context leaves the
board archive; defeats the problem statement). Revisit when: a provider can't express the id (OQ1).

**D7 — List keys (skills/toolsets) are delta-union; `replace` exists only per-role in
`overrides.`, never for skills, and needs `reason:`.** Context: §9.3 (survey: board differences
are additive; replace-default rebuilds clone drift as board.yaml restatements). Alternatives
rejected: replace-by-default, per-item priority grammars (incomprehensible). Revisit when: a real
board demonstrates toolset-union is insufficient for its role — expect specialize-the-role instead.

**D8 — Fencing at the shared client layer (`kanban_db._board_path`/`connect` +
`delegation_context`), not per-tool schemas.** Context: §10 (one client, two surfaces; CLI needs
the refusal too). Alternatives rejected: tool-schema removal (14 tools, misses CLI, false sense —
paths still resolvable), gateway-only check (cron/CLI bypass). Consequences: single choke point to
test; refusal message uniform. Note: cooperative scoping, not confinement (§2 non-goals) — matches
the existing worker-fence honesty.

**D9 — `boards: all` is a role-side capability, granted by an operator command, auditable, surfaced
everywhere, never granted by a board.** Context: §10.2. Alternatives rejected: CLI flag at launch
(cbypass-by-habit), board-side grant (board mints multi-board agents), profile pin interaction
(imply `*` pin — wrong: meta roles keep their memory; §10.2). Revisit when: a meta-role fleet
outgrows single-process memory volume.

**D10 — Layered-board detection = presence of `board.yaml` (file-as-marker), not an env var or
board.json flag.** Context: §12 zero-change guarantee. Alternatives rejected: board.json flag
(two sources of truth for one state; board.json hand-edits flip behavior invisibly), env var
(spawn chains lose it). Consequences: adding a file opts a board in, visibly; archiving carries it.

**D11 — Dispatcher needs (almost) no change**: workers already receive the pinned pair
(`HERMES_KANBAN_BOARD` + `HERMES_PROFILE`); child-side composition at startup is the mechanism.
Context: §11 dispatcher row (kanban_db_dispatch.py:2845-2854). Alternative rejected: dispatcher
pre-composes (extends dispatcher surface, breaks the "child composes itself" symmetry with
`--board` interactive launches). Consequences: claim-time `roles:` validation is the only
dispatcher-side add.

## 19. Docs-vs-source divergences (report per card constraints)

1. **Kanban doc page** (`/docs/user-guide/features/kanban`) opens with "every task is a row in
   `~/.hermes/kanban.db`" — stale vs source: per-board DBs live at
   `<kanban home>/kanban/boards/<slug>/kanban.db` (kanban_db.py:563-566), with `default` alone
   at the legacy path. Cosmetic, but this RFC depends on the per-board dir, so the filing draft
   states the current source layout.
2. **Profiles doc** frames profiles as strictly independent ("Never point two agent processes at
   the same profile… agents that need shared memory should use an external memory provider") —
   board layers must NOT read as softening this: composition keeps one writer per state root (§8.1);
   the doc's rule remains literally true of every physical home.
3. **`hermes-agent` skill reference** (background-systems.md) already documents
   "board is the hard boundary (workers get `HERMES_KANBAN_BOARD` pinned in env); tenant is a soft
   namespace" — this RFC's §10 generalizes an already-documented invariant, rather than inventing
   one. Good convergence signal for the upstream filing.
4. Doc-site llms.txt confirms the reference pages used here: `/user-guide/profiles`,
   `/user-guide/features/kanban`, `/user-guide/features/memory`, `/user-guide/features/skills`,
   `/user-guide/features/cron`, `/developer-guide/multiplexing-gateway`.

---

*End of RFC. Companion: `docs/BOARD-LAYERS-UPSTREAM-ISSUE-DRAFT.md` (local only — NOT filed; any
filing goes through the estate's gate chain and the operator final gate).*
