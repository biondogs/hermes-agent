# MPROV-TESTENV — Persistent local test environments for the mprov-ng repos (ga01)

Status: **live** since 2026-10-23 (kanban t_3f878612, sw-devops). Replaces the
per-card ephemeral scratch envs. Local infra only — no upstream changes.

## What exists, where

Host: **ga01**. Everything lives under `/local/projects/mprov-testenv/`:

| Path | What |
|---|---|
| `mprov_control_center/` | fresh clone, mprov-ng main @ `781ac6f` (2026-10-23) |
| `mprov_jobserver/` | fresh clone, mprov-ng main @ `df027c6` (2026-10-23) |
| `mash/` | fresh clone, mprov-ng main @ `36ef120` (2026-10-23) |
| `mprov_scripts/` | fresh clone, mprov-ng main @ `a44f519` (2026-10-23) |
| `ops/compose.yaml` | the stack definition (runtime only; builds are scripted) |
| `ops/build-images.sh` | builds all five images from the repos' native definitions |
| `ops/run-tests.sh` | one-command full-suite runs per repo, logs to `ops/logs/` |
| `ops/mash/Dockerfile`, `ops/scripts/Dockerfile` | glue for the two repos with no native Dockerfile (mirrors their CI; kept OUT of the repos) |
| `ops/js-runner-profile/` | CI-parity mask files for the js-tests container (see Known gaps) |

Docker objects (all prefixed so they are unambiguous):

- Images: `mprov-testenv/cc:main` (repo Dockerfile), `mprov-testenv/js:main`
  (repo Dockerfile + locally built wheel in `dist/`), `mprov-testenv/js-tests:main`
  (repo `tests/Dockerfile`), `mprov-testenv/mash:main`, `mprov-testenv/scripts-runner:main`.
- Containers: `mprovtestenv-cc`, `mprovtestenv-js-tests`, `mprovtestenv-mash`,
  `mprovtestenv-scripts-runner` — all `restart=unless-stopped`.
- Network: `mprov-testenv` (own bridge, **no published host ports** — zero
  collision surface with prod/services on ga01).
- Volume: `mprov-testenv_cc-etc-mprov` (CC secret key + apikey persist).

`/local/projects/mprov-maint` clones were not touched, and no repo file was
modified (`dist/` in the jobserver clone is a gitignored build artifact, as
in upstream CI).

## How each env is built (native tooling first)

