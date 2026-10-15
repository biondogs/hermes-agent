# APPROVED-FILING — mProv review program filing queue (record as filed)

Derived and filed 2026-10-15 by filing card t_290a32eb. The adjudication gate
(findings/ADJUDICATION.md, t_905714df) approved every finding in the four
registers AS WRITTEN — 118 reviewed + 1 adjudication-added (CC-040), zero
rejections, both amendments (CC-004 S2->S1, CC-040) already applied in-register —
so this queue is the full register contents, rendered per FILE-PLAN.md section 4
(`[Sx] ` title prefix, fixed body sections, labels type+severity+review-found).
Plus one doc-gap addendum row (ADD-001) authorized by operator comment on the
filing card; the other five doc-gaps were already register findings.

## biondogs/mprov_control_center (register: control_center.issues.yaml @ 98d4579b4c11)

| id | type | sev | title (filed verbatim) | labels | filed as |
|---|---|---|---|---|---|
| CC-001 | bug | S1 | [S1] Any API key grants unrestricted read-write access to every model endpoint | bug,s1-blocker,review-found | #4 |
| CC-002 | bug | S1 | [S1] API serializers expose BMC and image root passwords in cleartext | bug,s1-blocker,review-found | #5 |
| CC-003 | bug | S1 | [S1] BMC credentials printed to stdout and embedded in ipmitool argv | bug,s1-blocker,review-found | #6 |
| CC-004 | bug | S1 | [S1] Installers bake in admin:admin and changemenow default credentials | bug,s1-blocker,review-found | #7 |
| CC-005 | bug | S1 | [S1] Unauthenticated register endpoint binds attacker MAC to systems | bug,s1-blocker,review-found | #8 |
| CC-006 | bug | S1 | [S1] Unauthenticated image endpoints trust spoofable X-Forwarded-For | bug,s1-blocker,review-found | #9 |
| CC-007 | bug | S3 | [S3] Authenticated system endpoints trust spoofable X-Forwarded-For | bug,s3-robustness,review-found | #10 |
| CC-008 | bug | S1 | [S1] NFS export with no_root_squash exposes provisioning image share | bug,s1-blocker,review-found | #11 |
| CC-009 | bug | S3 | [S3] DRF default permissions require both session and API key | bug,s3-robustness,review-found | #12 |
| CC-010 | bug | S2 | [S2] Unauthenticated GET permanently removes jobservers from images | bug,s2-functional,review-found | #13 |
| CC-011 | bug | S2 | [S2] IPXE endpoint crashes with 500 when no bootable NIC exists | bug,s2-functional,review-found | #14 |
| CC-012 | bug | S2 | [S2] System config dict mutates a class attribute shared by all instances | bug,s2-functional,review-found | #15 |
| CC-013 | bug | S2 | [S2] Detail retrieval globally mutates serializer Meta depth and never resets | bug,s2-functional,review-found | #16 |
| CC-014 | bug | S2 | [S2] NetworkInterface save silently overwrites user-set hostname | bug,s2-functional,review-found | #17 |
| CC-015 | bug | S2 | [S2] IP calculation fallback can assign the same address to many NICs | bug,s2-functional,review-found | #18 |
| CC-016 | bug | S2 | [S2] NIC reconcile loop removes entries while iterating the same list | bug,s2-functional,review-found | #19 |
| CC-017 | bug | S2 | [S2] Scripts detail route uses int converter against slug primary key | bug,s2-functional,review-found | #20 |
| CC-018 | bug | S2 | [S2] JobServer save purges other jobservers on minute-boundary races | bug,s2-functional,review-found | #21 |
| CC-019 | bug | S2 | [S2] Image detail view returns list data and poisons its serializer class | bug,s2-functional,review-found | #22 |
| CC-020 | bug | S2 | [S2] Production installs never load jobqueue fixtures breaking job pipeline | bug,s2-functional,review-found | #23 |
| CC-021 | bug | S2 | [S2] LDAP self-signed cert flag sets global options to None | bug,s2-functional,review-found | #24 |
| CC-022 | bug | S3 | [S3] Image download loop cannot detect gunzip or tar failures | bug,s3-robustness,review-found | #25 |
| CC-023 | bug | S3 | [S3] Installer continues after failing to disable netboot | bug,s3-robustness,review-found | #26 |
| CC-024 | bug | S3 | [S3] Installer exception hook is never registered and is itself broken | bug,s3-robustness,review-found | #27 |
| CC-025 | bug | S3 | [S3] Error path references unbound response variable | bug,s3-robustness,review-found | #28 |
| CC-026 | bug | S3 | [S3] Unguarded get lookups return 500 on unknown identifiers | bug,s3-robustness,review-found | #29 |
| CC-027 | bug | S3 | [S3] Unauthenticated datamodel and status-changes endpoints leak internals | bug,s3-robustness,review-found | #30 |
| CC-028 | enhancement | S3 | [S3] Requirements are fully unpinned allowing silent dependency drift | enhancement,s3-robustness,review-found | #31 |
| CC-029 | enhancement | S3 | [S3] Installer pipes remote script from main branch into root shell | enhancement,s3-robustness,review-found | #32 |
| CC-030 | bug | S3 | [S3] BMC ipmitool command built by string interpolation breaks on spaces | bug,s3-robustness,review-found | #33 |
| CC-031 | bug | S3 | [S3] Model signals recover the request via stack-frame inspection | bug,s3-robustness,review-found | #34 |
| CC-032 | bug | S3 | [S3] Unguarded request data access returns 500 instead of 400 | bug,s3-robustness,review-found | #35 |
| CC-033 | bug | S3 | [S3] Image slug regenerated on every save silently drops renames | bug,s3-robustness,review-found | #36 |
| CC-034 | bug | S3 | [S3] Admin mark_rebuild action does not persist version and slug changes | bug,s3-robustness,review-found | #37 |
| CC-035 | bug | S3 | [S3] Power endpoint returns 500 for missing params and unknown ids | bug,s3-robustness,review-found | #38 |
| CC-036 | enhancement | S4 | [S4] No linting or static analysis in CI | enhancement,s4-hygiene,review-found | #39 |
| CC-037 | bug | S3 | [S3] LDAP group search built with set literal instead of string | bug,s3-robustness,review-found | #40 |
| CC-038 | bug | S2 | [S2] PATCH handler silently substitutes admin user for anonymous requests | bug,s2-functional,review-found | #41 |
| CC-039 | bug | S3 | [S3] Config comment filter removes list items while iterating them | bug,s3-robustness,review-found | #42 |
| CC-040 | bug | S1 | [S1] Power endpoint hostname parameter is a substring match hitting wrong nodes | bug,s1-blocker,review-found | #43 |

