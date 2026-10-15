# FILED-ISSUES — receipt register for the mProv review program filing

Filed 2026-10-15 by sw-pm (card t_290a32eb) via `gh issue create`, one call per
queue row (APPROVED-FILING.md), bodies verbatim per CIRCUMSCRIPTION R14.
120 issues total = 119 adjudicated findings + 1 doc-gap addendum. Zero code
commits; issues opened on biondogs forks only (upstream mprov-ng untouched).

## Context

- Operator GO (2026-10-15): doc commits pushed and "all other filings should
  make their way to the online repos"; standing rule: everything to biondogs
  forks in a shape that keeps fork -> mprov-ng PRs easy.
- **Enablement receipt**: issues were DISABLED on all four forks (R13 blocker).
  This run set `has_issues=true` via `gh api -X PATCH repos/biondogs/<repo>`)
  immediately before filing — settings-only, no code touched. Receipts:
  mprov_control_center/mprov_jobserver/mprov_scripts/mash all read back has_issues=true.
- Docs lane already merged FF to fork defaults (orchestrator-executed,
  2026-10-15): control_center main->7384c63, jobserver main->00d00bf,
  scripts master->aae84ee, mash master->f9bb463. No register issue references
  docs/sweep-2026-10-15 (registers are pinned to pre-merge commits 98d4579,
  4f73fc1, 55bdd51, d8871d4); nothing further to note inside bodies.
- Landing shape (once, per operator standing rule): fix work lands as topic
  branches off the linear fork default and PRs fork->mprov-ng; this pipeline
  added no commits to any fork default.
- **Doc-gap addendum dedupe**: of the 6 doc-gaps from the docs lane
  (t_dbb80b79), 5 were already approved register findings — manifest drift =
  SCR-015, gen_changelog wrong links = MASH-021, do_connect docstring config
  path = MASH-019, bmc '&' ignored = MASH-017, unpinned CC requirements =
  CC-028. Only the jobserver image-sync/nads README gap was new -> filed as
  ADD-001 (below, marked *doc-gap addendum*).

## Counts

| repo | bugs | enhancements | total |
|---|---|---|---|
| mprov_control_center | 37 | 3 | 40 |
| mprov_jobserver | 28 | 3 | 31 |
| mprov_scripts | 18 | 3 | 21 |
| mash | 23 | 5 | 28 |
| **total** | 106 | 14 | 120 |

## biondogs/mprov_control_center

