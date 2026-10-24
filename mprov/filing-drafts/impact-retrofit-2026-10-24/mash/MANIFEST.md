# Impact-retrofit draft pack — mprov-ng/mash — 2026-10-24

Program: retrofit every open biondogs mash filing with the FS9 Impact section
(operator directive 2026-10-24; rule text = MPROV-MAINT-POLICY.md "Filing
style" FS9 + gate check 5b). Drafts card: t_808ca10e. This pack = drafts
only; zero GitHub writes made here.

## Ground truth used
- gh identity: `biondogs` (verified live at fetch time).
- Live enumeration: `repos/mprov-ng/mash/issues?state=open` (36 items),
  bodies + per-item comment threads fetched fresh per item.
- Code state: origin/master tip `36ef120` (fetched fresh). Freshness
  receipt: `git diff 36b6a5e..36ef120` touches ONLY `openwiki/`,
  `AGENTS.md`, `CLAUDE.md` — zero code changes since the sha every filing
  body verifies at, so every cited defect site is still live. Spot-checks
  at master: `bmc.py` response-discard loop, `main.py` no-op signal
  handlers, `gen_changelog.sh` jobserver slug, unbounded
  `requirements.txt`, release-only `ci.yml` — all confirmed.
- PR file lists are the real diff file lists (`/pulls/N/files`), all PRs
  based on `36ef120`.

## Disposition (as of 2026-10-24)
- In scope / drafted: 35 = 27 issues (#18-20, #23-46) + 8 PRs (#47-53, #55).
- Skipped: #54 — author `Golden007-prog`, not biondogs (allowlist
  consequence clause). Untouched.
- Maintainer-engaged skips: NONE — zero non-biondogs comments on all 36
  open items (checked live per item).
- Fixed-upstream skips: NONE — receipt above.

## Insertion rules (byte-identity enforced programmatically)
- Issues: one `Impact:` paragraph inserted directly above the `Severity:`
  line; everything else byte-identical (prefix/suffix equality asserted
  against the freshly fetched live body).
- PRs: `## Impact` section inserted before the test-evidence section
  (`## Testing`; #55 uses `## Test evidence`); everything else
  byte-identical.
- Every block: touches / prod-behavior delta / repo-relative files.
  Uncertain file locations marked `(suspected)` — see #20/24/29/31/42/43.
- Word cap: all 35 revised bodies ≤175 words (max #52 = 172).
- Leak-scan: all 35 full files clean (`t_` ids, board/gate vocabulary,
  internal paths/usernames — regex scan over complete bodies).

## Apply plan (distiller)
Per t_b19bbdd2 precedent: gate-check each draft (check 5b + full style
ruleset), REST PATCH (`gh api -X PATCH .../issues/<n>` / `.../pulls/<n>`
with `--input` JSON; `gh pr edit` silently no-ops on this gh version),
then GET read-back byte-compare against the draft file. #55 is still
pre-style-remediation format — this pack adds ONLY the Impact section per
its card scope; do not restyle it here.

## Files
One draft per item: `<number>.md` = full revised body, paste-ready.