## biondogs/mprov_jobserver (register: jobserver.issues.yaml @ 00d00bfd7189)

| id | type | sev | title (filed verbatim) | labels | filed as |
|---|---|---|---|---|---|
| JS-001 | bug | S1 | [S1] Remove the committed mPCC API key from stack.env | bug,s1-blocker,review-found | #1 |
| JS-002 | bug | S1 | [S1] Stop exposing the distro root password in process argv and daemon logs | bug,s1-blocker,review-found | #2 |
| JS-003 | bug | S1 | [S1] Stop writing the fleet API key to world-readable files during provisioning | bug,s1-blocker,review-found | #3 |
| JS-004 | bug | S1 | [S1] Do not execute an unverified binary fetched to world-writable tmp | bug,s1-blocker,review-found | #4 |
| JS-005 | bug | S1 | [S1] Guard sweep cleanups so a mis-set image or repo directory cannot be wiped | bug,s1-blocker,review-found | #5 |
| JS-006 | bug | S2 | [S2] Fix status_code 404 comparisons that never match and crash sync loops | bug,s2-functional,review-found | #6 |
| JS-007 | bug | S2 | [S2] Fix malformed job query that claims every pending job in the queue | bug,s2-functional,review-found | #7 |
| JS-008 | bug | S2 | [S2] Fix group script dependency handling that crashes the resolver | bug,s2-functional,review-found | #8 |
| JS-009 | bug | S2 | [S2] Stop creating /etc/nologin before validation and leaking it on error paths | bug,s2-functional,review-found | #9 |
| JS-010 | bug | S2 | [S2] Propagate post-boot and image script failures instead of reporting success | bug,s2-functional,review-found | #10 |
| JS-011 | bug | S2 | [S2] Fix inverted switch merge so switches get DHCP entries | bug,s2-functional,review-found | #11 |
| JS-012 | bug | S2 | [S2] Fix load monitor guard that crashes the daemon under high load | bug,s2-functional,review-found | #12 |
| JS-013 | bug | S2 | [S2] Create the authorized_keys directory inside the image, not on the build host | bug,s2-functional,review-found | #13 |
| JS-014 | bug | S2 | [S2] Report the one-minute load average the field name promises | bug,s2-functional,review-found | #14 |
| JS-015 | bug | S2 | [S2] Fix repack_image so it does not destroy the image it repacks | bug,s2-functional,review-found | #15 |
| JS-016 | bug | S3 | [S3] Tolerate unset optional network fields in DHCP config generation | bug,s3-robustness,review-found | #16 |
| JS-017 | bug | S3 | [S3] Check dnsmasq worker outcomes before marking jobs successful | bug,s3-robustness,review-found | #17 |
| JS-018 | bug | S3 | [S3] Claim jobs per jobserver and atomically to prevent double processing | bug,s3-robustness,review-found | #18 |
| JS-019 | bug | S3 | [S3] Fix broken error paths in repo-update that crash instead of failing jobs | bug,s3-robustness,review-found | #19 |
| JS-020 | bug | S3 | [S3] Fix undefined jid reference in image-update error path | bug,s3-robustness,review-found | #20 |
| JS-021 | bug | S3 | [S3] Stop changing the daemon working directory from worker threads | bug,s3-robustness,review-found | #21 |
| JS-022 | enhancement | S3 | [S3] Reap jobs orphaned in running state when a worker dies mid-job | enhancement,s3-robustness,review-found | #22 |
| JS-023 | bug | S3 | [S3] Match the dnsmasq restart target precisely instead of killing by substring | bug,s3-robustness,review-found | #23 |
| JS-024 | bug | S3 | [S3] Fix handler attribute reference that breaks high-load shedding in the webserver | bug,s3-robustness,review-found | #24 |
| JS-025 | bug | S3 | [S3] Clean up image build bind mounts on failure and before archiving | bug,s3-robustness,review-found | #25 |
| JS-026 | bug | S3 | [S3] Stop interpolating mPCC-sourced values into shell command strings | bug,s3-robustness,review-found | #26 |
| JS-027 | bug | S3 | [S3] Close the file descriptor opened for connection-limit size checks | bug,s3-robustness,review-found | #27 |
| JS-028 | bug | S3 | [S3] Send job timestamps in UTC as the code intends | bug,s3-robustness,review-found | #28 |
| JS-029 | bug | S4 | [S4] Include the promised genders.include file in generated genders output | bug,s4-hygiene,review-found | #29 |
| JS-030 | enhancement | S4 | [S4] Enable flake8 and shellcheck lint gates in CI | enhancement,s4-hygiene,review-found | #30 |
| ADD-001 | enhancement | S4 | [S4] Document the image-sync and nads job modules in the README example | enhancement,s4-hygiene,review-found | #31 |

