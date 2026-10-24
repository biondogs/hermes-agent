## Why

`hermes chat -q` (and any finite `-q`/`-Q` run) launched from an automation-owned terminal — a kanban worker, a cron job, an a2a child — dies at agent init:

```
couldn't start the model connection: invalid_params
```

`HERMES_SESSION_SOURCE` is bridged into every child process of an automation session, and the classic client's `GatewaySessionStore` sent that inherited label verbatim as `session.create`'s `source`. The canonical create contract (`tui_gateway/contracts/canonical_sessions.py`, a closed Literal over `SURFACES`) refuses non-surface labels with a bare `invalid_params` — no field name, no detail, nothing logged at INFO — so the failure is invisible in logs. The thin client (`gateway_chat`) never inherited the label, which is why only the classic CLI one-shot path broke instead of both.

Reported live in #143653 (same failure shape as the closed #139035). Fixes #143653.

## What changes

2 files, +103/−4, of which 68 lines are tests. One touchpoint in the implementation surface.

`GatewaySessionStore.gateway_source()` keeps main's row label inside the surfaces the gateway itself advertises via `runtime.describe`:

- an inherited label the gateway serves (e.g. `tool`) passes through untouched — no behavior change for served labels;
- an inherited non-surface automation label (`kanban`, `cron`, ...) falls back to the thin client's own rule — the label this run would have had with no env at all: `oneshot` for a finite run, `cli` otherwise;
- an explicit `--source` the gateway cannot serve is never silently rewritten: it raises the thin client's existing `Gateway does not support source '...'` error instead of the opaque refusal;
- a gateway whose `describe` carries no `sources` (older build) keeps the old pass-through behavior exactly.

The contract lookup is folded into the store's single cached `runtime.describe` (`describe_create_contract`), which `client_env` already needed — the two share one round-trip on paths that call both, and the only added cost is one cached describe on paths that never asked for the create contract before.

## Relationship to #142456

#142456 fixes the same regression from the client side, with a `CREATE_SOURCES` frozenset mirroring the wire vocabulary in `agent/session_source.py`. Two concrete differences here, offered for maintainers to choose from:

1. **No duplicated vocabulary.** This reads the served surfaces from the gateway's own `runtime.describe` contract at runtime — one source of truth, no skew risk when the wire vocabulary changes. The frozenset approach has to be kept in sync by hand and needs a dedicated skew-guard test to catch drift.
2. **Explicit `--source` stays loud, but readable.** #142456 preserves an explicit unsupported `--source` verbatim, so the user still hits the bare `invalid_params`; here that case raises the thin client's "does not support source" error, which names the problem (the confusion class of #142991).

Happy to defer to whichever shape the maintainers prefer — the regression tests here cover the same failure shape either way.

## Test plan and results

- New regression tests in `tests/hermes_cli/test_gateway_session_store.py` against a `runtime.describe` that answers with the real create contract: an inherited automation label is demoted to a served surface (`oneshot` for a finite run, `cli` otherwise), an explicit unsupported source raises the named error, and served labels plus contract-less older gateways pass through unchanged. Both new tests pass on the branch (2/2).
- Full `tests/hermes_cli/` suite vs a main baseline on the same host: the set of failing test files is identical to the baseline — zero new failures. (The baseline itself has environment-dependent failures in this checkout; they are byte-for-byte the same set on both bases.)
- `scripts/check`: 12 checks ok; code health vs the merge base: 0 blocking, 0 advisory.
