# ADR-0001 (mprov series): One scoped agent-identity model — a valid API key IS the agent's identity, a named non-privileged service user (ruling v2: keys keep full write)

**Status:** Amended-Accepted. v1 (commit `b755603`, MPROV-CC-APIKEY-DESIGN t_5e0a4d72) adopted the maintainer's model with the mash write-scope question framed as an open operator ruling. **The operator ruled the same day (2026-10-24, via clarify on swco-butler; ruling recorded as comment #621 on t_5e0a4d72): Jason's option 1 — the API key keeps full write access for the admin CLI; mash is unchanged. The cc#315 full-read-write key hazard returns and is accepted in-terms, deliberately. Refinement C (per-key capabilities) stays deferred.** This v2 folds the ruling in and is the binding version: it supersedes v1's Layer 2 (write allowlist), the Layer-3 `?self` view guard, and both v1 amendment specs. Layer 1 (service-user identity) and the `patch()` guard survive unchanged. See the Amendment log at the end for the delta.
**Deciders:** uberlinuxguy (direction, cc#344 comment 6379582059 + cc#341 comment 6379582239, both 2026-10-24T03:59Z) · operator (mash write-scope ruling, 2026-10-24) · sw-architect (formulation) · Card: MPROV-CC-APIKEY-RULING (t_6d63915b, filed by swco-butler; superseding design in t_5e0a4d72; plain-text ref to FILING-WATCH t_b2d3c1c0 — not a parent edge by design, that card never completes).
**Relates to:** PR cc#341 (fix/mprov_control_center-315, head 75dfa76, claims fixes #315) · PR cc#344 (fix/mprov_control_center-331, head 408cb5c, fixes #331) · base `mprov-ng/mprov_control_center` main @ 058886d · dependency pin `djangorestframework-api-key==3.1.0` (no authentication module ships; `KeyParser` + `APIKey.objects.get_from_key()` + `HasAPIKey` are the whole surface) · out of scope: enrollment-token work (cc#336).

## Context

Two open PRs fix two real holes and contradict each other:

- **cc#341** ("Scope API key permission to what the jobserver agent needs", fixes #315): today `MProvView.permission_classes = [HasAPIKey|IsAuthenticated]`. The OR passes on a valid Api-Key alone, with **no user at all**, so any key holder is a full API admin (key-only `POST /jobs/` → 201, `DELETE /jobservers/1/` → 204). cc#341 replaces `HasAPIKey` with `HasScopedAgentAPIKey | IsAuthenticated`: safe methods plus a 4-entry `agent_write_rules` table, everything else requires a login.
- **cc#344** ("Reject anonymous PATCH mutations instead of running as admin", fixes #331): `MProvView.patch()` (common/views.py:212–214 @ 058886d) substitutes `User.objects.get(username='admin')` whenever `request.user` is anonymous. A key-authenticated request passes the permission gate anonymously, hits this path, and every PATCH is executed and recorded **as the superuser**. cc#344 refuses all anonymous PATCHes with 403.
- **The contradiction:** every deployed mProv agent client (jobserver, node post-boot scripts, stateful installer, mash) authenticates with **only** an `Api-Key` header — never a session. cc#344 as filed therefore 403s the exact `PATCH /jobs/<id>/` that cc#341's test asserts returns 200, and would stall the jobserver, brick the stateful installer's netboot disable, and break NIC/BMC registration.
- **Maintainer direction** (cc#344 comment 6379582059): "treat a valid API key as the agent's identity: a named, limited service user, as the issue suggests, rather than refusing it… settled together with #341's scope." cc#341 comment 6379582239 adds the missing allowlist entries and poses the binary: *"should an API key keep full write access for an admin CLI, or should mash need a user login?"*
- **Operator ruling on that binary (2026-10-24): the API key keeps full write access for the admin CLI.** mash (admin CLI) reads `jobserver.yaml`'s `apikey` by default (`app.py:183–185`; CLI `connect <url> apikey <key>` at `app.py:169/195`) and issues arbitrary POST/PATCH/DELETE on every model (`app.py:557–563`). Requiring a user login would force config (and possibly code) changes on every deployed mash for a protection that cannot today be scoped per key — 3.1.0's `APIKey` model has no role/capability column, so any write restriction binds **all** keys, and keys are the only credential every agent client has. The operator accepted in-terms that #315's hazard returns: a leaked jobserver key (one per cluster, distributed to every jobserver host) is again full API write. Refinement C (per-key capabilities, which would let mash-keys and agent-keys diverge) is the recorded path back and is deferred.

## Decision (v2, final)

**One scoped agent-identity model, permission half collapsed by ruling, identity half intact.** A valid Api-Key resolves at the authentication layer to the agent's identity — a single named, non-privileged Django service user — and, per the operator ruling, that identity retains **full API write access**. The write-allowlist enforcement of v1 is withdrawn; what survives is the identity layer that makes #331 impossible and attribution honest, in three layers:

### Layer 1 — Authentication: the key IS an identity (`AgentAPIKeyAuthentication`) — unchanged from v1

New DRF authentication class in `common/views.py` (the package ships none; build it on the pinned 3.1.0 surface):

```python
class AgentAPIKeyAuthentication(BaseAuthentication):   # rest_framework.authentication
    # KeyParser: rest_framework_api_key.permissions.KeyParser  (keyword "Api-Key")
    # validate via APIKey.objects.get_from_key(key)  (raises APIKey.DoesNotExist
    #   if bad/revoked) and api_key.has_expired
    # authenticate() returns (service_user, api_key) or None (invalid/absent key
    #   → request stays anonymous → permission layer denies with 403)
```

On first success it lazily does `User.objects.get_or_create(username='mprov-agent', is_staff=False, is_superuser=False)` with an unusable password. Lazy creation, **not** a data migration (the `common` app has no `migrations/` package today). Idempotent `get_or_create` is safe.

`settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` becomes `[SessionAuthentication, BasicAuthentication, TokenAuthentication, AgentAPIKeyAuthentication]` (agent class **last**). Standing rule: **a logged-in session wins over a stray Api-Key header** — DRF stops at the first authenticator that claims the request.

### Layer 2 — Permission: one plain class, full write for keys (`[IsAuthenticated]`) — collapsed by ruling

```python
MProvView.permission_classes = [permissions.IsAuthenticated]
```

The entire OR composition (`HasAPIKey | IsAuthenticated`) and cc#341's `HasScopedAgentAPIKey` are **dissolved**: after Layer 1, a key-authenticated request *is* an authenticated user (`mprov-agent`), so the stock `IsAuthenticated` suffices — keys keep full write per the ruling, session/basic/token users keep full access exactly as today, and anonymous requests are refused everywhere the class applies. A key principal is therefore: full read (as before), full write (ruling), executing as a **non-superuser, non-staff** named user.

The v2 reasoning behind dissolving rather than keeping `HasAPIKey` in the composition: with Layer 1 in place, any residual `HasAPIKey` arm is redundant (the key request is already authenticated), and any residual `| IsAuthenticated` arm is also redundant — but if Layer 1 ever fails to run (authentication_classes overridden, class ordering broken), a surviving `HasAPIKey` arm would re-create the identity-less anonymous-key request that feeds #331's `patch()` path. One plain `IsAuthenticated` makes the layers non-redundant: identity at the authentication layer, gate at the permission layer, attribution at the view layer.

Survey item for the dev card (not new design): any **other** view composing the same `HasAPIKey | IsAuthenticated` OR gets the same one-line `[IsAuthenticated]` substitution; grep the codebase for `HasAPIKey` before removing the import from `common/views.py` (`IPXEAPIView` et al. in `views_noauth.py` deliberately zero out `permission_classes` — leave that surface untouched).

### Layer 3 — View: `patch()` stops impersonating admin — survives verbatim; the `?self` guard is withdrawn

`MProvView.patch()` keeps **cc#344's fix verbatim in shape**: no `admin` lookup ever; if `request.user` is not authenticated → 403 `"Anonymous PATCH mutations are not allowed."`. Under the unified model the key-authenticated agent arrives at `patch()` already authenticated as `mprov-agent`, so key PATCHes run **as the service user** — neither superuser nor refused. The anonymous 403 remains as defense in depth (this codebase already has views that zero out `permission_classes`, so the write path must not assume the permission layer always ran).

**Withdrawn by ruling:** v1's `SystemAPIView.post()` view guard (`?self`-only for key-authenticated callers → 403). mash creates systems by key without `?self` (`app.py:557–563`), and the ruling keeps mash unchanged, so key `POST /systems/` without `?self` must continue to work. The pre-existing `?self` endpoint behavior itself (binds to the requester's IP → NIC → system, 403s any body key other than `netboot`) is untouched by this ADR — it stays exactly as it is on main.

### The verified agent wire protocol — non-normative inventory (Appendix A)

v1's 8-entry `AGENT_WRITE_RULES` table is **no longer an enforcement artifact**; it survives as an inventory of every verified agent call site, re-purposed as the seed allowlist for Refinement C (see Revisit when). It is reproduced in Appendix A for the record and must not be implemented as a permission class under this ruling.

### Status-code matrix v2 (reconciles the cc#344↔cc#341 tests under the ruling)

| Call | Base `058886d` (today) | After v2 (identity layer + ruling) |
|---|---|---|
| key GET (any model) | 200 | 200 |
| key `POST /jobservers/` (register) | 200 (anonymous) | 200 (as `mprov-agent`) |
| key `PATCH /jobs/<id>/` | 200 **run as admin** (#331) | 200 (as `mprov-agent`) — cc#341's counter-test stands, new rationale |
| key `PATCH /systemimages\|/repos ?addjs` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /systems/?self` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /systems/` (no `?self`) | 201 (as admin/anonymous) | 201 (`mprov-agent`) — **operator-accepted #315-class exposure** |
| key `PATCH /networkinterfaces/`, `/systembmcs/` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /ostypes/` | 200/201 as admin | 200/201 (`mprov-agent`) |
| key `POST /jobs/` | 201 **hole** (#315) | 201 (`mprov-agent`) — **operator-accepted** |
| key `DELETE /jobservers/<id>/` (any DELETE) | 204 **hole** | 204 (`mprov-agent`) — **operator-accepted**; never executed as superuser |
| key `PATCH /jobmodules/<slug>/` | 200 **run as admin** (#331) | **200 (as `mprov-agent`), object updated, no `admin` user required** — cc#344's test REWRITTEN (v1 expected 403; the refusal rationale is dead under the ruling) |
| no key, no session, any write | 403 (permission gate) | 403 (permission gate; `patch()` guard is defense in depth) |
| session-authenticated write | 200 (as that user) | 200 (as that user) |
| mash by key (`app.py:557–563`) | full write | full write, as `mprov-agent` — **unchanged by design (ruling)** |

**The cc#344 test conflict, restated under the ruling:** cc#344's `test_api_key_patch_is_rejected_not_run_as_admin` (key PATCH `/jobmodules/nads/` → 403, name still `NADS`) can no longer pass — a 403 for a key PATCH contradicts the ruling. What survives is the test's *point*: the write must not execute as `admin`. The rewrite asserts 200 + object updated + no `admin` user in the fixture + executed as `mprov-agent`. cc#341's `test_key_can_patch_job_status` (→ 200) stands. The two PRs stop contradicting each other here.

## Disposition of the two PRs

### cc#341 — amended in place (rescoped), not closed

The ruling negates cc#341's filed premise (scope the key to an allowlist; "fixes #315") but **rescopes it rather than killing it**, for four reasons:

1. The biondogs acks (6381139771 on cc#341, 6381139642 on cc#344) promise "one scoped agent-identity model"; closing cc#341 outright would strand that promise on its own thread.
2. The maintainer tied the settlement to "#341's scope" (comment 6379582059) — the thread is the venue.
3. The surviving functionality (Layer 1 + the permission-line change) lives in exactly the files cc#341's branch owns: `common/views.py` permission/auth region, `mprov_control_center/settings.py`, `common/test_apikey_scope.py`.
4. The identity layer is *required* for cc#344's guard to coexist with any key write: without Layer 1, key requests arrive at `patch()` anonymous and the guard 403s every agent PATCH. Something must land that makes keys real principals — this branch is the natural vehicle.

The amended cc#341 becomes, in substance: *"Give API keys a named non-privileged service-user identity"* (title amendment at the filing lane's discretion). Its PR body must drop the `Fixes #315` claim (see the filing note below) — the #315 issue itself is the maintainer's to disposition; our in-thread reply states the exposure stands by operator ruling, and per-key capabilities are the recorded path back.

**Fallback, recorded not chosen:** if the maintainer prefers, cc#341 closes as won't-fix-with-ruling-note and the Layer-1 delta lands as a fresh PR; the cc#344 spec below is unchanged either way. Do not split further than this — one PR owns the identity layer.

Filing note for the amendment: edit the PR body's opening `Fixes #315` line to a bare `#315` reference (or "Coordinates with #315") **before** merge, so a merged cc#341-v2 does not auto-close #315 while its hazard text is still true. Same for any commit-message `Fixes` trailers on the branch.

### cc#344 — survives entirely, test rewritten

The `patch()` guard is the whole surviving security fix and it is *stronger* under v2 than under v1: every key write in the API still passes through a path that can never touch the superuser. Only its tests change (see spec below), plus the import reconciliation already foreseen in v1.

## Amendment specs (v2 — supersede the v1 specs entirely)

Dev cards must execute **these** specs, not v1's. Any card text referencing `AGENT_WRITE_RULES`, `MProvScopedAccess`, or the `?self` view guard is stale.

### PR cc#341 rescoped (branch `fix/mprov_control_center-315`, current head 75dfa76) — owns Layer 1 + the permission line

Files:
- `common/views.py` — remove the branch's `HasScopedAgentAPIKey` and its rules table (never merged, so: do not add them); add `AGENT_SERVICE_USERNAME = "mprov-agent"` and `AgentAPIKeyAuthentication(BaseAuthentication)` (KeyParser → `APIKey.objects.get_from_key` → expiry check → lazy `get_or_create` service user, unusable password, `is_staff=False`, `is_superuser=False`; invalid/absent key → `return None`); set `MProvView.permission_classes = [permissions.IsAuthenticated]`, replacing `HasAPIKey|IsAuthenticated`. Grep for other `HasAPIKey` uses before dropping its import. Keep the class docstrings; they are the API docs rendered by `getJSONDataStructure`.
- `mprov_control_center/settings.py` — append `common.views.AgentAPIKeyAuthentication` **last** in `DEFAULT_AUTHENTICATION_CLASSES` (after Session/Basic/Token).
- `systems/views.py` — **no change** (v1's `?self` guard spec is withdrawn).
- PR body — replace the `Fixes #315` opener with a bare `#315` reference (above).

Tests (`common/test_apikey_scope.py` — the v1 "keep all 6 existing" instruction is **void**; several of those tests assert refusals the ruling accepts):
- DELETE: key `DELETE /jobservers/1/` → **204**, executed as `mprov-agent` — the accepted hazard, pinned by test so the ruling is visible in the suite.
- key `PATCH /jobs/<id>/` → 200; key `POST /jobservers/` → 200; key `POST /ostypes/` → 200/201 (upsert preserved).
- Attribution: service-user fixture assertions — `mprov-agent` exists after the first key request, `is_superuser=False`, `is_staff=False`, `has_usable_password() is False` — and the admin-not-required proof: drop the `admin` superuser from `setUp` and show key writes still succeed (the write path neither needs nor impersonates admin).
- Anonymous: no key, no session → 403.
- Session unaffected: session-authenticated write → 200 as that user; and session-wins: a request with both a valid session and a stray Api-Key header authenticates as the session user.
- Removed with rationale in the PR body: `test_key_cannot_delete_jobs`, `test_key_can_register_jobservers_but_not_delete_them` (and any other denial-of-write test) — they asserted Option-B behavior the operator rejected.

### PR cc#344 (branch `fix/mprov_control_center-331`, current head 408cb5c) — owns the `patch()` guard, rebases on rescoped cc#341

Files:
- `common/views.py` — the `patch()` change **survives verbatim in shape**: admin lookup deleted, not-authenticated → 403 `"Anonymous PATCH mutations are not allowed."`; comment updated to the v2 rationale (key writes arrive as the `mprov-agent` service user; the 403 is defense in depth for views with zeroed permission classes, cf. `IPXEAPIView`). **Import reconciliation stands:** cc#344 deletes `from django.contrib.auth.models import AnonymousUser, User`; rescoped cc#341 needs `User` for the service user — after rebase only `AnonymousUser` goes, or the guard switches to `not request.user.is_authenticated` and both drop.
- `common/test_foundation.py` (`AnonymousPatchTests`) — rewrite:
  - `test_api_key_patch_is_rejected_not_run_as_admin` → renamed (e.g. `test_api_key_patch_runs_as_service_user_not_admin`): key PATCH `/jobmodules/nads/` → **200**, name updated, `admin` user absent from the fixture, write executed as `mprov-agent`. The 403 assertion is removed; "not run as admin" keeps its teeth via the no-admin-fixture construction.
  - keep `test_authenticated_patch_still_works` (200).
  - add: truly anonymous (no key, no session) PATCH → 403, object unchanged — #331's original symptom, now at the defense-in-depth layer.

### Merge order (required, unchanged from v1)

1. cc#341 rescoped lands first (owns the authentication layer and the permission line; cc#344's guard depends on keys resolving to real users).
2. cc#344 rebases on it, applies the patch()-only delta + test rewrite, lands second.

Both branches touch the same `common/views.py` `patch()`/imports region — treat `common/views.py` as a merge hotspot; do not let the two branches diverge longer than one rebase.

## Note for sw-pm (deliverable: project-9 rows and dev cards)

- **project-9 rows: no rescoping needed, one rule to observe.** cc#341 and cc#344 PullRequest rows stay **In Progress** — the ruling changes neither PR's open state, and a title amendment on the PR carries the row with it automatically. The trap to flag for the filing lane: per MPROV-MAINT-POLICY, the *fixed issue's* project-9 item moves Done when the PR claiming it merges. Rescoped cc#341 **no longer claims #315** — do not move #315's issue item when cc#341-v2 merges; only #331's issue item moves (when cc#344 lands). If #315 is later closed by the maintainer as won't-fix, that closure moves its own row.
- **Dev cards: none exist yet for this line; all future cards must cite this v2.** v1 deliberately deferred dev cards ("filed separately after operator visibility"); the ruling is now the visibility. Any card drafted from the v1 handoff metadata (which still describes `MProvScopedAccess`, the 8-tuple table, and the `?self` guard) is drafting from a superseded spec and must be drafted from this v2 instead: two cards (cc#341-rescoped, cc#344-rebase) or one card with the two-stage merge order; assignee sw-dev-a/sw-dev-b per lane policy; the above specs are complete enough that no re-deciding is needed.
- Reply drafts for both PR threads are filed at `mprov/filing-drafts/cc341-cc344-ruling-replies-2026-10-24.md` — distiller-gated, biondogs posts after gate, each carries the `Assisted by JoeBot` trailer and uberlinuxguy as reviewer.

## Alternatives rejected

- **Option B — mash requires a user login (rejected by operator ruling, not by analysis).** The allowlist would have stood as the complete key contract and a leaked key's write blast radius would shrink to 8 operations; but every deployed mash reads `jobserver.yaml`'s `apikey` and has no user-credential config path, and per-key separation (Refinement C) does not exist to distinguish a mash key from an agent key. The operator accepted the returning #315 hazard deliberately. Record, not argument: v1 §"Operator ruling required" briefed both options; the operator picked A.
- **cc#344 as filed (blanket anonymous-refusal).** Still rejected, unchanged from v1: it 403s every deployed agent client (jobserver stalls PENDING/RUNNING, stateful nodes reinstall on every boot, NIC/BMC registration dies) — and under the ruling it also 403s mash. The guard survives; the refusal scope does not.
- **cc#341 as filed (allowlist scoping, `HasScopedAgentAPIKey`).** Rejected twice over: v1's reason (fixes #315's hole but leaves all agent writes executing as the impersonated `admin` superuser, attribution fiction) plus the ruling's reason (the write-scoping premise itself is withdrawn). The identity half is kept; the permission half is withdrawn.
- **Keep the allowlist as "documentation-in-code" (`AGENT_WRITE_RULES` defined but unused).** Dead constants whose shape promises enforcement invite a future dev to wire them back in against the ruling, or worse, wire them in half. The inventory lives in this ADR (Appendix A) where it can seed Refinement C without pretending to run.
- **Per-client service users** (`mprov-jobserver`, `mprov-node`, `mprov-installer`). Unchanged from v1: one key is shared by all agents, so per-client users buy distinction the credential layer cannot deliver. Revisits with Refinement C.
- **Object-level / row-scoped permissions.** Unchanged from v1: a rewrite of every view for a belt the client cannot reach; the pre-existing `?self` endpoint already covers the one case that matters.

## Non-goals

- Implementation of any of the above (dev cards, filed by sw-pm from this v2).
- **Mitigating #315's key-exposure blast radius at the permission layer — removed as a goal by the ruling.** The exposure is accepted, pinned by test (key DELETE → 204), and its only sanctioned path back is Refinement C.
- Refinement C (per-key capabilities: scoped `APIKey` model + migration) — deferred by ruling; not to be built now, but this ADR is its design seed.
- The enrollment-token work (cc#336) — separate card, untouched.
- The `views_noauth.py` endpoints (`IPXEAPIView` et al.) — a separate, deliberate unauthenticated surface (kubevip/ipxe boot path); a future finding, not this model.
- Changing any client (jobserver, mprov_scripts, mprov_stateful.py, mash) — the server-side change is backwards-compatible with every verified call site and with mash by explicit ruling.
- Disposition of issue #315 itself — the maintainer's call; our in-thread reply supplies the ruling context.

## Consequences

- `request.user` is a real, named, non-privileged principal for every key-authenticated write; attribution is honest and #331's superuser impersonation is dead — **this holds under the ruling and is the surviving security value of the whole line**: even a leaked key can never again act *as the superuser*; it acts as `mprov-agent`, full-write but non-privileged.
- #315's API-write exposure **returns to (slightly better than) base**: a leaked key is full API write. The delta versus base `058886d` is identity: writes are named, never superuser, never anonymous. The operator accepted this deliberately; dev cards must not quietly restore scoping.
- The "table change, not code change" consequence of v1 is void — there is no table. A future agent 403 at the permission layer would now be a bug (wrong permission class), not a missing allowlist entry; the resolution path is this ADR, not a tuple.
- mash is untouched: key-file config, CLI key mode, arbitrary writes — all exactly as deployed. Its pre-existing user basic-auth mode (`app.py:195–199`) remains available for deployments that opt in; nothing requires it.
- When cc#341-rescoped lands, *nothing about any client's write behavior changes* — the v1 scheduling risk (mash losing key-write between merge and ruling) is dissolved by the ruling arriving first.
- Refinement C, when built, can restore the v1 allowlist without reopening the identity model: Layer 1 is capability-agnostic by construction (it resolves whichever key authenticated); the permission layer regains a table keyed on the key's capability column; Appendix A is the seed entry list; mash gets an admin-CLI key class and no deployment breaks.

## Revisit when (falsifiers)

- **A leaked-key incident attributable to full-write keys** → reopen with the operator; Refinement C (per-key capabilities + the Appendix A allowlist for agent keys) becomes the remediation path. This ADR names the falsifier plainly: the ruling's safety rests on key-handling discipline alone.
- `djangorestframework-api-key` ships per-key scopes/roles upstream, or the operator revisits the accepted hazard → build Refinement C; Layers 1 and 3 survive unchanged, Layer 2 grows the capability branch.
- The maintainer rejects rescoping cc#341 (asks for won't-fix instead) → take the recorded fallback: close cc#341 with the ruling note, land the Layer-1 delta as a fresh PR; cc#344's spec is unchanged either way.
- Agents are issued distinct keys (per host/client) → revisit per-client service users for attribution alongside Refinement C.
- Any verified key-authenticated call site 403s after this lands → a wiring bug (missing `AgentAPIKeyAuthentication`, wrong `permission_classes`), never "out of allowlist" — there is no allowlist.

## Amendment log

| version | commit | what changed |
|---|---|---|
| v1 | `b755603` (2026-10-24, t_5e0a4d72) | Original: three-layer model with 8-entry `AGENT_WRITE_RULES` enforcement, `?self` view guard, amendment specs for cc#341/cc#344, mash write-scope framed as open operator ruling. |
| v2 | this commit (2026-10-24, t_6d63915b) | Operator ruling folded (key keeps full write; mash unchanged; #315 hazard accepted; Refinement C deferred). Layer 2 collapsed to `[IsAuthenticated]`; `?self` view guard withdrawn; `AGENT_WRITE_RULES` demoted to non-normative inventory (Appendix A); status-code matrix rewritten; cc#341 disposition = rescope-in-place (with recorded fallback); cc#344 = guard + test rewrite; v1 amendment specs superseded in full; scheduling risk for mash dissolved. Layers 1 and 3 unchanged. |

## Appendix A — verified agent wire protocol (non-normative inventory; NOT an enforcement spec)

Reproduced from v1 for the record and as the Refinement C seed. Every row is a verified, Api-Key-only client call site at a pinned commit. Under v2 **all** of these — and everything else — are permitted to key principals; nothing here is enforced.

| # | Model + method | Path | Client call site (verified) |
|---|---|---|---|
| 1 | `jobqueue.jobserver` POST | `POST /jobservers/` | jobserver self-registration/heartbeat (upsert) |
| 2 | `jobqueue.job` PATCH | `PATCH /jobs/<id>/` | jobserver `app.py:259` @ b07393d — job status updates |
| 3 | `systems.systemimage` PATCH | `PATCH /systemimages/<slug>/?addjs` | jobserver `image_sync.py:126`, `image_update.py:132/399` |
| 4 | `osmanagement.osrepo` PATCH | `PATCH /repos/<id>/?addjs` | jobserver `repo_sync.py:128`, `repo_update_mod/rhel.py:67` |
| 5 | `systems.system` POST (`?self` variant) | `POST /systems/?self` `{"netboot": false}` | stateful installer `static/mprov_stateful.py:518` — netboot disable |
| 6 | `systems.networkinterface` PATCH | `PATCH /networkinterfaces/<id>/` | mprov_scripts `post-boot/register_IPv6_ll.py:62` @ a44f519 |
| 7 | `systems.systembmc` PATCH | `PATCH /systembmcs/<id>/` | mprov_scripts `post-boot/setupBMC.py:134` @ a44f519 |
| 8 | `osmanagement.ostype` POST | `POST /ostypes/` | jobserver `image_update_mod/rhel.py:27`, `repo_update_mod/rhel.py:24` (upsert) |

Plus, by ruling: **mash** — arbitrary POST/PATCH/DELETE on every model by key (`app.py:557–563`, key from `jobserver.yaml` at `app.py:183–185`).

In-thread reply drafts answering the maintainer's binary on both PR threads live at `mprov/filing-drafts/cc341-cc344-ruling-replies-2026-10-24.md` (distiller-gated; biondogs posts after gate).