## biondogs/mprov_scripts (register: scripts.issues.yaml @ 55bdd511e4c6)

| id | type | sev | title (filed verbatim) | labels | filed as |
|---|---|---|---|---|---|
| SCR-001 | bug | S2 | [S2] Ansible loops never execute: over-escaped jq program is a compile error | bug,s2-functional,review-found | #1 |
| SCR-002 | bug | S2 | [S2] Missing-key jq null literal bypasses guards and corrupts root config | bug,s2-functional,review-found | #2 |
| SCR-003 | bug | S2 | [S2] Disk formatter crashes mounting non-RAID partitions: disk-level mount is None | bug,s2-functional,review-found | #3 |
| SCR-004 | bug | S2 | [S2] RAID build crashes: member disk id compared against disk slug string | bug,s2-functional,review-found | #4 |
| SCR-005 | bug | S3 | [S3] Unguarded cd before entity.json read leaves config variables empty | bug,s3-robustness,review-found | #5 |
| SCR-006 | bug | S3 | [S3] Service install scripts continue after failed commands and report success | bug,s3-robustness,review-found | #6 |
| SCR-007 | bug | S3 | [S3] Root fstab file deleted before rebuild with no failure isolation | bug,s3-robustness,review-found | #7 |
| SCR-008 | bug | S3 | [S3] Fill-partition handling reads stale loop variable for filesystem checks | bug,s3-robustness,review-found | #8 |
| SCR-009 | bug | S3 | [S3] BMC password passed on ipmitool command line is visible in process list | bug,s3-robustness,review-found | #9 |
| SCR-010 | bug | S3 | [S3] BMC setup crashes with NameError when systembmcs request fails | bug,s3-robustness,review-found | #10 |
| SCR-011 | bug | S3 | [S3] Post-boot python scripts exit 0 after reporting errors | bug,s3-robustness,review-found | #11 |
| SCR-012 | bug | S3 | [S3] Backup script always reports success even when every dump failed | bug,s3-robustness,review-found | #12 |
| SCR-013 | bug | S3 | [S3] BMC and InfiniBand IPs silently wrong when node IP misses mgmt prefix | bug,s3-robustness,review-found | #13 |
| SCR-014 | bug | S3 | [S3] Node import writes BMC credentials to world-readable temp file | bug,s3-robustness,review-found | #14 |
| SCR-015 | enhancement | S3 | [S3] Twelve shipped scripts missing from the mpcc_scripts manifest | enhancement,s3-robustness,review-found | #15 |
| SCR-016 | bug | S3 | [S3] Hardcoded python3.8 site-packages path breaks Rocky 9 installs silently | bug,s3-robustness,review-found | #16 |
| SCR-017 | enhancement | S3 | [S3] No guard against repartitioning the running OS disk | enhancement,s3-robustness,review-found | #17 |
| SCR-018 | bug | S4 | [S4] Broken shebang in gpfs_mmsdrrestore.sh prevents direct execution | bug,s4-hygiene,review-found | #18 |
| SCR-019 | bug | S4 | [S4] Error messages print literal placeholder instead of exception detail | bug,s4-hygiene,review-found | #19 |
| SCR-020 | enhancement | S4 | [S4] Enable shellcheck for shell scripts in CI | enhancement,s4-hygiene,review-found | #20 |
| SCR-021 | bug | S4 | [S4] Rsync errors bypass the log file due to redirect order | bug,s4-hygiene,review-found | #21 |

