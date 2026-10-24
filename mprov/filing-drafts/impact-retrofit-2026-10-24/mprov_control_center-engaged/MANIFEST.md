# Impact-retrofit pack — mprov_control_center ENGAGED re-drafts (rev2, 2026-10-24)

Source card: t_00ad011d (RETRO-IMPACT-CC-ENGAGED), disposition lane for the 11
items the apply lane (t_f21df19d, receipts commit e39613b) correctly
skip-engaged at PATCH time: each carries exactly one uberlinuxguy (Jason
Williams, CONFIRMED per contributor allowlist) triage comment timestamped
2026-10-24T03:59:32–04:00:01Z, pre-dating the drafting pass. Threads were read
in full this run; no comment is an operator note under the `biondogs` login, so
no COM-OPS in-thread response was due. Zero GitHub writes in this lane.

DISPOSITION — all 11 → (a) re-draft honoring the maintainer position. None are
moot: every defect is still live at main tip (fix PRs #336 #341 #343 #344 open,
#349 open; only #338, a sibling change, is merged), all items open, and no
comment requests stopping work — each states constraints/cross-refs the Impact
block must reflect. Each rev2 file = live body (re-fetched 2026-10-24T15:19Z,
zero drift vs the rev1 pin) with the rev1 Impact block REPLACED in place by the
rev2 block at the same FS9 position (single paragraph directly above the
`Severity:` line); everything else byte-identical. Asserted programmatically:
delete-rev2-block == live body, and rev2 differs from rev1 draft only in that
one line.

THREAD RECEIPTS (each issue: 1 comment, actor uberlinuxguy, no other actors):
310=6379590659 · 312=6379589000 · 315=6379587002 · 318=6379587347 ·
320=6379588051 · 321=6379589800 · 322=6379588681 · 325=6379587747 ·
327=6379589316 · 329=6379588377 · 331=6379586565

## In scope — 11 re-drafts (words = final body incl. Impact block, cap 175)

| # | words | blk w | payload sha256[:16] | maintainer point honored |
|---|-------|-------|---------------------|--------------------------|
| 310 | 159 | 45 | b204b557a50eeaf8 | null guard needs no migration; PROTECT alternative would need `AlterField` and blocks deleting in-use types — Impact now names the guard as expected fix with that caveat |
| 312 | 164 | 50 | daa4ce2791398c8b | job-queue semantics change; overlaps claim work mprov-ng/mprov_jobserver#112 and cc#296 — cross-ref added ("#296" in the comment = cc#296; mprov_jobserver#296 does not exist) |
| 315 | 167 | 57 | e6d52dba09e4ba20 | key scoping is client-visible for jobserver/installer/mprov_scripts/mash writes, installer `POST /systems/?self` critical — added, breakdown pointer #341 |
| 318 | 174 | 50 | cdf7b08a88c28b4e | token must be sent by jobserver `nads` plugin and reach the public N.A.D.S. image — added to expected (body's maintainer-decision paragraph left byte-identical) |
| 320 | 142 | 47 | 7c03230faacd00dc | deployment-dependent: socket-address right direct-to-Apache, trusted-proxy config needed behind a reverse proxy; #338 precedent — added |
| 321 | 157 | 46 | 3813bc44192f2ad6 | skip-instead-of-delete keeps failing servers listed until marked unhealthy — routing/stale work of #254 — added |
| 322 | 152 | 50 | 8218a3e7e2280b37 | dnsmasq plugins write `nic['hostname']` into host files; drop-field alternative would need a migration — added |
| 325 | 142 | 46 | b5162dc69e24f063 | CORRECTION: rev1 expected "staff auth" — maintainer notes mash's `datamodel` command calls with an API key (mprov-ng/mash#8); expected now = key or logged-in user, staff-session-only would break mash |
| 327 | 160 | 47 | 8ead1bfddcc78148 | replacement changes `created_by`/audit for every save path incl. management commands and API-key requests — added |
| 329 | 158 | 58 | c42ec63efffcffb7 | slug-at-creation means renames keep old ID; ID-changing renames need migration + change `/images/<slug>` URLs; related #297 — added |
| 331 | 162 | 53 | 580578e64498a569 | CORRECTION: flat rejection of anonymous PATCH would also reject jobserver job-status and mprov_scripts key writes — expected now = real actor, with that constraint; pointer #344 |

Batches: B1 310 312 315 318 320 321 · B2 322 325 327 329 331.

## Notes for the gate
- rev1 pack: `.../impact-retrofit-2026-10-24/mprov_control_center` (gate
  t_25418f17 approved the rev1 issue drafts verbatim; these 11 were only
  skipped at APPLY for engagement, never content-rejected).
- Blocks 45–58 words (rev1 range was 23–41) — length buys the maintainer
  constraints; each stays one paragraph at FS9 position.
- Leak-scan of the 11 inserted blocks clean (same lexical domain vocabulary
  as rev1: "enrollment-token gate", "permission gate" = domain sense).
- Apply-lane guards unchanged: immediately pre-PATCH re-check state/author/
  thread live; engagement now DISPOSITIONED — a NEW foreign comment (beyond
  the receipted uberlinuxguy triage note above) or body drift still skips.
- This card authorizes gate review only; PATCH + GET read-back receipts
  happen in the application lane after PASS.
