# APPROVED-FILING — biondogs/mprov_scripts (MPROV-M wave, 2026-10-23)

Adjudication: sw-architect, t_43e4e008, 2026-10-23. Register: `scripts.issues.yaml`
(t_412f1a54) — 28 findings: 20 ALREADY-FILED re-confirmed (fork #1, #3–#21), 8 NEW
(SCR-022..029), plus fork issue #2 resolved upstream. Validator PASS at pin.
Pins: reviewed at upstream eb80617 (10 commits past Oct-15 base 55bdd51); fork aae84ee
is docs-only over 55bdd51 — no product divergence.
Status: **all 8 NEW findings APPROVED** (severities confirmed as registered).
Gate: distiller PASS required before the filing card (t_31448dcb) runs. Issues only (Rule D).
Open-PR check (operator requirement): the only open PR on either remote is upstream
mprov-ng/mprov_scripts#19 (docs/OpenWiki regeneration) — no finding is covered.

## A. New issues to file (8)

### SCR-022 — labels: `bug,s2-functional,review-found`
Title: `[S2] Database backup written world-readable to volatile /tmp`

```text
symptom: Every backup run writes the full mPCC database dump — every SystemBMC
password plus media/ — to /tmp with default modes (directory 755, files 644; verified
by execution under umask 022) and leaves the tarball there; a reboot clears /tmp and
destroys the only backup copy.
evidence: tools/backup-mprov.sh:8-12 (mkdir/dumpdata into /tmp/mprov_backup/), :30
(tar written into /tmp). The repo's own operations doc warns the tarball is secret
material.
root cause: Backup staged in volatile world-readable /tmp with umask-default
permissions; no destination or mode policy.
proposed fix: Write to a root-only directory created mode 700 with files 600 (or an
operator-configured persistent destination) and verify the tarball's permissions.
severity: S2 — any local account on the control-center host harvests fleet-wide BMC
credentials. Larger blast radius than fork issue #14 (different script, different
root cause — not a duplicate). Source-verified by the adjudicator at eb80617.
```

### SCR-023 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Data-share fstab append corrupts fstab or skips the mount via loose match`

```text
symptom: Image builds on a host whose node fstab lacks a trailing newline produce a
corrupt fstab — the NFS entry concatenates onto the last line and boot drops to
emergency mode; a fstab merely mentioning /export/data in a comment or stale entry
silently skips the needed mount so /data never mounts.
evidence: image-gen/setup_data_share_mount.sh:23 —
`grep -qF '/export/data' /etc/fstab || echo "…" >> /etc/fstab`. Both failure modes
verified by execution with the script's exact logic at the pin; the line was
introduced by upstream fix 56e1991.
root cause: Fixed-string substring match for idempotence, plus append without
ensuring the previous line ends with a newline.
proposed fix: Match the intended mount entry at field level (the /data mount point)
and guarantee a newline before appending.
severity: S3 — happy path works; two named adverse fstab shapes yield severe or
silent failure.
```

### SCR-024 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Shadow file rewritten in place with no atomic write or backup`

```text
symptom: An interrupted root-password rewrite during image build (crash, full disk,
kill) leaves /etc/shadow empty or partial with no previous copy retained — no account,
including root on the console, can authenticate.
evidence: image-gen/set_root_pw.sh:23-28 — `cat /etc/shadow | grep -v "^root:" >
$TMPFILE` then `echo "root:…" | cat - $TMPFILE > /etc/shadow`: the final redirection
truncates the live file before new content streams in.
root cause: In-place truncate-then-write instead of assemble-then-atomic-replace, with
no failure checks.
proposed fix: Build the complete new content in the temp file first, then
write-and-rename into place (preserving ownership and mode), aborting nonzero on any
intermediate failure.
severity: S3 — data-loss path under interruption; standard truncate-then-write hazard.
```

### SCR-025 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Slurmd config rebuilt through fixed world-writable tmp path`

```text
symptom: On a multi-user node, a pre-created /tmp/slurmd symlink redirects a root-run
write to an attacker-chosen target, and the final mv then installs that symlink/file
as /etc/sysconfig/slurmd; independently, the rebuild is non-atomic with no backup, so
a failure mid-sequence leaves slurmd unconfigured.
evidence: post-boot/slurm_enable_gpus.sh:25-27 —
`cat /etc/sysconfig/slurmd | grep -v "Gres=gpu" > /tmp/slurmd`; append to the same
fixed path; `/bin/mv -f /tmp/slurmd /etc/sysconfig/slurmd`.
root cause: Staging through a fixed path in the world-writable /tmp plus blind mv.
proposed fix: Stage with mktemp in the system config area with restrictive mode,
verify the staged file, then rename into place.
severity: S3 — local-attacker write redirection on multi-user nodes; failure-prone
config rebuild everywhere.
```

### SCR-026 — labels: `enhancement,s3-robustness,review-found`
Title: `[S3] Unpinned network installs of jobserver and yq at image build time`

```text
symptom: Image builds pip-install mprov_jobserver and go-install yq at @latest as
root with no version constraints: builds are non-reproducible, there is no way to
audit what ran, and every future dependency-bad release flows straight onto fleet
nodes. register_IPv6_ll.py documents a required jobserver version floor in a comment
that nothing installs or verifies.
evidence: image-gen/install_mprov_jobserver.sh:15 (`pip3 install mprov_jobserver`);
image-gen/install_yq.sh:10-11 (`go install …yq/v4@latest`);
post-boot/register_IPv6_ll.py:3 ("THIS SCRIPT REQUIRES mprov-jobserver>=0.0.34").
root cause: No pinning policy for build-time network installs.
proposed fix: Pin both installs to known versions (pin file or explicit versions in
the commands) and fail the build when the installed jobserver is older than the
documented floor.
severity: S3 — missing protective feature on the provisioning path; per-repo instance
of the same class as mprov_control_center#31.
```

### SCR-027 — labels: `bug,s3-robustness,review-found`
Title: `[S3] Image name unvalidated into destructive rsync delete target`

```text
symptom: An image name containing path components makes image-grab mirror the node
OUTSIDE the image store, and with -d rsync --delete removes there whatever files the
node lacks — e.g. `image-grab.sh -n node01 -i ../../etc -d` overwrites/deletes two
levels above the store.
evidence: tools/image-grab.sh:53-56 — `mkdir -p "$IMAGE_DIR/$IMAGE_NAME/"` on the raw
name; :68 — `rsync … $DELETE root@$NODE:/ $IMAGE_DIR/$IMAGE_NAME/`.
root cause: IMAGE_NAME used raw in destination paths with no validation before
destructive filesystem use.
proposed fix: Validate IMAGE_NAME against a strict identifier pattern (no separators)
and assert the resolved destination stays inside IMAGE_DIR before creating or syncing
anything.
severity: S3 — operator input (typo or scripted caller) turns a destructive sync onto
an arbitrary directory.
```

### SCR-028 — labels: `bug,s3-robustness,review-found`
Title: `[S3] CSV import keeps CR and splits records on whitespace corrupting fields`

```text
symptom: Importing a spreadsheet-edited (CRLF-terminated) CSV silently writes
hostnames, MACs and IPs with stray carriage returns into the mPCC — verified by
execution (ip=[172.20.1.10\r]); any embedded space splits one CSV row into two
garbage records. The import reports success; provisioning those nodes later fails in
confusing ways. (Same script as fork issue #13's silent-wrong IPs — distinct defect.)
evidence: tools/import_systems_csv.sh:68-73 — `for entry in `cat $filename`` word
expansion over the file plus `IFS=',' read -ra DATA`, no field normalization.
root cause: Whitespace-split record loop with a comma-only field split.
proposed fix: Read records line-by-line, strip CR and surrounding whitespace from
every field, and reject rows whose field count is wrong.
severity: S3 — silent data corruption on ordinary operator input.
```

### SCR-029 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Duplicated ipmitool netmask block in BMC setup with trailing-space arg`

```text
symptom: BMC setup configures the netmask twice per node with a padded argument; the
duplicated block suggests an intended second lan setting (for example a default
gateway) was lost — no gateway is configured anywhere in the script.
evidence: post-boot/setupBMC.py:74-83 and :90-99 — two literally identical netmask
blocks; the f-string passes the netmask with a trailing space (:79, :95).
root cause: Copy-paste duplication with no validation of the ipmitool argument list.
proposed fix: Remove the duplicated block and the trailing space, and decide whether
a distinct second lan setting (gateway) was intended and implement it explicitly.
severity: S4 — redundant per-node BMC command and padded argument; no functional
failure demonstrated.
```

## B. Verdicts — no other new filings

All 8 NEW findings approved as registered (SCR-022 S2 held — see
ADJUDICATION-2026-10-23.md §3; the sibling local-read exposures #9/#14 are S3, this
one escalates one rung for full-database scope and persistence). SCR-022 vs fork #14:
NOT merged — different script, different root cause, evidence preserved per site.
SCR-008/SCR-004's CC-repo twins are filed separately in the control_center pack; the
two copies cross-reference each other.

## C. Existing fork issue actions (SCR #1–#21)

- **#2 (SCR-002 missing-key jq null literal)**: close by comment — "fixed upstream in
  4c2f703 (fix/config-param-null-16) which reworks the four affected scripts and adds
  container tests asserting exactly these failure modes; fork is 10 upstream commits
  behind, sync pending."
- **#5 (SCR-005)**: keep open, narrowed comment — upstream 8134d25 removed one of the
  four unguarded-cd sites (setup_mprov_share_mount.sh); the remaining installers
  still continue on a failed cd.
- **#6 (SCR-006)**: keep open, narrowed comment — upstream 8134d25 removed the
  primary original sites (create_slurm_client_service.sh); the no-errexit pattern
  survives at post-boot/enable_and_run_jobserver.sh.
- **#15 (SCR-015)**: optional fold-in comment — manifest also carries a name typo
  ("Scipts"); unchanged missing-script count at pin: 12 scripts + all of tools/.
- **#1, #3, #4, #7–#14, #16–#21**: no action this wave; all re-confirmed at eb80617
  (register DEDUPE lines carry the per-issue status).
