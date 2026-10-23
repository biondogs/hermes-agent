# APPROVED-FILING — biondogs/mprov_jobserver (MPROV-M wave, 2026-10-23)

Adjudication: sw-architect, t_43e4e008, 2026-10-23. Register:
`js-sweep-2026-10-23.issues.yaml` (t_a43d97bb): PART A re-derives the 31 Oct-15 fork
issues (all ALREADY-FILED), PART B carries 18 NEW findings (JSR2-01..18) plus one
flagged supplementary site (JSR2-19) belonging to fork issue #3.
Pins: fork 00d00bfd (product-identical to Oct-15 base 4f73fc1 — 0 src/ diffs); upstream
head checked 1fd4b123 (28 commits ahead, per-commit reviewed).
Status: **14 NEW APPROVED; 4 not filed — fixed upstream at head (merged PRs verified);
JSR2-19 folded into fork issue #3.**
Gate: distiller PASS required before the filing card (t_31448dcb) runs. Issues only (Rule D).
Open-PR check (operator requirement): upstream's open PR #152 is tests-only and the open
PR #153 is docs-only — no NEW or filed finding is covered; fork has no open PRs.

## A. New issues to file (14)

### JSR2-01 — labels: `bug,s2-functional,review-found`
Title: `[S2] Pulled images are re-downloaded in full every heartbeat, forever`

```text
symptom: An image-update jobserver that pulls an image from a peer re-downloads the
entire .img/.initramfs/.vmlinuz set on every heartbeat pass (default 10s), generating
permanent network and disk churn and rewriting the .img while clients may be fetching
it.
evidence: src/mprov_jobserver/plugins/image_update.py:137-163 — after the download
block writes image-versions (lines 162-163), imgVersions[image] was never set to
imageData['version']; contrast image_sync.py:109 which does record it.
root cause: The sync-from-peer path omits the version update and the
add-self-to-jobservers patch, so the version mismatch condition (line 137) stays true
on every pass.
proposed fix: Set imgVersions[image] = imageData['version'] after a successful peer
pull, write the file, then run the same addjs patch as the equal-version branch.
severity: S2 — wrong steady-state behavior in ordinary operation. Source-verified by
the adjudicator at 00d00bfd.
```

### JSR2-02 — labels: `bug,s2-functional,review-found`
Title: `[S2] Configured imageList path crashes: removal during iteration, then .items() on a list`

```text
symptom: With a config-supplied imageList, image-update either skips entries or dies
with AttributeError ('list' has no attribute 'remove at .items()'), never processing
the update.
evidence: src/mprov_jobserver/plugins/image_update.py:240-247 —
self.imageList.remove(image) inside `for image in self.imageList:`; :263 —
`for image,jid in self.imageList.items():` on the same list.
root cause: The configured-list branch mutates the list mid-iteration, then treats the
remaining list as a dict (copy-paste from the None branch which builds a dict at
:222).
proposed fix: Iterate over a copy for the removal pass and convert the survivor list
into {image: jid} (or iterate the list directly) before line 263.
severity: S2 — the documented config feature cannot work. Related to fork issue #7
(same input path, distinct defects). Source-verified at 00d00bfd.
```

### JSR2-03 — labels: `bug,s2-functional,review-found`
Title: `[S2] nads reports LLDP-detection failure as success and registers null switch/port`

```text
symptom: Nodes that fail LLDP detection still POST to /systems/register with
switch=None/port=None; the multi-interface retry loop never advances past the first UP
interface because failure looks like success, so detection on interface #2+ never
happens.
evidence: src/mprov_jobserver/plugins/nads.py:209-214 — prints "Error: Unable to
detect switch and port via LLDP" then unconditionally `return True`; :261-264 lldpRes
breaks the interface loop; :275 passes the False check; :292-301 registers.
root cause: getLLDP has one return statement for both outcomes.
proposed fix: Return False when port or switch is None; keep the interface loop trying
until an interface yields a completed capture.
severity: S2 — wrong registration data sent / detection silently crippled in ordinary
multi-NIC use. Source-verified at 00d00bfd.
```

