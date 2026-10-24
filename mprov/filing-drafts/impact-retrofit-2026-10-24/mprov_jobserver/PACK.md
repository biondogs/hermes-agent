# Impact-retrofit draft pack — mprov_jobserver — 2026-10-24

Program: retrofit FS9 Impact sections onto open biondogs filings (operator
directive 2026-10-24; rule FS9 in MPROV-MAINT-POLICY.md). Drafts only — no
GitHub writes in this pack. Each `<num>.md` is the FULL revised body:
original text byte-identical, Impact block inserted at the FS9 template
position, nothing else touched — EXCEPT PR 199/200, which are
FS5-normalized re-drafts (see Flags §1): full-body restyle to FS5
(`Fixes #N` line 1, content-named sections, Rule A trailer) with the
Impact block of this pack carried verbatim; byte-identity does not apply
to those two. Byte-identity was enforced
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

## Commit receipt (shared pack dir — history is not per-lane)

Management-repo commits for this lane: sibling CC-lane commit **f1b5f20**
(t_6a9550f5) accidentally swept this lane's then-untracked drafts in — it
already carries 29 of the 31 files at final content plus an intermediate
`196.md`/manifest. This lane's own commit **c9e381a** adds `PACK.md` and
the final `196.md` word-cap trim + manifest refresh. Diff this lane's
pack against `f1b5f20` + `c9e381a` together, not `HEAD~1`. `manifest.json`
sha256 prefixes are the per-file integrity baseline.

## Flags for the text gate

1. **PR 199 / PR 200 — FS5-normalized re-drafts (t_87d974be, post-gate
   t_6afe7564).** The originals pre-date the FS5 restyle (visible-label
   blocks, `Fixes #N` at the BOTTOM, no `Assisted by JoeBot` trailer) and
   failed gate checks 2/3/5 as byte-identical appends. Per the gate ruling
   these two drafts are now FULL FS5 rewrites: `^Fixes #N$` line 1, prose
   narrative + content-named sections (199 keeps `## Change`, dropped for
   200 to hold the cap — its bullet only restated the narrative), test
   evidence in counts+base-comparison sentence shape with every RED/GREEN
   fact preserved, `## Impact` verbatim from this pack's accepted draft
   (passes check 5b), `Assisted by JoeBot` exact last line. One PATCH
   carries restyle + Impact together (T-A/T-B anti-churn precedent);
   apply lane t_f21df19d holds these two items until the re-draft passes
   re-gate (one edit + re-gate per check 8). `manifest.json` `pos` reflects
   the rewrite; `orig_sha256_16` still pins the live body.
2. **Issue 96** (2025-01-24 enhancement) has no `Severity:` line, so its
   `Impact:` block is appended at the end of the body rather than above a
   Severity line; its files are marked `suspected` (new-module feature).
3. Insertion positions per item are in `manifest.json` (`pos` field).
4. Issue file paths are code-located (verified at `f6c0f5c`), so only
   issue 96 carries the `suspected` marker.
