# Filing drafts — ruling replies on PR cc#341 and PR cc#344 (2026-10-24)

Status: DRAFT, distiller-gated. biondogs posts after the gate passes; not before.
Scope: in-thread replies answering uberlinuxguy's binary ("should an API key keep
full write access for an admin CLI, or should mash need a user login?") — asked at
cc#341 comment 6379582239 and cc#344 comment 6379582059. The answer on both threads:
the former, per the operator ruling of 2026-10-24.
Design authority: ADR-0001 v2 (`mprov/docs/adr/0001-scoped-agent-identity-model.md`),
which supersedes the v1 Option-B amendment specs in full.
Style authority: `mprov/filing-templates/maintainer-reply.md` (his shape, our
receipts); house cap ≤150 words/body; `Assisted by JoeBot` trailer on every
publication; uberlinuxguy as reviewer. Claims below are design-level receipts
(ruling + pinned call sites), not test runs — no "we ran it" language.

---

## Draft reply — PR cc#341 thread (answers comment 6379582239)

Answering your question directly: an API key keeps full write access for the admin
CLI; mash does not need a user login. That was our operator's call, mainly for admin
CLI ergonomics — every deployed `mash` reads its key from `jobserver.yaml`
(`app.py:183–185`) and there is no user-credential config path today, and
`djangorestframework-api-key` 3.1.0 has no per-key capability column, so any
restriction would bind every agent key too. So we're rescoping this PR rather than
merging it as filed: the write allowlist and its refusal tests are withdrawn, but
we're keeping your named limited service user — a valid key resolves at the
authentication layer to a non-privileged `mprov-agent` user, so agent writes stop
executing as `admin` and attribution is honest. #344's `patch()` guard is rebased on
top of this. Per-key capabilities stay on our later list.

Assisted by JoeBot

---

## Draft reply — PR cc#344 thread (answers comment 6379582059)

Answering your question here too: the API key keeps full write access for the admin
CLI, so key-authenticated PATCHes can't be blanket-refused — but this PR's guard
survives exactly as designed. The ruling changes the test, not the fix:
`test_api_key_patch_is_rejected_not_run_as_admin` is rewritten to expect `200` with
the write executed as a new non-privileged `mprov-agent` service user and no
`admin` user in the fixture, so "not run as admin" keeps its teeth. Truly anonymous
PATCHes still get the 403 — #331's original symptom stays dead. Our operator took
the trade knowingly: a leaked key is again full API write, though now as
`mprov-agent`, never as the superuser. We'll rebase this on the rescoped #341 and
merge it second.

Assisted by JoeBot

---

Gate checklist (distiller): (1) each body ≤150 words — verified by `wc -w` at draft
time, re-verify at gate; (2) answers the binary verbatim-first on both threads;
(3) single paragraph, stance first, no headings/bullets; (4) the `Assisted by JoeBot`
trailer present; (5) same-repo refs bare `#N`, cross-repo refs full form; (6) no
un-run claims dressed as receipts; (7) reviewer-of-record on the publication:
uberlinuxguy.
