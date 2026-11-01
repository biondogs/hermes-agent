# hermes-upstream — always-fresh upstream Hermes container

Standing CI image rebuilt from `NousResearch/hermes-agent` `origin/main`.

## What it is

- **Source:** `hermes-board-layers/` clone of `NousResearch/hermes-agent` (fetched nightly).
- **Image:** `hermes-upstream:fresh` — only updated when the test suite is green.
- **Tags:** `hermes-upstream:YYYYMMDD-<sha7>` (dated, always written), `hermes-upstream:fresh`, `hermes-upstream:last-green`, `hermes-upstream:candidate` (build-time).
- **Isolation:** stub LLM (`sk-harness-stub-not-a-secret` / `http://127.0.0.1:1/v1`), throwaway `HERMES_HOME`, `--network none` for tests, no live estate contact.

## Usage

### Rebuild (manual)

```bash
./ci/hermes-upstream/rebuild.sh
# or via systemd unit:
systemctl --user start hermes-upstream-rebuild.service
# via hjob (long-job rule):
~/.hermes/scripts/hjob start t_e26d9c1f -- ci/hermes-upstream/rebuild.sh
```

### Run a branch against fresh

```bash
./ci/hermes-upstream/run-branch.sh ./hermes-board-layers
./ci/hermes-upstream/run-branch.sh /path/to/worktree -- -k test_kanban -q
./ci/hermes-upstream/run-branch.sh ./hermes-board-layers tests/cron/test_kanban_dispatcher.py -q
```

Mounts the clone into `hermes-upstream:fresh` with a throwaway `HERMES_HOME` and runs `pytest`. No host `~/.hermes` is touched.

### Health

```bash
./ci/hermes-upstream/health.sh
cat ci/hermes-upstream/STATUS.md
cat ci/hermes-upstream/status.json | python3 -m json.tool
```

Reports: age of `fresh`, last build result, drift (commits since last green). Failures leave a visible `STATUS.md` (never silence).

## Scheduling

`systemd --user` timer `hermes-upstream-rebuild.timer` — nightly 03:30 UTC (randomized 15m), `Persistent=true` so missed runs catch up.

Install:

```bash
mkdir -p ~/.config/systemd/user
cp ci/hermes-upstream/systemd/hermes-upstream-rebuild.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hermes-upstream-rebuild.timer
systemctl --user list-timers hermes-upstream-rebuild.timer
```

Logs: `journalctl --user -u hermes-upstream-rebuild.service` and `~/.hermes/hjobs/hermes-upstream-rebuild/rebuild.log` (if using hjob).

Do NOT add a crontab entry — the timer is the scheduler.

## Retention

Last `HERMES_UPSTREAM_KEEP` dated images kept (default 7). Older `hermes-upstream:YYYYMMDD-*` images are pruned on each rebuild. `fresh`/`last-green`/`candidate` are never pruned.

## Status artifacts

- `ci/hermes-upstream/status.json` — machine-readable (upstream sha, test counts, result, drift).
- `ci/hermes-upstream/STATUS.md` — human-readable, includes health badge and retention note.

Both are written on every run, green or red. A red build does NOT update `fresh`.

## Reset

```bash
# Remove all hermes-upstream images
docker images --format '{{.Repository}}:{{.Tag}}' | grep '^hermes-upstream:' | xargs -r docker rmi
# Rebuild from scratch
./ci/hermes-upstream/rebuild.sh
# Reset timer
systemctl --user restart hermes-upstream-rebuild.timer
```

## Dockerfile reuse

`ci/hermes-upstream/Dockerfile` reuses `hermes-board-layers/dev/board-layers-harness/Dockerfile` (same base, same deps, same isolation). Build context is the upstream clone.
