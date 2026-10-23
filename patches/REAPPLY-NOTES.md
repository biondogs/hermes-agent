# kanban-stream FIX2 (stream cosmetics) — re-apply notes

**What:** two defects in the kanban-stream plugin's DM stream, fixed on card
t_df30ec0c (default board, operator GO 2026-10-23 DM "send the fix though"):

- **D1 — false-positive ❌:** `_is_error_result()` substring-scanned any short
  (<500ch) string result for "error"/"failed"/"traceback", flagging successes that
  merely mention errors (browser_console "no JavaScript errors", log tails). Fix:
  structured dict signals ONLY (`result["error"]` truthy, `success is False`,
  `status in error/failed/failure`); non-dict results are never errors.
- **D2 — retry spam:** consecutive identical failure lines were pushed one per
  attempt ("❌ terminal failed" ×4 for one flaky command). Fix:
  `StreamState.push_error` replaces a repeat of the immediately-preceding line with
  `"<line> ×N"` instead of appending (counter `_error_repeat` added to `__init__`).

**Patch time (for the Oct-25 soak collector / t_4ddfc8b8 annotation):** applied
live **2026-10-23 ~16:29–16:36 UTC** to all 58 copies (root install + 57 worker
profile installs), each verified by sha256 before overwrite and after copy.
Behavior-neutral for running sessions (workers load the module at spawn); soak
clocks on t_4ddfc8b8 unaffected.

## Identifiers

| Item | Value |
|---|---|
| Patch file | `patches/kanban-stream-fix2.patch` (git format-patch, 1 commit) |
| SHA256 | `767bb0b2b5745bd61859a87d54d6ea7a1b5f6288cc529c1e277777f0db143ee9` |
| Patch base | `d6c3e80` (upstream v1.0.2 tag state at clone) |
| Live apply commit | `bc9b220` (LOCAL HOTFIX commit in the install clone) |
| Install location | `~/.hermes/plugins/kanban-stream/` (root) **plus** `~/.hermes/profiles/<name>/plugins/kanban-stream/` ×57 |
| Upstream | `github.com/mbgulden/hermes-kanban-stream` — **upstream-reportable but NOT posted** (local only, per card constraint) |

## One-command re-apply (if the plugin is reinstalled/updated from upstream)

Re-apply whenever any install copy lacks the fix — i.e.
`grep -q _error_repeat ~/.hermes/plugins/kanban-stream/__init__.py` returns
nothing. The 57 profile copies are plain directory installs, so propagate the
root fix to all of them (hash-guarded; refuses unknown states):

```bash
cd ~/.hermes/plugins/kanban-stream && \
  git apply --3way /local/projects/software-co/patches/kanban-stream-fix2.patch && \
  git add __init__.py tests/smoke_test.py && \
  git commit -m "LOCAL HOTFIX re-apply: kanban-stream FIX2 (see /local/projects/software-co/patches/REAPPLY-NOTES.md)" && \
  for d in ~/.hermes/profiles/*/plugins/kanban-stream; do
    cp -p __init__.py "$d/__init__.py" && cp -p tests/smoke_test.py "$d/tests/smoke_test.py"
  done
```

## Verification checklist (after re-apply)

1. `python3 ~/.hermes/plugins/kanban-stream/tests/smoke_test.py` → **SMOKE OK, 26
   checks, 0 failures** (includes: string-result-mentioning-"error" is NOT an
   error; `{"error": "x"}` IS; ×2/×3 collapse; different-failure reset;
   interleaved-tool-line reset).
2. All install copies identical:
   `sha256sum ~/.hermes/plugins/kanban-stream/__init__.py ~/.hermes/profiles/*/plugins/kanban-stream/__init__.py | awk '{print $1}' | sort -u | wc -l` → `1`.

## Rollback

```bash
cd ~/.hermes/plugins/kanban-stream && git revert --no-edit bc9b220
# then re-run the profile propagation loop above to resync the 57 copies
```

## Gateway bounce receipt

Per card acceptance, a graceful drain-restart of `hermes-gateway` was launched
deferred+dettached from the t_df30ec0c worker shell (`setsid`, waits for the card
to leave `running`), via the operator's proven `hermes gateway restart` (SIGUSR1
drain → systemd relaunch). Launcher: `patches/gateway-bounce-fix2.sh`; runtime
receipt log: `patches/gateway-bounce-fix2-2026-10-23.log` (written by the
detached process after card completion).

---

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

---

# one-shot `chat -q` source-label hotfix — re-apply notes

**What:** classic-CLI one-shot (`hermes chat -q`) failed host-wide with
`agent_init_failed: invalid_params` when the shell inherited
`HERMES_SESSION_SOURCE` from an automation session (kanban/cron/a2a): the label is
not a creatable surface and the canonical `session.create` contract refuses it with a
bare 4001 (no field/detail, nothing at INFO in the gateway log). Fix = client-side
`GatewaySessionStore.gateway_source()` (`hermes_cli/gateway_session_store.py`)
demoting an inherited non-surface label to the thin client's own default
(`oneshot`/`cli`); an explicit `--source` the gateway cannot serve raises the thin
client's copy instead. Found on card t_c58c5eed (software-co board, 2026-10-23);
root-caused during PLUGIN-PILOT t_4ddfc8b8.

## Identifiers

| Item | Value |
|---|---|
| Patch file | `patches/chat-oneshot-source-local.patch` (git format-patch, 1 commit) |
| SHA256 | `f39ca5e918c5eafcdb8e8238900757ae44f5545fea1dd15e2edf8ddb056a9eb7` |
| Patch base | `fe5e8bd91a` (live HEAD with the kanban_archive hotfix) |
| Live apply commit | `c69ae0d911` |
| Rollback anchor | `fe5e8bd91a` |

## One-command re-apply (after every auto-updater run)

Re-apply whenever
`grep -q gateway_source ~/.hermes/hermes-agent/hermes_cli/gateway_session_store.py`
returns nothing:

```bash
cd ~/.hermes/hermes-agent && \
  git apply --3way /local/projects/software-co/patches/chat-oneshot-source-local.patch && \
  git add hermes_cli/gateway_session_store.py tests/hermes_cli/test_gateway_session_store.py && \
  git commit -m "LOCAL HOTFIX: one-shot chat -q source-label demotion (re-applied; see /local/projects/software-co/patches/REAPPLY-NOTES.md)"
```

**No gateway restart needed** (client-side only: every new CLI process loads the
module fresh).

## Verification checklist (after re-apply)

1. `env -i PATH=/usr/bin:/bin HOME=$HOME ~/.hermes/hermes-agent/venv/bin/python -m
   pytest ~/.hermes/hermes-agent/tests/hermes_cli/test_gateway_session_store.py -q -k inherited`
   → 2 passed.
2. End-to-end (the repro): from a shell WITH `HERMES_SESSION_SOURCE=kanban` exported:
   `hermes -p plugin-ab chat -q "Reply with exactly the word OK and nothing else."` →
   prints OK, exit 0; the new row in that profile's state.db has `source=oneshot`.

## Retirement

An upstream fix for the classic-CLI create path (thin-client parity for `source`)
makes this moot — the next updater pull ships it; keep the history here.

## Rollback (live install)

```bash
cd ~/.hermes/hermes-agent && git revert --no-edit c69ae0d911
```
