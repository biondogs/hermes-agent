# kanban_archive local hotfix — re-apply notes

**What:** model-callable `kanban_archive` tool (task-scoped kanban tool), hot-applied
to the live install at `~/.hermes/hermes-agent` so butlers/profiles get it while
upstream decides. Upstream anchor: https://github.com/NousResearch/hermes-agent/issues/143206
Branch deliverable (for the PR): `biondogs/hermes-agent` `feat/kanban-archive-tool`
@ `c6e085330101148d959a576c009afd69712d71c9` (base `a01edde680`).

**Apply dates:** 2026-10-22 (card t_47a58cbe, software-co board).

## Identifiers

| Item | Value |
|---|---|
| Patch file | `patches/kanban-archive-local.patch` (git format-patch, 1 commit) |
| SHA256 | in `patches/SHA256SUMS` — verify before applying |
| Patch base | `a01edde680a73fdcabc2aa20b94d0581338e499b` (upstream main at branch point) |
| Live pre-patch HEAD (rollback anchor) | `4d04303818b61bf3aa09278af48356315515965b` |
| Live apply commit | `fe5e8bd91a` (LOCAL HOTFIX commit on live working tree) |

## One-command re-apply (after every auto-updater run)

The updater pulls upstream and moves HEAD; the hotfix commit is local-only and
**will be lost or conflict on the next update**. Re-apply whenever
`grep -q kanban_archive ~/.hermes/hermes-agent/tools/kanban_tools.py` returns
nothing:

```bash
cd ~/.hermes/hermes-agent && \
  (sha256sum -c <(grep kanban-archive-local /local/projects/software-co/patches/SHA256SUMS) && \
   git apply --3way /local/projects/software-co/patches/kanban-archive-local.patch && \
   git add tools/kanban_tools.py tools/kanban_tools_schemas.py toolsets.py tests/tools/test_kanban_archive_tool.py && \
   git commit -m "LOCAL HOTFIX: kanban_archive stopgap until upstream #143206 lands (re-applied; see /local/projects/software-co/patches/REAPPLY-NOTES.md)")
```

`--3way` handles drift in the three touched files; a hard conflict means upstream
restructured the kanban tool surface — port the handler by hand from the patch and
prefer re-reading issue #143206 for an upstream landing first.

## Verification checklist (after re-apply)

1. `grep -c kanban_archive ~/.hermes/hermes-agent/tools/kanban_tools.py` ≥ 3
2. Import: run the smoke
   `python /local/projects/software-co/patches/smoke_branch.py ~/.hermes/hermes-agent`
   (throwaway HERMES_HOME; asserts create+archive roundtrip + schema registration;
   run with `~/.hermes/hermes-agent/venv/bin/python` or any hermes env python;
   unset `HERMES_KANBAN_DB`/`HERMES_KANBAN_BOARD`/`HERMES_DELEGATED_CHILD_CONTEXT` first).
3. CLI regression: `python /local/projects/software-co/patches/probe_cli.py` — create/archive/re-archive through the
   real CLI on a throwaway home.
4. **Gateway restart required** for running sessions to pick the tool up (tool schemas
   assemble at session start; the gateway process holds old code in memory). Operator
   batches restarts — do NOT restart the gateway as part of re-apply.

## Kanban comment convention

Stamp `re-apply after update` as a comment on the card that performed a live apply
whenever an auto-update is observed to have dropped the patch (checker: step-1 grep).
Any butler seeing that comment on an open card re-runs the one-liner above.

## Retirement

- Upstream #143206 **accepted/merged** → stop carrying the patch; next updater pull
  ships it natively; delete this file's live-apply duty (keep history).
- Upstream **closed/rejected** → decision point for the operator: keep carrying the
  local patch vs. remove (revert live commit `fe5e8bd91a`, delete tool usage from any
  skills/playbooks).

## Rollback (live install)

```bash
cd ~/.hermes/hermes-agent && git revert --no-edit fe5e8bd91a
```

(revert, not reset --hard: keeps updater state; the hotfix is a single local commit on
top of whatever upstream HEAD the updater left.)
