# MPROV-MAINT-PINS — clone paths, remote topology, head pins

Authored 2026-10-23 by sw-pm (kanban t_f46200db). Snapshot taken at
maintenance-wave provisioning time; pins are the review baseline.

## Remote topology (verified via `gh repo view` — no ambiguity, no block)

Our GitHub account is **biondogs**. All four repos are GitHub-native forks
(`isFork: true`) whose API-reported parent is the **`mprov-ng`**
organisation. There are **no** `uberlinuxguy/<repo>` repositories — that
owner resolves to nothing (`gh` GraphQL: `Could not resolve to a
Repository`). `uberlinuxguy` is the human maintainer behind `mprov-ng`, not
a separate fork owner, so the operator's `uberlinuxguy/*` vs `biondogs/*`
ambiguity does not materialise.

Standing rule from the operator (recorded in `MPROV-PRODUCT-REPORT.md` §4):
fix work lands as topic branches off the linear fork default, **PR
`biondogs/*` → `mprov-ng/*`**. Combined with `MPROV-MAINT-POLICY.md` Rule B,
that means: push to the fork, open the PR against `mprov-ng`, request
`uberlinuxguy` as reviewer.

## Fresh clones (maintenance workspace area)

Per the management-repo convention (`/local/projects/<repo>` per-repo work),
maintenance clones live under `/local/projects/mprov-maint/<repo>`. Each has
`origin = biondogs/<repo>` and `upstream = mprov-ng/<repo>`.

| Repo | Clone path | Default | `origin` head | `upstream` head | ahead / behind |
|---|---|---|---|---|---|
| mprov_control_center | `/local/projects/mprov-maint/mprov_control_center` | `main` | `7384c6364fb2e052db1be64bcc44788326d7ee5e` | `d7c2094137b4b9b781d80760382445fcef6a6278` | 1 / 264 |
| mprov_jobserver | `/local/projects/mprov-maint/mprov_jobserver` | `main` | `00d00bfd71899f9b638a2a093065278c79a05723` | `1fd4b123295a06831ac2b670c940bb5c17184eab` | 1 / 28 |
| mprov_scripts | `/local/projects/mprov-maint/mprov_scripts` | `master` | `aae84eecc57c37205206f92ebe71b9a78d5bedb4` | `eb806171457b2c9494488e1fe44b01fa4247eb38` | 1 / 10 |
| mash | `/local/projects/mprov-maint/mash` | `master` | `f9bb463c24306a5a873d8bb8833f7a69a714b72f` | `36b6a5efc68fa620812b401a412a469bdb6dcf3f` | 1 / 12 |

Fork URLs: `https://github.com/biondogs/<repo>`; upstream URLs:
`https://github.com/mprov-ng/<repo>`.

The single fork-side commit on every repo is `docs: openwiki generation +
documentation sweep (mprov CI/CD phase)` — the Oct-15 docs lane merge. No
fork carries product-code divergence.

## Drift warning for the sweep

All four upstreams have moved since the Oct-15 review pins
(`mprov_control_center` 98d4579, `mprov_jobserver` 4f73fc1,
`mprov_scripts` 55bdd51, `mash` d8871d4). `mprov-ng` pushed as recently as
2026-10-23. `mprov_control_center` is the biggest gap at **264 upstream
commits**. Any downstream card that reasons about current code must
re-verify against the upstream heads pinned above, not the Oct-15 pins, and
must check upstream history before filing (a finding may already be fixed).

## Prior-filing state snapshot (dedupe baseline)

Oct-15 wave filed 120 issues to the forks. Snapshot 2026-10-23 via
`gh api repos/biondogs/<repo>/issues?state=all`:

| Repo | Range | Open | Closed |
|---|---|---|---|
| mprov_control_center | #4–#43 | 40 | 0 |
| mprov_jobserver | #1–#31 | 31 | 0 |
| mprov_scripts | #1–#21 | 21 | 0 |
| mash | #1–#28 | 28 | 0 |
| **Total** | | **120** | **0** |

Per-issue titles + state: `maint-2026-10-23/issue-state-2026-10-23.json`
(120 records). Nothing has been closed or picked up upstream yet, so dedupe
against the full 120-issue set.

## Companion files

- Standing rules: `MPROV-MAINT-POLICY.md`
- Oct-15 index / register: `MPROV-PRODUCT-REPORT.md`, `FILED-ISSUES.md`
