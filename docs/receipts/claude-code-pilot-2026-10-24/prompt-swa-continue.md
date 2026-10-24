# CONTINUATION — sw-dev-a pilot (shot 2 of 2)

The working tree contains an in-progress implementation of two fixes (advisory state-dir lock per QA-001 + typed StateLogCorrupt at the CLI door per QA-002), plus a new test file tests/test_state_dir_lock.py. Read docs/qa/FINDINGS.md (QA-001, QA-002) and the current dirty tree.

1. Review the partial work for correctness and completeness against the two findings, including: serve must HOLD the lock for its lifetime; direct CLI/engine opens must refuse typed with `state-dir-locked (a server owns it — pass --url)`; every CLI verb against a corrupt state log must exit with a one-line typed StateLogCorrupt error (no traceback).
2. Complete whatever is missing; keep minimum footprint, no drive-by refactors. mypy-strict + ruff compliant.
3. Run your new tests plus closely-related existing tests (e.g. tests/test_cli_parity.py, lifecycle/engine tests). Targeted only — not the full suite.
4. Finish with: files changed, exact test pass/fail receipts, and any residual risk.

Do NOT: git commit, git push, network commands, or anything outside this repo directory.
