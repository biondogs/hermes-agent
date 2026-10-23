# FILING STYLE PROFILE — Jason's pattern vs ours (empirical, live)

Produced 2026-10-23 by sw-pm (kanban t_302a8bf1). Operator directive: "Feedback
from Jason is that he doesn't like the formatting of many of our issue and PR
comments. Review the issues and PRs posted by Jason and create new guidelines
that will make our filings look more like his."

## Method

Full-corpus pull from the four live `mprov-ng` repos (issues+PRs state=all,
conversation comments, review threads) on 2026-10-23 via `gh api`, then
mechanical stats (script + JSON kept in the card workspace:
`analyze.py`, `profile_stats.json`, `stats_dump.txt`).

| corpus | Jason (`uberlinuxguy`+`jhujasonw`) | ours (`biondogs`) |
|---|---|---|
| issues | 277 | 153 on mprov-ng (112 still open) |
| PRs | 142 | 35 (24 open) |
| thread comments | 219 | 9 |
| review bodies with text | 0 | 0 |

Account split (matters): **`uberlinuxguy` 2026-era is the norm** — complete,
evidence-rich filings. `jhujasonw` legacy PRs (2022–2025) are spartan
(lowercase one-liner titles, often empty bodies, e.g. `Closes #41` as a whole
body). Both accounts, always: zero template structure. Jason never files
text-gated review bodies — he comments conversationally instead.

## Jason's pattern (uberlinuxguy, Oct-2026)

