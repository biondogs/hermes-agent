# WORKLIST — 2026 Issue Sprint (project mprov-ng/9), ours-waves only

Generated 2026-10-23 by card t_0c186368 (sw-pm fanout). Scope: 110 issues = 83 Oct-15 migrated + 27 wave-2 relayed (receipts: oct15-migration/results.jsonl, sprint-sync/relay-receipts.json).
Live join (gh, 2026-10-23): project-9 status x issue state x open-PR overlap. 109/110 open+Todo; JS-001 closed (fixed by merged mprov_jobserver#190, project item Done) — excluded from batch 1.
Overlap scan: all open PRs in the four repos checked. mprov_scripts#19 + mash#17 (docs) MERGED 2026-10-23 — no fix overlap. Open mash#47/#48 (biondogs, re-approach lane of archived t_7531eb52) cover mash#33/#34 (S3) — flagged below. Open CC#306 targets issue #160 (not ours).

Priorities per operator pace ruling 2026-10-23: S1=8, S2=4 (t_d777f94d created at pre-ruling P6, steered to 4 by comment — only discrepancy). Batch 1 = S1+S2 = 30 fix cards, assignees alternating sw-dev-a/sw-dev-b (15/15).

| S | wave | fid | repo | issue | title | live | p9 | overlap | batch-1 card |
|---|------|-----|------|-------|-------|------|----|---------|--------------|
| S1 | wave2 | CC-051 | CC | [313] mprov-ng/mprov_control_center/issues/313 | OSDistro API serializer returns the distro root password in cleartext | open | Todo |  | t_1323a4f9 |
| S1 | oct15 | CC-001 | CC | [315] mprov-ng/mprov_control_center/issues/315 | Any API key grants unrestricted read-write access to every model endp... | open | Todo |  | t_b98c1339 |
| S1 | oct15 | CC-002 | CC | [316] mprov-ng/mprov_control_center/issues/316 | SystemBMCDetailSerializer returns BMC passwords in cleartext via ?detail | open | Todo |  | t_39267cd6 |
| S1 | oct15 | CC-004 | CC | [317] mprov-ng/mprov_control_center/issues/317 | Installers bake in admin:admin and changemenow default credentials | open | Todo |  | t_7ee1b88c |
| S1 | oct15 | CC-005 | CC | [318] mprov-ng/mprov_control_center/issues/318 | Unauthenticated register endpoint binds attacker MAC to systems | open | Todo |  | t_2f20d546 |
| S1 | oct15 | CC-006 | CC | [319] mprov-ng/mprov_control_center/issues/319 | Unauthenticated image endpoints trust spoofable X-Forwarded-For | open | Todo |  | t_e7923e46 |
| S1 | oct15 | CC-040 | CC | [332] mprov-ng/mprov_control_center/issues/332 | Power endpoint hostname parameter is a substring match hitting wrong ... | open | Todo |  | t_3cb052d1 |
| S1 | oct15 | JS-001 | JSR | [167] mprov-ng/mprov_jobserver/issues/167 | Remove the committed mPCC API key from stack.env | closed | Done | FIXED: merged JS#190; issue closed; p9 Done | — (batch 2+ pending operator GO) |
| S1 | oct15 | JS-002 | JSR | [168] mprov-ng/mprov_jobserver/issues/168 | Stop exposing the distro root password in process argv and daemon logs | open | Todo |  | t_95df5fb6 |
| S1 | oct15 | JS-003 | JSR | [169] mprov-ng/mprov_jobserver/issues/169 | Stop writing the fleet API key to world-readable files during provisi... | open | Todo |  | t_ca21d654 |
| S1 | oct15 | JS-004 | JSR | [170] mprov-ng/mprov_jobserver/issues/170 | Do not execute an unverified binary fetched to world-writable tmp | open | Todo |  | t_3215102f |
| S1 | oct15 | JS-005 | JSR | [171] mprov-ng/mprov_jobserver/issues/171 | Guard sweep cleanups so a mis-set image or repo directory cannot be w... | open | Todo |  | t_ed6f41d6 |
| S2 | wave2 | MASH-101 | MASH | [18] mprov-ng/mash/issues/18 | Script text is compiled as an unsandboxed Jinja2 template | open | Todo |  | t_d777f94d |
| S2 | oct15 | MASH-002 | MASH | [23] mprov-ng/mash/issues/23 | Plugin dispatch mangles arguments containing the plugin name | open | Todo |  | t_a30e12f9 |
| S2 | oct15 | MASH-003 | MASH | [24] mprov-ng/mash/issues/24 | BMC power commands fail unless mprovURL ends with a slash | open | Todo |  | t_5e03dbf6 |
| S2 | oct15 | MASH-004 | MASH | [25] mprov-ng/mash/issues/25 | BMC power commands give no success or failure feedback | open | Todo |  | t_ad6a98f4 |
| S2 | oct15 | MASH-005 | MASH | [26] mprov-ng/mash/issues/26 | Failed API calls leave stale MPROV_RESULT from the previous command | open | Todo |  | t_271e542c |
| S2 | oct15 | MASH-006 | MASH | [27] mprov-ng/mash/issues/27 | Pvar cannot print comma-separated variables with multi-character names | open | Todo |  | t_73a731de |
| S2 | oct15 | CC-010 | CC | [321] mprov-ng/mprov_control_center/issues/321 | Unauthenticated GET permanently removes jobservers from images | open | Todo |  | t_8d6cead3 |
| S2 | oct15 | CC-014 | CC | [322] mprov-ng/mprov_control_center/issues/322 | NetworkInterface save silently overwrites user-set hostname | open | Todo |  | t_066bd511 |
| S2 | oct15 | CC-038 | CC | [331] mprov-ng/mprov_control_center/issues/331 | PATCH handler silently substitutes admin user for anonymous requests | open | Todo |  | t_a4012130 |
| S2 | oct15 | JS-007 | JSR | [172] mprov-ng/mprov_jobserver/issues/172 | Fix malformed job query that claims every pending job in the queue | open | Todo |  | t_c0788988 |
| S2 | oct15 | JS-009 | JSR | [173] mprov-ng/mprov_jobserver/issues/173 | Stop creating /etc/nologin before validation and leaking it on error ... | open | Todo |  | t_2f505422 |
| S2 | oct15 | JS-010 | JSR | [174] mprov-ng/mprov_jobserver/issues/174 | Propagate post-boot and image script failures instead of reporting su... | open | Todo |  | t_ab709b77 |
| S2 | oct15 | JS-013 | JSR | [175] mprov-ng/mprov_jobserver/issues/175 | Create the authorized_keys directory inside the image, not on the bui... | open | Todo |  | t_88072414 |
| S2 | oct15 | JS-014 | JSR | [176] mprov-ng/mprov_jobserver/issues/176 | Report the one-minute load average the field name promises | open | Todo |  | t_fb1ef1c6 |
| S2 | oct15 | JS-015 | JSR | [177] mprov-ng/mprov_jobserver/issues/177 | Fix repack_image so it does not destroy the image it repacks | open | Todo |  | t_ffe3c8a5 |
| S2 | wave2 | SCR-022 | SCR | [20] mprov-ng/mprov_scripts/issues/20 | Database backup written world-readable to volatile /tmp | open | Todo |  | t_f84488db |
| S2 | oct15 | SCR-001 | SCR | [28] mprov-ng/mprov_scripts/issues/28 | Ansible loops never execute: over-escaped jq program is a compile error | open | Todo |  | t_ad39dbe4 |
| S2 | oct15 | SCR-003 | SCR | [29] mprov-ng/mprov_scripts/issues/29 | Disk formatter crashes mounting non-RAID partitions: disk-level mount... | open | Todo |  | t_01679e4f |
| S2 | oct15 | SCR-004 | SCR | [30] mprov-ng/mprov_scripts/issues/30 | RAID build crashes: member disk id compared against disk slug string | open | Todo |  | t_2500e704 |
| S3 | wave2 | MASH-102 | MASH | [19] mprov-ng/mash/issues/19 | GET and DELETE query values are concatenated unencoded into the query... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-007 | MASH | [28] mprov-ng/mash/issues/28 | Malformed command arguments crash the entire shell with a traceback | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-008 | MASH | [29] mprov-ng/mash/issues/29 | API calls have no timeout and hang the shell indefinitely | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-009 | MASH | [30] mprov-ng/mash/issues/30 | Signal handlers swallow SIGINT and SIGTERM during hung requests | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-010 | MASH | [31] mprov-ng/mash/issues/31 | Error messages are written to stdout, polluting piped script output | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-011 | MASH | [32] mprov-ng/mash/issues/32 | Script mode always exits 0 regardless of command failures | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-013 | MASH | [33] mprov-ng/mash/issues/33 | Common config file shapes crash connect with raw tracebacks | open | Todo | open PR mash#47 (re-approach lane) | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-014 | MASH | [34] mprov-ng/mash/issues/34 | Foreach silently drops list items containing a hash character | open | Todo | open PR mash#48 (re-approach lane) | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-015 | MASH | [35] mprov-ng/mash/issues/35 | Dict-typed argument kills the whole interactive session | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-016 | MASH | [36] mprov-ng/mash/issues/36 | Unparseable query tokens are silently swallowed and sent anyway | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-017 | MASH | [37] mprov-ng/mash/issues/37 | Trailing ampersand on bmc commands silently disables the command | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-024 | MASH | [42] mprov-ng/mash/issues/42 | Add machine-readable JSON output mode | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-025 | MASH | [43] mprov-ng/mash/issues/43 | Add dry-run mode to destructive verbs | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-026 | MASH | [44] mprov-ng/mash/issues/44 | Validate config file and warn about unknown keys | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | MASH-027 | MASH | [45] mprov-ng/mash/issues/45 | Bound dependency versions in requirements.txt | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | CC-041 | CC | [309] mprov-ng/mprov_control_center/issues/309 | IPv6 jobserver addresses lack bracket wrapping in image URLs | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | CC-042 | CC | [310] mprov-ng/mprov_control_center/issues/310 | Script save crashes with AttributeError when script type is null | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | CC-043 | CC | [311] mprov-ng/mprov_control_center/issues/311 | PXE bootdev ipmitool exit status ignored so failed setup reports success | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | CC-044 | CC | [312] mprov-ng/mprov_control_center/issues/312 | Change signals reset in-flight jobs to pending under the same name | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-007 | CC | [320] mprov-ng/mprov_control_center/issues/320 | Authenticated system endpoints trust spoofable X-Forwarded-For | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-023 | CC | [323] mprov-ng/mprov_control_center/issues/323 | Installer continues after failing to disable netboot | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-026 | CC | [324] mprov-ng/mprov_control_center/issues/324 | Unguarded System/image pk lookups return 500 on unknown ids (powersta... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-027 | CC | [325] mprov-ng/mprov_control_center/issues/325 | Unauthenticated datamodel and status-changes endpoints leak internals | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-028 | CC | [326] mprov-ng/mprov_control_center/issues/326 | Runtime dependencies except Django remain fully unpinned | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-031 | CC | [327] mprov-ng/mprov_control_center/issues/327 | Model signals recover the request via stack-frame inspection | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-032 | CC | [328] mprov-ng/mprov_control_center/issues/328 | Unguarded request.data key access on jobservers/ostype register retur... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | CC-033 | CC | [329] mprov-ng/mprov_control_center/issues/329 | Image slug regenerated on every save silently drops renames | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-07 | JSR | [156] mprov-ng/mprov_jobserver/issues/156 | script-runner silently falls back to the nads image on any -i fetch f... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-08 | JSR | [157] mprov-ng/mprov_jobserver/issues/157 | repo-update never joins its worker threads — overlapping reposyncs, o... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-09 | JSR | [158] mprov-ng/mprov_jobserver/issues/158 | image-delete rmtree path built from unvalidated job param (traversal)... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-11 | JSR | [159] mprov-ng/mprov_jobserver/issues/159 | register_server exits the whole daemon on a transient mPCC 500 | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-12 | JSR | [160] mprov-ng/mprov_jobserver/issues/160 | MProvScript assigns a sockaddr tuple to ip_address | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-13 | JSR | [161] mprov-ng/mprov_jobserver/issues/161 | repo-delete module is a stub that claims jobs and simulates success | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | JSR2-14 | JSR | [162] mprov-ng/mprov_jobserver/issues/162 | setup.py feeds requirements lines with inline comments into install_r... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-016 | JSR | [178] mprov-ng/mprov_jobserver/issues/178 | Tolerate unset optional network fields in DHCP config generation | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-017 | JSR | [179] mprov-ng/mprov_jobserver/issues/179 | Check dnsmasq worker outcomes before marking jobs successful | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-022 | JSR | [180] mprov-ng/mprov_jobserver/issues/180 | Reap jobs orphaned in running state when a worker dies mid-job | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-023 | JSR | [181] mprov-ng/mprov_jobserver/issues/181 | Match the dnsmasq restart target precisely instead of killing by subs... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-024 | JSR | [182] mprov-ng/mprov_jobserver/issues/182 | Fix handler attribute reference that breaks high-load shedding in the... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-025 | JSR | [183] mprov-ng/mprov_jobserver/issues/183 | Clean up image build bind mounts on failure and before archiving | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-026 | JSR | [184] mprov-ng/mprov_jobserver/issues/184 | Stop interpolating mPCC-sourced values into shell command strings | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-027 | JSR | [185] mprov-ng/mprov_jobserver/issues/185 | Close the file descriptor opened for connection-limit size checks | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | JS-028 | JSR | [186] mprov-ng/mprov_jobserver/issues/186 | Send job timestamps in UTC as the code intends | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-023 | SCR | [21] mprov-ng/mprov_scripts/issues/21 | Data-share fstab append corrupts fstab or skips the mount via loose m... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-024 | SCR | [22] mprov-ng/mprov_scripts/issues/22 | Shadow file rewritten in place with no atomic write or backup | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-025 | SCR | [23] mprov-ng/mprov_scripts/issues/23 | Slurmd config rebuilt through fixed world-writable tmp path | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-026 | SCR | [24] mprov-ng/mprov_scripts/issues/24 | Unpinned network installs of jobserver and yq at image build time | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-027 | SCR | [25] mprov-ng/mprov_scripts/issues/25 | Image name unvalidated into destructive rsync delete target | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | wave2 | SCR-028 | SCR | [26] mprov-ng/mprov_scripts/issues/26 | CSV import keeps CR and splits records on whitespace corrupting fields | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-005 | SCR | [31] mprov-ng/mprov_scripts/issues/31 | Unguarded cd before entity.json read leaves config variables empty | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-006 | SCR | [32] mprov-ng/mprov_scripts/issues/32 | Service install scripts continue after failed commands and report suc... | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-007 | SCR | [33] mprov-ng/mprov_scripts/issues/33 | Root fstab file deleted before rebuild with no failure isolation | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-008 | SCR | [34] mprov-ng/mprov_scripts/issues/34 | Fill-partition handling reads stale loop variable for filesystem checks | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-009 | SCR | [35] mprov-ng/mprov_scripts/issues/35 | BMC password passed on ipmitool command line is visible in process list | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-010 | SCR | [36] mprov-ng/mprov_scripts/issues/36 | BMC setup crashes with NameError when systembmcs request fails | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-011 | SCR | [37] mprov-ng/mprov_scripts/issues/37 | Post-boot python scripts exit 0 after reporting errors | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-012 | SCR | [38] mprov-ng/mprov_scripts/issues/38 | Backup script always reports success even when every dump failed | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-013 | SCR | [39] mprov-ng/mprov_scripts/issues/39 | BMC and InfiniBand IPs silently wrong when node IP misses mgmt prefix | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-014 | SCR | [40] mprov-ng/mprov_scripts/issues/40 | Node import writes BMC credentials to world-readable temp file | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-015 | SCR | [41] mprov-ng/mprov_scripts/issues/41 | Twelve shipped scripts missing from the mpcc_scripts manifest | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-016 | SCR | [42] mprov-ng/mprov_scripts/issues/42 | Hardcoded python3.8 site-packages path breaks Rocky 9 installs silently | open | Todo |  | — (batch 2+ pending operator GO) |
| S3 | oct15 | SCR-017 | SCR | [43] mprov-ng/mprov_scripts/issues/43 | No guard against repartitioning the running OS disk | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | MASH-103 | MASH | [20] mprov-ng/mash/issues/20 | Plugin output and plugin help bypass the shell's redirectable stdout | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | MASH-018 | MASH | [38] mprov-ng/mash/issues/38 | Connect silently ignores non-200 responses from the control center | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | MASH-020 | MASH | [39] mprov-ng/mash/issues/39 | Dead exception handler is defined but never installed | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | MASH-021 | MASH | [40] mprov-ng/mash/issues/40 | Changelog generator links to the mprov_jobserver repository | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | MASH-022 | MASH | [41] mprov-ng/mash/issues/41 | Bmc power help omits pxe and pxeefi actions supported by the server | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | MASH-028 | MASH | [46] mprov-ng/mash/issues/46 | Add linting to CI | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | CC-036 | CC | [330] mprov-ng/mprov_control_center/issues/330 | No lint or static-analysis gate in CI | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | JSR2-15 | JSR | [163] mprov-ng/mprov_jobserver/issues/163 | Dead enableDHCP=False in the dnsmasq no-jobs branch misleads readers | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | JSR2-16 | JSR | [164] mprov-ng/mprov_jobserver/issues/164 | Image build runs 'dnf -y clean all' against the build host | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | JSR2-17 | JSR | [165] mprov-ng/mprov_jobserver/issues/165 | Installer fetches the systemd unit from the upstream main tip over th... | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | JSR2-18 | JSR | [166] mprov-ng/mprov_jobserver/issues/166 | Runtime dependencies are unpinned in requirements.txt | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | JS-030 | JSR | [187] mprov-ng/mprov_jobserver/issues/187 | No lint gate in CI | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | wave2 | SCR-029 | SCR | [27] mprov-ng/mprov_scripts/issues/27 | Duplicated ipmitool netmask block in BMC setup with trailing-space arg | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | SCR-018 | SCR | [44] mprov-ng/mprov_scripts/issues/44 | Broken shebang in gpfs_mmsdrrestore.sh prevents direct execution | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | SCR-019 | SCR | [45] mprov-ng/mprov_scripts/issues/45 | Error messages print literal placeholder instead of exception detail | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | SCR-020 | SCR | [47] mprov-ng/mprov_scripts/issues/47 | Enable shellcheck for shell scripts in CI | open | Todo |  | — (batch 2+ pending operator GO) |
| S4 | oct15 | SCR-021 | SCR | [48] mprov-ng/mprov_scripts/issues/48 | Rsync errors bypass the log file due to redirect order | open | Todo |  | — (batch 2+ pending operator GO) |

## Tallies
- S1: 12 items, 11 batch-1 cards
- S2: 19 items, 19 batch-1 cards
- S3: 62 items, 0 batch-1 cards
- S4: 17 items, 0 batch-1 cards
- Hotspots flagged in card bodies: mprov_control_center/common/views.py (#315+#331), mprov_control_center/systems/views_noauth.py (#319+#321), mash/src/mash/app.py (#18,#23,#26,#27), mash/src/mash/plugins/bmc.py (#24,#25), mprov_jobserver/plugins/script_runner.py (#173+#174), mprov_jobserver/plugins/image_update.py (#168+#170+#175), mprov_scripts/post-boot/localTempDisk.py (#29+#30)

Batch 2 (S3 x62) and batch 3 (S4 x17) await operator GO; recommendation: gate on review-queue absorption of batch 1 (>=50% of the 30 batch-1 cards merged/closed, roughly 2-3 days of reviewer throughput), and note 2 of the 62 S3 items (mash#33/#34) are already in flight via mash#47/#48.
