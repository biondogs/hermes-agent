> Status: current (pattern doctrine). Card t_6d1b4e61 (CI-CONTAINERS-3-GUIDANCE), 2026-11-01. Instance of this pattern on software-co: `docs/CI-CONTAINERS-GUIDANCE.md`. Live instances: `ci/hermes-upstream/` (t_e26d9c1f, commit `dc42521`), `ci/hermes-estate-twin/` (t_9953d256, commit `b859885`). Scope note: the operator ruled 2026-11-01 that software-co is the estate's only dev board — the other boards are operations boards — so this document contains **no candidate-twin proposals for other boards**; it ends with the routing rule that brings such work here (§4).

# Standing Containers for Ongoing Work — the generalized pattern

## Plain-language summary (for the operator)

- A **standing container** is a ready-to-use, throwaway-safe environment for a
  recurring kind of work — built once, refreshed by timer, used on demand. It
  replaces per-card ad-hoc setup and makes "tested it" a reproducible claim.
- Two flavors cover nearly everything: a **fresh-upstream image** (clean copy
  of the thing you build on, rebuilt nightly against green tests) and a
  **synchronized twin** (a secret-scrubbed, network-isolated replica of your
  live deployment, refreshed hourly). Test against the one that matches where
  the change must work; never test against the live system.
- Cost on software-co today: ~630 MB/image for upstream (keep-7 retention,
  fresh/last-green never pruned), ~960 MB twin image + ~2.8 GB regenerable
  twin-root on disk, two systemd user timers, zero standing containers left
  running except the twin (~idle CPU).
- What you get: every build/test result is pinned to an image tag + sha (or a
  sync timestamp), so any QA or review claim can be re-verified later; the live
  estate stops being a test bench and stops being at risk from dev work.
- Other boards don't need their own containers — they need the **routing rule**
  in §4: Hermes dev/test work gets filed on software-co, which already owns
  these two.

## 1. The problem this pattern solves

Ongoing work on a live system has two bad defaults. Testing *on* the live
system is dangerous and unprovable (results depend on hidden state nobody
pinned). Spinning up a *fresh ad-hoc* environment per task is expensive and
inconsistent (every card re-pays setup, no two results are comparable). A
standing container is the third option: the environment is built once,
refreshed automatically, health-reported, and every use costs one command.

## 2. The pattern, per board/project

### (a) A fresh-upstream image — for work that must work on clean upstream

What it is: a container image built from the upstream project's current
`main`, with the project's dev dependencies and nothing of yours baked in.
Rebuilt on a timer (nightly is fine), and **green-gated**: the `fresh` tag
only advances when the image's own test run passes; failures leave a dated
"candidate" image + a red status instead of silently poisoning users of the
stable tag.

Conventions that make it work:

- Tags: `:fresh` (stable, green-gated), `:last-green` (rollback), dated
  `:YYYYMMDD-<sha7>` (immutable, never pruned for recent N, the
  reproducibility anchor).
- Status artifacts written **every** run, green or red: machine-readable
  (`status.json`: upstream sha, test counts, result, drift) + human-readable
  (`STATUS.md`). Never silence a failure — a red STATUS file on disk is the
  alert.
- The command surface is one runner script (`run-branch.sh <worktree>`): mount
  a branch/worktree in, run its tests, throw away the world. No host
  `HERMES_HOME` involvement; stub credentials/env so nothing live is
  reachable.

### (b) A synchronized twin — for work that must work in the live deployment

What it is: a container holding a continuously-synced mirror of the live
deployment (code checkout *including local patches*, config tree, data
snapshots), mounted read-mostly, on an isolated network. It answers "will this
work *here*, as deployed?" without ever touching the deployment.

Non-negotiables:

- **The live system is read-only for the twin.** Every sync pulls
  (clone/fetch/rsync/`sqlite3 .backup`); nothing ever writes back.
- **Secret stripping in three layers:** *exclude* files that must never enter;
  *scrub* config that must parse but not carry real secrets (placeholder
  values); *scan* after every sync with a quarantine trip — a hit writes a
  `.quarantined` marker and the container refuses to work until fixed. Prove
  the scanner with a seeded canary test.
- **Network isolation:** dedicated bridge with `internal: true`; no host
  route, no ports, no live DB mounts. Prove it with a probe test.
- **Data that changes shape needs snapshots, not file copies** (sqlite
  `.backup`, not rsync of a hot DB).
- **Never bake the mirrored data into image layers** — bind-mount it from a
  gitignored on-disk root so scrubbing/resyncing never requires an image
  rebuild, and imagePulls never leak estate data.

### (c) STATUS.md + timers + hjob conventions

- All refresh machinery lives in `systemd --user` timers (not crontab, not
  worker background processes) — restart-safe, visible in `list-timers`,
  `Persistent=true` so missed runs catch up.
- Any single refresh that can exceed ~10 min runs under `hjob` (G-29:
  restart-safe own-unit jobs), not a worker process — the estate long-job law
  applies inside the pattern too.
- Every automated run rewrites the status artifacts (PASS/FAIL + the identity
  of what it synced/built: shas, timestamps, counts). A consumer (worker,
  butler, human) must be able to answer "is this environment usable, and
  exactly what is in it?" from one file read.
