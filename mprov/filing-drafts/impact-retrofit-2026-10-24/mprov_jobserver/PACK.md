# Impact-retrofit draft pack — mprov_jobserver — 2026-10-24

Program: retrofit FS9 Impact sections onto open biondogs filings (operator
directive 2026-10-24; rule FS9 in MPROV-MAINT-POLICY.md). Drafts only — no
GitHub writes in this pack. Each `<num>.md` is the FULL revised body:
original text byte-identical, Impact block inserted at the FS9 template
position, nothing else touched. Byte-identity was enforced
programmatically (re-insertion inverse reproduces the original) for every
draft; per-item sha256 prefixes of original vs draft are in
`manifest.json` (orig body captured via REST GET, single trailing newline
normalized).

Verification baseline: mprov-ng/mprov_jobserver `upstream/main` = `f6c0f5c`
(2026-10-24). Every in-scope issue's defect was re-confirmed present at
that sha before drafting; PR file lists come from the real PR diffs
(`gh pr view --json files`). Leak-scan run over all 31 drafts: clean.
All 31 revised bodies are within the 175-word cap (max 175: PR #195).

## Coverage

- Open items enumerated live: 54 issues + 8 PRs; biondogs-authored: 27 issues + 8 PRs = 35 candidates.
- In scope (drafted): 25 issues + 6 PRs = **31** — `96 156 157 158 159 160 161 162 163 164 165 166 169 170 173 174 177 178 179 181 183 184 185 186 187 | 193 195 196 197 199 200`
- Fixed-upstream skips: **none** — all 25 open in-scope issue defects re-verified present at `f6c0f5c`; all 6 PRs still open against them.

## Skips with receipts

| item | reason | evidence |
|---|---|---|
| issue 172 | maintainer-engaged | uberlinuxguy comment 2026-10-24T03:12Z: "dup of #112?" |
| issue 180 | maintainer-engaged | uberlinuxguy comment 2026-10-24T03:15Z: "dip of #94?" |
| PR 194 | maintainer-engaged | uberlinuxguy comment 2026-10-24T03:26Z: "Related: #113, whose point 3 is this fix (`one_minute_load` is set from `os.getloadavg()[2]`, the 15-minute average; use `[0]`). #176 duplicates that point." |
| PR 198 | maintainer-engaged | uberlinuxguy comment 2026-10-24T03:26Z: "Related: #128, which covers this bug … #175 duplicates the keys half of #128." |

Non-biondogs open items (uberlinuxguy/jhujasonw/mattcprotzman authored)
were excluded at enumeration — never touched.

## Flags for the text gate

1. **PR 199 / PR 200 pre-date the FS5 restyle.** Their bodies use the
   visible-label layout, carry `Fixes #N` at the BOTTOM, and have NO
   trailing `Assisted by JoeBot` line. This card's contract is
   byte-identical original + Impact only, so those pre-existing
   Rule A / FS5-position violations remain in the drafts; the gate must
   decide whether the PATCH also normalizes them (they fail gate checks 2
   and 3 as-is).
2. **Issue 96** (2025-01-24 enhancement) has no `Severity:` line, so its
   `Impact:` block is appended at the end of the body rather than above a
   Severity line; its files are marked `suspected` (new-module feature).
3. Insertion positions per item are in `manifest.json` (`pos` field).
4. Issue file paths are code-located (verified at `f6c0f5c`), so only
   issue 96 carries the `suspected` marker.
