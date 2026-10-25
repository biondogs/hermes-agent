Ran into the same regression (reported in #143653) and rolled a variant of this fix on a branch, in case it's useful as input: https://github.com/biondogs/hermes-agent/tree/fix/chat-oneshot-source-labels

Two differences from this PR, both small:

- Instead of mirroring the wire vocabulary in a client-side `CREATE_SOURCES` frozenset, the store reads the served surfaces straight from the gateway's `runtime.describe` (`session_create.sources`, cached on the describe round-trip the store already makes), so there is no second list to keep in sync and no skew guard to maintain when the vocabulary changes. On a gateway whose describe carries no `sources` it keeps the old pass-through behavior.
- An explicit `--source` the gateway cannot serve raises the thin client's existing `Gateway does not support source '...'` error rather than surfacing the bare `invalid_params`, which reads friendlier for the confusion class in #142991.

Test evidence: the inherited-`kanban`-label case, the finite/attended fallbacks, and the explicit-source refusal are covered by new regression tests in `tests/hermes_cli/test_gateway_session_store.py` — 2/2 green on the branch, and the set of failing files in `tests/hermes_cli/` is identical to a plain-main baseline on the same checkout (no new failures).

This PR looks like a solid fix either way — happy for the frozenset shape to win; the regression tests translate to it directly.