### JSR2-07 — labels: `bug,s3-robustness,review-found`
Title: `[S3] script-runner silently falls back to the nads image on any -i fetch failure`

```text
symptom: A typo'd or transiently-unavailable -i <systemimage-ID> runs the NADS image's
scripts instead, with no error naming the failed ID — plausible-looking wrong run on
an image the operator never named.
evidence: src/mprov_jobserver/plugins/script_runner.py:136-152 — the 404/exception
handler for `systemimages/{id}/` silently issues `systemimages/nads/` as a fallback;
:273-277 then keys the apikey-off policy off entityId ("nads") that no longer matches
the entity actually processed, so the real fleet apikey can ride along on the
public-nads path.
root cause: One except path conflates "system not yet registered" (legitimate nads
use, -s mode) with "requested image missing" (-i mode).
proposed fix: In -i mode, fail loudly on fetch error; restrict the nads fallback to
the -s post-boot flow and derive the apikey decision from the fetched entity, not the
original argument.
severity: S3 — wrong-target silent execution under an adverse input.
```

### JSR2-08 — labels: `bug,s3-robustness,review-found`
Title: `[S3] repo-update never joins its worker threads — overlapping reposyncs, orphaned work at shutdown`

```text
symptom: New repo-update jobs claimed on the next heartbeat start while the previous
reposync is still running (two dnfs on the same repo/dir); a daemon restart orphans
the running reposync with its job left in RUNNING.
evidence: src/mprov_jobserver/plugins/repo_update.py:112 — `repo_update.start()` with
no join(); contrast image_update.py:300-302 which joins its submodule.
root cause: Missing join on the spawned UpdateRepo thread.
proposed fix: join() the worker (and check its outcome) before handle_jobs returns,
mirroring the image-update pattern.
severity: S3 — resource races and lost work under ordinary queue pressure.
```

### JSR2-09 — labels: `bug,s3-robustness,review-found`
Title: `[S3] image-delete rmtree path built from unvalidated job param (traversal) and crashes on missing key`

```text
symptom: (a) A crafted or corrupted imageId job param ("../<dir>") makes the root
daemon rmtree outside the image store; (b) a job whose params lack imageId crashes the
thread on KeyError at `params['imageId']`, leaving the claimed job stuck in RUNNING.
evidence: src/mprov_jobserver/plugins/image_delete.py:26-31 —
`shutil.rmtree(self.imageDir + '/' + params['imageId'])` with the try/except at
:20-25 guarding only `job['params']`, never the imageId lookup or the path.
root cause: Destructive path assembled by string concatenation from an mPCC-sourced
value with no basename/containment validation.
proposed fix: Validate imageId with os.path.basename and confirm the realpath stays
inside imageDir before rmtree; fail the job (not the thread) on malformed params.
severity: S3 — unguarded destructive call site, distinct from fork issue #5 (which
covers the sync sweeps).
```

### JSR2-11 — labels: `bug,s3-robustness,review-found`
Title: `[S3] register_server exits the whole daemon on a transient mPCC 500`

```text
symptom: One 500 from POST jobservers/ (or any non-JSON error body) terminates the
daemon via sys.exit(1) in the main thread — a restart loop exactly when the mPCC is
distressed — instead of retrying next heartbeat.
evidence: src/mprov_jobserver/app.py:315-324 — inside the 500 branch,
`result = json.loads(response.json())` re-parses an already-parsed object, raising
TypeError, whose handler calls sys.exit(1); the bare except at :319-322 also
sys.exits. Same double-parse fragility on the success path at :341.
root cause: requests .json() result fed back to json.loads; exit used as error
handling in a long-running daemon's heartbeat.
proposed fix: Parse once, log the body, set sessionOk=False and return so the main
loop retries on its normal cadence.
severity: S3 — adverse-condition daemon death.
```

### JSR2-12 — labels: `bug,s3-robustness,review-found`
Title: `[S3] MProvScript assigns a sockaddr tuple to ip_address`

