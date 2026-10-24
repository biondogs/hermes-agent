# ADR-0001 (mprov series): One scoped agent-identity model — a valid API key IS the agent's identity, a named limited service user with an explicit write allowlist

**Status:** Accepted (maintainer direction, cc#344 comment 6379582059 + cc#341 comment 6379582239, both 2026-10-24T03:59Z; acks by biondogs 6381139771 / 6381139642 promise exactly "one scoped agent-identity model"). One sub-question (mash's write scope) is **framed for operator ruling below and deliberately not decided here** — it does not block the agent model or either PR amendment.
**Deciders:** uberlinuxguy (direction) · sw-architect (formulation) · Card: MPROV-CC-APIKEY-DESIGN (t_5e0a4d72, filed by sw-pm; plain-text ref to FILING-WATCH t_b2d3c1c0 — not a parent edge by design, that card never completes)
**Relates to:** PR cc#341 (fix/mprov_control_center-315, head 75dfa76, fixes #315) · PR cc#344 (fix/mprov_control_center-331, head 408cb5c, fixes #331) · base `mprov-ng/mprov_control_center` main @ 058886d · dependency pin `djangorestframework-api-key==3.1.0` (no authentication module ships; `KeyParser` + `APIKey.objects.get_from_key()` + `HasAPIKey` are the whole surface) · out of scope: enrollment-token work (cc#336).

## Context

Two open PRs fix two real holes and contradict each other:

- **cc#341** ("Scope API key permission to what the jobserver agent needs", fixes #315): today `MProvView.permission_classes = [HasAPIKey|IsAuthenticated]`. The OR passes on a valid Api-Key alone, with **no user at all**, so any key holder is a full API admin (key-only `POST /jobs/` → 201, `DELETE /jobservers/1/` → 204). cc#341 replaces `HasAPIKey` with `HasScopedAgentAPIKey | IsAuthenticated`: safe methods plus a 4-entry `agent_write_rules` table, everything else requires a login.
- **cc#344** ("Reject anonymous PATCH mutations instead of running as admin", fixes #331): `MProvView.patch()` (common/views.py:212–214 @ 058886d) substitutes `User.objects.get(username='admin')` whenever `request.user` is anonymous. A key-authenticated request passes the permission gate anonymously, hits this path, and every PATCH is executed and recorded **as the superuser**. cc#344 refuses all anonymous PATCHes with 403.
- **The contradiction:** every deployed mProv agent client (jobserver, node post-boot scripts, stateful installer, mash) authenticates with **only** an `Api-Key` header — never a session. cc#344 therefore 403s the exact `PATCH /jobs/<id>/` that cc#341's test asserts returns 200, and would stall the jobserver (no job ever leaves PENDING/RUNNING), brick the stateful installer's netboot disable (node reinstalls on every boot), and break NIC/BMC registration.
- **Maintainer direction** (cc#344 comment 6379582059): "treat a valid API key as the agent's identity: a named, limited service user, as the issue suggests, rather than refusing it… settled together with #341's scope." cc#341 comment 6379582239 adds the missing allowlist entries (installer `?self` netboot disable, networkinterfaces/systembmcs PATCHes, ostypes POSTs) and names the mash question: "should an API key keep full write access for an admin CLI, or should mash need a user login?"

## Decision

Adopt the maintainer's model, refined into three layers. **One scoped agent-identity model**: a valid Api-Key resolves to the agent's identity — a single named, non-privileged Django service user — and that identity may write only what the verified agent protocol actually sends, per an explicit table.

### Layer 1 — Authentication: the key IS an identity (`AgentAPIKeyAuthentication`)

New DRF authentication class in `common/views.py` (the package ships none; build it on the pinned 3.1.0 surface):

```python
class AgentAPIKeyAuthentication(BaseAuthentication):   # rest_framework.authentication
    # KeyParser: rest_framework_api_key.permissions.KeyParser  (keyword "Api-Key")
    # validate via APIKey.objects.get_from_key(key)  (raises APIKey.DoesNotExist
    #   if bad/revoked) and api_key.has_expired
    # authenticate() returns (service_user, api_key) or None (invalid/absent key
    #   → request stays anonymous → permission layer denies with 403)
```

On first success it lazily does `User.objects.get_or_create(username='mprov-agent', is_staff=False, is_superuser=False)` with an unusable password. Lazy creation, **not** a data migration: the `common` app has no `migrations/` package today and the other apps' migration chains must not take a dependency on an auth fixture. Idempotent `get_or_create` is safe.

`settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` becomes `[SessionAuthentication, BasicAuthentication, TokenAuthentication, AgentAPIKeyAuthentication]` (agent class **last**). Consequence, stated as a rule: **a logged-in session wins over a stray Api-Key header** — DRF stops at the first authenticator that claims the request.

### Layer 2 — Permission: one class, one table (`MProvScopedAccess` + `AGENT_WRITE_RULES`)

`MProvView.permission_classes = [MProvScopedAccess]` replaces the entire OR composition. Branch on principal type via `isinstance(request.auth, APIKey)`:

- **Session/basic/token user** (human/admin): full access, unchanged.
- **Key-authenticated agent**: safe methods allowed; a write allowed **iff** `('app.model', method)` is in `AGENT_WRITE_RULES`; otherwise 403.

**The trap that forces the single class:** once the key resolves to a real authenticated user (Layer 1), any residual `… | IsAuthenticated` arm passes for the service user on *every* write — reopening #315 through the back door. The OR must be dissolved, not extended. cc#341's existing `test_key_cannot_delete_jobs` / `test_key_can_register_jobservers_but_not_delete_them` (key DELETE → 401/403) are the regression guards for exactly this trap and must be kept.

### Layer 3 — View: `patch()` stops impersonating admin, does not refuse the agent

`MProvView.patch()` keeps **cc#344's fix verbatim in shape**: no `admin` lookup ever; if `request.user` is not authenticated → 403. Under the unified model the key-authenticated agent arrives at `patch()` already authenticated as `mprov-agent`, so allowlisted PATCHes run **as the service user** — neither superuser nor refused. The anonymous 403 remains as defense in depth: this codebase already has views that zero out `permission_classes` (e.g. `IPXEAPIView`), so the write path must not assume the permission layer always ran.

One view-level tightening carries the "limited" in "limited service user" (a query param is invisible to model-level permission rules):

- `SystemAPIView.post()`: if `isinstance(request.auth, APIKey)` and `'self'` not in `request.query_params` → 403. The `?self` handler already binds to the **requester's IP** (`get_client_ip`-style resolution → NIC → system) and already 403s any body key other than `netboot`; the grant is only ever "a machine may edit itself."

### The allowlist — `AGENT_WRITE_RULES` (8 entries, all from verified call sites)

| # | Rule tuple | Method + path | Client call site (verified) | Expected status |
|---|---|---|---|---|
| 1 | `('jobqueue.jobserver', 'POST')` | `POST /jobservers/` | jobserver self-registration/heartbeat (upsert) — cc#341 test: 200 | 200 |
| 2 | `('jobqueue.job', 'PATCH')` | `PATCH /jobs/<id>/` | jobserver `app.py:259` @ b07393d — job status updates | 200 |
| 3 | `('systems.systemimage', 'PATCH')` | `PATCH /systemimages/<slug>/?addjs` | jobserver `image_sync.py:126`, `image_update.py:132/399` — "this jobserver hosts this image" | 200 |
| 4 | `('osmanagement.osrepo', 'PATCH')` | `PATCH /repos/<id>/?addjs` | jobserver `repo_sync.py:128`, `repo_update_mod/rhel.py:67` — same for repos | 200 |
| 5 | `('systems.system', 'POST')` | `POST /systems/?self` `{"netboot": false}` — **only** the `?self` variant (Layer-3 view guard) | stateful installer `static/mprov_stateful.py:518` — netboot disable; failure ⇒ stateful node reinstalls every boot | 200; `POST /systems/` non-self by key → **403** |
| 6 | `('systems.networkinterface', 'PATCH')` | `PATCH /networkinterfaces/<id>/` | mprov_scripts `post-boot/register_IPv6_ll.py:62` @ a44f519 — IPv6 LL registration | 200 |
| 7 | `('systems.systembmc', 'PATCH')` | `PATCH /systembmcs/<id>/` | mprov_scripts `post-boot/setupBMC.py:134` @ a44f519 — BMC registration | 200 |
| 8 | `('osmanagement.ostype', 'POST')` | `POST /ostypes/` | jobserver `image_update_mod/rhel.py:27`, `repo_update_mod/rhel.py:24` — ostype registration (upsert: existing slug → 200 empty, new → 201) | 200 / 201 |

Everything else — `POST /jobs/`, `DELETE` anything, `PATCH /jobmodules/`, writes to any model not listed — is human-only: session/basic/token auth required, key-only → 403. `PATCH /ostypes/` is **not** granted (no client sends it; entry 8's upsert covers the need).

### Status-code matrix (reconciles the cc#344↔cc#341 test conflict)

| Call | Base `058886d` (today) | After the unified model |
|---|---|---|
| key GET (any model) | 200 | 200 |
| key `POST /jobservers/` (register) | 200 | 200 (as `mprov-agent`) |
| key `PATCH /jobs/<id>/` | 200 **run as admin** (#331) | 200 (as `mprov-agent`) — **cc#341's test stands unchanged** |
| key `PATCH /systemimages|/repos ?addjs` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /systems/?self` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /systems/` (no `?self`) | 201 **hole** | **403** (view guard) |
| key `PATCH /networkinterfaces/`, `/systembmcs/` | 200 as admin | 200 (`mprov-agent`) |
| key `POST /ostypes/` | 200/201 as admin | 200/201 (`mprov-agent`) |
| key `POST /jobs/` | 201 **hole** (#315) | 403 |
| key `DELETE /jobservers/<id>/` (or any DELETE) | 204 **hole** | 403 |
| key `PATCH /jobmodules/<slug>/` | 200 **run as admin** (#331) | **403, object unchanged** — cc#344's test stands unchanged **because jobmodule is not allowlisted** |
| no key, no session, any write | 403 (permission gate) | 403 (permission gate; `patch()` guard is defense in depth) |
| session-authenticated write | 200 (as that user) | 200 (as that user) |
| mash's arbitrary POST/PATCH/DELETE by key (`app.py:557–563`) | full write | 403 pending operator ruling (below) |

**The cc#344 test conflict, stated exactly:** cc#344's `test_api_key_patch_is_rejected_not_run_as_admin` (key PATCH `/jobmodules/nads/` → 403, name still `NADS`) remains valid **only** under the new rationale "**the service user may not write outside `AGENT_WRITE_RULES`**," not "anonymous PATCHes are refused." Any amendment that reasserts a blanket "key PATCH ⇒ 403" is wrong and must fail review: cc#341's `test_key_can_patch_job_status` (→ 200) is the binding counter-test. The two PRs stop contradicting each other precisely where each test's model is in the table above.

## Operator ruling required (NOT decided here): mash's write scope

mash (admin CLI) authenticates by reading `jobserver.yaml`'s `apikey` by default (`app.py:183–185`; also CLI `connect <url> apikey <key>`, `app.py:169/195`) and issues arbitrary POST/PATCH/DELETE on every model (`app.py:557–563`). Under the agent model above it gets read-only. **Both options briefed; the operator must pick; the ruling changes nothing about the agent allowlist or Layer 1–3 — it is orthogonal.**

- **Option A — the API key keeps full write for the admin CLI.** Implement by treating any valid key as a full principal for non-`mprov-agent`… concretely: `MProvScopedAccess` grants writes to key-authenticated principals without consulting the table (or a capability flag; see below). *Blast radius:* zero client/config changes; mash works exactly as deployed — but cc#315's real-world hazard returns in full: every leaked/cloned jobserver key (one per cluster, distributed to every jobserver host) is again full API admin, including `DELETE /jobservers/`, `DELETE /systems/`. The allowlist then defends nothing against the most numerous credential in the deployment.
- **Option B — mash requires a user login.** The allowlist stands as the complete key contract. mash already has a non-key auth path (its `user` basic-auth mode, `app.py:195–199`); the change is deployment/config: `jobserver.yaml` carries user credentials instead of `apikey` (config-file support for the user path must be verified in mash before this option is ruled — `app.py:169` today shows it as a CLI mode). *Blast radius:* every mash deployment needs a config + possibly code change; admin credentials live in `jobserver.yaml`/CLI usage; runbook and docs updates; in exchange, keys become agent-only and the allowlist is the true blast radius of a key leak.
- **Refinement C (future, either option): per-key capabilities.** `djangorestframework-api-key` 3.1.0's `APIKey` model has no role/scope column, so A and B are currently **global** choices — one class of key. If the ruling comes back "both must work," extend `APIKey` with a scoped model + migration (agent key vs. admin-CLI key) rather than reopening the global write. Do not build this pre-ruling.

## Alternatives rejected

- **cc#344 as written (blanket anonymous-refusal).** Direct break of every deployed agent client, enumerated by the maintainer himself: jobserver stalls PENDING/RUNNING forever, stateful nodes reinstall on every boot, NIC/BMC registration dies. Rejected on maintainer's own client-impact evidence (comment 6379582059).
- **cc#341 as written (permission-only scoping, no named identity).** Fixes #315's hole but leaves all agent writes executing as the impersonated `admin` superuser via `patch()` (cc#331 latent), and leaves agent POSTs (register, `?self`, ostypes) executing as `AnonymousUser`, so any future serializer/model logic keyed on `request.user` is wrong and attribution/audit stays fiction. The maintainer's "named" is load-bearing: identity must exist **before** the write, not after.
- **Per-client service users** (`mprov-jobserver`, `mprov-node`, `mprov-installer`). Right shape for attribution if there were distinct credentials; today one key (`mProv Jobserver Key`, created by `install_scripts/init_mpcc.sh`) is shared by all agents, so per-client users buy distinction the credential layer cannot deliver. Revisit when keys are issued per client (would pair naturally with Refinement C).
- **Object-level / row-scoped permissions (agent may only touch its own jobs/NICs).** Correct end-state for `?self`-style safety, but DRF object permissions + this codebase's view overrides are a rewrite of every view. The `?self` view guard delivers the one case that matters (a machine editing itself); the rest is belt the client cannot currently reach.

## Amendment specs

### PR cc#341 (branch `fix/mprov_control_center-315`, current head 75dfa76) — owns Layers 1–2

Files:
- `common/views.py` — replace `HasScopedAgentAPIKey` with: `AGENT_SERVICE_USERNAME = "mprov-agent"`, `AGENT_WRITE_RULES` (the 8 tuples above), `AgentAPIKeyAuthentication(BaseAuthentication)` (KeyParser → `APIKey.objects.get_from_key` → expiry check → lazy `get_or_create` service user, unusable password, `is_staff=False`, `is_superuser=False`; invalid/absent key → `return None`), `MProvScopedAccess(permissions.BasePermission)` (branch on `isinstance(request.auth, APIKey)`; model key via `view.model` or `view.queryset.model`; non-safe non-listed → False); `MProvView.permission_classes = [MProvScopedAccess]`. Keep the class docstrings; they are the API docs rendered by `getJSONDataStructure`.
- `mprov_control_center/settings.py` — append `common.views.AgentAPIKeyAuthentication` **last** in `DEFAULT_AUTHENTICATION_CLASSES` (after Session/Basic/Token).
- `systems/views.py` — `SystemAPIView.post()`: first statements become the `?self`-only guard for key-authenticated callers (403).

Tests (`common/test_apikey_scope.py`, keep all 6 existing — the DELETE tests are the OR-trap regression guards — and add):
- key PATCH `/networkinterfaces/<id>/` → 200; key PATCH `/systembmcs/<id>/` → 200.
- key POST `/systems/?self` from the test client's REMOTE_ADDR with a NIC fixture → 200 and that system's NICs `bootable=False`.
- key POST `/systems/` **without** `?self` → 403, system count unchanged (the hole #315-style, at the view layer).
- key POST `/ostypes/` new slug → 201; existing slug → 200 with empty body (upsert preserved).
- service-user fixture assertions: `mprov-agent` exists after first key request, `is_superuser=False`, `is_staff=False`, `has_usable_password() is False`.
- the agent writes are attributed: after a key PATCH on `/jobs/`, re-authenticate as `mprov-agent`… least-fragile form: assert `response.status_code == 200` and that no `admin` user is required to exist for the write path to succeed (drop the `admin` superuser from this test's `setUp` and show the agent write still succeeds — proves the write is not executing as admin).

### PR cc#344 (branch `fix/mprov_control_center-331`, current head 408cb5c) — owns Layer 3, rebases on amended cc#341

Files:
- `common/views.py` — the `patch()` change **survives as designed**: admin lookup deleted, not-authenticated → 403 `"Anonymous PATCH mutations are not allowed."`. Comment updated to the new rationale (service-user path; guard = defense in depth, cf. `IPXEAPIView`'s zeroed permission classes). **Reconcile the import:** cc#344 deletes `from django.contrib.auth.models import AnonymousUser, User`; amended cc#341 needs `User` again for the service user — after rebase only `AnonymousUser` goes (or the guard switches to `not request.user.is_authenticated` and both drop).
- `common/test_foundation.py` (`AnonymousPatchTests`) — keep `test_api_key_patch_is_rejected_not_run_as_admin` (403 + `NADS` unchanged; re-word the comment: refused **because jobqueue.jobmodule is not in AGENT_WRITE_RULES**, not because key PATCHes are blanket-refused) and `test_authenticated_patch_still_works` (200). Add: (a) key PATCH on an allowlisted model (job status) → 200 — the binding counter-test that ends the conflict with cc#341; (b) truly anonymous (no key, no session) write → 403, never admin-executed — #331's original symptom, now at the defense-in-depth layer.

### Merge order (required)

1. cc#341 amended lands first (it owns the permission and authentication design).
2. cc#344 rebases on it, applies the patch()-only delta + tests, lands second.
Both branches touch the same `common/views.py` `patch()` region — treat `common/views.py` as a merge hotspot; do not let the two branches diverge longer than one rebase.

## Non-goals

- Implementation of any of the above (dev cards, filed separately after operator visibility).
- The enrollment-token work (cc#336) — separate card, untouched.
- The `views_noauth.py` endpoints (`IPXEAPIView` et al.) — a separate, deliberate unauthenticated surface (kubevip/ipxe boot path); a future finding, not this model.
- Changing any client (jobserver, mprov_scripts, mprov_stateful.py, mash) — the design is server-side and backwards-compatible with every verified call site.
- Deciding the mash write-scope question (operator ruling, above).

## Consequences

- `request.user` is a real, named, non-privileged principal for every key-authenticated write; attribution is honest and #331's superuser impersonation is dead.
- Any future agent write that 403s in the field is a **table change, not a code change** — the 8-tuple table is the wire contract between mPCC and its agents, and new call sites get added to it by PR (with the client call-site evidence, as this ADR's table does).
- A leaked jobserver key's write blast radius shrinks from "entire API, as admin" to "the 8 allowlisted operations" — unless Option A wins the mash ruling, in which case the table's protection against key leaks evaporates and this ADR's security value rests on key handling discipline alone.
- Mash admins lose write-by-key the moment cc#341-amended lands, before the ruling. Sequence mitigation: if the operator cannot rule before merge, land with the allowlist (Option B behavior) and treat any mash breakage reports as the ruling input — or hold the merge for the ruling. **Flag for sw-pm: this sequencing vs. ruling timing is the one scheduling risk.**

## Revisit when (falsifiers)

- Any verified agent call site gets a 403 in integration testing → the table is missing an entry; add it with client evidence (the table serves clients, not the reverse).
- `djangorestframework-api-key` adopts per-key scopes/roles upstream, or the operator picks "A and B both" → build Refinement C (scoped `APIKey` model + migration) and split keys per client class; the single user splits with it.
- mProv grows per-object permissions → replace the `?self` view guard with object-level rules for the agent principal; Layers 1–2 survive unchanged.
- Agents are issued distinct keys (per host/client) → revisit per-client service users for attribution.
