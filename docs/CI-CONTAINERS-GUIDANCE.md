> Status: current (software-co CI/CD doctrine). Card t_6d1b4e61 (CI-CONTAINERS-3-GUIDANCE), 2026-11-01. Revised 2026-11-19 by card t_42ab1cec (twin receipt hygiene: §5a offline in-twin run surface, §5b broken/stale twin, §6a receipt labeling rule, `twin-clone-test`). Parents: t_e26d9c1f (fresh-upstream container, commit `dc42521`) and t_9953d256 (estate twin, commit `b859885`). Companion: `docs/STANDING-CONTAINERS-PATTERN.md` (the generalized pattern), per-container READMEs under `ci/hermes-upstream/` and `ci/hermes-estate-twin/`.

# CI Containers — how software-co builds and tests Hermes work

## 1. The rule

Hermes-related build/test work on this board runs in one of the two **standing
containers** — `hermes-upstream:fresh` (clean upstream) or the
**hermes-estate-twin** (synchronized replica of the live estate). The **live
estate is never a build/test environment**: no pytest against
`~/.hermes/hermes-agent`, no experimental installs into `~/.hermes`, no
scratch worktrees of the live checkout. The live checkout is the running
gateway's runtime — mutating it from a dev card risks the estate and produces
results that cannot be reproduced later.

The containers already exist, sync on timers, and are health-reported — using
them costs one command. Not using them costs an ad-hoc environment whose
results nobody can vouch for.

## 2. The two containers

| | `hermes-upstream:fresh` | `hermes-estate-twin` |
|---|---|---|
| What it is | Image rebuilt nightly from `NousResearch/hermes-agent` `origin/main` | Container with an hourly-synced mirror of the **live** estate: hotfix-carrying checkout + `~/.hermes` tree + `hermes-estate`, bind-mounted from `ci/hermes-estate-twin/twin-root/` |
| Represents | clean upstream (what a PR will be judged against) | the running estate exactly (hotfixes, profiles, SOULs, config, snapshot DBs) |
| Isolation | stub LLM, throwaway `HERMES_HOME`, `--network none` for tests | dedicated `internal: true` bridge — no host network, no ports, no live DBs; secrets scrubbed + scanner with quarantine |
| Refresh | nightly timer `hermes-upstream-rebuild.timer` (03:30) + `rebuild.sh` | hourly timer `hermes-estate-twin-sync.timer` + `make sync` |
| Health/state | `ci/hermes-upstream/STATUS.md`, `status.json` (upstream sha, test counts, drift) | `ci/hermes-estate-twin/twin-root/STATUS.md` / `STATUS.json` (live sha match, profile set, quarantined flag, sync time) |
| Entry points | `ci/hermes-upstream/run-branch.sh`, `rebuild.sh`, `health.sh` | `scripts/twin-clone-test` (test a ref, offline, self-labeling receipt — §5a), `twin-shell`, `twin-test`, `twin-rebase-check`, `sync-now`, `Makefile` |
| README | `ci/hermes-upstream/README.md` | `ci/hermes-estate-twin/README.md` |

## 3. Decision rule — which container

Ask **"where does this change have to work?"**

- It has to work on **clean upstream** (a PR will merge into `main` without our
  hotfixes) → **fresh**.
- It has to work in **the running estate** (our hotfix stack, our profiles,
  our config) → **twin**.
- Both → run **both** and attach both receipts; the fresh run is the
  portability check, the twin run is the production-representative check.

| Work class | Container | Command |
|---|---|---|
| Upstream-bound feature, upstream PR prep/validation | fresh | `ci/hermes-upstream/run-branch.sh <worktree> [pytest args]` |
| "Does X still work on current upstream?" canary | fresh | `ci/hermes-upstream/run-branch.sh ./hermes-board-layers` |
| Porting a local hotfix / carrying the stack onto a new upstream ref | twin first, then fresh | `ci/hermes-estate-twin/scripts/twin-rebase-check <upstream-ref>` for the dry-run; final validation via `run-branch.sh` on the rebased branch |
| Estate regression (hotfix-stack tests, gateway/kanban behavior as deployed) | twin | a specific ref/branch: `ci/hermes-estate-twin/scripts/twin-clone-test --repo <repo> --ref <rev> -- <test paths>` (§5a); the twin checkout as synced: `ci/hermes-estate-twin/scripts/twin-test [pytest args]` |
| Profile / SOUL / config changes that should be regression-tested before touching the live estate | twin | `make sync` → `twin-shell` → edit/inspect inside twin → `twin-test`; twin `verify.sh` already checks profile set + config parse on every sync |
| Reproducing a reported Hermes bug | twin if it smells estate-specific; fresh if it smells upstream | repro in the container that matches the report; if unsure, reproduce in both — the one that reproduces localizes the bug |
| Interactive exploration of either world | fresh (throwaway `HERMES_HOME`) / twin (`twin-shell`) | never the live estate |

