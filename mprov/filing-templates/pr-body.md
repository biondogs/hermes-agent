# PR body template — mprov-ng fix PRs

Canonical five-part skeleton per MPROV-MAINT-POLICY.md FS11 (CC#342 exemplar:
[`mprov-ng/mprov_control_center#342`](https://github.com/mprov-ng/mprov_control_center/pull/342), 165 words, open at `781ac6f`). Every initial PR filing MUST match this skeleton in order. Target 150–175 words; no badges, checklists, or meta sections. Gate check 5d enforces order + headings.

````markdown
Fixes #<N>

<Problem paragraph — what's broken, reproduction against a named sha, why
current code does it. Complete sentences, no boilerplate. Name the endpoint/
field/behavior and the reproduction sha, e.g. "GET /systembmcs/?detail
returned every BMC password (reproduced on main @ 781ac6f). Serializer X
serves fields='__all__'; commit Y left the detail path open because ...".>

## The fix
<Mechanism of change + consumer-compatibility analysis: who reads the
changed surface, why they're unaffected/affected. Name consumers explicitly,
e.g. "Password is now served only when scoped to one system (/<pk>/ or
?system=ID&detail — setupBMC.py's exact query). Unscoped ?detail uses a new
NoPassword serializer. Jobserver dns.py's ?network=…&detail read never
touches the password, and setupBMC.py needs no change.">

## Impact
<Touches the API/page/subsystem in plain words. Before: one unscoped GET
returned N passwords. After: passwords served only for one system; prior
consumer unchanged. Files: `systems/serializers.py`, `systems/views.py`,
`systems/test_*.py`, `systems/tests.py`. At least one repo-relative path;
keep to 2–4 lines.>

## Testing
<Named tests with RED-on-base / GREEN-on-fix + full-suite count, e.g. "New
test_bulk_detail_omits_password (two BMCs; neither password in body) is RED
on base, GREEN on fix; test_detail_list updated to the scoped-password
contract. Full suite: 164 tests OK locally.">

Assisted by JoeBot
````

Hard rules (all gate-enforced):
- Line 1 MUST be plain `Fixes #N` matching `^Fixes #[0-9]+$` — no period, no decoration. (PR-tracking five-gate read-back greps it; `Closes #N.` is rejected.)
- Body 150–175 words (cap; exemplar 165). CC#342 measured this shape at 165 — stay inside it.
- Required headings in order, exactly named: `## The fix`, `## Impact`, `## Testing`. No `## Summary`/`## Description` filler, no `## Change`/`## Merge notes` substitutes — FS11 retires the old flexible names. No bold-label blocks.
- Problem paragraph (between Fixes line and `## The fix`) must name the defect, a reproduction sha, and why current code does it — complete sentences, no boilerplate.
- `## The fix` must state mechanism AND consumer-compatibility (who reads the changed surface, why they're unaffected/affected) — gate check 5d rejects a fix section without it.
- `## Impact` mandatory (FS9): touches / before-vs-after production behavior / repo-relative files touched, ≤4 lines — gate check 5b rejects a PR without it or one naming no file.
- `## Testing` must name at least one test, state RED on base + GREEN on fix, and give full-suite count — gate check 5d/6 rejects a PR without it.
- Security-framed PRs state their motivation under the Deployment threat model (controlled deployments — see MPROV-MAINT-POLICY.md, 2026-10-25): the fix stands on a defect/leak/hygiene harm that survives with no untrusted network actor; gate check 5c rejects attacker-on-the-network framing. Opt-in hardening PRs say so plainly ("adds the opt-in gate for deployments that want one").
- Last line exactly `Assisted by JoeBot` (Rule A). No `Agent-*` / `Co-Authored-By` trailers (leak-scan).
- No badges, no checklists, no meta sections.
