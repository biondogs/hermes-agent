# Impact-retrofit pack — mprov_control_center (2026-10-24)

Source card: t_6a9550f5 (RETRO-IMPACT-DRAFT-CC). Rule basis: FS9 in
MPROV-MAINT-POLICY.md (t_b0c9922b, commit 5187b6c) as amended by the
operator retrofit directive on-card 2026-10-24 (retrofit ALL open
unengaged biondogs filings). Method mirrors t_b19bbdd2: drafts here →
distiller text gate → REST PATCH lane → GET read-back byte-compare.

Every draft = live body byte-identical + ONE Impact block at the FS9
template position (issues: `Impact:` line directly above the Severity
line; PRs: `## Impact` section after the change narrative, before
Testing/merge lines). Asserted programmatically: removing the inserted
block restores the live body exactly. All file paths code-verified
against main tip `058886d` (fetched 2026-10-24); PR file lists from
`gh pr view --json files`.

## In scope — 22 drafts (word counts include the Impact block; cap 175)

| # | kind | words | notes |
|---|------|-------|-------|
| 309 | issue | 140 | bracket-wrap sites re-verified at tip (`systems/views_noauth.py:116-118`, active wrap on `osmanagement/views_noauth.py:78-79`) |
| 310 | issue | 143 | `scriptType.slug` derefs live at `scripts/models.py:47-68,139,148` |
| 311 | issue | 142 | ipmitool sites live `systems/views.py:914`, `systems/admin.py:286-292` (rc discarded) |
| 312 | issue | 153 | six `update_or_create` sites re-verified; note: body says helper lives in `common/__init__.py`, at tip `queue_job` is `jobqueue/models.py:60` — body left byte-identical per card |
| 315 | issue | 148 | `common/views.py:67` OR-permission live at tip |
| 316 | issue | 153 | detail serializer `__all__` live `systems/serializers.py:59-63` |
| 317 | issue | 133 | `Dockerfile:75-77` admin:admin live at tip |
| 318 | issue | 159 | `systems/views.py:67-68` auth disabled live |
| 320 | issue | 119 | XFF sites live `systems/views.py:292,377` |
| 321 | issue | 141 | remove-on-failed-fetch live `systems/views_noauth.py:134-137` |
| 322 | issue | 133 | forced hostname live `systems/models.py:258` |
| 323 | issue | 142 | print-and-continue live `static/mprov_stateful.py:525-527` |
| 324 | issue | 111 | raw pk gets live `systems/views.py:327,714` |
| 325 | issue | 122 | datamodel anonymous at tip (`mprov_control_center/views.py:47-71`, `urls.py:87`). PARTIALLY fixed upstream: status-changes now staff-gated (`5bfcf12`); Impact wording therefore names only the datamodel sites — original body untouched |
| 326 | issue | 131 | only Django bounded in `requirements.txt` at tip |
| 327 | issue | 142 | `inspect.stack()` live `systems/models.py:390,453`, `networks/models.py:108` |
| 328 | issue | 119 | unguarded keys live `jobqueue/views.py:297-315`, `osmanagement/views.py:222-226` |
| 329 | issue | 133 | slug-from-name on every pre_save live `systems/models.py:464` (`instance.slug = slugify(instance.name)`) with slug=PK at `:265` |
| 330 | issue | 122 | zero ruff/flake8/shellcheck refs in workflows at tip |
| 331 | issue | 146 | `request.user = User.objects.get(username='admin')` live `common/views.py:214` |
| 342 | PR | 165 | `## Impact` before `## Testing`; files from real diff |
| 349 | PR | 141 | `## Impact` before `Fixes #322`; files from real diff |

## Skipped — receipts (live enumeration 2026-10-24: 88 open items)

(a) Maintainer-engaged biondogs PRs — do-not-touch per card:
- PR #344 — uberlinuxguy comment (client-impact: jobserver/node scripts auth)
- PR #343 — uberlinuxguy comment (model-behavior flag re #321)
- PR #341 — uberlinuxguy comment (allowlist misses writes clients make today)
- PR #337 — uberlinuxguy comments x2 (env-var rename ask; admin-pass question)
- PR #336 — uberlinuxguy comments x2 (prefers open-enrollment default; N.A.D.S. break)

(b) Fixed upstream: none fully; #325 partially fixed (see table note) —
kept in scope with tip-accurate Impact wording.

(c) Author not biondogs: 55 items (uberlinuxguy/jhujasonw/mattcprotzman/
Valdimar authored; incl. all #346-#348, #333, #335, #306, #254-#298 block,
#152-#180 block, legacy #5-#65 Jason items).

Operator-era legacy biondogs issues EXCLUDED on the t_b19bbdd2 precedent
("already human-register", never restyled; FS9 wording is for new
biondogS-authored filings — operator-authored asks are not agent
filings): #19 #45 #123 #124 #128.

## Gate-batch proposal (TEXT-GATE precedent, <=10 per batch)

- Batch 1: issues 309 310 311 312 315 316 317 318 320 321
- Batch 2: issues 322 323 324 325 326 327 328 329 330 331
- Batch 3: PRs 342 349

## Distiller notes

- Leak-scan of every draft: only lexical false-positive is the word
  "gate" appearing inside ORIGINAL body prose (#315 permission gate,
  #330 lint gate, #318 enrollment-token gate, #331 permission gate) —
  byte-identity forbids touching it; no internal ids/personas/paths in
  any inserted block.
- Impact blocks are single-paragraph (1 line, under the 2-4 line cap)
  and each names >=1 repo-relative file path (gate check 5b).
- Original bodies already carry severity lines / Rule-A trailers where
  required; nothing else added or removed.
