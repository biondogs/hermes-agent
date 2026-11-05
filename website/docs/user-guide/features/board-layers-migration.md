---
sidebar_position: 15
title: "Migrating Cloned Profiles to Board Layers"
description: "Turn N per-board profile clones into one role plus board layers, without losing memory or sessions"
---

# Migrating Cloned Profiles to Board Layers

If you already run per-board clones — `assistant-proj-a`, `assistant-proj-b`, `research-proj-a`,
… — this page shows how to collapse them into **one role + N board layers** without losing
the memories and session history each clone accumulated.

Layering a board never moves anyone's state automatically. There is no live migration: you
move each clone deliberately, one at a time. A one-command migration helper
(`hermes board adopt-profile`) is on the roadmap; until it lands, this is the manual
recipe — and it's also exactly what the helper will do under the hood, with a dry-run diff.

## What a clone contains, and where each piece goes

Take `assistant-proj-a`, the per-board clone of the role `assistant`:

| In the clone | Goes to | How |
|---|---|---|
| `SOUL.md` board-specific paragraphs (host facts, board rules, board discipline prose) | `kanban/boards/proj-a/SOUL.md` fragment and `board.yaml soul.slots.*` | cut/paste; replace the paragraphs in the role SOUL with `{{board.*}}` slots |
| Per-board skills directory entries | `kanban/boards/proj-a/skills/` + `board.yaml skills.add` | move the board-only skills; list shared ones in neither place (they stay on the role) |
| Board bot token and other per-board env in `.env` | `kanban/boards/proj-a/env/manifest.yaml` (+ `secrets.env`, 0600) | names into `export:`, values into `secrets.env` |
| Memory: `MEMORY.md`, `USER.md`, provider storage / bank | `kanban/boards/proj-a/state/assistant/memories/` | move the files; keep the derived-bank default so the name matches the pair |
| Session history (`state.db`, `sessions/`) | `kanban/boards/proj-a/state/assistant/` | move the files |
| Model / provider choice, toolsets, personality prose | **stay on the role** | nothing to do — this is what "identity" means |
| Everything else that diverged between clones | nowhere | this is drift; review and discard deliberately |

Two rules keep you safe: **the board wins for state presence** (memory/sessions move into
the board home), **the role wins for identity** (model, toolsets, base SOUL stay defined
once). Anything else is a human decision — write it down as you go.

## Recipe, one clone at a time

1. **Freeze the clone.** Stop its gateway/worker activity. One writer per home still
   applies while you move its files.
2. **Layer the board** if you haven't: `board.yaml` + fragment + env manifest, per the
   [quick-start](./board-layers-quickstart.md). List the role in `roles:`.
3. **Move the state:**
   ```bash
   B=~/.hermes/kanban/boards/proj-a/state/assistant
   mkdir -p "$B"
   mv ~/.hermes/profiles/assistant-proj-a/MEMORY.md      "$B/memories/MEMORY.md"
   mv ~/.hermes/profiles/assistant-proj-a/USER.md        "$B/memories/USER.md"
   # provider storage (e.g. a hindsight bank dir) moves under $B/memories/ too;
   # with the default derived bank you may not need a memory.* key at all
   mv ~/.hermes/profiles/assistant-proj-a/state.db       "$B/state.db"
   mv ~/.hermes/profiles/assistant-proj-a/sessions       "$B/sessions"
   ```
   If the clone used an explicit memory-bank name you can't reproduce with the derived
   default, pin it explicitly: `memory: {bank: <old-name>}` in `board.yaml`.
4. **Extract the deltas.** Board prose → fragment/slots; board skills → `skills/`; bot
   token → env manifest. Delete the corresponding paragraphs from the role SOUL and replace
   them with slots.
5. **Verify by dry-run:**
   ```bash
   hermes profile effective --profile assistant --board proj-a
   ```
   Expect: the old clone's behavior, composed — same SOUL content (slots filled), same
   skills, same env names, `board=proj-a pinned`, exit code `0` or `1` with warnings you
   have read. Compare against `--board none` to see what the role alone still carries.
6. **Re-point launch paths** at `role × board`: dispatch cards to `assistant` (not
   `assistant-proj-a`), launch interactive/gateway sessions with `-p assistant --board proj-a`,
   declare `board: proj-a` on cron jobs.
7. **Watch one week, then delete the clone.** `hermes profile delete assistant-proj-a`. Until
   then the clone is your rollback: nothing was mutated in place except the files you moved
   (which you can move back).

## What changes in day-2 operation

- **One identity fix fixes every board.** SOUL/model/toolset edits happen on the role once.
- **Board prose edits happen on the board** — by whoever runs the board, without touching
  the shipped role. If a board truly needs a *different* behavior on a pinned key, that is
  the signal to create a new specialized role, not to widen an override.
- **Drift becomes visible.** `profile effective` diffs are how you audit "what is this
  agent, really" — per pair, in one command.
- **Archiving is unchanged but richer:** archiving a board now archives its agents' memory
  and sessions with it.

## Roadmap: `hermes board adopt-profile`

The planned helper automates steps 3–4 with a mandatory dry-run:

```
hermes board adopt-profile assistant-proj-a --role assistant --board proj-a --dry-run
```

Report shape: what state moves (memory/sessions → board state root), what merges (skills
union, shadow entries), what is discarded (the clone's divergent config — the drift that
motivated all this), and what needs a human decision. Conflict policy matches the two
rules above: board wins state presence, role wins identity, everything else is reported.
Operator-driven, one clone at a time — the same recipe, without the `mv` commands.
