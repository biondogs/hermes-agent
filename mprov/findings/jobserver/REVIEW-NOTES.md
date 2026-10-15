# mprov_jobserver — Comprehensive Review Notes (R2)

Review: 2026-10-15, sw-reviewer, main @ 4f73fc1b2ca17c24a7639057249d04168008e121.
Register: ../jobserver.issues.yaml (30 findings: S1=5, S2=10, S3=13, S4=2).
This file holds the architecture summary, coverage record, destructive-op guard
analysis, and observations that are NOT register findings (CIRCUMSCRIPTION R8/R10).

## 1. Architecture summary

mprov_jobserver is the provisioning workhorse daemon of the mProv stack. It runs
as root (required for chroot, mounts, dnsmasq management) on one or more
jobservers and connects to the mPCC control center over a DRF-style REST API
authenticated with a single shared API key (Authorization: Api-Key), configured
in /etc/mprov/jobserver.yaml under the global section.

Process model (src/mprov_jobserver/app.py): a single-threaded main loop wakes
every heartbeatInterval (10s). Each pass it re-registers the server with the mPCC
(jobservers/ POST) and re-spawns one thread per configured job module. Threads
die at the end of their handle_jobs pass and are respawned next tick; long-lived
modules (mprov-webserver) instead serve inside their thread until the daemon
stops. update_job_status is the shared claim API: it GETs a job list (by id, by
raw query string, or by module-substring search) and PATCHes each non-terminal
job to a new status, overwriting the jobserver field with self.

Module inventory (src/mprov_jobserver/plugins/):
- image-sync / repo-sync: not job-based; compare version files under imageDir /
  repoDir against the mPCC, download changed artifacts, then sweep-delete any
  subdirectory not in the current list.
- image-update: job-based image BUILDER. Claims image-update jobs, then for each
  image runs a distro-specific submodule (image_update_mod/rhel.py: dnf
  --installroot groupinstall, pip, dracut), writes a script-runner config into
  the image tree, copies rootsshkeys / sets rootpw, runs the in-image
  script-runner under chroot with bind mounts, tars the tree with a downloaded
  busybox, and registers itself as an image source.
- image-delete: job-based rmtree of imageDir/<imageId>.
- script-runner: runonce-only harness (-r flag) that runs mPCC-defined scripts
  (image-gen inside chroot via the generated script-runner.sh, or post-boot on
  nodes via mprov_jobserver_postboot.service). Downloads script files by URL and
  executes them; creates /etc/nologin for the duration.
- dnsmasq (+ dnsmasq_mod): regenerates dnsmasq DNS/DHCP config from Jinja2
  templates out of mPCC network/interface/switch data, then kills/restarts the
  dnsmasq process found by name scan.
- repo-update / repo-delete: repo mirror builds via dnf reposync submodules.
- mprov-webserver: threaded stdlib HTTP server serving the image/repo export
  tree for PXE/image pulls, with load- and connection-shedding logic.
- nads: LLDP-based node auto-detection at boot, registers switch/port/MAC with
  the mPCC, optional reboot.
- libgenders: regenerates /etc/genders from mPCC systems data.

Deployment artifacts: systemd units (root daemon + post-boot oneshot), a
Rocky 8.8 container with a start_server.sh that renders jobserver.yaml from env
vars (MPROV_APIKEY among them), a dev compose stack whose stack.env contains the
committed key (JS-001), and a repack_image helper script added 2026-07.

## 2. Coverage

Full-tree read: 71/71 tracked files (source, plugin configs, Jinja2 templates,
systemd units, Dockerfile, CI workflows, packaging). LICENSE and the vendored
wait-for-it.sh (upstream vishnubob script, standard and unmodified in behavior)
were skim-read; dist/.placeholder is an empty placeholder. No skipped packages
or directories. All evidence in the register was checked verbatim against
git show <commit>:<path> by scripts/validate_register.py (PASS).

## 3. Verification log (real commands run during review, 2026-10-15)

- set() of dict objects raises TypeError (confirms JS-008 group-deps crash):
  python3 verified: "TypeError: cannot use a 'dict' as a set element".
- CPython interns the empty string from json.loads, so the `is not ""`
  comparison at image_update.py:111 currently behaves like an inequality test in
  practice (verified False/True on empty/non-empty). Filed under the lint gate
  (JS-030) as fragile-by-accident, not as a functional finding.
- Jinja2 membership test against None raises TypeError (confirms JS-016):
  ran the same construct with jinja2 in a venv: "argument of type 'NoneType'
  is not a container or iterable".
