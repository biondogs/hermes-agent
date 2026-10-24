# PILOT TASK — sw-dev-a lane replay (Claude Code vs muse track record)

You are implementing a bug-fix card in an isolated clone of the metatron-rewrite repo (branch w4/qa-ready). This is a coding task only.

## Context to read first
- docs/qa/FINDINGS.md — findings QA-001 and QA-002 (full repro details; code-verified against this tree).

## Task: fix both findings

**QA-001 (prevention missing):** while `serve` runs, a direct CLI opener of the same state dir writes a SECOND state-log record with a duplicate seq (the server's in-memory counter doesn't see it) → next cold open raises StateLogCorrupt "seq 11 -> 11 (treat as tampering)". Detection is honest; PREVENTION is missing.
Fix: advisory lock (fcntl.flock on e.g. `<state>/.lock`) taken for the lifetime of `serve`; any direct CLI/engine open of a locked state dir must refuse with a TYPED error: `state-dir-locked (a server owns it — pass --url)` — not a traceback, not a generic exception. The remote door (--url) is already correct and must remain untouched.

**QA-002 (typed error at CLI door):** any CLI verb against a corrupt state log currently exits with a Rich traceback. Fix: the CLI door must catch the corrupt-state-log condition and exit with a one-line typed error (StateLogCorrupt), no traceback dump.

## Requirements
- Regression tests for BOTH fixes, with teeth: a test that would fail on the unfixed tree. Follow the existing test conventions in tests/.
- Minimum footprint: touch only what the fixes require; no drive-by refactors, no format sweeps.
- Repo gates are mypy strict + ruff clean — keep the code compliant (run them if quick).
- Run the targeted tests you added plus any closely-related existing tests. Do NOT run the full 573-test suite if it is slow; targeted is fine.
- Do NOT: git commit, git push, any network command, any command touching files outside this repo directory.
- Finish with a summary: files changed, test results (exact pass/fail counts), and any residual risk.