- Health has an age dimension: a green status from 5 days ago is a stale
  status. Document the staleness threshold that forces a refresh
  (~2× cadence, or ~48 h for nightly, is a good default).

### (d) Retention & cost

- Images: keep N dated tags (7 works; ~600 MB–1 GB each for a Python stack),
  prune older; **never** prune `fresh`/`last-green`/the failure candidate.
- Twin roots are regenerable by definition — gitignore them, don't back them
  up as precious data, and treat their disk use (a few GB) as the cost of the
  pattern.
- Two timers worth of cron-load and one mostly-idle container is the steady
  state. If a flavor hasn't been used in weeks, stop its timer and keep the
  build scripts — standing up again is one `rebuild.sh`/`make sync` away.
  Record the teardown command on the delivering card so decommissioning is
  never a mystery.

## 3. Checklist to stand one up (per project)

1. Pick the flavor(s): upstream-bound work only → (a); estate-shaped work →
   (b); a real dev board probably wants both.
2. Write the sync/rebuild script first, with the status artifacts in it, and
   the gate (green-gate for images, quarantine for twins) *before* wiring any
   timer.
3. Write the runner surface: one script per common action (run-tests,
   shell, rebase-check/dry-run) — cards reference scripts, never raw docker
   invocations.
4. Prove the invariants with tests (canary secret, isolation probe,
   gate-refuses-on-red) and put them in `tests/`.
5. Install the `systemd --user` timer; verify with `list-timers` and force one
   run.
6. Write the README (usage, sync source table, secret stripping, teardown) and
   a STATUS.md on first sync/build.
7. Write/point-at the decision-rule doctrine (like
   `docs/CI-CONTAINERS-GUIDANCE.md`) so cards know which container and what
   evidence to pin.
8. Commit everything to the owning repo — the containers are repo artifacts,
   not host pets.

## 4. When another board should use these (operator ruling 2026-11-01)

The estate's other boards (gaudi, gargantua01/02, skipjack*) are **operations
boards**: they operate deployments, they don't develop software, and none of
them needs its own container twin. software-co is the only dev board and is
the standing home of both containers. No candidate-twin proposals for other
boards exist by operator ruling.

What other boards DO need is the **routing rule** — recognizing when their
work is Hermes dev/test work and sending it here:

**Triggers — any of these means a software-co card, not local improvising:**

- A change to Hermes source code, plugin code, or tool code.
- Porting or rebasing local hotfixes onto a newer upstream.
- A profile / SOUL / config change that should be regression-tested before it
  touches the live estate.
- Reproducing or diagnosing a Hermes bug (as opposed to an ops incident whose
  cause is already external — hardware, network, a vendor service).

**Routing rule:** file the card on the **software-co** board via
**swco-butler** (or the **default orchestrator** when the request is
cross-board / no butler is appropriate), target `hermes-upstream:fresh` or the
estate twin per the decision rule in `docs/CI-CONTAINERS-GUIDANCE.md` §3, and
the result flows back to the requesting board as a handoff (card comment,
attached artifact, or a completion summary). The requesting board's own card
stays free of build/test machinery — it just links the software-co card id as
plain text.

### Cheat sheet (drop verbatim into other boards' guidance)

> **Hermes build/test work runs in software-co's standing containers — never on the live estate.**
> Upstream-bound work (features, PR prep): `ci/hermes-upstream/run-branch.sh <worktree>` in `hermes-upstream:fresh`.
> Estate-shaped work (hotfix rebases, profile/SOUL/config regression, bug repro): `ci/hermes-estate-twin` — `twin-test`, `twin-rebase-check`, `twin-shell`.
> File it on the **software-co** board (swco-butler; default orchestrator for cross-board) and demand a pinned image tag + sha as the test receipt.
> Full decision rule + evidence requirements: `software-co/docs/CI-CONTAINERS-GUIDANCE.md`.

## 5. Cost & retention as built (software-co, measured 2026-11-01)

| Item | Size / cadence | Retention |
|---|---|---|
| `hermes-upstream` image (all tags share layers) | ~632 MB | keep 7 dated; `fresh`/`last-green`/`candidate` never pruned |
| `hermes-estate-twin` image | ~962 MB | latest only |
| `twin-root/` mirror | ~2.8 GB (agent 1.4 G, estate 1.1 G, home 261 M, snapshots 47 M) | regenerable — gitignored, never backed up as precious |
| Timers | upstream rebuild nightly 03:30; twin sync hourly | `systemd --user`, `Persistent=true` |

## 6. Revisit triggers

- A second genuinely dev-shaped board appears (its own repo, its own build) →
  it stands up its own pair per §3; the routing rule in §4 then gains a second
  destination.
- An operations board starts repeatedly asking for repro/verification of
  Hermes behavior → that's §4-routing working; only if the volume justifies a
  *specialized* fixture (e.g. a gargantua-shaped twin) does it get considered —
  as an operator decision, not a default.
- The live deployment gains a second distinct shape (separate estate instance)
  → the twin pattern gains an instance; never overload one twin with two
  shapes.
