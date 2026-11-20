# Hermes Estate Twin — synchronized live-estate mirror container

**Card:** `t_9953d256` · **Parent:** `t_f120564c` (BOARD-LAYERS-0-HARNESS)

A standing container that mirrors the LIVE Hermes estate — the running
`hermes-agent` checkout (with local hotfix commits) plus the estate configuration
tree (profiles, SOULs, skills, kanban boards, cron, `hermes-estate` docs) — kept
synchronized on a cadence so feature-porting, hotfix-rebase, and estate CI work
can be exercised against an exact replica **without touching the live system**.

## Live-estate-is-read-only rule

> **The twin NEVER writes to the live estate.** Every sync is a read-only
> `git clone` / `rsync` / `sqlite3 .backup` from the live paths into
> `twin-root/` on disk. The container sees only that copy via bind-mounts.
> Nothing in this directory touches `~/.hermes`, `~/.hermes/hermes-agent`,
> `~/hermes-estate`, or any live DB.

## Layout

```
ci/hermes-estate-twin/
  README.md               — this file
  Dockerfile              — twin image (deps baked, NO estate data baked)
  docker-compose.yml      — isolated network, bind-mounts twin-root
  .dockerignore
  Makefile                — build/up/down/shell/test/rebase-check helpers
  twin-root/              — mirror on disk (gitignored, bind-mounted read-only
                            for code, read-write for hermes runtime)
    hermes-agent/         — git clone of the live checkout incl. all branches
    hermes-home/          — rsync mirror of ~/.hermes (scrubbed)
    hermes-estate/        — git clone of ~/hermes-estate
    snapshots/            — consistent sqlite .backup snapshots of kanban DBs
    STATUS.json / STATUS.md
    .quarantined          — present only when scanner found a secret
  sync/
    sync.sh               — main sync (hourly + manual sync-now)
    scrub.sh              — secret scrubbing (EXCLUDE + SCRUB lists)
    scan.sh               — post-sync secret scanner (fails+quarantines)
    verify.sh             — post-sync verification (profiles, git sha, configs)
    exclude-list.txt      — explicit rsync exclude list (authoritative)
    scrub-rules.yaml      — per-file placeholder replacements
    scan-patterns.txt     — regex set for the scanner
  systemd/
    hermes-estate-twin-sync.service
    hermes-estate-twin-sync.timer   — hourly
  scripts/
    twin-shell            — open a shell in the twin container
    twin-test             — run the twin checkout's test suite inside twin
                            (offline: hands run_tests.sh HERMES_PYTHON=/usr/bin/python3)
    twin-clone-test       — test a specific ref in an isolated in-twin repo,
                            offline, with a self-identifying TWIN-RECEIPT log
    twin-rebase-check     — dry-run rebase of hotfixes onto upstream ref
    sync-now              — manual sync trigger (wraps sync.sh)
    probe-isolation.sh    — network-isolation probe
  tests/
    test_scrub_canary.sh  — seeded canary secret proves scanner blocks
    test_isolation.sh     — isolation probe test
```

## Quick start

```bash
cd ci/hermes-estate-twin

# First-time: sync twin-root from live estate, build image, start container
make sync          # or ./scripts/sync-now
make build
make up

# Daily use
./scripts/twin-shell                          # shell in twin
./scripts/twin-test                           # run tests in twin
./scripts/twin-rebase-check origin/main       # dry-run rebase

# Manual sync
make sync          # re-sync twin-root from live, re-verify, update STATUS

# Teardown
make down          # docker compose down -v (only this stack)
```

## Sync — what is included

| Source (live, read-only)              | Destination (`twin-root/`) | Method |
|---------------------------------------|----------------------------|--------|
| `~/.hermes/hermes-agent` (all branches, hotfix commits) | `hermes-agent/` | `git clone --mirror` + `git fetch` + checkout of live HEAD |
| `~/.hermes` tree (profiles, skills, cron, kanban boards metadata) | `hermes-home/` | `rsync -a --delete` with `exclude-list.txt` |
| `~/hermes-estate`                     | `hermes-estate/` | `git clone` + `git fetch` |
| `~/.hermes/kanban.db` + `~/.hermes/kanban/boards/*/kanban.db` | `snapshots/` | `sqlite3 .backup` (consistent snapshot) |