## biondogs/mash (register: mash.issues.yaml @ d8871d44c7c7)

| id | type | sev | title (filed verbatim) | labels | filed as |
|---|---|---|---|---|---|
| MASH-001 | bug | S2 | [S2] Connect with user and password never authenticates | bug,s2-functional,review-found | #1 |
| MASH-002 | bug | S2 | [S2] Plugin dispatch mangles arguments containing the plugin name | bug,s2-functional,review-found | #2 |
| MASH-003 | bug | S2 | [S2] BMC power commands fail unless mprovURL ends with a slash | bug,s2-functional,review-found | #3 |
| MASH-004 | bug | S2 | [S2] BMC power commands give no success or failure feedback | bug,s2-functional,review-found | #4 |
| MASH-005 | bug | S2 | [S2] Failed API calls leave stale MPROV_RESULT from the previous command | bug,s2-functional,review-found | #5 |
| MASH-006 | bug | S2 | [S2] Pvar cannot print comma-separated variables with multi-character names | bug,s2-functional,review-found | #6 |
| MASH-007 | bug | S3 | [S3] Malformed command arguments crash the entire shell with a traceback | bug,s3-robustness,review-found | #7 |
| MASH-008 | bug | S3 | [S3] API calls have no timeout and hang the shell indefinitely | bug,s3-robustness,review-found | #8 |
| MASH-009 | bug | S3 | [S3] Signal handlers swallow SIGINT and SIGTERM during hung requests | bug,s3-robustness,review-found | #9 |
| MASH-010 | bug | S3 | [S3] Error messages are written to stdout, polluting piped script output | bug,s3-robustness,review-found | #10 |
| MASH-011 | bug | S3 | [S3] Script mode always exits 0 regardless of command failures | bug,s3-robustness,review-found | #11 |
| MASH-012 | bug | S3 | [S3] Nonexistent script file argument is silently ignored | bug,s3-robustness,review-found | #12 |
| MASH-013 | bug | S3 | [S3] Common config file shapes crash connect with raw tracebacks | bug,s3-robustness,review-found | #13 |
| MASH-014 | bug | S3 | [S3] Foreach silently drops list items containing a hash character | bug,s3-robustness,review-found | #14 |
| MASH-015 | bug | S3 | [S3] Dict-typed argument kills the whole interactive session | bug,s3-robustness,review-found | #15 |
| MASH-016 | bug | S3 | [S3] Unparseable query tokens are silently swallowed and sent anyway | bug,s3-robustness,review-found | #16 |
| MASH-017 | bug | S3 | [S3] Trailing ampersand on bmc commands silently disables the command | bug,s3-robustness,review-found | #17 |
| MASH-018 | bug | S4 | [S4] Connect silently ignores non-200 responses from the control center | bug,s4-hygiene,review-found | #18 |
| MASH-019 | bug | S4 | [S4] Connect help documents the wrong config file paths | bug,s4-hygiene,review-found | #19 |
| MASH-020 | bug | S4 | [S4] Dead exception handler is defined but never installed | bug,s4-hygiene,review-found | #20 |
| MASH-021 | bug | S4 | [S4] Changelog generator links to the mprov_jobserver repository | bug,s4-hygiene,review-found | #21 |
| MASH-022 | bug | S4 | [S4] Bmc power help omits pxe and pxeefi actions supported by the server | bug,s4-hygiene,review-found | #22 |
| MASH-023 | bug | S3 | [S3] Release workflow uses retired actions and removed set-output syntax | bug,s3-robustness,review-found | #23 |
| MASH-024 | enhancement | S3 | [S3] Add machine-readable JSON output mode | enhancement,s3-robustness,review-found | #24 |
| MASH-025 | enhancement | S3 | [S3] Add dry-run mode to destructive verbs | enhancement,s3-robustness,review-found | #25 |
| MASH-026 | enhancement | S3 | [S3] Validate config file and warn about unknown keys | enhancement,s3-robustness,review-found | #26 |
| MASH-027 | enhancement | S3 | [S3] Bound dependency versions in requirements.txt | enhancement,s3-robustness,review-found | #27 |
| MASH-028 | enhancement | S4 | [S4] Add linting to CI | enhancement,s4-hygiene,review-found | #28 |

