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

**Re-provisioned 2026-10-23 (kanban t_2beff046)** per the venue amendment:
`/local/projects/mprov-maint/<repo>` are fresh clones with
**`origin = https://github.com/mprov-ng/<repo>`** (no `upstream` remote; the
forks are disused). The old fork-oriented clones are archived intact at
`/local/projects/mprov-maint/.archive-2026-10-23/<repo>` — the archived
`mash` clone carries unique unpushed work (`rescue/js29`, `rescue/js30`
branches + staged `src/mash/app.py`/`tests/test_load_config.py` changes,
fixing fork issues #29/#30) that was preserved, not deleted; it needs its
own card to land or retire that work.

| Repo | Clone path | Default | `origin` (= mprov-ng) head |
|---|---|---|---|
| mprov_control_center | `/local/projects/mprov-maint/mprov_control_center` | `main` | `6afb41436df003f04a6cf00c09c6ea7121bc2f30` |
| mprov_jobserver | `/local/projects/mprov-maint/mprov_jobserver` | `main` | `b07393d39256707d743db7490d7d33c244f195a4` |
| mprov_scripts | `/local/projects/mprov-maint/mprov_scripts` | `master` | `eb806171457b2c9494488e1fe44b01fa4247eb38` |
| mash | `/local/projects/mprov-maint/mash` | `master` | `36b6a5efc68fa620812b401a412a469bdb6dcf3f` |

### Historical topology (superseded 2026-10-23, kept for audit)

Originally (kanban t_f46200db) each clone had `origin = biondogs/<repo>`
and `upstream = mprov-ng/<repo>`, with fork heads
CC `7384c63`, JS `00d00bfd`, SCR `aae84ee`, MASH `f9bb463` — each exactly 1
commit ahead of upstream (the Oct-15 openwiki docs sweep commit; no
fork-side product-code divergence).

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
