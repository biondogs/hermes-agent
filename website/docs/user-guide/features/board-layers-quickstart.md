---
sidebar_position: 14
title: "Board Layers Quick-Start"
description: "Set up one role profile serving two kanban boards with isolated memory, skills, SOUL context, and env"
---

# Quick-Start: One Role, Two Boards

This walkthrough replaces the common "clone the profile per board" setup with a single
role. We'll take one assistant role and run it on two boards — `proj-a` and `proj-b` —
each with its own memory, its own board skills and SOUL context, and (for the messaging
case) its own bot token.

**What you'll end up with**

```
role "assistant"            # defined once: SOUL, model, toolsets
├── × board proj-a          # proj-a's memory, sessions, skills, env
└── × board proj-b          # proj-b's memory, sessions, skills, env  (fully isolated)
```

## 1. Make sure the role exists

```bash
hermes profile create assistant   # or use an existing profile as your role
```

Give its SOUL slots where board context should land:

```markdown
# SOUL.md (excerpt)

You keep project work moving: triage, unblock, report.

## Board facts
{{board.hosts}}

## Board law
{{board.rules}}
```

## 2. Add the layer files to each board

Board homes live under `<kanban home>/kanban/boards/<slug>/` (run
`hermes kanban boards list` if you need the paths). For `proj-a`:

```bash
cd ~/.hermes/kanban/boards/proj-a
```

```yaml
# board.yaml
version: 1
roles: [assistant]
skills:
  add: [./skills/proj-a-runbook]
soul:
  slots:
    hosts: |
      - Staging: https://staging.example.com (deploys auto)
    rules: |
      - Deploy only via the board pipeline; never by hand.
env:
  manifest: ./env/manifest.yaml
```

```markdown
<!-- SOUL.md — optional board fragment, appended after the role SOUL -->
You are working on **proj-a**: the widget redesign. Ship small, verify with receipts.
```

```yaml
# env/manifest.yaml
version: 1
vars:
  TELEGRAM_BOT_TOKEN               # value goes in ./env/secrets.env (chmod 600)
  DEPLOY_TARGET: {value: staging}
export: [TELEGRAM_BOT_TOKEN, DEPLOY_TARGET]
```

```bash
mkdir -p skills/proj-a-runbook    # drop a SKILL.md in there
printf 'TELEGRAM_BOT_TOKEN=123:abc-proj-a-token\n' > env/secrets.env
chmod 600 env/secrets.env
```

Repeat for `proj-b` with its own slots, skill, and token. **Do not copy anything from
`proj-a`** — that's the point.

## 3. Inspect before you launch

```bash
hermes profile effective --profile assistant --board proj-a
```

Check the four things that matter:

- **SOUL** — role text, then your `{{board.hosts}}` / `{{board.rules}}` filled from
  *proj-a's* `board.yaml`, then proj-a's fragment. An unfilled slot shows inline as
  `[UNFILLED SLOT {{board.x}} — define soul.slots.x in proj-a/board.yaml]`.
- **Skills** — role skills + `proj-a-runbook`, shadowed entries marked.
- **Env** — `TELEGRAM_BOT_TOKEN`, `DEPLOY_TARGET` listed **by name** (values never print).
- **Fencing** — `board=proj-a pinned`, plus the refusal text a cross-board call would get.

Run it for `proj-b` too, and for `--board none` to see the role exactly as it behaves
today. Exit codes: `0` clean, `1` warnings, `2` composition errors — CI-checkable.

## 4. Launch each way

```bash
# interactive
hermes --board proj-a -p assistant chat

# dispatcher workers — nothing to do: a worker spawned for a task on a
# layered board composes that board automatically from its env pin

# cron — declare the board on the job
#   board: proj-b
```

## 5. Verify the isolation

From a session on `proj-a`, try a board call against `proj-b`:

```
hermes kanban list --board proj-b
→ Error: board-pinned agent (board=proj-a): refusing cross-board operation
  board=proj-b; grant boards:all to this profile for multi-board access
```

And check state really is per pair — memory written on `proj-a` lands under
`proj-a/state/assistant/memories/`, sessions under `proj-a/state/assistant/`, and nothing
ever appears under `proj-b`.

If you genuinely need one cross-board role (a monitor that reads every board), an
operator grants it explicitly and audibly:

```bash
hermes board grant-all assistant   # writes an audited capability record
hermes profile effective --profile assistant --board proj-a   # shows "boards: all (operator-granted …)"
```

## Next

- Full concepts and reference: [Board Layers](./board-layers.md)
- Converting existing per-board clones: [Migration notes](./board-layers-migration.md)
