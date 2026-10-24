## Summary

In a dispatcher-fenced caller (a dispatched worker with `HERMES_KANBAN_TASK` + `HERMES_KANBAN_DB` pinned, or a delegate lineage), the scoped `kanban_*` tools silently **redirect an explicit `board=` argument to the pinned session board and return success** instead of refusing. `kanban_create(board="X", ...)` from such a session returns `{"ok": true, "task_id": ...}` — and the card lands on the *session's* board, not `X`. No error, no warning, and no board echo in the response.

The pin-first resolution for fenced callers is the intentional "workers cannot see other boards" isolation (see `hermes_cli/kanban_db.py::_board_path` / `_explicit_board_intent_pinned()`, and the #30678 resolution, which made explicit intent win only for *unfenced* callers). This issue is **not** about changing that isolation — it's that crossing the fence silently surfaces to the caller as an `ok:true` write against the wrong board.

## Repro

Worker env as injected by the dispatcher:

```bash
HERMES_KANBAN_TASK=<task-id>
HERMES_KANBAN_BOARD=<session-board>
HERMES_KANBAN_DB=$HERMES_HOME/kanban.db
```

From that process:

```python
from tools import kanban_tools as kt
kt._handle_create({"board": "board-b", "title": "t", "assignee": "x"})
# -> {"ok": true, "task_id": "<task-id>", ...}   # card created on the session's pinned board, not board-b
```

Read-side twin: `kanban_show(task_id=<card on board-b>, board="board-b")` returns `task ... not found` even though the card exists — same silent redirect, confusing failure mode (cf. the read-side reports in #30678 and #108401).

## Why silent success is the hazard

- The caller's own verification (checking the *named* board) shows nothing, while the card is live on the wrong board, visible to a different set of workers.
- A confused or prompt-injected worker doing this gets no signal at all.
- The correct escape hatch (an unfenced process / operator shell) is never hinted at.

## Suggested fix

Loud, structured refusal at the tool layer — the one place where `board=` is unambiguously caller intent. In `tools/kanban_tools.py::_board` (which at main performs no board-intent check at all):

```python
db_pin = (os.environ.get("HERMES_KANBAN_DB", "") or "").strip()
if db_pin and explicit_board_intent_is_pinned():
    requested = (kb.kanban_home() / "kanban.db" if wanted == kb.DEFAULT_BOARD
                 else kb.board_dir(wanted) / "kanban.db")
    if requested.resolve() != Path(db_pin).expanduser().resolve():
        raise _Reject(f"the dispatcher fence pins this session to its own kanban "
                      f"board, so the explicit board={wanted!r} is REFUSED ...")
```

Notes:

- Keep the core `_board_path` silent pin-first **unchanged** — machine flows that enumerate board slugs (`pin_first_board_resolution`: gateway notifier / watcher / dispatcher ticks) depend on it; the slug there is an iteration variable, not intent.
- Gate on the actual `HERMES_KANBAN_DB` pin so a `HERMES_KANBAN_TASK`-only context (no DB pin) keeps honoring explicit boards — without the pin there is no redirect and no fence to enforce there.
- Naming the session's *own* board must keep working (compare resolved paths, not slugs).
- Regression guard: `tests/tools/test_kanban_tools.py::test_create_explicit_scratch_ignores_ambient_board_project` encodes the no-pin explicit-board-wins behavior; a fix must keep it green.

Related: #30678 (closed; intent-wins for unfenced callers), #108401 (CLI `--board` no-op under `HERMES_KANBAN_DB`), #133353 (marker fence scope), #127679 (marker carried into CLI contexts).