| Repo | Image source | Test invocation (same as the repo's CI) |
|---|---|---|
| mprov_control_center | repo `Dockerfile` (Rocky 8.8 / py3.8 venv) — exactly what CI's `test-and-publish-dev.yml` builds | `manage.py check && manage.py test` inside the container, with a generated `SECRET_KEY` |
| mprov_jobserver | repo `Dockerfile` (Rocky 8.8, wheel built per `dockerimage-dev.yml`) → repo `tests/Dockerfile` on top | repo `tests/Dockerfile` ENTRYPOINT: `python3 -m pytest -v -p no:cacheprovider /tests` |
| mash | no Dockerfile in repo → `ops/mash/Dockerfile` mirrors `tests.yml` (py3.11 + requirements + pytest) | `python -m pytest -v tests` (matches `tests.yml`) |
| mprov_scripts | no Dockerfile for the runner → `ops/scripts/Dockerfile` mirrors `tests.yml` (py3.11 + pytest + docker CLI); the Rocky 9 image the scripts run in is built by the repo's own `tests/Dockerfile` at test time | `python -m pytest -v tests` in the runner container, which drives the host docker daemon over the mounted socket (what its CI does natively) |

## Start / stop / restart

```bash
cd /local/projects/mprov-testenv

# ensure the stack is up (safe to re-run; recreates only if config changed):
docker compose -f ops/compose.yaml up -d

# stop the whole stack (data: images + cc volume survive; container fs does not):
docker compose -f ops/compose.yaml stop
docker compose -f ops/compose.yaml start     # come back

# full teardown (REQUIRES operator go — this stack only, never `docker system prune`):
docker compose -f ops/compose.yaml down
docker volume rm mprov-testenv_cc-etc-mprov   # only if the seeded CC db/keys are unneeded
# images are not removed by `down`; delete with:
docker rmi mprov-testenv/cc:main mprov-testenv/js:main mprov-testenv/js-tests:main \
           mprov-testenv/mash:main mprov-testenv/scripts-runner:main

# rebuild after pulling repo updates:
cd mprov_control_center && git pull && cd ..
cd mprov_jobserver && git pull && rm -rf dist && cd ..      # wheel must be rebuilt from new sources
cd mash && git pull && cd ..
cd mprov_scripts && git pull && cd ..
bash ops/build-images.sh && docker compose -f ops/compose.yaml up -d
```

`restart=unless-stopped` means the stack also survives ga01 reboots / daemon
restarts with no action. The containers are keepalives except `cc`, which runs
the image's native CMD (`init_mpcc.sh` → migrate/seed → apachectl FOREGROUND);
readiness check: `docker exec mprovtestenv-cc curl -sk https://localhost/` → 200.

## Run the tests

```bash
cd /local/projects/mprov-testenv/ops
bash run-tests.sh all            # or: cc | js | mash | scripts
# per-suite logs land in ops/logs/<repo>-<timestamp>.log; non-zero exit = any failure
```

Under the hood (what the script execs):

```bash
# cc — CI-parity invocation from test-and-publish-dev.yml
docker exec mprovtestenv-cc bash -c 'cd /var/www/mprov_control_center && . bin/activate && \
  export SECRET_KEY="$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")" && \
  python manage.py check && python manage.py test'

# js
docker exec mprovtestenv-js-tests python3 -m pytest -v -p no:cacheprovider /tests

# mash
docker exec -w /app mprovtestenv-mash python -m pytest -v tests

# scripts (builds/runs Rocky 9 containers via the mounted docker socket)
docker exec -w /local/projects/mprov-testenv/mprov_scripts \
  mprovtestenv-scripts-runner python -m pytest -v tests
```

## Verification receipt (2026-10-23, full suites, all green)

| Repo | Result | Suite |
|---|---|---|
| mprov_control_center | **Ran 163 tests — OK** (manage.py check clean) | 13.0 s |
| mprov_jobserver | **158 passed, 16 xfailed, 0 failed** | 4.6 s |
| mash | **31 passed, 2 skipped** | 1.4 s |
| mprov_scripts | **20 passed** (Rocky 9 script containers included) | 11.8 s |

The 16 jobserver xfails are upstream-declared `strict` xfails for known issues
(#147/#148 etc.) and are green in the sense that CI defines green.

## Resource footprint (measured idle, 2026-10-23)

- Images: ~8.1 GB total (cc 2.13, js 2.52, js-tests 2.61, mash 0.24, scripts-runner 0.58).
- Containers idle: ~138 MB RAM (cc 127.5 MiB running Apache; the three
  keepalives ~2–5 MiB each), CPU ~0 %.
- Disk I/O while testing only; Rocky 9 script-image build is cached in the
  daemon after first run. `/local` has 20 T free; no pressure.

## Known gaps / caveats

1. **jobserver CI-parity masks (read before debugging js suite "failures").**
   The jobserver suite implicitly assumes GitHub's idle 4-core runners:
   `test_high_load_skips_the_heartbeat` (strict xfail, #147) only takes its
   KeyError path when `99.0 >= multiprocessing.cpu_count()`, and
   `mprov_webserver.do_GET()` refuses `/images/` when the **real** 5-min
   loadavg >= cpu_count(). On ga01 (256 cores, steady load ~32) the suite is
   not reproducible unmasked. The `js-tests` container therefore bind-mounts
   `ops/js-runner-profile/cpu-online` over `/sys/devices/system/cpu/online`
   (cpu_count→4) and `cpu-loadavg` over `/proc/loadavg` (load→0.00), exactly
   emulating an idle CI runner. No test asserts on real host loadavg (every
   getloadavg() reader in the suite is monkeypatched). If the masks are ever
   removed, expect 1 failure at 256 cores; if ga01 load ever exceeded 99 the
   webserver tests could still flake before the mask's 0.00 loadavg makes
   that impossible — the mask is what makes this hermetic.
   Upstream filing candidate (out of scope here): the two #147 tests conflate
   machine size with test expectations.
2. **CC sqlite DB lives on the container fs** (`db/db.sqlite3`), as upstream's
   image ships it. It survives `stop/start` and reboots, but a `down`/recreate
   re-runs first-run init (fresh admin/admin superuser + fixtures; apikey is
   regenerated). Secret key + apikey files persist via the named volume.
   Tests do not depend on the seeded DB (`manage.py test` uses its own test db).
3. **scripts-runner needs the docker socket.** Its suite inherently builds and
   runs containers (that IS the repo's test design); child containers run
   `--rm`, no ports, on the default bridge, and are gone when tests end.
4. **mash env pins py3.11** (middle of the CI matrix); CI also covers 3.9/3.13,
   not reproduced here.
5. **js runtime container not run.** `mprov-testenv/js:main` exists (image
   chain + daemon parity), but the jobserver daemon needs a live mPCC + DHCP
   config to do anything; this env is test-scoped. The tests image contains the
   same runtime.
6. **Restart drill partially gated.** `docker compose up -d` after a config
   change was exercised (js-tests recreated + suite re-green). Full
   `stop`→`start` cycling was not exercised in the setup session because
   unattended sessions gate container-lifecycle commands; policy
   (`restart=unless-stopped`) verified via inspect.
7. **Pinned mains.** Clones track main @ 2026-10-23; refresh with the pull +
   rebuild recipe above (rebuild the js wheel — `rm -rf mprov_jobserver/dist`).
8. Pre-existing docker objects NOT owned by this stack and never touched:
   `ghcr.io/mprov-ng/mprov-control-center:dev`, exited `cc319-*` containers,
   `mprov-js-local` / `mprov-js-tests` / `mprov-scripts-test` images from
   earlier cards (can be reclaimed once this env is accepted).
