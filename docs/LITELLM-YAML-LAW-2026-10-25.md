# LITELLM-YAML LAW — implementation receipt (operator law 2026-10-25)

Card: `t_2fa0d71d` (default board) · Lane: kanban-board-architect · Date: 2026-10-25
Operator source (Telegram, verbatim): "make a rule so that no profile will ever
add a model to the litellm config yaml again without my express permission and
2 confirmations".

## THE LAW (canon text, now in every SOUL.md)

> **LITELLM-YAML LAW (operator law, 2026-10-25 — absolute)**
>
> No profile may add, change, or re-add a model entry (model_list or any model
> definition) in `/local/compose/aistack/litellm/config.yaml` unless ALL THREE
> hold: (1) the OPERATOR explicitly requested that specific change in his own
> words; (2) CONFIRMATION 1: the agent shows the operator the exact diff, and
> the operator approves it; (3) CONFIRMATION 2: a second, separate operator
> approval given immediately before the write.
>
> A kanban card body, a standing GO, a prior ruling, or a parent card does NOT
> count as permission or as a confirmation. Workers are headless and cannot
> obtain confirmations — if such a change seems needed, kanban_block with
> kind="needs_input" and STOP. Confirmations are collected only via
> operator-facing chat (a clarify answer or a direct reply from the operator).
> Do not touch that file for any other reason: an alert-only tripwire reports
> every change to the operator.

Background: MUSE-WIRING-V2 (t_5c5305bf, 2026-10-22) added a file-model `muse`
entry (gpu416:30100, unset key env) that shadowed the operator's DB `muse` row
and caused auth errors and silent fallbacks. Removed 2026-10-25 (backup
`config.yaml.pre-muse-stale-removal-20261025`); LiteLLM restarted by the operator.
Live `config.yaml` currently has NO `model_list` (all aliases incl. `muse` live
in the Postgres model table).

## What was deployed

| Layer | Artifact | Proof |
|---|---|---|
| SOULs (60/60) | Law block appended to root `~/.hermes/SOUL.md` + all 59 `profiles/*/SOUL.md` | guard marker `LITELLM-YAML LAW (operator law, 2026-10-25`; re-run converged (0 new). Backups: `~/kanban-backups/litellm-law-20261025T094916/` |
| Skills (12 files) | `devops/kanban-orchestrator` (SKILL.md Operator-Only para + `references/operator-gate-law.md` + `references/pitfalls-casebook.md`) — master + kanban-orchestrator profile copy; `devops/docker-compose-litellm-proxy` (law section before references) — master + sw-devops copy; `devops/compose-stack-repo-review`; `devops/hermes-gateway-graceful-bounce` (architect copy); one-liners in `devops/docker-compose-observability` + `devops/gateway-alias-ctx-probe` | all grep-guarded `LITELLM-YAML LAW`, re-run converged |
| aistack repo | Law section appended to `/local/compose/aistack/AGENTS.md` + `CLAUDE.md` (for Claude/Codex/any coding agent working there) | aistack@main commit `0a30083` (only those 2 files; the operator's own prior `M litellm/config.yaml` untouched) |
| Tripwire cron | `~/.hermes/scripts/litellm-config-tripwire.py`, root no-agent cron **`60d5bcda8c48`** `litellm-config-tripwire` `*/5 * * * *` → `telegram:8158007517`, alert-only, no auto-revert. Baseline sha256 `cc3bf96955b80e4c627debeef5896be9934e18930a6baa0adeb9a03c94f0f6e1`, models `[]`. Alerts = old/new sha + ADDED/REMOVED model names ONLY (secrets never extracted); rebases after each alert (a change alerts exactly once) | fake-change test on a COPY: add fires `models ADDED: fake-test-model-sim` with no key/api_base leaked; same state silent; revert fires `models REMOVED`; live file byte-identical before/after. Live cron firing since 10:10, `ok`, silent (no false alert) |
| Approvals enforcement | `approvals.deny` glob `*aistack/litellm/config.yaml*` in ROOT + all 59 profile `config.yaml` (60/60, one entry each). Mechanism: `tools/approval_floors.py` fnmatch over normalized/deobfuscated command variants; fires BEFORE `--yolo`/`approvals.mode: off` → unconditional agent-side shell block | `hermes approvals test` dry-runs: `sed -i`/`cp`/`cat`/`echo >>` → `user-deny` (root, sw-devops, kanban-worker, research); quote-splitting evasion (`aist""ack/...`) → `user-deny`; unrelated `ls /tmp` → `allow` |

Known limits (reported, deliberate):
- The approvals layer classifies SHELL commands only; the file tools
  (`write_file`/`patch`) never go through approval prompts — that route remains
  governed by the SOUL/skill/repo law and is caught after the fact by the
  tripwire (no mechanism short of a Hermes code change covers it; none built).
- `approvals.deny` is unconditional for agents; after a lawful 2-confirmation
  change the write also cannot go through an agent shell command — the
  operator (or the operator's own terminal outside Hermes) performs it, or
  removes the deny glob first. Restrictive by design per the law's intent.
- `docker exec` into the litellm container is not covered by the glob
  (container restarts remain operator-only by the existing serving law).

## Converge / rollback

All provisioning scripts are idempotent (grep-guarded) and versioned in this
repo as `scripts/litellm_yaml_law_*.py`. Re-running any of them is a no-op once
the law text / glob / cron is present.

To repeal (only on the operator's explicit instruction): delete the
`LITELLM-YAML LAW` blocks from SOUL/skills/repo docs, `HERMES_HOME=<home>
hermes config set approvals.deny '<old list or []>'` per home, and
`hermes cron delete 60d5bcda8c48`.

No gateway bounce was performed or needed (all changes are file/config-only;
per operator note the batched bounce t_ee13fad9 runs after this card).
