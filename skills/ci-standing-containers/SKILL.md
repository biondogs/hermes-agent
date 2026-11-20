---
name: ci-standing-containers
description: "Use when building, testing, or verifying anything Hermes-shaped on the software-co board — agent source, plugins, tools, porting/rebasing hotfixes, profile/SOUL/config regression, bug reproduction. Carries the decision rule (fresh-upstream vs estate-twin), the two container command surfaces, and the pinned-tag test-receipt requirement. Never build or test against the live estate."
version: 1.1.0
author: kanban-board-architect
license: MIT
metadata:
  hermes:
    tags: [ci, containers, testing, hermes, software-co]
    related_skills: [upstream-hermes-filing, kanban-orchestrator]
---

# Standing CI containers — build/test here, never the live estate

software-co owns two standing containers (built by CI-CONTAINERS-1/2, doctrine card
t_6d1b4e61). Every Hermes build/test/verify claim comes from one of them, pinned to
an image tag + sha (or a twin sync timestamp) — a tested claim without the pin is
not a receipt.

## Decision rule (full doctrine: /local/projects/software-co/docs/CI-CONTAINERS-GUIDANCE.md §3)

- **Upstream-bound work** — must work on clean upstream (new features, upstream PR
  prep, upstream-first fixes): run in **`hermes-upstream:fresh`** —
  `ci/hermes-upstream/run-branch.sh <worktree>` (mounts your branch/worktree in, runs
  the repo's own test suite, throws the world away). Check
  `ci/hermes-upstream/STATUS.md` is green and fresh (~48 h staleness threshold)
  before relying on `:fresh`.
- **Estate-shaped work** — must work on the live deployment's shape (hotfix rebases
  onto a newer upstream, profile/SOUL/config change regression, bug repro against
  deployed code/config/data): run in the **`hermes-estate-twin`** container —
  `twin-test`, `twin-rebase-check`, `twin-shell`. The twin is a secret-scrubbed,
  network-isolated mirror of the live estate, read-only toward the live system by
  construction.
- **Never the live estate**: no Hermes dev/test/repro directly against the running
  deployment, ever.

## Receipts

Every "tested" claim in a card or completion metadata pins: the container
(`hermes-upstream` or `hermes-estate-twin`), plus the image tag + sha (dated tag, or
`:fresh` + the STATUS.md upstream sha) or the twin's sync timestamp. Cards that name
no container are not compliant with the intake rule — say so in review.

## Twin runs are offline: never fall back to the host (guidance §5a)

The twin's network is internal-only, so a checkout's `scripts/run_tests.sh` dies
staging uv from GitHub, and the twin checkout's `.venv` points at a host path.
That is not a licence to run on the host. Use the image's baked interpreter:

- **A specific ref (the usual case):**
  `~/.hermes/scripts/hjob start <card> --name <run> -- /local/projects/software-co/ci/hermes-estate-twin/scripts/twin-clone-test --repo <git dir> --ref <rev> --out <durable dir> --name <run> -- <test paths>`
  It builds an isolated repo in the container's `/tmp` (twin object store via
  alternates, plus a pack of whatever the twin lacks; the twin work tree is never
  touched), checks that imports resolve to it, and runs
  `HERMES_PYTHON=/usr/bin/python3 scripts/run_tests.sh` (`--raw` = one
  `/usr/bin/python3 -m pytest` process). The host repo is only read, and lazy
  fetches are blocked. If the script is not on disk at that path, take it from
  `master`:
  `git -C /local/projects/software-co show master:ci/hermes-estate-twin/scripts/twin-clone-test > "$TMPDIR/twin-clone-test"; chmod +x "$TMPDIR/twin-clone-test"`.
- **The twin checkout as synced:** `twin-test` (it does the same
  `HERMES_PYTHON` hand-off offline).
- **Twin broken or stale:** fix or re-sync it, or block the card. A stale sync
  is fine for code-only tests of an imported ref; keep the `STALE` flag in the
  receipt.

## Receipt labeling: what may be called a "twin" run (guidance §6a)

- A receipt may say *twin* only if its log shows it ran in the container: the
  `=== TWIN-RECEIPT v1 ===` header from `twin-clone-test` (image sha, sync stamp,
  `hostname=hermes-estate-twin`, `/home/arch` absent, `interpreter: /usr/bin/python3`,
  `import_check: PASS`), or else the in-container interpreter, rootdir and
  hostname in the log, plus the quoted image sha and sync stamp. A bare `-q`
  tail proves nothing about where it ran.
- Any `/home/arch/...` interpreter or rootdir in the log (e.g.
  `/home/arch/.hermes/hermes-agent/.venv/bin/python3`) means a **host run**.
  Label it `surface: host (isolated clone <path>, interpreter <path>)`. It is
  acceptable only as narrow, env-independent evidence (the R27c precedent), it
  never carries a twin pin, and it never satisfies a twin requirement.
- Reviewers: a twin claim without the header or container markers is a finding
  ("receipt not container-verifiable"). The fix is to re-run through
  `twin-clone-test`, not to relabel.

## Where the rest lives

- Card-body boilerplate + the 4-rung in-container test ladder:
  `docs/CI-CONTAINERS-GUIDANCE.md`.
- Generalized pattern (cost, timers, teardown, cross-board routing):
  `docs/STANDING-CONTAINERS-PATTERN.md` (§4 = cross-board routing rule).