- dnsmasq --test ACCEPTS a dhcp-host line with an empty element, so the
  undefined `{{hostid}}` in dhcp_host.conf.j2 (renders as empty) is tolerated
  by dnsmasq 2.90: "syntax check OK". Potential fatal-config theory tested and
  rejected; noted as observation only.
- stack.env is git-tracked since commit 7479327 (2024-12-12), last touched in
  7218cdb (2025-06-28); the API key line was present across that history (JS-001).
- Cross-repo grounding (control_center, read-only): JobAPIView search_fields is
  module__slug only and the get() reads exactly the params, module, jobserver,
  status query keys, ignoring all others (jobqueue/views.py:99-119) — this is
  what makes JS-007's bare-JSON querystring return the unfiltered queue, and it
  grounds JS-018's assignment-ignoring claim. Network.gateway / nameserver1 /
  dhcpstart / dhcpend are all blank=True, null=True (networks/models.py:47-63)
  and the API docstring marks gateway and nameserver1 "(Optional)" — grounds
  JS-016.
- Register mechanical validation: scripts/validate_register.py — PASS, 30
  findings, tallies as reported.

## 4. Destructive-operation guard analysis (charter question: what stops a
typo from wiping the wrong fleet?)

Call sites examined:
- image_sync.py:140 and repo_sync.py:143 sweep rmtree: NO guard at all beyond
  list membership. Wrong/overlapping imageDir or repoDir + any pass = arbitrary
  subtree deletion. Empty list from a bad API reply widens it. → JS-001(S1) class
  finding JS-005 in register.
- image_delete.py:31 rmtree of imageDir/<params['imageId']>: partially guarded
  (existence check + imageList membership when configured), but the path segment
  comes straight from job params with no format validation (see observations).
- repack_image rm of the target image: unguarded, and the replacement artifact
  is produced broken (JS-015).
- dnsmasq/dns/dhcp process kill: unguarded name-substring match (JS-023).
- repack/build paths through os.system with rm -f: path strings built from
  config + mPCC slugs; slugs are DB-validated upstream but the jobserver itself
  applies no validation before destructive shell use (JS-026 context).
- The image build tar step can ingest host filesystems via leaked bind mounts
  (JS-025).

## 5. Idempotency, retry, and job lifecycle

Jobs are claimed by status flip (1→2) with no lease, timeout, or owner-check; a
crashed worker leaves jobs in RUNNING forever (JS-022). No startup reaping.
image/repo sync are naturally idempotent (version-file comparisons) except the
sweep steps. script-runner runs are not idempotent (scripts re-run wholesale on
retry) but that is their design. Retries of failed builds happen only by operator
re-trigger because failures are recorded late or not at all (JS-010, JS-017,
JS-019, JS-020).

## 6. Logging

Unstructured print() to stdout (console/journald per unit). No levels, no job
correlation ids. Secrets reachable in log lines are registered as JS-002
(rootpw dump); the generic structured-logging improvement is NOT filed because
upstream already tracks it — see collisions below. Log rotation is delegated to
systemd/journald, acceptable for this deployment model.

## 7. Concurrency on shared state

- Process-wide os.chdir from worker threads (JS-021).
- Unclaimed-race job claiming (JS-018).
- Class-attribute connection counter on the webserver handler is incremented
  from request threads without synchronization (observation below, not filed).
- plugin threads are respawned each tick; module reload via importlib.reload of
  running plugin modules is attempted each tick but is benign for idle modules.

## 8. Observations (NOT findings; no register entry, per R8/R10/R11)

- dhcp_host.conf.j2 references undefined `{{hostid}}`, which renders empty;
  verified harmless with dnsmasq --test (empty element tolerated). Should be
  host.id or removed, cosmetic only.
- image_update.py:111 `is not ""` relies on CPython interning; flake8 F632
  flags it; covered by JS-030 lint gate.
- dnsmasq.py:1 imports from distutils (removed in Python 3.12) while
  setup.cfg classifiers claim 3.12 support. Import-time breakage on 3.12 hosts
  would be loud, not silent; covered by JS-030 and noted here for calibration
  debate (S3 vs S4 was considered; visible-crash-on-unsupported-platform classed
  as hygiene given documented Rocky8/py3.8-3.11 deployment targets).
- update_job_status PATCH bodies include a `pk` field equal to the module name;
  harmless if the mPCC serializer ignores it (it appears to), but the field is
  meaningless and worth dropping when the claim mechanism is reworked (JS-018).
- register_server 500-path does json.loads on the already-parsed response
  (app.py:318-324) and the success path re-loads too (app.py:341); the 500 path
  degrades to printing raw text. Ugly but prints something on every branch.
