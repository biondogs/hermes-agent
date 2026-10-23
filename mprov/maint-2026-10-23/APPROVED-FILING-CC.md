# APPROVED-FILING — biondogs/mprov_control_center (MPROV-M wave, 2026-10-23)

Adjudication: sw-architect, t_43e4e008, 2026-10-23. Register: `cc-sweep-2026-10-23.issues.yaml`
(CC-041..CC-051, validator PASS) + `cc-oct15-dispositions.md` (fork issues #4–#43) from t_2eae052c.
Pins: reviewed at upstream d7c2094 (264 commits past Oct-15 base 98d4579); fork head 7384c63.
Status: **ADJUDICATED — all 11 NEW findings APPROVED** (one severity amendment: CC-051 S2→S1).
Gate: distiller PASS required before the filing card (t_31448dcb) runs. Issues only (Rule D).
Open-PR check (operator requirement, 2026-10-23): no NEW finding is covered by an open PR on
upstream or fork (PR-by-PR analysis in ADJUDICATION-2026-10-23.md §4).

## A. New issues to file (11)

### CC-041 — labels: `bug,s3-robustness,review-found`
Title: `[S3] IPv6 jobserver addresses lack bracket wrapping in image URLs`

```text
symptom: A node booting from an image served by an IPv6 jobserver fails to fetch kernel,
initramfs or image: the download URL is invalid because the IPv6 literal is not
bracketed. IPv4 deployments are unaffected.
evidence: systems/views_noauth.py:84-86 — the two bracket-wrap lines sit commented out
immediately above `imageURL = "http://" + js.address + ":" + str(js.port) + "/images/..."
(plain concatenation); the identical wrap IS active on the osrepos path at
osmanagement/views_noauth.py:78-79, so the work was started and abandoned, not omitted.
root cause: IPv6 bracket wrapping never applied to the image-path URL construction.
proposed fix: Re-enable the two commented lines and bracket-wrap the jobserver address at
every URL-construction site so images and osrepos behave identically.
severity: S3 — happy path (IPv4) works; IPv6 transport degrades with no error beyond a
failed download.
```

### CC-042 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Script save crashes with AttributeError when script type is null`

```text
symptom: After a ScriptType is deleted, saving any dependent Script (or File /
AnsiblePlaybook / AnsibleRole sharing the pattern) from admin or API raises
AttributeError ('NoneType' has no attribute 'slug') — a 500 on every save until a
type is force-reassigned, stranding that content.
evidence: scripts/models.py:30 — `scriptType = ForeignKey(ScriptType,
on_delete=SET_NULL, null=True)` makes a null type a legal DB state; unguarded
`self.scriptType.slug` dereferences at scripts/models.py:47-53, :68, and :139/:148
(playbooks).
root cause: Every save/filename path dereferences scriptType without a null guard.
proposed fix: Guard each dereference and handle a null type explicitly (validation
error), or switch the FK to PROTECT if a typeless script is not a supported state.
severity: S3 — legal-state edge input crashes content management in admin and API.
```

### CC-043 — labels: `bug,s3-robustness,review-found`
Title: `[S3] PXE bootdev ipmitool exit status ignored so failed setup reports success`

```text
symptom: Admin and API PXE provisioning power-cycle a node even when setting its boot
device failed (wrong BMC password, unreachable BMC): the flow reports success while the
node reboots into its old OS.
evidence: systems/views.py:917-920 and systems/admin.py:289-292 —
`subprocess.run(args=ipmitool_cmd, env=ipmitool_env)` with the result discarded; only
OSError is caught, never the exit status.
root cause: The ipmitool return code is unchecked and no timeout is set, so
application-level failures are indistinguishable from success and the forced chassis
reset proceeds regardless.
proposed fix: Check the return code, add a timeout, surface stderr to the
response/admin message, and skip the forced reset when bootdev failed.
severity: S3 — happy path works; adverse BMC condition yields a false success that is
found only by hand.
```

### CC-044 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Change signals reset in-flight jobs to pending under the same name`

```text
symptom: Editing a NIC, network, OS repo or system while a jobserver is already RUNNING
that regeneration job flips the running row back to PENDING: the job runs twice with
different configuration data or its completion status is lost, yielding stale node
configuration.
evidence: `Job.objects.update_or_create(name=..., module=..., defaults={'status': 1})`
at networks/models.py:133-136, systems/models.py:372-375 and :414, the OSRepo signals,
and the register flow (systems/views.py:157) — six sites, all skipping the queue_job
helper in common/__init__.py which only creates when no PENDING row exists.
root cause: Regeneration jobs re-queued by blindly resetting status keyed only on
name/module.
proposed fix: Route all six sites through queue_job, or add a current-status guard so
RUNNING or COMPLETED rows are never blindly reset.
severity: S3 — requires an edit inside a job's execution window; happy path works.
```

### CC-045 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Jobserver registration endpoint returns double-encoded JSON`

```text
symptom: A client that parses the jobserver registration POST reply per the documented
JSON contract receives a string, not an object, and must decode twice; the error branch
is misshapen the same way.
evidence: jobqueue/views.py:320 and :323 — `Response(data=json.dumps(data))` hands
pre-encoded JSON text to a DRF Response, which JSON-encodes the string a second time.
root cause: Manual json.dumps of a payload passed to DRF's serializer-aware Response.
proposed fix: Pass the plain dictionary to Response and let DRF do the encoding, on
both the success and error branches.
severity: S4 — no shipped consumer parses this body today; only new/plugin clients hit
the broken contract. Upstream twin: mprov-ng#268.
```

### CC-046 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Admin add wizard mutates shared ModelAdmin state per request`

```text
symptom: Two admin users adding systems at the same time (or one user with two tabs)
see each other's wizard steps: the wrong form fields can be shown or required for a
step. Single-user operation is unaffected, which is why it survives casual testing.
evidence: common/admin.py:21-25 — AdminWizardModel's __init__ empties inlines and
readonly_fields on the process-wide shared admin instance, and get_form stores the
current wizard step on that same instance per request.
root cause: Per-request wizard state kept on a shared singleton ModelAdmin instance
instead of the request session.
proposed fix: Keep the step in the user's session and derive per-request field/inline
sets in request scope, leaving the shared instance untouched.
severity: S3 — interleaved requests corrupt each other's state under multi-operator
use. Upstream twin: mprov-ng#270.
```

### CC-047 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Container init captures Django shell banner into the jobserver API key`

```text
symptom: On a fresh container start under a Django version that prints a shell banner,
the generated jobserver API key is corrupted (banner text prepended) and written to
/etc/mprov; every jobserver configured from it then fails authentication, invisibly
until registration fails.
evidence: install_scripts/init_mpcc.sh:214 —
`apikey=`cat /tmp/genAPIKey.py | python3 manage.py shell`` captures the entire stdout
of an interactive shell, banner included.
root cause: Key generated by piping a script into an interactive manage.py shell and
capturing all output, instead of emitting only the key.
proposed fix: Generate the key non-interactively (shell -c with a script that prints
just the key, or write the key to a file and read it back) so only the key is captured.
severity: S3 — environment-version-dependent credential corruption on first run.
Upstream twin: mprov-ng#288.
```

### CC-048 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Container runs bash as PID 1 and ignores SIGTERM so docker stop kills hard`

```text
symptom: Every docker stop, restart or host shutdown waits out the grace timeout and
then SIGKILLs the mPCC container: Apache children never drain and in-flight requests
are killed on each cycle.
evidence: install_scripts/init_mpcc.sh:230 — the entrypoint keeps bash as PID 1 and
traps SIGINT only; the SIGTERM that docker stop delivers is never handled or forwarded.
root cause: No SIGTERM trap/forwarding and no exec of the final server process.
proposed fix: Trap SIGTERM alongside SIGINT and forward it to the child, or exec the
server so it becomes PID 1 and receives signals directly.
severity: S4 — noisy operational delays and killed in-flight requests; no data
corruption. Upstream twin: mprov-ng#290.
```

### CC-049 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Stateful installer judges the fill partition by the previous loop variable`

```text
symptom: A disklayout mixing RAID members with a fill partition installs a node whose
remainder-of-disk volume is left unformatted and absent from fstab even though it
carries a filesystem and mount point.
evidence: static/mprov_stateful.py:219-226 — after the partition loop, the
format-or-skip decision reads `part['filesystem']`/`part['mount']` (the leftover loop
variable of the LAST regular partition) while every action applies to `fillpart`; when
the last regular partition is a RAID member, the fill partition is skipped entirely.
root cause: Stale loop variable consulted instead of fillpart's own fields.
proposed fix: Test fillpart['filesystem'] and fillpart['mount'] instead of the stale
loop variable, so the fill partition is formatted and recorded unless it is itself a
raid member.
severity: S3 — wrong node disk state under a named layout condition. Upstream twin:
mprov-ng#273. Same pattern as mprov_scripts fork issue #8 (post-boot/localTempDisk.py)
— distinct code site, fix BOTH copies.
```

### CC-050 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Stateful installer RAID member loop can use a stale or unset disk variable`

```text
symptom: A disklayout whose RAID references a missing or renamed disk slug makes the
installer crash on an unbound variable or silently reuse the previous member's disk:
mdadm and partition math act on the wrong device — destructive partition changes can
hit the wrong disk.
evidence: static/mprov_stateful.py:240-246 — the member loop assigns `dev` only on a
slug match with no not-found handling; `partOffset = 0` and the bootdisk comparison
then run on the unbound/stale value.
root cause: RAID member resolution has no validation for a member that matches no
disk entry.
proposed fix: Fail immediately with a clear error when a member resolves to no disk
entry, so the installer aborts BEFORE any destructive command instead of proceeding
with a stale device.
severity: S3 — unguarded destructive path under an adverse layout. Upstream twin:
mprov-ng#274. Parallel defect in mprov_scripts fork issue #4 — distinct code site,
fix BOTH copies.
```

### CC-051 — labels: `bug,s1-blocker,review-found`
Title: `[S1] OSDistro API serializer returns the distro root password in cleartext`

```text
symptom: Any holder of the shared API key can read the root password baked into every
node installed from a distribution: the OSDistro API list and detail responses
include rootpw in cleartext — an agent credential becomes fleet-wide node login.
evidence: osmanagement/serializers.py:8-14 — OSDistroAPISerializer with
`fields = '__all__'`; osmanagement/models.py:70 — rootpw CharField (default
"changeme") is the install root password. BMC passwords were made write-only
upstream; this credential class stayed readable.
root cause: `fields = '__all__'` instead of an explicit field list; the BMC
write-only treatment never extended to the distro rootpw.
proposed fix: Exclude rootpw from the API serializer or mark it write-only, matching
the BMC-credential treatment, keeping it settable on write.
severity: S1 — secret exposure with a concrete path (any API key reads every
installed node's root password). Open remainder of fork issue #5 (Oct-15 S1 class);
source-verified at d7c2094.
```

## B. Verdicts — no other new filings

All 11 register findings are approved above; nothing rejected, nothing deduped away.
CC-049/CC-050 mirror mprov_scripts fork issues #8/#4 as parallel implementations in a
different repo — kept as separate filings (the fix must land in both repos), bodies
cross-referenced.

## C. Existing fork issue actions (CC #4–#43; details: cc-oct15-dispositions.md)

- **Close by comment (18, fixed upstream at d7c2094)** — cite the upstream commit refs
  in cc-oct15-dispositions.md and upstream's own REVIEW-2026-10.md:
  #6 (S-01 ed147bf), #11 (installer removed, DEAD-08), #14 (H-01 8d6cdfd), #15, #16
  (c6819c9), #18, #19 (D-19), #20, #22 (D-20/c6819c9), #23 (H-10), #24 (H-04), #27
  (dead code removed), #32 (DEAD-07), #33 (S-01), #37 (F-version persist), #38 (D-23/24),
  #40 (H-05), #42.
- **Keep open, narrowed comment (4 partials + 1)**:
  - #39 (CC-036 lint-CI): upstream added a real test/build CI; lint gates still absent
    — narrow the issue to the lint-gate remainder (adjudicated: keep open, narrowed).
  - #5: BMC list password fixed (ed147bf); OSDistro rootpw remains open — now covered
    by NEW issue CC-051; cross-link them.
  - #29: power-by-id site fixed; powerstate (views.py:327) and addjs (:714) remain.
  - #35: systems register guarded; jobqueue (views.py:297,303-315,112,121) and
    osmanagement (views.py:221-225) sites remain.
- **Still present at pin (21: #4,#7,#8,#9,#10,#12,#13,#17,#21,#25,#26,#28,#30,#31,#34,
  #36,#41,#43)** — no new filing; optionally a one-line "still present at d7c2094"
  comment. #43 (CC-040) re-confirmed at head, including against open upstream PR #306
  (it renames _doPowerCmd and adds provisioning gating but leaves hostname__contains
  and the [:10] truncation untouched).