**Issue titles** — plain declarative sentence naming the concrete failure;
verb present ("Booted nodes run with no SELinux labels: the image tarball
drops security.selinux, and nothing relabels"; "Stateful install never
reboots: ..."). Enhancement titles are imperative ("Let job servers claim a
job atomically"). Median 8 words. 0% severity/tag prefixes. 12% use a
`fact: mechanism` colon form. No trailing period, no quotes, backticks rare.

**Issue bodies** — prose, first paragraph = the observable symptom in one or
two sentences. Evidence lives *inside the prose* as commit-pinned permalinks
(`blob/2413899/static/mprov_boot_init.sh#L337`) or backticked `file:line`,
with real error output pasted verbatim in fenced blocks when it exists.
H2 headings: 2.7% (essentially never). Bold mini-labels: 27%, and almost
all are the single label `**Fix:** <sentence>` (48 uses; rare others:
`**Proposed:**`, `**Check first:**`, `**Likely cause:**`, `**Seen:**`,
`**Coordinate with:**`, `**Needs verification:**`). Median body 41 words
(19% of his issues ship bodyless — title + link sufficed; we never do and
never will — content rigor stays). Code fences 7%, permalinks 24%, `#N`
refs 20%, bullets 20%. Closes with a provenance/footer line: "Found during
the #306 PXE test. Related: #347." Severity is *never* stated as a label or
prefix — impact is woven into the prose ("IPv4 unaffected" style).

**PR titles** — imperative or descriptive clause, median 9 words, no tags.

**PR bodies** — `Closes #N.` (with period) as the literal first line(s);
multi-issue PRs stack one `Closes` per issue. Then narrative prose of what
was true before / what the change does. Sections exist but are **named for
their content**, never a fixed template: `## Change(s)`, `## Testing(s)`
(most common, 25×), `## Summary`, `## Merge notes`, `## API clients`,
`## The bug`/`## The fix`, `## Still needed outside this PR`. Test evidence
is a sentence with counts and a base comparison: "Full suite: 153 passed,
16 xfailed, 3 runs, in the image built from this branch. Against main's
code, 6 of the new tests fail." Bold labels `**Checked on running
containers:**` style for verification receipts; before/after markdown
tables for behavior changes. Cross-PR coordination spelled out: "Depends on
#263. Merge that first.", "Unblocks mprov-ng/mprov_control_center#268".
He discloses his own AI assistance as a final trailer line ("🤖 Generated
with [Claude Code]") — precedent that our `Assisted by JoeBot` line is
*house-consistent*. Median body 157 words (p95 435) — he is longer than our
150w cap on PRs, which stays a cap, not a loosening.

**Thread comments** — median 18 words, mean 37. Single flowing paragraph,
sentence case, no headings (0%), bullets 7%, code fences 5%. Stance first,
reason second, first person, softly worded asks: "I would prefer to see
DJANGO_SUPERUSER_PASSWORD renamed to MPROV_SUPERUSER_PASSWORD for the env
var to pass into the container." / "This is an interesting idea but I would
prefer if the token isn't set to allow open enrollment not disable it all
together. The point was ..., adding a token means ... I don't see much gain
for." Closures state verdict + provenance: "Closing as won't fix: replaced
by #306. This branch conflicts with main, and all of its commits except
`898cd1da` are already on main." / "Already fixed by `cd314a3` (review item
D-10, merged to `main` on 2026-10-19). ... `systems/test_bmc_inline.py`
covers it." Coordination: "Blocked by mprov-ng/mprov_jobserver#155 (...).
That has to reach `:dev` or a jobserver release before this merges."
Code/file/sha tokens always backticked. Same-repo refs bare `#N`;
cross-repo refs full `mprov-ng/repo#N`.

**Labels/milestones** — his *current* (Oct-2026) issues: zero labels, zero
milestones (76 recent issues; only 10 carry a label at all, and those are
old-era triage). PRs: labels rare (3 in 142). Milestones were used in the
2022–2024 era only. Current practice = no labels, no milestones.

## The delta (ours → his)

| dimension | Jason (now) | ours | verdict |
|---|---|---|---|
| issue title `[Sx]` prefix | 0% | 106/112 open | **drop** (cosmetic, high-visibility) |
| issue title form | declarative `fact: mechanism` | topic noun-phrases | rewrite to his form |
| issue body structure | prose; `**Fix:**` at most (27%) | 100% five-label block on the 106 sprint issues (`**Symptom.**/**Evidence.**/**Root cause.**/**Proposed fix.**/**Severity.**` — 79 bold variant, 27 plain-`symptom:` variant; the other 6 open issues are operator-era human filings already in his register) | **biggest divergence** — same five *contents*, his shape |
| issue body length | median 41 w | median 90 w | keep ≤150 cap; prefer brevity |
| code fences in issues | 7% | 0% | paste real output where it exists |
| evidence permalinks | 24% | 0% (plain `file:line` text) | pin at least defect-site evidence |
| `#N` refs in bodies | 20% | 5% | weave Related:/Found while: lines |
| issue labels | none (recent) | `bug,review-found,sN-*` on 100% | **conflict — flagged, see below** |
| PR title | imperative, no tags | imperative, no tags (46% colon-form) | already aligned |
| PR body opener | `Closes #N.` line 1 | `Fixes #N` line (pos. varies) | his position, our keyword (gate regex keeps `^Fixes #N$`) |
| PR body sections | content-named `## Testing` etc. | templated `**Symptom.**/**Fix.**` bold blocks (57%) | adopt his section names or none |
| PR test evidence | counts + base-compare sentence | counts present, RED/GREEN jargon | reword to his sentence, keep rigor |
| PR body length | median 157 w | median 129 w | cap 150 stays (we'll read slightly terser — fine) |
| `Assisted by JoeBot` | (he ships his own trailer) | **missing from 22/24 open PR bodies** | Rule-A gap, not style — remediation tier T-A |
| thread comments | 18 w median, one paragraph, stance-first | 64 w mean, bold headers, fenced blocks, bullet receipts | adopt his shape; keep verdicts+receipts content |
| tone | first-person preference asks, reasons after stance | neutral-impersonal | adopt |

**House-rule conflicts flagged (kept, not silently dropped — operator to adjudicate):**

1. **Rule C five-section fixed order vs his prose.** Rule C (this file) mandates
   visible `symptom/evidence/root cause/proposed fix/severity` structure;
   Jason uses zero of those labels. Resolution drafted in FILING STYLE: the
   five become a *content checklist every body must satisfy*, expressed in
   his prose + `**Fix:**` shape. The gate enforces presence of the five
   contents, not the five labels.
2. **Severity taxonomy vs his label-free practice.** REVIEW-CHARTER §3 and
   our filing lane stamp `[Sx]` + `sN-*` labels + `review-found`; his current
   issues carry nothing. Title prefix is pure look → dropped. Labels are
   board tooling metadata (worklist join, project-9 sync use them) → kept by
   default pending operator ruling; removing them is cheap if he objects.
3. **≤150w cap vs his PR median 157w.** Operator carve-out says keep the cap;
   note recorded that it keeps our PRs marginally terser than his own — a
   deliberate standard, not a style miss.

Reference: `FILING-STYLE-REMEDIATION-2026-10-23.md` for the open-filing
restyle proposal; `filing-templates/` for the three templates; policy rules
in `MPROV-MAINT-POLICY.md` § Filing style.