```text
symptom: Any script-runner helper script subclassing MProvScript and using
self.ip_address gets tuple data — "(('127.0.0.1', 49942))" — instead of the address
string; posted/consumed values are garbage.
evidence: src/mprov_jobserver/script.py:80-83 —
`address = s.getsockname(); self.ip_address = address` assigns the tuple (compare
app.py:371-374 which correctly subscripts sockinfo[0]).
root cause: Missing [0] subscript (copy-paste slip vs app.py).
proposed fix: `self.ip_address = address[0]` and close the fromfd duplicate socket.
severity: S3 — broken template API for the documented extension point.
```

### JSR2-13 — labels: `bug,s3-robustness,review-found`
Title: `[S3] repo-delete module is a stub that claims jobs and simulates success`

```text
symptom: A jobserver offering the shipped repo-delete module (plugins/repo-delete.yaml
is shipped; the jobserver registers the module with mPCC) accepts repo-delete jobs and
marks them SUCCESS after the base class's 15-second simulated work — no repository is
ever deleted.
evidence: src/mprov_jobserver/plugins/repo_delete.py:1-4 — class body is `pass`, so
plugin.py:69-95 handle_jobs (sleep 15; set_job_success) runs; nothing stops the
jobserver advertising the module.
root cause: Unimplemented module inherits the template's fake-work handler, with no
"not implemented" guard.
proposed fix: Either implement deletion or refuse the module at load/register time;
never map a real mPCC job module onto the demo handler.
severity: S3 — lying job outcomes for a shipped module id.
```

### JSR2-14 — labels: `bug,s3-robustness,review-found`
Title: `[S3] setup.py feeds requirements lines with inline comments into install_requires (invalid PEP 508)`

```text
symptom: Building the sdist/wheel with current toolchains (setuptools>=66 via the
pyproject build backend) rejects the metadata; older setuptools produce mangled
Requires-Dist entries for pyyaml and jinja2.
evidence: setup.py:12-16 — `requirements = f.readlines(); setup(...,
install_requires=requirements)`; requirements.txt:1-2 — "pyyaml  # https://pypi.org/
… MIT" and "jinja2 # https://pypi.org/… 3 Clause BSD". Verified 2026-10-23:
packaging.Requirement raises InvalidRequirement on both lines.
root cause: pip-format comments in a file consumed raw by setuptools.
proposed fix: Strip comments/whitespace when loading requirements.txt, or move to
comment-free PEP 508 lines.
severity: S3 — packaging path breaks on standard modern builds (execution-verified).
```

### JSR2-15 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Dead enableDHCP=False in the dnsmasq no-jobs branch misleads readers`

```text
symptom: Code appears to permanently disable DHCP handling when no jobs are pending;
actually the plugin instance is recreated with fresh config on every heartbeat, so the
write is a no-op.
evidence: src/mprov_jobserver/plugins/dnsmasq.py:134-136 — `pass # no jobs.` followed
by `self.enableDHCP = False` inside the same branch, with no effect outliving the
thread.
root cause: Leftover intent ("stop retrying?") applied to a per-cycle instance.
proposed fix: Delete the line or document the per-cycle instance lifecycle; output is
otherwise identical.
severity: S4 — confusing-but-harmless.
```

### JSR2-16 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Image build runs 'dnf -y clean all' against the build host`

```text
symptom: Every RHEL-family image build silently wipes the build host's own dnf cache,
slowing later host package operations.
evidence: src/mprov_jobserver/plugins/image_update_mod/rhel.py:159 —
`os.system('dnf -y clean all')` with no --installroot and no chroot (the correct
installroot form follows immediately at :164).
root cause: Host-scope command left in front of the installroot variant, likely an
editing remnant. Not fixed upstream (390e57c removed only the chdir).
proposed fix: Delete the bare host-scope clean (line 164 already cleans the image).
severity: S4 — unintended host state mutation, bounded harm.
```

### JSR2-17 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Installer fetches the systemd unit from the upstream main tip over the network`

