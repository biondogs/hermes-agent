# NO-SELF-GATE mechanical enforcer — receipts (card t_ad14438a, operator GO 2026-10-28)

Law: NO-SELF-GATE (R6), `docs/gate-wait-pattern-2026-10-28.md` @ 31d5b4b; operated as fleet
law via GOVERNANCE G-02 extension (t_1a66c496). This deliverable = MECH-A scope items 1-4.

## Deliverable

- `scripts/no-self-gate-enforcer.py` — installed at `~/.hermes/scripts/no-self-gate-enforcer.py`
  (byte-identical, sha256 `1a9f830f0929b844`-prefixed full hash below). SYSTEM crontab entry
  (every minute, flock-guarded, gateway-independent — wake-driver/dead-man pattern):

  ```
  * * * * * flock -n $HOME/.hermes/scripts/.nsg-enforcer.lock /usr/bin/python3 $HOME/.hermes/scripts/no-self-gate-enforcer.py >> $HOME/.hermes/logs/nsg-enforcer.log 2>&1
  ```

- Coverage: default board DB + every `~/.hermes/kanban/boards/*/kanban.db` (auto-discovered).
- Detection: R6.1 gate-declaration regex (title: qualifier-gate `[distiller|text|review|auditor|audit|ship|code|qa|re]` + `:`/em-dash/hyphen/EOS, or bare `GATE:`; body markers `^Gate for|`, `## Assignee: distiller|sw-reviewer`, "independent … gate on", `^VERDICT:`; law/meta cards excluded). Author set = gate creator ∪ parents+body-referenced work cards' {created_by, assignee, completed-run profile}; butlers/orchestrator/decomposer filtered (they route, not author). Violation kinds: self-assigned / author-gate / unassigned.
- Enforcement (supported `hermes kanban` CLI mutators only, never raw SQL):
  - INTAKE refusal (active, created ≥ law TS): exact R6.4 text `misassigned gate — reassign to <profile>` comment + mechanical `reassign` to distiller/sw-reviewer, `--reclaim` if running (in-flight author self-gate refused before verdict). Undeterminable profile → comment + `block needs_input` + operator alert.
  - SELF-PASS VOID (done, completed ≥ activation TS — retro-exempt): R6.3 mechanically — void annotation on gate + released apply legs, legs blocked, voided gate unlinked, gate re-filed independently (`--created-by nsg-enforcer`), legs reparented + unblocked (todo-gated until fresh PASS). Verdict excerpt quoted in the receipt.
- Idempotence: state file `~/.hermes/state/nsg-enforcer.state` + `[NO-SELF-GATE-ENFORCER` marker-comment double-check; per-board EXCEPTIONS; daily heartbeat line (silent log = provably healthy).
- Operator alerting: alert-sink.sh on every action (TG DM + private GH issue, dedupe tag `nsg-enforcer`).
- Selftest: `--selftest` = 18 checks incl. the t_fecde306 incident fixture (detected self-assigned, author derived from body-referenced work card, marker suppression). ALL PASS at deploy.
- Fence-hardening discovered during deploy: `cli()` scrubs inherited `HERMES_DELEGATED_CHILD_CONTEXT`/board-scope env vars so hand-run and crontab runs behave identically (first manual run without this failed all mutations; documented, re-run succeeded end-to-end).

## Which half landed where (scope item 3)

- **Board-tooling half (LANDED HERE):** detection + refusal + void within ≤1 cron tick (60 s), all boards, gateway-independent. Proven below.
- **Kernel-native half (filed upstream, not approximated):** 0-second refusal at claim/complete inside the kanban kernel is impossible from the board layer (kernel = hermes-agent). Comms-clean FR staged at `~/.hermes/patches/upstream-fr-kanban-self-gate/` (title sha256 `42aaac1c840161005d148bf92d4d9e916cbd73f459b60f2dda1c7983ba86d90f`, body sha256 `615a404d6a00ac0246281a1f04ece96c7f39de2bb21ac2ee75b9aa1800120de9`, leak-scan 0). Duplicate pre-flight done: neighbors #135749 / #97910 / #95141 / #138403 disclosed in-body. Filing routed through the chain: distiller gate card t_db1d358f (parents=[t_ad14438a]) → operator-GO submit card t_906c6152 (parents=[t_db1d358f]) — full Final-Gate law; NOTHING is filed upstream from this card.
- **Known residual (recorded, not papered over):** R6.2 check-set relaxation is not mechanically detectable at the board layer (no structured check-set data) — doc-law + gate-PASS discipline + the FR's `gate` metadata direction cover the long term. Mech-B hold card t_a044b6aa remains gated on this proof, as ruled.