Tie-breakers:

- **Never** the live estate as a build/test target. Read-only git inspection of
  the live checkout (`git log`, `git show`, `git status`) is fine; anything
  that runs tests, installs packages into `~/.hermes`, switches branches, or
  creates worktrees there is not. The only sanctioned mutations of the live
  estate are the update runbook (`docs/HERMES-UPDATE-PREP-2026-10-29.md` §6)
  and the canonical gateway bounce — kanban-board-architect/operator lanes,
  not dev-lane work.
- If a container is unhealthy or stale (§7), **fix the container first**
  (rebuild / re-sync) rather than falling back to the host.
- The twin never writes to the live estate (every sync is read-only from the
  live side); a `.quarantined` marker means a scanner hit — stop, fix scrub,
  never bypass.

## 4. Card-body boilerplate (paste into implementer cards)

Filers of implementation cards that touch Hermes code, config, profiles, or
SOULs SHOULD include this block, filled in. It makes the test environment a
checked-in part of the card, not an afterthought.

```markdown
## CI containers (per docs/CI-CONTAINERS-GUIDANCE.md)

- Container: <hermes-upstream:fresh | hermes-estate-twin>
- Why this one: <upstream-bound feature / estate regression / port+rebase / bug repro>
- Test commands:
  - rung 1 (targeted): <e.g. ci/hermes-upstream/run-branch.sh <worktree> tests/<file> -q
                        | ci/hermes-estate-twin/scripts/twin-clone-test --repo <repo> --ref <rev> -- tests/<file>>
  - rung 2 (suite):    <e.g. twin-clone-test --repo <repo> --ref <rev> (no test args = full suite)>
  - rung 3 (rebuild):  <fresh-clone rebuild — see guidance §6>
- Baseline to pin: image tag + sha at test time (read from status.json / twin STATUS.md;
  twin-clone-test prints both into its TWIN-RECEIPT header)
- Evidence to attach: test-output tail with pass/fail counts + the pinned tag/sha line;
  for twin runs the log WITH its TWIN-RECEIPT header (§6a)
- Known environmental failures to expect: <none | list, e.g. full-suite root/socket failures — see guidance §6 note>
- Forbidden: running tests on the live estate; mutating ~/.hermes outside the twin sync;
  labeling a host run "twin" (§6a)
```

## 5. Test ladder (in-container)

Climb rung by rung; a card's completion evidence names the highest rung that
passed. All rungs run **in a container** — never on the live estate, and
preferably not on the host either (host runs are acceptable only for narrow,
env-independent cases, and must be labeled as such).

| Rung | What | fresh | twin |
|---|---|---|---|
| 1. Unit (targeted) | the tests nearest your diff | `run-branch.sh <worktree> tests/<file>::<test> -q` | `twin-clone-test --repo <repo> --ref <rev> -- tests/<file>` (§5a) |
| 2. Suite | the repo's suite via `scripts/run_tests.sh` (never bare `pytest` — R27c) | `run-branch.sh <worktree>` (full gated subset) | `twin-clone-test --repo <repo> --ref <rev>` (runs `scripts/run_tests.sh` offline, §5a); `twin-test` for the twin checkout as synced |
| 3. Fresh-clone rebuild | prove the change survives a clean clone + dependency install, not just the prepared container | clone your branch into a scratch dir, `run-branch.sh <that-clone>` | `twin-test` in a re-synced twin (`make sync` first) — the twin's own sync+verify already proves the estate shape rebuilds |
| 4. Integration | the change under estate-shaped conditions (profiles, config, snapshots) | n/a — fresh has no estate shape | `twin-shell`: `hermes profile list`, `hermes -p <profile> config check/validate`, plus the fix-class's live-probe equivalents (the runbook's §Phase-4 probe list is the menu) |

**Full-suite caveat (fresh):** the upstream full suite currently has ~78
environment-specific failures (root/socket) that are unsuitable for a green
gate; the nightly green-gate runs a curated subset (114 tests over 4 kanban
files as of 2026-11-01). Never claim "full suite green" unless you ran the
full suite and the only failures are the documented environmental set — count
and name them in the evidence.

