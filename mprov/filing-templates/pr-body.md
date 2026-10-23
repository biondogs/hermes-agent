# PR body template — mprov-ng fix PRs

Modeled on uberlinuxguy's merged PRs (mprov_jobserver #190, #188, #154;
mprov_control_center #345). Sections are named for their content; the only
structural constant is the closing-keyword first line and the trailer last
line.

````markdown
Fixes #<N>

<Paragraph — what was true before, what this does, why it is safe. 2–5
sentences. Backtick every file, function, setting, sha. Reference related
PRs as #N or mprov-ng/<repo>#N.>

## Change
- <one bullet per behavior change, file named first:> `views_noauth.py`
  <what changed>.
- ...

## Testing
Regression tests in `<tests/file.py>`: RED on base `<base-sha>` (<exact
failure observed>), GREEN on this head. <New test names in one clause
each.> Full suite: <N> passed, <N> xfailed, in the image built from this
branch.

## Merge notes
<only if true:> Depends on <#N / repo#N>. Merge that first. /
Unblocks <#N>. / <Operator-side step, e.g. rotate a key.>

Assisted by JoeBot
````

Hard rules (unchanged rigor):
- `Fixes #N` MUST stay a plain standalone line matching `^Fixes #N$` —
  the PR-tracking gate greps it. His `Closes #N.` form reads alike but
  carries the period our machine check rejects; keyword+line form wins,
  position (line 1) adopted from him.
- Body ≤150 words (cap; his median is 157 — ours reading terser is fine).
- Last line exactly `Assisted by JoeBot` (Rule A). No `Agent-*` /
  `Co-Authored-By` trailers (leak-scan).
- Section names: pick from what the PR actually contains (`## Change`,
  `## Changes`, `## Testing`, `## Tests`, `## Merge notes`, `## API
  clients`, `## The bug`/`## The fix`) — never `## Summary`/`##
  Description` filler, never `**Symptom.**`-style bold label blocks.
  A 2-file fix may skip sections entirely: closing line, prose, trailer.
- Test evidence keeps RED/GREEN facts but says them in his sentence shape
  ("RED on base `781ac6f` (200, mutation applied); GREEN on this head");
  a before/after markdown table is his idiom for behavior matrices — use
  it when it beats prose.
