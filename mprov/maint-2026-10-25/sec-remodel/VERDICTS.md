# SEC-REMODEL verdict table — 2026-10-25 (kanban t_2450bd52)

Reassessment of every OPEN biondogs-framed security item across the four
mprov-ng repos against the maintainer's controlled-deployment ruling
(uberlinuxguy, mcc#318 comment 6393012139, 2026-10-25T03:35:02Z — full text:
`jason-comment-6393012139.md` in this directory). Sweep: 30 open
security-labeled items (exactly the SEC-RECLASS register, receipt t_5e7399b2)
+ a full 131-item vocabulary rescreen for untrusted-network framing outside
the security-30 → **0 additional items**.

Premise for every verdict: deployments are tightly controlled (deliberate
cabling for port-match; unexpected systems land in auto-detection until an
admin assigns them; no untrusted actor on the deployment L2/network). A harm
survives only if it stands with no untrusted network actor.

## Counts

| verdict | n | items |
|---|---|---|
| KEEP-UNCHANGED | 24 | cc#315 #316 #317 #321 #325 #331 #337 #341 #342 #343 #344, js#158 #169 #198 #199, scr#20 #23 #25 #35 #40 #51, mash#18 #19 #49 |
| RESTRIKE | 5 | cc#320, cc#336, js#170, js#184, js#193 |
| CLOSE-INTENDED | 1 | cc#318 |
| **total** | **30** | |

## Verdict table