**Hotfix rebases (twin):** rung 3 means `twin-rebase-check <upstream-ref>`
(dry-run rebase in a temp worktree inside the twin, reports clean vs conflicts
with the conflicted files) before any real rebase is proposed on a card.

### 5a. The offline in-twin run surface (card t_42ab1cec)

The twin sits on an `internal: true` network: nothing inside it can reach
GitHub. A checkout's own `scripts/run_tests.sh` normally re-executes under
`scripts/run-in-hermes-env`, which stages a pinned uv from GitHub, so **it dies
offline** (`curl: (6) Could not resolve host: github.com … setup failed`). The
twin checkout's `.venv/bin/python` is a symlink into a host uv-python path and
is broken in-container too. That is not a reason to run on the host. The
working surface is:

- **Interpreter:** the image's baked system python, `/usr/bin/python3`
  (Python 3.13, twin-runtime deps + pytest baked into
  `/usr/local/lib/python3.13/dist-packages`).
- **Runner:** `HERMES_PYTHON=/usr/bin/python3 scripts/run_tests.sh <paths>`.
  `run_tests.sh` honours an explicit `HERMES_PYTHON` that has pytest and then
  skips `run-in-hermes-env`/uv staging entirely, while keeping its own hermetic
  `env -i` per-file runner, so this is still the canonical R27c runner. Use bare
  `/usr/bin/python3 -m pytest` only for a deliberate one-process run (e.g. a
  co-run that must share `sys.modules`).
