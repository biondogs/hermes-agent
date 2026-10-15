# mprov_scripts — R3 comprehensive review notes (REVIEW-NOTES.md)

Register: ../scripts.issues.yaml — 21 findings (S2 x4, S3 x13, S4 x4; 18 bug,
3 enhancement). Zero S1. Reviewed at master @55bdd511e4c6912b0a6d44aefb22fc6e791e60d5
(full tree, 33/33 files: image-gen x10, post-boot x13, tools x7, plus
mpcc_scripts.yaml, README.md, LICENSE). Zero commits, zero issues filed, per
charter. The register passes scripts/validate_register.py with all evidence
verified against the commit.

## CRITICAL for the filing lane (t_290a32eb / adjudication)

`gh issue list -R biondogs/mprov_scripts` returns: "the 'biondogs/mprov_scripts'
repository has disabled issues". Issues are DISABLED on the fork today, so
R13 collision checking was vacuous (no open issues can exist) and the filing
card cannot file anything until issues are enabled on the fork (and presumably
on the other three — worth re-checking each before filing). This must be
resolved before or during adjudication; noting it here because it blocks the
queue for ALL four registers, not just this one.

## Findings verified by actual execution (not just reading)

- SCR-001: the exact line-50 pipeline from run_ansible.sh was executed against
  a fixture entity.json -> "jq: error: syntax error, unexpected
  INVALID_CHARACTER ... 1 compile error", loop body never runs. With the
  escaping reduced by one level the same pipeline returns the URL and the loop
  body executes. Same escape pattern at lines 68 and 101.
- SCR-002: `jq -r '.rootpw'` / '.rootsshkey' / '.gpus' on a config_params
  object lacking the key each print the literal `null` (jq 1.6). Also
  verified: extra_packages.sh's jq pipeline ERRORS to empty output
  ("Cannot iterate over null") when .extra_packages is absent, so its
  empty-string guard accidentally works for the missing-key case — this is
  why extra_packages.sh is NOT a SCR-002 site.
- SCR-018: first 12 bytes of gpfs_mmsdrrestore.sh read `#/bin/bash` (od
  verified) — comment, not shebang.
- SCR-015: manifest check run programmatically: 12 entries, none dangling,
  12 of 23 image-gen/post-boot files unlisted.
- SCR-011 mechanism: an unquoted empty `[ $var != "null" ]` test in bash
  emits "unary operator expected" and takes the else branch (tested); that
  specific site in run_ansible.sh is guarded downstream by the entity.json
  existence check, so it stayed an observation, not a finding.

## Cross-repo observations — route to the R2 (jobserver) register

Primary evidence lives in mprov_jobserver, so per charter §5 these belong to
that reviewer, not this register. Flagging here so they are not lost:

- script_runner.py:316 — `subprocess.run(local_file, shell=True)` discards the
  return code entirely; per-script failures of every script in this repo are
  invisible to the orchestrator today. Several mprov_scripts findings
  (SCR-006, SCR-011, SCR-012 class "lies about success") are compounded by
  this; the jobserver fix is complementary, not a substitute.
- script_runner.py:285-289/304 — entity.json is written to the script temp
  dir with default `open()` permissions (world-readable under root umask 022)
  and deleted only after the run. It contains the jobserver apikey and the
  entity's config_params — which by this repo's own conventions include
  rootpw (set_root_pw.sh), rootsshkey (setup_ssh.sh) and possibly BMC
  credentials. On a live multi-user node, or during image build, any local
  user can read the fleet apikey and node root password for the duration of
  the run. This is an S1-secret-exposure-shaped finding owned by jobserver;
  R2 should review it.
- image_update.py:311/348 (jobserver) embed imageDetails rootpw into
  command-line strings via os.system — same argv-exposure class as SCR-009.
  R2's territory.
- Call-shape evidence used by SCR-003 and SCR-004 was verified against
  mprov_control_center @98d4579 disklayouts/serializers.py (getMount returns
  None for non-mdrd disks; DiskPartition disklayout is a PK integer via
  PrimaryKeyRelatedField). No control_center finding is claimed here.

## Observations not filed (R8/R9/R11 discipline; observations, not findings)

