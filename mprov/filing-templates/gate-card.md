# Distiller gate card — canonical skeleton (mprov filings)

Canonical skeleton for every mprov text-gate card (NO-SELF-GATE law,
software-co `docs/gate-wait-pattern-2026-10-28.md` R6; check payload per
`MPROV-MAINT-POLICY.md` § Distiller text-gate ruleset for mprov). Filed with
`kanban_create(board="software-co", ...)`.

```markdown
kanban_create(
  board="software-co",
  title="DISTILLER GATE — <artifact slug>",
  assignee="distiller",            # MANDATORY — never the creating lane (R6.1)
  parents=[<drafting card id>],    # GATE-WAIT R1: edge at create time
  body=<skeleton below>)

## Assignee
distiller

## Goal
Independent text gate on the filing bytes named below. PASS releases per
policy (external surfaces: to the OPERATOR FINAL GATE only — a gate PASS
never authorizes posting); REJECT routes numbered fixes to the author lane.

## Inputs (mandatory — a gate card without these is incomplete)
- Draft artifact(s): exact paths under `mprov/filing-drafts/...`
- sha256 of each draft's exact bytes at filing time
- Policy: `mprov/MPROV-MAINT-POLICY.md` § "Distiller text-gate ruleset for mprov"
- Templates: `mprov/filing-templates/` (all four files)

## Check set
The full ruleset, every check, in order (1, 2, 3, 4, 5, 5a–5d, 6, 7a, …).
The check set is fixed by policy + operator directives — see NO-SELF-GATE
R6.2 below; it is not this card's to relax.

## Acceptance
- Verdict comment opens with exactly `VERDICT: PASS` or `VERDICT: REJECT`
  (process step 3; PASS receipt carries `sha256:` per file).
- REJECT → numbered, verifiable fixes via `kanban_request_changes`.
```

Hard rules:

- **Assignee MUST be `distiller` (R6.1 — NO-SELF-GATE).** A gate card assigned
  to the creating lane or to the author of the bytes under review is invalid;
  its PASS is void (R6.3). If `distiller` is unavailable, the card waits —
  there is no self-gate fallback.
- The gate may not weaken or drop any check to reach PASS (R6.2). A deviation
  you believe justified is a finding: record it in the verdict comment and
  escalate it to the operator; do not absorb it.
- The drafting lane files the card with `parents=[<drafting card>]`, then parks
  per GATE-WAIT R3 (complete with `metadata.pending_gate`, or link-before-block).
- Apply/submit legs belong to a follow-up card created `parents=[<gate card>]` —
  never released on a verdict the author issued itself.