- **Code under test:** an isolated repo in the container's `/tmp`, borrowing the
  twin object store through `objects/info/alternates` (no clone transport, no
  object copy), with the ref's missing objects imported from the host as a
  pack. The twin checkout's work tree is never used: other cards edit it, and
  it is not your ref. Run from the repo root so imports resolve to that repo,
  not the editable install of `/opt/twin/hermes-agent`; check it (the script
  refuses to run if they don't).

`ci/hermes-estate-twin/scripts/twin-clone-test` does all of it and writes a
self-identifying receipt (§6a):

```bash
# from a checkout that has ci/ on master (or fetch the script:
#   git -C /local/projects/software-co show master:ci/hermes-estate-twin/scripts/twin-clone-test > "$TMPDIR/twin-clone-test" && chmod +x "$TMPDIR/twin-clone-test")
~/.hermes/scripts/hjob start <card-id> --name <run> -- \
  ci/hermes-estate-twin/scripts/twin-clone-test \
    --repo <any git dir holding the ref, e.g. your worktree> --ref <branch|sha> \
    --out <durable dir> --name <run> [--raw] [--timeout 7200] [--require-fresh] \
    -- tests/hermes_cli/test_x.py tests/tools/test_y.py      # no paths = full suite
```

- Host side it only reads the source repo (`rev-parse`, `for-each-ref`,
  `rev-list`, `pack-objects --stdout`), with `protocol.allow=never` and
  `--missing=allow-promisor`, so even a partial (promisor) clone such as the
  live checkout is never lazy-fetched into.
- Exit code = the test runner's (124 = `--timeout`). Long runs go through
  `hjob` (G-29). `hjob stop` triggers the script's cleanup, which also stops the
  in-container run and removes its `/tmp/twinrun-*` dir.
- `twin-test` (no args) now does the same `HERMES_PYTHON` hand-off when the
  container is offline, but it tests the twin checkout's work tree as it
  stands. Use `twin-clone-test` whenever the claim is about a specific ref.

### 5b. When the twin itself is broken or stale

If the twin's sync is failing or STATUS is stale, fix or re-sync the twin, or
block the card. Do **not** move the run to the host and still call it a twin
run. A stale twin is still a valid surface for code-only tests of a ref you
import (the code comes from your pack, not from the sync); the receipt must
carry the `STALE` flag the script prints.

## 6. Reproducibility — pin the sha

A test result is only evidence if the exact code and environment are
identified. Every card that ran container tests states:

- **fresh:** the dated tag and upstream sha from
  `ci/hermes-upstream/status.json` at test time
  (e.g. `hermes-upstream:20261101-c627ec8`,
  upstream `c627ec84664d…`). The dated tag is never overwritten, so a result
  can be re-verified by running that tag directly.
- **twin:** the live sha and branch from
  `ci/hermes-estate-twin/twin-root/STATUS.md` (e.g.
  `a0107dcf9090837468f0bcb1e4a17d30b93a77ab` @
  `local/hotfix-carried-2026-11-01-0935`) **plus** the sync timestamp — twin
  content is time-varying, so timestamp + sha together pin what you actually
  tested. If your card's results must survive a later re-sync, run
  `make sync` immediately before testing and quote the new STATUS stamp.

Before starting work, check health and age:

```bash
./ci/hermes-upstream/health.sh            # fresh age, last result, drift
cat ci/hermes-upstream/STATUS.md          # human summary
cat ci/hermes-estate-twin/twin-root/STATUS.md   # twin sync stamp, PASS/FAIL, quarantine
```

- `fresh` older than ~48 h or last build red → `./ci/hermes-upstream/rebuild.sh`
  first (long job → hjob per G-29: `~/.hermes/scripts/hjob start <card-id> -- ci/hermes-upstream/rebuild.sh`).
- twin STATUS older than ~2× the sync cadence, or quarantined → `make sync`
  (from `ci/hermes-estate-twin/`) and read STATUS again before testing.
- Never report results against "latest" — always the pinned tag/sha.

### 6a. Receipt labeling rule: what counts as a "twin" run (card t_42ab1cec)

A test receipt may say *twin*, *in-twin* or *hermes-estate-twin* only when
the attached log proves by itself that it ran inside the container:

1. **Preferred:** the log starts with the `=== TWIN-RECEIPT v1 ===` header
   written by `twin-clone-test`. Host-side it pins the container, image tag,
   **image sha** and **twin sync stamp** (with age and a `STALE` flag).
   In-container it records `hostname=hermes-estate-twin`, `/.dockerenv`
   present, `/home/arch` absent, `interpreter: /usr/bin/python3`, the clone
   path under `/tmp/twinrun-*`, and `import_check: PASS`.
2. **Otherwise:** the log itself shows the container: the in-container
   interpreter path (`/usr/bin/python3`), a pytest `rootdir:` under `/opt/twin/…`
   or the container's `/tmp/…`, and the container hostname. The receipt also
   quotes the image sha and the sync stamp (§6). A bare `-q` tail
   (`20 passed in 8s`) proves nothing about where it ran, so it does not
   qualify.

**Disqualifier:** any host path in the log (an interpreter or rootdir under
`/home/arch/…`, e.g. `/home/arch/.hermes/hermes-agent/.venv/bin/python3`)
means it was a **host run**, whatever the card says.

**Host runs** of an isolated clone are acceptable evidence for narrow,
environment-independent checks *when labeled as host runs* (`surface: host,
isolated clone <path>, interpreter <path>`), the same precedent as R27c.
They never get a twin image sha or sync stamp attached, and they never satisfy
a card that asks for a twin run.

**Reviewers** (sw-reviewer, gates) check the header or the container markers
before accepting a twin claim. A twin claim without either is a finding
("receipt not container-verifiable"). The fix is to re-run through
`twin-clone-test`, not to relabel.

## 7. Evidence to attach on completion

1. The pinned baseline line (container, tag, sha, sync timestamp) from §6.
2. Test-output tail (≈ last 40 lines) including the pass/fail counts, per rung
   you claim.
3. For twin work: the twin STATUS line (overall PASS + live sha) at test time,
   and the log's TWIN-RECEIPT header (or the container markers, §6a). A host
   run is labeled `surface: host` and is never presented as a twin run.
4. Any failure you are explaining away, named and counted — never an
   undifferentiated "tests pass".

Attach as card comment / completion `metadata.tests_run` in the usual
receipt style. Do not paste secrets — the twin is scrubbed for a reason;
logs from inside it still go through the normal leak discipline.

## 8. Non-goals

- Not a CI-as-a-service: no per-push automation registry, no web dashboard.
  "CI" here = these two standing environments + this doctrine.
- Not for mprov / metatron work — those have their own harnesses
  (e.g. `mprov/MPROV-TESTENV-RUNBOOK.md`). The pattern doc generalizes; the
  instances are per-project.
- Does not replace review or gates: sw-reviewer still adversarially checks
  implementations against ADRs; distiller + operator gates still own outbound
  artifacts. Containers fix the *evidence* layer, not the *approval* layer.
- No profile SOUL/config edits from this doctrine — wiring it into profile
  guidance is kanban-board-architect's lane (CI-CONTAINERS-4).

## 9. Revisit triggers

- Upstream ships an official CI/test container → consider adopting it as the
  fresh-upstream base instead of our Dockerfile.
- The gated test subset in `rebuild.sh` drifts badly from the suite → re-gate
  (the count is stamped in `status.json`; watch it on every rebuild).
- A third Hermes deployment shape appears (e.g. a second estate) → the twin
  pattern gains a second instance; do not overload the existing twin.
- Twin sync cadence (hourly) proves too stale for a work class → add a
  pre-test `make sync` requirement rather than changing the timer.
