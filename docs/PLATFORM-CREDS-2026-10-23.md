> Status: current. Canonical registry entry: hermes-estate/docs/GOVERNANCE.md G-05 (2026-10-26).

# PLATFORM-CREDS-POLICE — 2026-10-23 (t_3ea14912)

Operator ruling 2026-10-23 (DM): "On ga01 only the default profile should have access to my
slack and it should not be actively listening to the platform anywhere. Nothing should share
default telegram credentials at all, if the profile isn't associated with default or a butler
it probably shouldn't have telegram at all."

Executor: kanban-board-architect. Host: ga01. Values are never recorded — sha256(value)[:12] only.

## Doctrines enforced

- **D1** Slack creds (SLACK_APP_TOKEN / SLACK_BOT_TOKEN) exist ONLY in default.
- **D2** No slack inbound listener anywhere — default's `platforms.slack.enabled: false` is an
  explicit disable that beats env-credential auto-enable (`gateway/config_env.py`
  `_warn_explicit_disable_beats_env`); creds retained in root `.env` for reads/outbound.
  xoxp user-token posture is INTENTIONAL (standing memory) — not converted, not re-proposed.
- **D3** TELEGRAM_BOT_TOKEN only in default + the five butlers, each a DISTINCT token.
  KANBAN_STREAM_BOT_TOKEN is a separate bot (dedicated kanban-stream plugin) and is out of scope.

## Pre-inventory (before mutation) — profile | file | cred | sha256[:12]

See card attachment `pre-inventory-2026-10-23.txt` (72 rows incl. KANBAN_STREAM_BOT_TOKEN).
In-scope (slack + telegram) grouping:

| cred | sha256[:12] | holders |
|---|---|---|
| SLACK_BOT_TOKEN  | 15c8f7dca491 | default(root) ✓, **coding ✗**, **kworker-muse-probe ✗** |
| SLACK_APP_TOKEN  | 784b3c5b0c7c | default(root) ✓, **coding ✗**, **kworker-muse-probe ✗** |
| TELEGRAM_BOT_TOKEN (main) | 14e57d1b3c42 | default(root) ✓, **coding ✗**, **kworker-muse-probe ✗** |
| TELEGRAM_BOT_TOKEN | b23f421e7336 | g01-butler ✓ (distinct) |
| TELEGRAM_BOT_TOKEN | 69f4ef2e3ceb | g02-butler ✓ (distinct) |
| TELEGRAM_BOT_TOKEN | 64f3fc3eff79 | gaudi-butler ✓ (distinct) |
| TELEGRAM_BOT_TOKEN | 9dda85b91816 | sjproto-butler ✓ (distinct) |
| TELEGRAM_BOT_TOKEN | baa18411712f | swco-butler ✓ (distinct) |
| KANBAN_STREAM_BOT_TOKEN | 8f04fee3ec3a | root + all 61 profile dirs (separate bot; fine per ruling) |

Sweep covered all 62 `~/.hermes/profiles/*/.env` + `config.yaml` and root `.env` + `config.yaml`.
No config.yaml anywhere contained token values; all findings were `.env` lines. The sweep found
exactly the doctor-flagged pairs (#3–#6) and no additional violators.

## Mutations

1. **Backups** → `/home/arch/kanban-backups/platform-creds-2026-10-23/` (0700/0600):
   `coding.env`, `kworker-muse-probe.env`, `default.env`, `default-config.yaml` (cp -p).
2. **Stripped** `^TELEGRAM_BOT_TOKEN=` / `^SLACK_APP_TOKEN=` / `^SLACK_BOT_TOKEN=` lines from
   `profiles/coding/.env` (521→518 lines) and `profiles/kworker-muse-probe/.env` (521→518).
   Both files: 0 in-scope cred lines remain. BUTLER FILES NOT TOUCHED.
   TELEGRAM_FALLBACK_IPS left everywhere (explicitly not a credential; needed by butlers).
3. **D2**: `hermes -p default config set platforms.slack.enabled false` (root config.yaml
   `platforms: slack: enabled: false`). Slack creds retained in root `.env`
   (15c8f7dca491 / 784b3c5b0c7c). Before this change default's slack socket-mode adapter WAS
   actively listening (gateway.log 16:46:54 "Socket Mode connected (1 workspace(s))",
   "✓ slack connected" — the violation D2 targets).
4. **`hermes gateway migrate --multiplex`**: converged — default gateway already multiplexing
   all 63 profiles; zero legacy per-profile gateways to fold in.

## Post-strip inventory (in-scope)

```
default(root)|.env|SLACK_BOT_TOKEN|15c8f7dca491
default(root)|.env|SLACK_APP_TOKEN|784b3c5b0c7c
default(root)|.env|TELEGRAM_BOT_TOKEN|14e57d1b3c42
g01-butler|.env|TELEGRAM_BOT_TOKEN|b23f421e7336
g02-butler|.env|TELEGRAM_BOT_TOKEN|69f4ef2e3ceb
gaudi-butler|.env|TELEGRAM_BOT_TOKEN|64f3fc3eff79
sjproto-butler|.env|TELEGRAM_BOT_TOKEN|9dda85b91816
swco-butler|.env|TELEGRAM_BOT_TOKEN|baa18411712f
```
= exactly D1+D3 compliant. (KANBAN_STREAM_BOT_TOKEN rows unchanged, out of scope.)

## Doctor

Pre-mutation (baseline): 7 issues — #4–#7 all "both hold the same" telegram/slack duplicate
warnings (default⇄coding ×2, default⇄kworker-muse-probe ×2).

Post-strip, pre-restart: **3 issues** — #1 missing-keys notice (pre-existing), #2/#3 npm
vulnerabilities in web/ui-tui workspaces (out of scope per card: wait for upstream lockfile).
**Zero "both hold the same" warnings. No new warnings introduced.**

## Gateway restart + post-restart verification

(Section appended by restart-verify script — see below.)

### Post-restart verification (appended 2026-10-23T15:41:24-04:00 by transient unit `platform-creds-restart-verify`)

```
restart: rc=1 ; gateway after restart: active ; adapters-settled=0
CHECKS: slack_socket=0 slack_conn=0 slack_disabled=0 slack_auth=0 tg_default=0 tg_butlers=0 dupwarn=0 gateway_up=0
getme default: ok=true username=@hermes_m7pbhr5y3t7pndbd_bot
getme g01-butler: ok=true username=@hermes_x7ekkuvwjfq65xc2_bot
getme g02-butler: ok=true username=@hermes_e7qpgliym674gowu_bot
getme gaudi-butler: ok=true username=@hermes_kjrlofdh4ufebfbt_bot
getme sjproto-butler: ok=true username=@hermes_jwgdpmnxsr34d4gd_bot
getme swco-butler: ok=true username=@hermes_gt7qqfll3hr3h3d7_bot
getme kanban-stream: ok=true username=@ga01_kanbanops_23_bot
doctor post-restart: Found 2 issue; 'both hold the same' count: 0
VERDICT: FAIL
```
Full transcript: `~/kanban-backups/platform-creds-2026-10-23/restart-verify.log`;
journal region: `journal-post-restart.txt`; doctor: `doctor-postrestart.txt`.