- Lint-class items beyond the single SCR-020 allowance: unquoted `$pkgs` in
  extra_packages.sh:15-16 (intentional word splitting, but a quoting bug if a
  package name ever contains spaces); unquoted `$imgSlug` test in
  run_ansible.sh:20; unquoted command substitutions throughout; `cd`
  statements without failure handling in several files (the ones with traced
  corruption consequences are SCR-005). shellcheck in CI (SCR-020) owns the
  class.
- extra_packages.sh treats missing entity.json or missing config_params the
  same as "no packages configured": prints "No extra packages." and exits 0.
  Error-swallowing, but blast radius is one silently lean image; left as an
  observation rather than an issue.
- Supply-chain posture: install_yq.sh does `go install yq/v4@latest` and
  install_mprov_jobserver.sh does `pip3 install mprov_jobserver` (unpinned)
  as root at image build. Intentional design, but unpinned remote fetches
  executed as root — if the operators want a pinning policy it should be a
  program-level decision, not 21 per-script issues.
- run_ansible.sh downloads operator-specified playbooks by URL and runs them
  as root (lines 101-113). By-design provisioning trust; noted only.
- setup_data_share_mount.sh / setup_mprov_share_mount.sh derive the NFS server
  with `awk -F/ '{print $3}'`; if mprovURL carries an explicit port the fstab
  entry gets `host:port:/export/...`, which is not a valid NFS source. Folded
  into SCR-005's guard requirement conceptually; not filed separately (R1).
- slurm_enable_gpus.sh writes /tmp/slurmd (fixed name) as root before
  renaming over /etc/sysconfig/slurmd (lines 25-27). Symlink-or-race abuse
  requires a pre-existing local attacker on a freshly provisioned node — too
  speculative for R10; if the jobserver ever runs post-boot scripts on live
  multi-user nodes, revisit.
- tools/set_bmc_pw bulk-updates every matching system's BMC password to the
  hardcoded value `changeme` (line 13), and tools/add_systems.mash defaults
  bmcUser/bmcPass to root/root. These are operator tools, but shipping
  default-credential examples invites exactly the wrong copy-paste.
- backup-mprov.sh writes its backup into /tmp (volatile, wiped on reboot) —
  folded into SCR-012's fix idea.
- Dead code kept on purpose: NetworkManager-1.40-COPR.sh exits 0 with "no
  longer needed" before its body; nads.sh is self-marked DEPRICATED with
  exit 0. Fine as tombstones; they are counted in the SCR-015 unlisted set.
- Disposing details: setupBMC.py line 3 imports EXACT_TOKEN_TYPES from the
  token module (auto-import artifact, unused); setupBMC.py sets the BMC
  netmask twice (lines 79 and 95, harmless duplicate); localTempDisk.py's
  startSession prints "Retrying" but exits after one attempt;
  mpcc_scripts.yaml entry name has a "Scipts" typo; tools/README.md is empty.
- register_IPv6_ll.py can KeyError on interfaces lacking AF_PACKET or
  AF_INET6 entries (netifaces returns no such key) — happy path fine, no
  traced production case.
- The register_IPv6_ll.py comment line 3 pins "REQUIRES mprov-jobserver>=0.0.34"
  while install_mprov_jobserver.sh installs unpinned — version-drift note for
  the operators.

## Severity calibration notes for adjudication

- No S1 filed. The two candidate data-loss paths (localTempDisk wiping the
  OS disk; buildRAIDs wiping a wrong partition on a stale `dev`) were traced:
  the stale-`dev` wipe is unreachable because `dev` can never be assigned at
  all (it crashes first — SCR-004), and the OS-disk wipe requires a wrong
  server-side record, making it a missing-guard S3 (SCR-017) rather than a
  nameable attacker path.
- SCR-002 sits at S2 (guards exist for exactly the missing-key case and are
  bypassed, silently corrupting root access config); downgrade to S3 would
  not be fought, but the "whole fleet unreachable" worst case argues S2.
- SCR-009 (BMC password in argv) held at S3 because the normal post-boot
  window has no local users; becomes S1-shaped the day post-boot scripts can
  be re-run on live multi-user nodes (see the entity.json observation above —
  same conditional).