## Canary proofs (scope item 4)

**C2 — void arm (R6.3), deterministic one-shot run 2026-10-29T02:03-02:04Z:**
- Staged: t_7f16b9a2 "DISTILLER GATE" self-assigned (created_by == assignee == kanban-board-architect), VERDICT: PASS comment + completed (done) — exact t_fecde306 shape; apply leg t_06311921 parented on it.
- Enforcer fired: VOID-ARM self-assigned; void comment on t_7f16b9a2 quoting the verdict; leg t_06311921 stopped+commented, unlinked; RE-GATE t_405d2e8d created (created_by nsg-enforcer, assignee distiller) and linked as the leg's true parent; leg unblocked → todo-gated.
- Dispatcher accepted the mechanical re-gate: distiller completed it independently; leg then promoted and was completed by sw-docs. Full chain: self-PASS → void → independent re-gate → fresh release.

**C1 — intake refusal arm (R6.4), LIVE crontab path 2026-10-29T02:05Z:**
- Staged: t_b6c002de "DISTILLER GATE" created self-assigned (blocked so no dispatch race).
- The 02:05:02Z CRON TICK caught it in <60 s: comment `misassigned gate — reassign to distiller` + mechanical reassignment (assignee now distiller). After canary-only unblock, distiller ran the gate independently and issued its own VERDICT: PASS receipt.

**Control — negative control t_491e0587:** self-assigned card saturated with gate vocabulary (NO-SELF-GATE, self-gate, dependency gate, gateway, gated-work) — **zero** enforcer actions across 3+ live ticks (02:05–02:08Z; marker-comment count = 0), then completed as receipt. Declaration regex does not over-fire on law/chat vocabulary.

**Live-cadence + clean-scan receipts:** dry-run over ALL boards pre-deploy = clean scan, 0 violations (no false positives on ~6k live cards). Post-deploy log: `02:05:02Z INTAKE-ARM`, `02:05:09Z enforced 1`, `02:06:01Z heartbeat: clean scan, 0 violations` (subsequent ticks silent by design — log carries actions + one heartbeat/day).

**Alert receipts (critical-alerts.log):** `22:03:28 alert-sink[nsg-enforcer]: TG sent` + `GH issue #10 created`; `22:04:08 TG sent` + `GH comment on issue #10` (dedupe works; first alert corresponds to the fence-hardening failed attempt, receipted here truthfully — that attempt's mutations all failed pre-write and its state stamp was cleared before the clean re-run).

## Enforcement actions on canaries (all accounted above)

| card | canary | action |
|---|---|---|
| t_7f16b9a2 | C2 void arm | R6.3 void comment (fake self-PASS) |
| t_06311921 | C2 apply leg | stop comment + block + re-link to t_405d2e8d + unblock |
| t_405d2e8d | C2 re-gate | created by enforcer, distiller, completed independently |
| t_b6c002de | C1 intake | R6.4 refusal comment + reassign to distiller (cron path) |
| t_491e0587 | control | none (proven), completed as receipt |

## G-30 note

Fleet-infra provisioning (new system-cron script + crontab line) following the wake-driver precedent
(t_ce6087a1) / dead-man precedent (t_6d5d076f): ZERO SOUL/config/dispatcher/litellm surface (no G-30
carrier text changed; no profile touched; no board DB written directly). State: activation stamp +
handled map in `~/.hermes/state/nsg-enforcer.state`. Rollback: remove crontab line + script; canary
cards remain as receipts; enforcer actions are reversible per-card (reassignments/blocks recorded).

## Enforcer sha256 (deployed)

1a9f830f0929b844… (full: see `sha256sum scripts/no-self-gate-enforcer.py` at this commit; deployed
copy byte-identical, verified at install).