- startSession derives the local IP by duplicating the fd of the streamed
  response (app.py:371, script.py:80); fragile against connection pooling but
  only exercised when myaddress is unset (the shipped configs set it).
- sys.exit(1) inside plugin threads (image_sync.py:19, repo_sync.py:20,
  image_update.py:31, dnsmasq.py:101) only ends the thread, not the process,
  despite "Job Module Halted!!!" messaging; combined with respawn-per-tick this
  becomes a warn-and-retry loop, not a halt.
- repo_update.py:112 starts the repo update thread without join; the claiming
  semantics incidentally prevent duplicate work next tick, but the thread can
  outlive its plugin instance.
- dnsmasq.py:136 sets enableDHCP=False on the no-jobs path; dead letter since
  plugin instances are recreated each tick.
- mprov_webserver connCount is an unsynchronized class attribute across request
  threads (mprov_webserver.py:11,61-68); lost updates can only flip the
  registration flag around the maxConn threshold when serving >10 concurrent
  large files. Not filed: traced harm requires a low-frequency lost-update AND
  a sustained-over-limit condition; left here for the fix lane when JS-004/024
  work touches this file.
- mprov-webserver rootDir default is empty string, which makes the stdlib server
  serve the daemon's (mutable, see JS-021) working directory if the operator
  omits the config; the shipped plugin yaml sets /export/, so this is
  misconfiguration-adjacent.
- Dockerfile `if [ -e /tmp/dist/*.whl ]` glob test is unreliable for 0 or >1
  wheels; build-time only.
- install_mprov_jobserver.sh pipes a remotely fetched script to bash, fetches
  the systemd unit from branch main un-pinned, and runs one jobserver pass
  during install with the stock config; install-time convenience tradeoffs,
  outside the runtime daemon's trust boundary.
- dev-docker-compose.yml runs privileged with host networking; dev-only.
- CI uses old action majors (checkout@v2, build-push-action@v2) and a python→
  python3 symlink step; CI hygiene, out of product scope.
- README example apikey is an obvious placeholder, not a credential.
- app.py startSession sets sessionOk=True before checking the response status,
  so a 401 (bad key) is only surfaced via downstream errors; low impact given
  register_server's 400/500 handling re-flags the session.

## 9. Open-issue collision check (CIRCUMSCRIPTION R13)

Checked gh issue list --state open on both biondogs/mprov_jobserver (filing
target) and mprov-ng/mprov_jobserver (upstream).
- biondogs/mprov_jobserver has ISSUES DISABLED. Flagging for the filing lane
  and adjudication: filing per FILE-PLAN section 4 will fail until issues are
  enabled on the fork (or the program re-targets upstream).
- Upstream open issues considered:
  - #94 (restart should fail running jobs): overlaps JS-022's symptom space but
    is a different mechanism (restart-trigger vs mid-job worker death with no
    reaper). KEPT in register; adjudication may merge if it disagrees.
  - #108 (reassess the dnsmasq full restart, suggests HUP): JS-023 was
    deliberately scoped to the target-selection defect (substring name match
    killing the wrong process); the restart-policy aspect of that area belongs
    to upstream #108 and is NOT filed here.
  - #102 (jobserver cannot talk https to the mpcc): a candidate S3 enhancement
    ("warn/refuse non-https mprovURL, since examples ship http:// and the API
    key transits cleartext") was DROPPED from the register as an adjacent
    duplicate of this open bug. The cleartext-key exposure fact remains worth
    noting: every shipped example config uses http://.
  - #103/#104/#105 (journald job-status/warning/provisioning-time logging): the
    candidate S4 structured-logging enhancement was DROPPED as a duplicate.
  - #110, #96, #95, #91, #92, #29, #15: reviewed; no register entry collides.

## 10. Severity calibration notes for adjudication

All five S1s carry named attack/loss scenarios in blast_radius (credential in
repo, rootpw in ps/logs, apikey in world-readable tmp files, busybox pre-plant
execution, mis-configured sweep wiping arbitrary trees). The sweep-rmtree S1
(JS-005) is the one most likely to be argued S3 ("operator error, not
attacker"): the charter's own S1 definition enumerates "destructive op able to
hit the wrong target", and this card explicitly demanded that guard analysis, so
it stands as filed unless adjudication disagrees. JS-027 (fd leak) was
considered S2 vs S3; filed S3 per the "degrades under a named adverse
condition" calibration. JS-014 (one_minute_load actually 15-minute) is filed S2
as literally "wrong data shown/sent in normal operation".
