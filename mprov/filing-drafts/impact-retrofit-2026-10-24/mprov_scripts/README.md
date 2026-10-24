# Pack: impact-retrofit drafts — mprov-ng/mprov_scripts (2026-10-24)

Program: retrofit the FS9 Impact section (MPROV-MAINT-POLICY.md, rule from
t_b0c9922b) onto all open unengaged biondogs filings. Lane card: t_bf0012b1
(drafts only, zero GitHub writes). Gate: distiller TEXT-GATE batch card filed
from the lane; apply: t_f21df19d.

- One `<num>.md` per in-scope item (28: issues 20–29, 31–45, 47, 48; PR 49):
  the FULL revised body = live body fetched byte-exact via `gh api` raw JSON
  + the Impact block inserted at the template position, nothing else edited.
  Issues: plain `Impact:` label block directly above the `Severity:` line.
  PR: `## Impact` section between the fix section and `## Testing`.
- Byte identity asserted programmatically: removing the inserted block from
  each draft reproduces the fetched original exactly.
- `RECEIPTS.json`: per item — sha256 of the fetched original body, total
  word count (≤175 enforced), leak-scan hits (none), fetch timestamp.
  Baseline for the apply lane's body-changed re-check.
- Verified against origin/master @ a44f519; all cited defect sites re-read
  live this pass. Files paths are repo-relative and exist at that sha
  (except #47's new workflow, marked suspected).
- Skipped items and receipts: `SKIP-RECEIPTS.md`.