```text
symptom: install_mprov_jobserver.sh deploys a systemd unit that can drift from the
released package it just installed, fetched from raw.githubusercontent.com at install
time — an install-time supply-chain and drift wart.
evidence: install_mprov_jobserver.sh:71-72 —
`wget -O /usr/lib/systemd/system/mprov_jobserver.service
https://raw.githubusercontent.com/mprov-ng/mprov_jobserver/main/mprov_jobserver.service`.
root cause: Network fetch of a service file at install time instead of shipping it
with the package (mprov_jobserver.service sits in the repo root).
proposed fix: Install the unit from the package payload (or a pinned tag), not the
mutable main branch.
severity: S4 — install-time reproducibility/supply-chain hygiene.
```

### JSR2-18 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Runtime dependencies are unpinned in requirements.txt`

```text
symptom: The root-privileged provisioning daemon installs whatever current PyPI
versions of requests/jinja2/pyyaml/pyroute2/sh etc. are latest at build time; only
pyparted and pyroute2 carry pins.
evidence: requirements.txt:1-11 — all entries unpinned except "pyparted==3.11.7" and
"pyroute2==0.8.1".
root cause: No floor/ceiling policy for a long-lived daemon.
proposed fix: Pin (or at minimum floor) remaining runtime deps and let CI updates bump
them deliberately.
severity: S4 — dependency hygiene; no immediate defect. Per-repo instance of the same
class as mprov_control_center#31.
```

## B. Not filed — fixed at upstream head (merge-verified 2026-10-23)

Per the prior-art/drift rule these four NEW register findings are **not** to be filed;
they ship in any fork fast-forward to upstream head, and filing them would waste
maintainer review (reviewer + adjudicator confirmed both defect and fix):

| id | fixed by | evidence |
|---|---|---|
| JSR2-04 (DHCP host tags id-vs-slug) | bcb08c1, mprov-ng PR #126 (merged, closes mprov-ng#119) — also fixes JS-011 | merged 2026-10-21 |
| JSR2-05 (0-byte snponly_ipv4.efi sentinel) | adf623a, mprov-ng PR #132 (merged) | merged 2026-10-23 |
| JSR2-06 (dns.py switchless-network crash) | d13cefd, mprov-ng PR #138 (merged) | merged 2026-10-23 |
| JSR2-10 (genders group-name concatenation) | 2a962b2, mprov-ng PR #118 (merged, closes mprov-ng#117) | merged 2026-10-21 |

Recommended: mention JSR2-04 in the same comment as fork issue #11 (same fixing commit).

## C. Fold — JSR2-19 (S1 site) into fork issue #3

Do NOT file separately. Add a comment on fork issue #3 with:
`Supplementary site: start_server.sh:15-19 renders the apikey-bearing jobserver.yaml
with default 0644 permissions on every container boot (jinja render of
jobserver.yaml.j2 embedding MPROV_APIKEY; main.py:47 chmods only the initially-copied
packaged file). Fix: chmod 0600 the rendered config (or open with restrictive mode).`
— a third JS-003-class site, same S1 standing.

## D. Existing fork issue actions (JS #1–#31)

- **#11 (JS-011 inverted switch merge)**: comment "fixed upstream in bcb08c1 (mprov-ng
  PR #126, closes mprov-ng#119) — fast-forward brings the fix; also covers the
  id-vs-slug tag mismatch the same commit fixes."
- **#21 (JS-021 chdir from worker threads)**: keep open, narrowed comment — 3 of 4
  sites fixed upstream (390e57c image_update rhel, 5fc62a3 repo_update rhel, adf623a
  dnsmasq iPXE); repo_sync.py:87 still un-fixed at upstream head.
- **#22 (JS-022 orphaned RUNNING jobs)**: keep as-is; upstream 92e619e is CI-only and
  does NOT close it.
- **#30 (JS-030 lint gates)**: keep open, narrowed comment — both cited evidence items
  were fixed upstream (ec1d8e7 customIPXE; adf623a distutils import), but the lint
  gate itself is still absent.
- **Remaining issues** (#1–#10, #12–#20, #23–#29, #31): no action required this wave;
  all 31 re-confirmed at pin with spot evidence (register Part A).