Regenerable bulk excluded (same rationale as `estate-sync.sh`): `installs/`,
`tools/`, `bin/`, `cache/`, `logs/`, `hjobs/`, `*.db-wal`, `*.db-shm`,
`*.lock`, `*.sock`, `workspaces/`, `lsp/`, `audio_cache/`, `image_cache/`.

Secret material excluded/scrubbed — see `sync/exclude-list.txt` and
`sync/scrub-rules.yaml`.

## Secret stripping

1. **Exclude** — files that must never enter the twin at all (`.env` with real
   values, `auth.json`, `hosts.yml`, kubeconfigs, SSH keys) are in
   `sync/exclude-list.txt` and dropped by rsync.
2. **Scrub** — config files that must parse but must not carry real secrets
   have their secret keys replaced with `__TWIN_PLACEHOLDER__` per
   `sync/scrub-rules.yaml`.
3. **Scan** — `sync/scan.sh` runs after every sync: a regex scanner over the
   entire `twin-root/` for live-looking secrets. On hit it writes
   `twin-root/.quarantined`, refuses to start the container, and exits non-zero.
   Proven by `tests/test_scrub_canary.sh`.

Never read secret VALUES into logs or cards — names only.

## Network isolation

The compose file puts the twin on a dedicated bridge with `internal: true`:
no route to the host network, gateway, LiteLLM/orb, Hindsight, Telegram, or
live kanban DBs. Kanban DBs are snapshot copies; the twin's gateway cannot
start with real tokens (placeholders only). Verified by
`scripts/probe-isolation.sh` and `tests/test_isolation.sh`.

## Verification after each sync

`sync/verify.sh` checks:

- `hermes profile list` inside twin equals live profile set
- config validation passes for all profiles (`hermes config validate` / yaml parse)
- `git log -1` of twin `hermes-agent` checkout equals live HEAD

Results written to `twin-root/STATUS.json` and `twin-root/STATUS.md`.

## Timer

Hourly sync via `systemd --user`:

```
hermes-estate-twin-sync.timer   — OnCalendar=hourly
hermes-estate-twin-sync.service — ExecStart=.../sync/sync.sh
```

Install:

```bash
mkdir -p ~/.config/systemd/user
ln -sf $(pwd)/systemd/hermes-estate-twin-sync.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hermes-estate-twin-sync.timer
systemctl --user status hermes-estate-twin-sync.timer
```

Long steps inside the twin use `hjob` (estate long-job rule G-29).

## Running tests offline in the twin (card t_42ab1cec)

The twin has no route to GitHub, so a checkout's `scripts/run_tests.sh` dies
when it tries to stage uv (`run-in-hermes-env`), and the twin checkout's
`.venv` symlinks to a host path. Never fall back to the host. Use the image's
baked interpreter instead:

```bash
# a specific ref (preferred): isolated repo in the container's /tmp, twin work tree untouched
~/.hermes/scripts/hjob start <card> --name <run> -- \
  ./scripts/twin-clone-test --repo <git dir> --ref <rev> --out <dir> --name <run> -- tests/<file>.py
# the twin checkout as synced
./scripts/twin-test
```

Both run `HERMES_PYTHON=/usr/bin/python3 scripts/run_tests.sh` (the repo's own
hermetic per-file runner, no uv staging); `twin-clone-test --raw` runs one
`/usr/bin/python3 -m pytest` process instead. A test receipt may be called a
"twin" run only if its log shows that it ran in the container (the
`TWIN-RECEIPT v1` header, or the in-container interpreter/rootdir/hostname). A
log showing `/home/arch/...` paths is a host run and must be labeled as one. The
full rule is in `docs/CI-CONTAINERS-GUIDANCE.md` §5a/§6a.

## Teardown

```bash
make down
# or directly:
docker compose down -v
```

Only the twin stack is affected. The qwen38 production container and every
other board's stack are never touched.