| item | verdict | action | evidence |
|---|---|---|---|
| cc#315 | KEEP-UNCHANGED | none (ADR-0001 v2 hold) | any-key-full-admin exposure ACCEPTED IN-TERMS by operator ruling (key keeps full write, ADR-0001 v2 commit b10af56); consistency cross-check PASS |
| cc#316 | KEEP-UNCHANGED | none | bulk BMC-password cleartext in one GET is a leak into API output (systems/serializers.py:63-68); harm stands with no attacker; fix PR cc#342 rides |
| cc#317 | KEEP-UNCHANGED | none | shipped admin:admin defaults are credential exposure actively live on fresh installs (crisis-tier per severity model); fix PR cc#337 maintainer-engaged |
| cc#318 | CLOSE-INTENDED | gated close comment (86w) + close as not_planned, citing 6393012139 | register-endpoint "harm" exists only with an untrusted network actor; maintainer ruled code functions as intended; acknowledgment reply already posted by t_bf6277f2 (comment 6393165133, byte-pin verified); PR cc#336 stays OPEN |
| cc#320 | RESTRIKE | body reframed to reverse-proxy misresolution robustness; `security` label dropped; retitle SKIPPED (maintainer-engaged — never retitle a quoted item, receipted) | surviving harm = `?self` misresolves behind an untrusted proxy (maintainer's own framing, comment 6379588051); "authenticated forger" premise dies (authenticated callers trusted under accepted model) |
| cc#321 | KEEP-UNCHANGED | none | transient fetch failure permanently deletes image–jobserver association (systems/views_noauth.py:95-100): silent data-integrity destruction, no attacker needed; fix PR cc#343 rides |
| cc#325 | KEEP-UNCHANGED | none | anonymous data-model + job-history enumeration is a leak into API output; fix direction (API key or login) is the maintainer's own (comment 6379587747) |
| cc#331 | KEEP-UNCHANGED | none (ADR-0001 v2 hold) | identity layer; ADR already encodes his rulings; consistency cross-check PASS |
| cc#336 | RESTRIKE (stays OPEN) | PR symptom reframed ("enrollment is open by design … opt-in token"); security label KEPT | maintainer shaped the opt-in default himself (comments 6374477697/6379582419); unset-token default matches his design; original framing leaned on unauthenticated-network-attacker |
| cc#337 | KEEP-UNCHANGED | none | fix PR for cc#317; maintainer engaged (password-var question answered) |
| cc#341 | KEEP-UNCHANGED | none (ADR-0001 v2 hold) | API-key scoping; consistency cross-check PASS |
| cc#342 | KEEP-UNCHANGED | none | fix PR for cc#316 (scoped password serving; setupBMC.py preserved) |
| cc#343 | KEEP-UNCHANGED | none | fix PR for cc#321; maintainer flagged model-behavior, direction endorsed |
| cc#344 | KEEP-UNCHANGED | none (ADR-0001 v2 hold) | anonymous-PATCH impersonation; consistency cross-check PASS |
| js#158 | KEEP-UNCHANGED | none | corrupted/malformed imageId into root rmtree + KeyError sticks a RUNNING job: break-on-malformed-input, no attacker needed (unengaged; already [SEC] tier) |
| js#169 | KEEP-UNCHANGED | none | fleet API key written world-readable on every provisioned node: persistent live credential exposure (crisis-tier), local file hygiene — not a network premise |
| js#170 | RESTRIKE | retitle ("Ignored busybox download: the image build executes whatever sits at /tmp/busybox, as root"); severity S1→S2 (break); labels s1-blocker→s2-functional, security dropped; body attacker scenario dropped | surviving harm = failed download unnoticed, stale/partial bytes executed as root (image_update.py:364-366, 379-380); "local account plants /tmp/busybox" framing doesn't survive the controlled-setting ruling; unengaged so retitle allowed |
| js#184 | RESTRIKE | retitle ("Pass mPCC-sourced values to subprocess as argument lists, not shell strings"); [SEC] prefix + security label dropped; body injection framing dropped | surviving harm = values the API legitimately accepts (spaces/quotes) silently change the root command line: break-on-valid-input; "API-editable string = injection" premise dies (API editors trusted under the accepted any-key-full-admin model) |
| js#193 | RESTRIKE | PR body "planted by any local user" clause reframed to failed-download framing; security label dropped (aligns with restruck js#170); PR stays OPEN | fix itself unchanged in substance: verified fetch to root-only dir, fail on nonzero |
| js#198 | KEEP-UNCHANGED | none | functional defect: rootsshkeys never reach the image, silent swallowed failure; no attacker framing; maintainer-linked (cc ref js#128 relation, answered) |
| js#199 | KEEP-UNCHANGED | none | fix PR for js#169 (0700/0600/finally cleanup) |
| scr#20 | KEEP-UNCHANGED | none | world-readable credential dump AND the only backup copy destroyed on reboot: persistent exposure + standalone data loss (tools/backup-mprov.sh:8-12) |
| scr#23 | KEEP-UNCHANGED | none | multi-user-node symlink redirection (Slurm compute nodes are multi-user by design) + non-atomic slurmd config rebuild; already [SEC] tier |
| scr#25 | KEEP-UNCHANGED | none | operator typo or scripted caller aims rsync --delete outside the store: unvalidated operator input into a destructive tool; body already framed without an attacker |
| scr#35 | KEEP-UNCHANGED | none | BMC password visible in process argv (transient local exposure; already [SEC] nice-to-have tier per the persistence discriminator) |
| scr#40 | KEEP-UNCHANGED | none | BMC creds left world-readable in /tmp until reboot: persistent local exposure |
| scr#51 | KEEP-UNCHANGED | none | fix PR for scr#20 (root-only persistent dir, mode policy) |
| mash#18 | KEEP-UNCHANGED | none | unsandboxed Jinja2 rendering of script text: already [SEC] enhancement, no network premise involved; PR mash#49 rides |
| mash#19 | KEEP-UNCHANGED | none | reserved characters silently corrupt GET/DELETE queries: pure correctness (request corruption can feed a destructive foreach), no attacker |
| mash#49 | KEEP-UNCHANGED | none | sandbox fix PR for mash#18 |

## ADR-0001 v2 consistency cross-check (recorded, not re-litigated)

cc#315 (accepted any-key exposure), cc#331, cc#341, cc#344: the ADR
(docs/adr/0001-scoped-agent-identity-model.md, v2 at b10af56) already encodes
the operator's rulings (key keeps full write; #315 hazard accepted in-terms;
Refinement C deferred). Cross-checked against the controlled-deployment
ruling: **consistent — no contradictions, no action.** These four and their
threads are left untouched by this pass.

## Retitle-skip receipts (never renumber a quoted item)

- cc#320 — uberlinuxguy commented (6379588051): title retains
  "spoofable X-Forwarded-For"; the reframe lives in the body, severity line,
  and labels. Skip receipted here.

## Execution state

- Applies (GitHub writes) execute after the distiller text-gate card for this
  pack PASSes; per-write GET read-back receipts land in
  `write-receipts.jsonl` in this directory when applied.
