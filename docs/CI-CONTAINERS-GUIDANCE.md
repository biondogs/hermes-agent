> Status: current (software-co CI/CD doctrine). Card t_6d1b4e61 (CI-CONTAINERS-3-GUIDANCE), 2026-11-01. Parents: t_e26d9c1f (fresh-upstream container, commit `dc42521`) and t_9953d256 (estate twin, commit `b859885`). Companion: `docs/STANDING-CONTAINERS-PATTERN.md` (the generalized pattern), per-container READMEs under `ci/hermes-upstream/` and `ci/hermes-estate-twin/`.

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
| Entry points | `ci/hermes-upstream/run-branch.sh`, `rebuild.sh`, `health.sh` | `scripts/twin-shell`, `twin-test`, `twin-rebase-check`, `sync-now`, `Makefile` |
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
| Estate regression (hotfix-stack tests, gateway/kanban behavior as deployed) | twin | `ci/hermes-estate-twin/scripts/twin-test [pytest args]` |
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
  - rung 1 (targeted): <e.g. ci/hermes-upstream/run-branch.sh <worktree> tests/<file> -q>
  - rung 2 (suite):    <e.g. ci/hermes-estate-twin/scripts/twin-test>
  - rung 3 (rebuild):  <fresh-clone rebuild — see guidance §6>
- Baseline to pin: image tag + sha at test time (read from status.json / twin STATUS.md)
- Evidence to attach: test-output tail with pass/fail counts + the pinned tag/sha line
- Known environmental failures to expect: <none | list, e.g. full-suite root/socket failures — see guidance §6 note>
- Forbidden: running tests on the live estate; mutating ~/.hermes outside the twin sync
```

## 5. Test ladder (in-container)

Climb rung by rung; a card's completion evidence names the highest rung that
passed. All rungs run **in a container** — never on the live estate, and
preferably not on the host either (host runs are acceptable only for narrow,
env-independent cases, and must be labeled as such).

| Rung | What | fresh | twin |
|---|---|---|---|
| 1. Unit (targeted) | the tests nearest your diff | `run-branch.sh <worktree> tests/<file>::<test> -q` | `twin-test "python -m pytest tests/<file> -q"` (or `scripts/run_tests.sh <file>`) |
| 2. Suite | the repo's suite via `scripts/run_tests.sh` (never bare `pytest` — R27c) | `run-branch.sh <worktree>` (full gated subset) | `twin-test` (defaults to `scripts/run_tests.sh`, falls back to `pytest tests/`) |
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

## 7. Evidence to attach on completion

1. The pinned baseline line (container, tag, sha, sync timestamp) from §6.
2. Test-output tail (≈ last 40 lines) including the pass/fail counts, per rung
   you claim.
3. For twin work: the twin STATUS line (overall PASS + live sha) at test time.
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
