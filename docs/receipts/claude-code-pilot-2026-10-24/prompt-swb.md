# PILOT TASK — sw-dev-b lane replay (Claude Code vs muse's landed fix for mash#24)

You are fixing mprov-ng/mash issue #24 in a local clone parked at the exact base sha where the defect reproduces (36ef120). Coding task only.

## Defect
BMC power commands fail when the mprov server URL is typed without a trailing slash, e.g.:
    connect http://127.0.0.1:8080 apikey KEY
then `bmc power on` produces requests like 'http://127.0.0.1:8080power/on/...' and every power command fails with "is not a valid host or port".

## Fix requirement
Normalize mprovURL to exactly one trailing slash at connect time (or join the power path in one shared helper — your choice, minimum footprint wins). The fix must make BMC power work with a URL typed with or without the trailing slash.

## Requirements
1. Freshness gate FIRST: verify the defect reproduces on this tree (pin what you ran).
2. Regression tests with teeth: tests that FAIL on the unfixed tree and PASS with your fix (show RED on base → GREEN on fix by actually running them with and without the fix).
3. Minimum merge footprint: touch ONLY what the fix requires — no drive-by refactors, no format sweeps.
4. Run the repo's test suite (it is small — run it fully).
5. Do NOT: git commit, git push, network commands, or anything outside this repo directory.
6. Finish with: files changed (with the actual diff stat), test receipts (RED/GREEN counts), and a one-paragraph root-cause summary.
