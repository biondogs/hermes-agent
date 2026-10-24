# BUTLER-DECISION-PROMPT-E2E ACCEPTANCE — t_cab52849
Date: 2026-10-24, 02:23–02:45 EDT | Executor: kanban-board-architect | Oracle card: t_cab52849 (default board)
Gates: BUTLER-CLARIFY-ENABLE (t_6feb021e, done) + SKILL-FALLBACK-TIGHTEN (t_39b67a87, done)

## Verdict: **PASS 5/5 — every butler delivers blocked-decision clarify cards from a fresh post-bounce session.**

Precondition proved: the gateway bounced at ~02:23 EDT (operator bounce; run-97 of this card
crashed on "Gateway disconnected" during it); all five butler Telegram adapters reconnected
02:24:21–02:25:15 ("✓ telegram connected (profile: <butler>)" ×5, gateway.log), so every wake
below ran on a post-bounce agent instance. Attempt-97 left zero probe residue; this run started
clean.

## Matrix (per-card criteria)

Criterion (1) = butler-blocked-decision-prompt loaded/visible in the fresh session;
(2) = clarify in the live toolset; (3) = synthetic blocked-decision delivered as an
interactive clarify card via that butler's own bot.

| butler | board | probe card | (1) skill | (2) clarify | (3) interactive card | ruling | fresh-agent marker |
|---|---|---|---|---|---|---|---|
| g01-butler | gargantua01 | t_36bf8266 | PASS | PASS | PASS | 🚀 Rocket | runtime_rev 7→8 |
| g02-butler | gargantua02 | t_1c09cf0a | PASS | PASS | PASS | 🚀 Rocket | runtime_rev 22→23 |
| gaudi-butler | gaudi | t_147acdcf | PASS | PASS | PASS | 🚀 Rocket | runtime_rev 17→18 |
| swco-butler | software-co | t_74404c2a | PASS | PASS | PASS | 🚀 Rocket | runtime_rev 205→206 |
| sjproto-butler | skipjack-prototype | t_4c7f0529 | PASS | PASS | PASS | 🚀 Rocket | session born 01:48; wake served by post-02:23 gateway |

## Evidence trail

**Toolset layer.** Each butler's telegram DM session `tool_names` hash resolves to a stored
tools JSON containing a `clarify` function — 24 tools, clarify present, 5/5 (evidence_layer.py).
Resolver (hermes_cli.tools_config._get_platform_tools) unchanged since t_6feb021e's PASS 5/5.

**Freshness.** Pre-fire vs post-wake `runtime_revision`/`runtime_generation` bumped +1 on
g01/g02/gaudi/swco (agent rebuild at wake); sjproto's session was created 01:48 and its 02:31
wake ran in a gateway process started 02:23 — fresh by construction. `tool_same=True` everywhere
(toolset content identical across the bounce, as expected — configs unchanged).

**Delivery chain (identical shape ×5), e.g. gaudi @ 02:31:**
```
02:30:58 gateway: derived to board owner ... board gaudi re-stamped from default to gaudi-butler
02:30:58 gateway: woke agent for t_147acdcf ... profile=gaudi-butler events={'blocked'}
02:31:06 butler: kanban_show t_147acdcf (probe body read; no investigation attempted)
02:31:13 butler: clarify {"questions":[{"choices":["🚀 Rocket","🛰️ Satellite","🧭 Compass"],
              "question":"Synthetic probe decision (t_147acdcf — fresh-session E2E test...)..."}]}
02:31:27 result: {"status":"answered","user_response":"🚀 Rocket","outcome":"submitted"}
02:31:34 butler: kanban_comment — ruling stamped on the probe card
```
All five clarify calls conformed exactly to butler-blocked-decision-prompt v1.1.0: one decision,
3 choices ordered best-first (Rocket first), no hand-rolled Other (UI auto-appends), question text
carried the probe id. Operator answered all 5 cards on Telegram within ~30 s (🚀 Rocket ×5).
Wake lines 02:30:57–02:31:10, re-stamped to the board owner on all 5 (F22 derivation re-verified
on fresh post-bounce traffic).

**Ruling stamps read back:** g01 #36, g02 #614 (full body: "ruling = 🚀 Rocket … submitted via
Telegram"), gaudi #481, sjproto #2 — all verified. swco-butler did NOT stamp a new comment;
see observation 1.

## Observations (not FAILs; no defect cards filed)

1. **swco-butler receipt-slip:** after its (correct) clarify call and the operator's answer, it
   replied "Already handled — … ruled 🚀 Rocket … stamped on t_74404c2a (comment 613)", citing a
   stale comment number from the 02:13 t_9352cfb0 probe, and stamped nothing. All three matrix
   criteria still PASS (its clarify card was delivered and answered); the probe owner stamped the
   receipt instead (its owner-receipt comment happened to land as comment #613 on software-co).
   Behavioral note only — the butler conflated the new probe with the archived one on a repeat
   blocked-notification wake.
2. **Skill master-vs-tree drift:** all 5 butler trees carry the t_6feb021e corrected
   both-locks remediation hint (md5 5e51acf274a…) while the root master
   (~/.hermes/skills/devops/butler-blocked-decision-prompt/SKILL.md) still carries the pre-fix
   single-lock hint (aaf82f1a… — t_39b67a87's 02:04 sync point). Trees (5/5 identical) are what
   butler sessions load, so acceptance is unaffected. The nightly skill-curator does not do
   master→profile content sync (evolution candidates + safe frontmatter fixes only; destructive
   moves are operator-gated), so no auto-revert risk tonight; master should be brought up to the
   both-locks text at the next skill meta-work touch.

## Cleanup
5/5 probe cards archived, subs purged 5/5, wakes after archive delivery: 0 → residue verdict
**CLEAN** (residue_check.py). Probe owner receipts stamped on each card pre-archive
(#37 / #615 / #482 / #3 / #613).

## Artifacts (workspace t_cab52849)
`baseline_sessions.py` / `baseline_freshness.py` (pre-fire snapshots) · `evidence_layer.py`
(tools-JSON clarify proof) · `probe_fire.py` (fire/verify/cleanup, F22-sanctioned clean-env pattern)
· `probe_state.json` (probe ids + gateway.log byte offsets) · `scan_clarify_calls.py` /
`swco_trace.py` (transcript receipts) · `verify_stamps.py` / `verify_stamps_v2.py` (ruling
read-back) · `cleanup.py` / `residue_check.py` · this receipt.
