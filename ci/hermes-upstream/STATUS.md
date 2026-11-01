# hermes-upstream — STATUS

_Last rebuild: 20261101-161000 UTC · upstream `c627ec84664d43e0b18b95d9d86d8963747d56c7`_

| Field | Value |
|-------|-------|
| Upstream SHA | `c627ec84664d43e0b18b95d9d86d8963747d56c7` (`c627ec8`) |
| Subject | c627ec8466 perf(desktop): ignore root geometry in theme observation |
| Dated tag | `hermes-upstream:20261101-c627ec8` |
| Result | **green** (pass) |
| Tests | 114 passed / 0 failed (total 114) |
| Fresh age | 0h (created 2026-11-01T16:04:51.105883844Z) |
| Fresh SHA | `unknown` |
| Drift | fresh sha unknown; upstream is c627ec8 |
| Keep | 7 dated images |

## Health

✅ fresh is green

- `hermes-upstream:fresh` — stable tag for CI (only updated on green).
- `hermes-upstream:last-green` — previous green (same as fresh after a green build).
- Dated tag `hermes-upstream:20261101-c627ec8` always exists (even on red) for diagnosis.
- On failure, check `/local/projects/software-co/ci/hermes-upstream/status.json` and `docker logs` / build log above.

## Retention

Last 7 dated images kept; older pruned on each rebuild. `fresh`/`last-green` are never pruned.

## Manual trigger

```bash
./ci/hermes-upstream/rebuild.sh
# or
systemctl --user start hermes-upstream-rebuild.service
```