| issue# | id | title | severity | type | url |
|---|---|---|---|---|---|
| [4](https://github.com/biondogs/mprov_control_center/issues/4) | CC-001 | [S1] Any API key grants unrestricted read-write access to every model endpoint | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/4 |
| [5](https://github.com/biondogs/mprov_control_center/issues/5) | CC-002 | [S1] API serializers expose BMC and image root passwords in cleartext | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/5 |
| [6](https://github.com/biondogs/mprov_control_center/issues/6) | CC-003 | [S1] BMC credentials printed to stdout and embedded in ipmitool argv | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/6 |
| [7](https://github.com/biondogs/mprov_control_center/issues/7) | CC-004 | [S1] Installers bake in admin:admin and changemenow default credentials | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/7 |
| [8](https://github.com/biondogs/mprov_control_center/issues/8) | CC-005 | [S1] Unauthenticated register endpoint binds attacker MAC to systems | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/8 |
| [9](https://github.com/biondogs/mprov_control_center/issues/9) | CC-006 | [S1] Unauthenticated image endpoints trust spoofable X-Forwarded-For | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/9 |
| [10](https://github.com/biondogs/mprov_control_center/issues/10) | CC-007 | [S3] Authenticated system endpoints trust spoofable X-Forwarded-For | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/10 |
| [11](https://github.com/biondogs/mprov_control_center/issues/11) | CC-008 | [S1] NFS export with no_root_squash exposes provisioning image share | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/11 |
| [12](https://github.com/biondogs/mprov_control_center/issues/12) | CC-009 | [S3] DRF default permissions require both session and API key | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/12 |
| [13](https://github.com/biondogs/mprov_control_center/issues/13) | CC-010 | [S2] Unauthenticated GET permanently removes jobservers from images | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/13 |
| [14](https://github.com/biondogs/mprov_control_center/issues/14) | CC-011 | [S2] IPXE endpoint crashes with 500 when no bootable NIC exists | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/14 |
| [15](https://github.com/biondogs/mprov_control_center/issues/15) | CC-012 | [S2] System config dict mutates a class attribute shared by all instances | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/15 |
| [16](https://github.com/biondogs/mprov_control_center/issues/16) | CC-013 | [S2] Detail retrieval globally mutates serializer Meta depth and never resets | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/16 |
| [17](https://github.com/biondogs/mprov_control_center/issues/17) | CC-014 | [S2] NetworkInterface save silently overwrites user-set hostname | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/17 |
| [18](https://github.com/biondogs/mprov_control_center/issues/18) | CC-015 | [S2] IP calculation fallback can assign the same address to many NICs | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/18 |
| [19](https://github.com/biondogs/mprov_control_center/issues/19) | CC-016 | [S2] NIC reconcile loop removes entries while iterating the same list | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/19 |
| [20](https://github.com/biondogs/mprov_control_center/issues/20) | CC-017 | [S2] Scripts detail route uses int converter against slug primary key | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/20 |
| [21](https://github.com/biondogs/mprov_control_center/issues/21) | CC-018 | [S2] JobServer save purges other jobservers on minute-boundary races | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/21 |
| [22](https://github.com/biondogs/mprov_control_center/issues/22) | CC-019 | [S2] Image detail view returns list data and poisons its serializer class | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/22 |
| [23](https://github.com/biondogs/mprov_control_center/issues/23) | CC-020 | [S2] Production installs never load jobqueue fixtures breaking job pipeline | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/23 |
| [24](https://github.com/biondogs/mprov_control_center/issues/24) | CC-021 | [S2] LDAP self-signed cert flag sets global options to None | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/24 |
| [25](https://github.com/biondogs/mprov_control_center/issues/25) | CC-022 | [S3] Image download loop cannot detect gunzip or tar failures | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/25 |
| [26](https://github.com/biondogs/mprov_control_center/issues/26) | CC-023 | [S3] Installer continues after failing to disable netboot | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/26 |
| [27](https://github.com/biondogs/mprov_control_center/issues/27) | CC-024 | [S3] Installer exception hook is never registered and is itself broken | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/27 |
| [28](https://github.com/biondogs/mprov_control_center/issues/28) | CC-025 | [S3] Error path references unbound response variable | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/28 |
| [29](https://github.com/biondogs/mprov_control_center/issues/29) | CC-026 | [S3] Unguarded get lookups return 500 on unknown identifiers | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/29 |
| [30](https://github.com/biondogs/mprov_control_center/issues/30) | CC-027 | [S3] Unauthenticated datamodel and status-changes endpoints leak internals | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/30 |
| [31](https://github.com/biondogs/mprov_control_center/issues/31) | CC-028 | [S3] Requirements are fully unpinned allowing silent dependency drift | S3 | enhancement | https://github.com/biondogs/mprov_control_center/issues/31 |
| [32](https://github.com/biondogs/mprov_control_center/issues/32) | CC-029 | [S3] Installer pipes remote script from main branch into root shell | S3 | enhancement | https://github.com/biondogs/mprov_control_center/issues/32 |
| [33](https://github.com/biondogs/mprov_control_center/issues/33) | CC-030 | [S3] BMC ipmitool command built by string interpolation breaks on spaces | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/33 |
| [34](https://github.com/biondogs/mprov_control_center/issues/34) | CC-031 | [S3] Model signals recover the request via stack-frame inspection | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/34 |
| [35](https://github.com/biondogs/mprov_control_center/issues/35) | CC-032 | [S3] Unguarded request data access returns 500 instead of 400 | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/35 |
| [36](https://github.com/biondogs/mprov_control_center/issues/36) | CC-033 | [S3] Image slug regenerated on every save silently drops renames | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/36 |
| [37](https://github.com/biondogs/mprov_control_center/issues/37) | CC-034 | [S3] Admin mark_rebuild action does not persist version and slug changes | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/37 |
| [38](https://github.com/biondogs/mprov_control_center/issues/38) | CC-035 | [S3] Power endpoint returns 500 for missing params and unknown ids | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/38 |
| [39](https://github.com/biondogs/mprov_control_center/issues/39) | CC-036 | [S4] No linting or static analysis in CI | S4 | enhancement | https://github.com/biondogs/mprov_control_center/issues/39 |
| [40](https://github.com/biondogs/mprov_control_center/issues/40) | CC-037 | [S3] LDAP group search built with set literal instead of string | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/40 |
| [41](https://github.com/biondogs/mprov_control_center/issues/41) | CC-038 | [S2] PATCH handler silently substitutes admin user for anonymous requests | S2 | bug | https://github.com/biondogs/mprov_control_center/issues/41 |
| [42](https://github.com/biondogs/mprov_control_center/issues/42) | CC-039 | [S3] Config comment filter removes list items while iterating them | S3 | bug | https://github.com/biondogs/mprov_control_center/issues/42 |
| [43](https://github.com/biondogs/mprov_control_center/issues/43) | CC-040 | [S1] Power endpoint hostname parameter is a substring match hitting wrong nodes | S1 | bug | https://github.com/biondogs/mprov_control_center/issues/43 |

## biondogs/mprov_jobserver

| issue# | id | title | severity | type | url |
|---|---|---|---|---|---|
| [1](https://github.com/biondogs/mprov_jobserver/issues/1) | JS-001 | [S1] Remove the committed mPCC API key from stack.env | S1 | bug | https://github.com/biondogs/mprov_jobserver/issues/1 |
| [2](https://github.com/biondogs/mprov_jobserver/issues/2) | JS-002 | [S1] Stop exposing the distro root password in process argv and daemon logs | S1 | bug | https://github.com/biondogs/mprov_jobserver/issues/2 |
| [3](https://github.com/biondogs/mprov_jobserver/issues/3) | JS-003 | [S1] Stop writing the fleet API key to world-readable files during provisioning | S1 | bug | https://github.com/biondogs/mprov_jobserver/issues/3 |
| [4](https://github.com/biondogs/mprov_jobserver/issues/4) | JS-004 | [S1] Do not execute an unverified binary fetched to world-writable tmp | S1 | bug | https://github.com/biondogs/mprov_jobserver/issues/4 |
| [5](https://github.com/biondogs/mprov_jobserver/issues/5) | JS-005 | [S1] Guard sweep cleanups so a mis-set image or repo directory cannot be wiped | S1 | bug | https://github.com/biondogs/mprov_jobserver/issues/5 |
| [6](https://github.com/biondogs/mprov_jobserver/issues/6) | JS-006 | [S2] Fix status_code 404 comparisons that never match and crash sync loops | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/6 |
| [7](https://github.com/biondogs/mprov_jobserver/issues/7) | JS-007 | [S2] Fix malformed job query that claims every pending job in the queue | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/7 |
| [8](https://github.com/biondogs/mprov_jobserver/issues/8) | JS-008 | [S2] Fix group script dependency handling that crashes the resolver | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/8 |
| [9](https://github.com/biondogs/mprov_jobserver/issues/9) | JS-009 | [S2] Stop creating /etc/nologin before validation and leaking it on error paths | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/9 |
| [10](https://github.com/biondogs/mprov_jobserver/issues/10) | JS-010 | [S2] Propagate post-boot and image script failures instead of reporting success | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/10 |
| [11](https://github.com/biondogs/mprov_jobserver/issues/11) | JS-011 | [S2] Fix inverted switch merge so switches get DHCP entries | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/11 |
| [12](https://github.com/biondogs/mprov_jobserver/issues/12) | JS-012 | [S2] Fix load monitor guard that crashes the daemon under high load | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/12 |
| [13](https://github.com/biondogs/mprov_jobserver/issues/13) | JS-013 | [S2] Create the authorized_keys directory inside the image, not on the build host | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/13 |
| [14](https://github.com/biondogs/mprov_jobserver/issues/14) | JS-014 | [S2] Report the one-minute load average the field name promises | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/14 |
| [15](https://github.com/biondogs/mprov_jobserver/issues/15) | JS-015 | [S2] Fix repack_image so it does not destroy the image it repacks | S2 | bug | https://github.com/biondogs/mprov_jobserver/issues/15 |
| [16](https://github.com/biondogs/mprov_jobserver/issues/16) | JS-016 | [S3] Tolerate unset optional network fields in DHCP config generation | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/16 |
| [17](https://github.com/biondogs/mprov_jobserver/issues/17) | JS-017 | [S3] Check dnsmasq worker outcomes before marking jobs successful | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/17 |
| [18](https://github.com/biondogs/mprov_jobserver/issues/18) | JS-018 | [S3] Claim jobs per jobserver and atomically to prevent double processing | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/18 |
| [19](https://github.com/biondogs/mprov_jobserver/issues/19) | JS-019 | [S3] Fix broken error paths in repo-update that crash instead of failing jobs | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/19 |
| [20](https://github.com/biondogs/mprov_jobserver/issues/20) | JS-020 | [S3] Fix undefined jid reference in image-update error path | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/20 |
| [21](https://github.com/biondogs/mprov_jobserver/issues/21) | JS-021 | [S3] Stop changing the daemon working directory from worker threads | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/21 |
| [22](https://github.com/biondogs/mprov_jobserver/issues/22) | JS-022 | [S3] Reap jobs orphaned in running state when a worker dies mid-job | S3 | enhancement | https://github.com/biondogs/mprov_jobserver/issues/22 |
| [23](https://github.com/biondogs/mprov_jobserver/issues/23) | JS-023 | [S3] Match the dnsmasq restart target precisely instead of killing by substring | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/23 |
| [24](https://github.com/biondogs/mprov_jobserver/issues/24) | JS-024 | [S3] Fix handler attribute reference that breaks high-load shedding in the webserver | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/24 |
| [25](https://github.com/biondogs/mprov_jobserver/issues/25) | JS-025 | [S3] Clean up image build bind mounts on failure and before archiving | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/25 |
| [26](https://github.com/biondogs/mprov_jobserver/issues/26) | JS-026 | [S3] Stop interpolating mPCC-sourced values into shell command strings | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/26 |
| [27](https://github.com/biondogs/mprov_jobserver/issues/27) | JS-027 | [S3] Close the file descriptor opened for connection-limit size checks | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/27 |
| [28](https://github.com/biondogs/mprov_jobserver/issues/28) | JS-028 | [S3] Send job timestamps in UTC as the code intends | S3 | bug | https://github.com/biondogs/mprov_jobserver/issues/28 |
| [29](https://github.com/biondogs/mprov_jobserver/issues/29) | JS-029 | [S4] Include the promised genders.include file in generated genders output | S4 | bug | https://github.com/biondogs/mprov_jobserver/issues/29 |
| [30](https://github.com/biondogs/mprov_jobserver/issues/30) | JS-030 | [S4] Enable flake8 and shellcheck lint gates in CI | S4 | enhancement | https://github.com/biondogs/mprov_jobserver/issues/30 |
| [31](https://github.com/biondogs/mprov_jobserver/issues/31) | ADD-001 | [S4] Document the image-sync and nads job modules in the README example | S4 | enhancement | https://github.com/biondogs/mprov_jobserver/issues/31 *(doc-gap addendum)* |

## biondogs/mprov_scripts

| issue# | id | title | severity | type | url |
|---|---|---|---|---|---|
| [1](https://github.com/biondogs/mprov_scripts/issues/1) | SCR-001 | [S2] Ansible loops never execute: over-escaped jq program is a compile error | S2 | bug | https://github.com/biondogs/mprov_scripts/issues/1 |
| [2](https://github.com/biondogs/mprov_scripts/issues/2) | SCR-002 | [S2] Missing-key jq null literal bypasses guards and corrupts root config | S2 | bug | https://github.com/biondogs/mprov_scripts/issues/2 |
| [3](https://github.com/biondogs/mprov_scripts/issues/3) | SCR-003 | [S2] Disk formatter crashes mounting non-RAID partitions: disk-level mount is None | S2 | bug | https://github.com/biondogs/mprov_scripts/issues/3 |
| [4](https://github.com/biondogs/mprov_scripts/issues/4) | SCR-004 | [S2] RAID build crashes: member disk id compared against disk slug string | S2 | bug | https://github.com/biondogs/mprov_scripts/issues/4 |
| [5](https://github.com/biondogs/mprov_scripts/issues/5) | SCR-005 | [S3] Unguarded cd before entity.json read leaves config variables empty | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/5 |
| [6](https://github.com/biondogs/mprov_scripts/issues/6) | SCR-006 | [S3] Service install scripts continue after failed commands and report success | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/6 |
| [7](https://github.com/biondogs/mprov_scripts/issues/7) | SCR-007 | [S3] Root fstab file deleted before rebuild with no failure isolation | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/7 |
| [8](https://github.com/biondogs/mprov_scripts/issues/8) | SCR-008 | [S3] Fill-partition handling reads stale loop variable for filesystem checks | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/8 |
| [9](https://github.com/biondogs/mprov_scripts/issues/9) | SCR-009 | [S3] BMC password passed on ipmitool command line is visible in process list | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/9 |
| [10](https://github.com/biondogs/mprov_scripts/issues/10) | SCR-010 | [S3] BMC setup crashes with NameError when systembmcs request fails | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/10 |
| [11](https://github.com/biondogs/mprov_scripts/issues/11) | SCR-011 | [S3] Post-boot python scripts exit 0 after reporting errors | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/11 |
| [12](https://github.com/biondogs/mprov_scripts/issues/12) | SCR-012 | [S3] Backup script always reports success even when every dump failed | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/12 |
| [13](https://github.com/biondogs/mprov_scripts/issues/13) | SCR-013 | [S3] BMC and InfiniBand IPs silently wrong when node IP misses mgmt prefix | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/13 |
| [14](https://github.com/biondogs/mprov_scripts/issues/14) | SCR-014 | [S3] Node import writes BMC credentials to world-readable temp file | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/14 |
| [15](https://github.com/biondogs/mprov_scripts/issues/15) | SCR-015 | [S3] Twelve shipped scripts missing from the mpcc_scripts manifest | S3 | enhancement | https://github.com/biondogs/mprov_scripts/issues/15 |
| [16](https://github.com/biondogs/mprov_scripts/issues/16) | SCR-016 | [S3] Hardcoded python3.8 site-packages path breaks Rocky 9 installs silently | S3 | bug | https://github.com/biondogs/mprov_scripts/issues/16 |
| [17](https://github.com/biondogs/mprov_scripts/issues/17) | SCR-017 | [S3] No guard against repartitioning the running OS disk | S3 | enhancement | https://github.com/biondogs/mprov_scripts/issues/17 |
| [18](https://github.com/biondogs/mprov_scripts/issues/18) | SCR-018 | [S4] Broken shebang in gpfs_mmsdrrestore.sh prevents direct execution | S4 | bug | https://github.com/biondogs/mprov_scripts/issues/18 |
| [19](https://github.com/biondogs/mprov_scripts/issues/19) | SCR-019 | [S4] Error messages print literal placeholder instead of exception detail | S4 | bug | https://github.com/biondogs/mprov_scripts/issues/19 |
| [20](https://github.com/biondogs/mprov_scripts/issues/20) | SCR-020 | [S4] Enable shellcheck for shell scripts in CI | S4 | enhancement | https://github.com/biondogs/mprov_scripts/issues/20 |
| [21](https://github.com/biondogs/mprov_scripts/issues/21) | SCR-021 | [S4] Rsync errors bypass the log file due to redirect order | S4 | bug | https://github.com/biondogs/mprov_scripts/issues/21 |

## biondogs/mash

| issue# | id | title | severity | type | url |
|---|---|---|---|---|---|
| [1](https://github.com/biondogs/mash/issues/1) | MASH-001 | [S2] Connect with user and password never authenticates | S2 | bug | https://github.com/biondogs/mash/issues/1 |
| [2](https://github.com/biondogs/mash/issues/2) | MASH-002 | [S2] Plugin dispatch mangles arguments containing the plugin name | S2 | bug | https://github.com/biondogs/mash/issues/2 |
| [3](https://github.com/biondogs/mash/issues/3) | MASH-003 | [S2] BMC power commands fail unless mprovURL ends with a slash | S2 | bug | https://github.com/biondogs/mash/issues/3 |
| [4](https://github.com/biondogs/mash/issues/4) | MASH-004 | [S2] BMC power commands give no success or failure feedback | S2 | bug | https://github.com/biondogs/mash/issues/4 |
| [5](https://github.com/biondogs/mash/issues/5) | MASH-005 | [S2] Failed API calls leave stale MPROV_RESULT from the previous command | S2 | bug | https://github.com/biondogs/mash/issues/5 |
| [6](https://github.com/biondogs/mash/issues/6) | MASH-006 | [S2] Pvar cannot print comma-separated variables with multi-character names | S2 | bug | https://github.com/biondogs/mash/issues/6 |
| [7](https://github.com/biondogs/mash/issues/7) | MASH-007 | [S3] Malformed command arguments crash the entire shell with a traceback | S3 | bug | https://github.com/biondogs/mash/issues/7 |
| [8](https://github.com/biondogs/mash/issues/8) | MASH-008 | [S3] API calls have no timeout and hang the shell indefinitely | S3 | bug | https://github.com/biondogs/mash/issues/8 |
| [9](https://github.com/biondogs/mash/issues/9) | MASH-009 | [S3] Signal handlers swallow SIGINT and SIGTERM during hung requests | S3 | bug | https://github.com/biondogs/mash/issues/9 |
| [10](https://github.com/biondogs/mash/issues/10) | MASH-010 | [S3] Error messages are written to stdout, polluting piped script output | S3 | bug | https://github.com/biondogs/mash/issues/10 |
| [11](https://github.com/biondogs/mash/issues/11) | MASH-011 | [S3] Script mode always exits 0 regardless of command failures | S3 | bug | https://github.com/biondogs/mash/issues/11 |
| [12](https://github.com/biondogs/mash/issues/12) | MASH-012 | [S3] Nonexistent script file argument is silently ignored | S3 | bug | https://github.com/biondogs/mash/issues/12 |
| [13](https://github.com/biondogs/mash/issues/13) | MASH-013 | [S3] Common config file shapes crash connect with raw tracebacks | S3 | bug | https://github.com/biondogs/mash/issues/13 |
| [14](https://github.com/biondogs/mash/issues/14) | MASH-014 | [S3] Foreach silently drops list items containing a hash character | S3 | bug | https://github.com/biondogs/mash/issues/14 |
| [15](https://github.com/biondogs/mash/issues/15) | MASH-015 | [S3] Dict-typed argument kills the whole interactive session | S3 | bug | https://github.com/biondogs/mash/issues/15 |
| [16](https://github.com/biondogs/mash/issues/16) | MASH-016 | [S3] Unparseable query tokens are silently swallowed and sent anyway | S3 | bug | https://github.com/biondogs/mash/issues/16 |
| [17](https://github.com/biondogs/mash/issues/17) | MASH-017 | [S3] Trailing ampersand on bmc commands silently disables the command | S3 | bug | https://github.com/biondogs/mash/issues/17 |
| [18](https://github.com/biondogs/mash/issues/18) | MASH-018 | [S4] Connect silently ignores non-200 responses from the control center | S4 | bug | https://github.com/biondogs/mash/issues/18 |
| [19](https://github.com/biondogs/mash/issues/19) | MASH-019 | [S4] Connect help documents the wrong config file paths | S4 | bug | https://github.com/biondogs/mash/issues/19 |
| [20](https://github.com/biondogs/mash/issues/20) | MASH-020 | [S4] Dead exception handler is defined but never installed | S4 | bug | https://github.com/biondogs/mash/issues/20 |
| [21](https://github.com/biondogs/mash/issues/21) | MASH-021 | [S4] Changelog generator links to the mprov_jobserver repository | S4 | bug | https://github.com/biondogs/mash/issues/21 |
| [22](https://github.com/biondogs/mash/issues/22) | MASH-022 | [S4] Bmc power help omits pxe and pxeefi actions supported by the server | S4 | bug | https://github.com/biondogs/mash/issues/22 |
| [23](https://github.com/biondogs/mash/issues/23) | MASH-023 | [S3] Release workflow uses retired actions and removed set-output syntax | S3 | bug | https://github.com/biondogs/mash/issues/23 |
| [24](https://github.com/biondogs/mash/issues/24) | MASH-024 | [S3] Add machine-readable JSON output mode | S3 | enhancement | https://github.com/biondogs/mash/issues/24 |
| [25](https://github.com/biondogs/mash/issues/25) | MASH-025 | [S3] Add dry-run mode to destructive verbs | S3 | enhancement | https://github.com/biondogs/mash/issues/25 |
| [26](https://github.com/biondogs/mash/issues/26) | MASH-026 | [S3] Validate config file and warn about unknown keys | S3 | enhancement | https://github.com/biondogs/mash/issues/26 |
| [27](https://github.com/biondogs/mash/issues/27) | MASH-027 | [S3] Bound dependency versions in requirements.txt | S3 | enhancement | https://github.com/biondogs/mash/issues/27 |
| [28](https://github.com/biondogs/mash/issues/28) | MASH-028 | [S4] Add linting to CI | S4 | enhancement | https://github.com/biondogs/mash/issues/28 |

