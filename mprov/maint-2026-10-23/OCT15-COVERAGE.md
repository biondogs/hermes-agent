# Oct-15 wave → mprov-ng migration coverage receipt (120/120)

Card: t_74e17627 (MPROV-M-OCT15-MIGRATE) · executed 2026-10-23 by sw-pm.
Source of the 120: mprov/FILED-ISSUES.md (2026-10-15 filing wave on biondogs forks;
CC fork #4–#43, JS fork #1–#31, SCR fork #1–#21, mash fork #1–#28; 119 findings + ADD-001).
Forks are deleted/archived — mprov-ng is now the only venue (FORK-ENDGAME ruling).

Re-verification heads used: mprov_control_center 6afb414, mprov_jobserver b07393d,
mprov_scripts eb80617, mash 36b6a5e. CC dispositions from t_2eae052c sweep (pin d7c2094;
d7c2094..6afb414 delta verified: Django pin (PR #308) + docs only) — 4 partials re-verified
at head; 3 fixed-refs spot-checked at head (CC-003 IPMI_PASSWORD sites, CC-035 400/404 paths,
CC-040 substring match still live). JS drift 1fd4b12..b07393d verified: repo_sync chdir fix
(#131) + tests + docs only; SCR/MASH sweep pins == current heads.

Tally: **83 migrated** (new mprov-ng issues, distilled ≤150w bodies, labels per 2026-10-23
wave precedent) · **26 fixed-upstream** (upstream refs) · **11 already-upstream-twin**
(live mprov-ng issues) · **0 dead**. Sum = 120.

## Coverage table

| fork-repo#issue | finding id | disposition | project 9 |
|---|---|---|---|
| biondogs/mprov_control_center#4 | CC-001 | migrated → mprov-ng/mprov_control_center#315 (https://github.com/mprov-ng/mprov_control_center/issues/315) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#5 | CC-002 | migrated → mprov-ng/mprov_control_center#316 (https://github.com/mprov-ng/mprov_control_center/issues/316) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#6 | CC-003 | fixed-upstream → S-01 ed147bf (PR #194) | n/a (not filed) |
| biondogs/mprov_control_center#7 | CC-004 | migrated → mprov-ng/mprov_control_center#317 (https://github.com/mprov-ng/mprov_control_center/issues/317) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#8 | CC-005 | migrated → mprov-ng/mprov_control_center#318 (https://github.com/mprov-ng/mprov_control_center/issues/318) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#9 | CC-006 | migrated → mprov-ng/mprov_control_center#319 (https://github.com/mprov-ng/mprov_control_center/issues/319) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#10 | CC-007 | migrated → mprov-ng/mprov_control_center#320 (https://github.com/mprov-ng/mprov_control_center/issues/320) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#11 | CC-008 | fixed-upstream → DEAD-08 b30a5af (PR #192, installer deleted) | n/a (not filed) |
| biondogs/mprov_control_center#12 | CC-009 | already-upstream-twin → mprov-ng/mprov_control_center#272 — Default DRF permissions require both a login and an API key (OPEN) | n/a (not filed) |
| biondogs/mprov_control_center#13 | CC-010 | migrated → mprov-ng/mprov_control_center#321 (https://github.com/mprov-ng/mprov_control_center/issues/321) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#14 | CC-011 | fixed-upstream → H-01 8d6cdfd (PR #183) | n/a (not filed) |
| biondogs/mprov_control_center#15 | CC-012 | fixed-upstream → H-03 d306b1e (PR #185) | n/a (not filed) |
| biondogs/mprov_control_center#16 | CC-013 | fixed-upstream → D-02 c6819c9 (detail_serializer_class; verified absent at 6afb414) | n/a (not filed) |
| biondogs/mprov_control_center#17 | CC-014 | migrated → mprov-ng/mprov_control_center#322 (https://github.com/mprov-ng/mprov_control_center/issues/322) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#18 | CC-015 | fixed-upstream → D-43 bddcb9f (PR #239) | n/a (not filed) |
| biondogs/mprov_control_center#19 | CC-016 | fixed-upstream → D-19 a839e65 (PR #220) | n/a (not filed) |
| biondogs/mprov_control_center#20 | CC-017 | fixed-upstream → D-01 834ff60 (PR #205) | n/a (not filed) |
| biondogs/mprov_control_center#21 | CC-018 | already-upstream-twin → mprov-ng/mprov_control_center#254 — Track job servers per network... flag stale job servers instead of deleting them (OPEN; upstream moved CC-018 here) | n/a (not filed) |
| biondogs/mprov_control_center#22 | CC-019 | fixed-upstream → D-20 c6819c9 (detail serializer; verified absent at 6afb414) | n/a (not filed) |
| biondogs/mprov_control_center#23 | CC-020 | fixed-upstream → H-10 4f6e79b (PR #193) | n/a (not filed) |
| biondogs/mprov_control_center#24 | CC-021 | fixed-upstream → H-04 f4fcf12 (PR #186) | n/a (not filed) |
| biondogs/mprov_control_center#25 | CC-022 | already-upstream-twin → mprov-ng/mprov_control_center#286 — Image download retry only checks tar's exit status (OPEN; upstream moved CC-022 here) | n/a (not filed) |
| biondogs/mprov_control_center#26 | CC-023 | migrated → mprov-ng/mprov_control_center#323 (https://github.com/mprov-ng/mprov_control_center/issues/323) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#27 | CC-024 | fixed-upstream → B-08/DEAD-06 11f0a8f (PR #202, dead code deleted) | n/a (not filed) |
| biondogs/mprov_control_center#28 | CC-025 | already-upstream-twin → mprov-ng/mprov_control_center#280 — genNetworkInterfaces.py reads response in the except block where it's unbound (OPEN) | n/a (not filed) |
| biondogs/mprov_control_center#29 | CC-026 | migrated → mprov-ng/mprov_control_center#324 (https://github.com/mprov-ng/mprov_control_center/issues/324) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#30 | CC-027 | migrated → mprov-ng/mprov_control_center#325 (https://github.com/mprov-ng/mprov_control_center/issues/325) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#31 | CC-028 | migrated → mprov-ng/mprov_control_center#326 (https://github.com/mprov-ng/mprov_control_center/issues/326) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#32 | CC-029 | fixed-upstream → DEAD-08 b30a5af (PR #192, installer deleted) | n/a (not filed) |
| biondogs/mprov_control_center#33 | CC-030 | fixed-upstream → S-01 ed147bf (PR #194, argv form at CC-003 sites) | n/a (not filed) |
| biondogs/mprov_control_center#34 | CC-031 | migrated → mprov-ng/mprov_control_center#327 (https://github.com/mprov-ng/mprov_control_center/issues/327) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#35 | CC-032 | migrated → mprov-ng/mprov_control_center#328 (https://github.com/mprov-ng/mprov_control_center/issues/328) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#36 | CC-033 | migrated → mprov-ng/mprov_control_center#329 (https://github.com/mprov-ng/mprov_control_center/issues/329) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#37 | CC-034 | fixed-upstream → D-09 640404f (PR #215) | n/a (not filed) |
| biondogs/mprov_control_center#38 | CC-035 | fixed-upstream → D-23 38a08c1 (PR #223) | n/a (not filed) |
| biondogs/mprov_control_center#39 | CC-036 | migrated → mprov-ng/mprov_control_center#330 (https://github.com/mprov-ng/mprov_control_center/issues/330) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#40 | CC-037 | fixed-upstream → H-05 2ffe323 (PR #187) | n/a (not filed) |
| biondogs/mprov_control_center#41 | CC-038 | migrated → mprov-ng/mprov_control_center#331 (https://github.com/mprov-ng/mprov_control_center/issues/331) | Todo ✓ (read-back Todo) |
| biondogs/mprov_control_center#42 | CC-039 | fixed-upstream → D-29 9d3b07c (PR #227) | n/a (not filed) |
| biondogs/mprov_control_center#43 | CC-040 | migrated → mprov-ng/mprov_control_center#332 (https://github.com/mprov-ng/mprov_control_center/issues/332) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#1 | JS-001 | migrated → mprov-ng/mprov_jobserver#167 (https://github.com/mprov-ng/mprov_jobserver/issues/167) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#2 | JS-002 | migrated → mprov-ng/mprov_jobserver#168 (https://github.com/mprov-ng/mprov_jobserver/issues/168) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#3 | JS-003 | migrated → mprov-ng/mprov_jobserver#169 (https://github.com/mprov-ng/mprov_jobserver/issues/169) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#4 | JS-004 | migrated → mprov-ng/mprov_jobserver#170 (https://github.com/mprov-ng/mprov_jobserver/issues/170) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#5 | JS-005 | migrated → mprov-ng/mprov_jobserver#171 (https://github.com/mprov-ng/mprov_jobserver/issues/171) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#6 | JS-006 | already-upstream-twin → mprov-ng/mprov_jobserver#141 — image_sync and repo_sync crash when an image or repo was deleted (OPEN; same status_code=='404' string compare) | n/a (not filed) |
| biondogs/mprov_jobserver#7 | JS-007 | migrated → mprov-ng/mprov_jobserver#172 (https://github.com/mprov-ng/mprov_jobserver/issues/172) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#8 | JS-008 | already-upstream-twin → mprov-ng/mprov_jobserver#146 — script_runner: scripts with dependencies crash (OPEN; same dependsOn shape TypeError) | n/a (not filed) |
| biondogs/mprov_jobserver#9 | JS-009 | migrated → mprov-ng/mprov_jobserver#173 (https://github.com/mprov-ng/mprov_jobserver/issues/173) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#10 | JS-010 | migrated → mprov-ng/mprov_jobserver#174 (https://github.com/mprov-ng/mprov_jobserver/issues/174) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#11 | JS-011 | fixed-upstream → bcb08c1 (PR #126, closes mprov-ng/mprov_jobserver#119) | n/a (not filed) |
| biondogs/mprov_jobserver#12 | JS-012 | already-upstream-twin → mprov-ng/mprov_jobserver#147 — loadmon is read from config_data, where it never is (OPEN; same KeyError sites app.py + mprov_webserver) | n/a (not filed) |
| biondogs/mprov_jobserver#13 | JS-013 | migrated → mprov-ng/mprov_jobserver#175 (https://github.com/mprov-ng/mprov_jobserver/issues/175) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#14 | JS-014 | migrated → mprov-ng/mprov_jobserver#176 (https://github.com/mprov-ng/mprov_jobserver/issues/176) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#15 | JS-015 | migrated → mprov-ng/mprov_jobserver#177 (https://github.com/mprov-ng/mprov_jobserver/issues/177) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#16 | JS-016 | migrated → mprov-ng/mprov_jobserver#178 (https://github.com/mprov-ng/mprov_jobserver/issues/178) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#17 | JS-017 | migrated → mprov-ng/mprov_jobserver#179 (https://github.com/mprov-ng/mprov_jobserver/issues/179) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#18 | JS-018 | already-upstream-twin → mprov-ng/mprov_jobserver#112 — Job servers claim every pending job of a module, including jobs for other job servers (OPEN) | n/a (not filed) |
| biondogs/mprov_jobserver#19 | JS-019 | already-upstream-twin → mprov-ng/mprov_jobserver#145 — repo_update: the error paths crash instead of failing the job (OPEN; same self.js attr sites) | n/a (not filed) |
| biondogs/mprov_jobserver#20 | JS-020 | already-upstream-twin → mprov-ng/mprov_jobserver#144 — image_update: other error-path bugs in handle_jobs() (OPEN; covers jid used before defined at image_update.py:259) | n/a (not filed) |
| biondogs/mprov_jobserver#21 | JS-021 | fixed-upstream → 390e57c + 5fc62a3 + adf623a (PRs #129/#140/#132) + fab1ffd (PR #150, issue #131); all chdir sites fixed | n/a (not filed) |
| biondogs/mprov_jobserver#22 | JS-022 | migrated → mprov-ng/mprov_jobserver#180 (https://github.com/mprov-ng/mprov_jobserver/issues/180) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#23 | JS-023 | migrated → mprov-ng/mprov_jobserver#181 (https://github.com/mprov-ng/mprov_jobserver/issues/181) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#24 | JS-024 | migrated → mprov-ng/mprov_jobserver#182 (https://github.com/mprov-ng/mprov_jobserver/issues/182) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#25 | JS-025 | migrated → mprov-ng/mprov_jobserver#183 (https://github.com/mprov-ng/mprov_jobserver/issues/183) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#26 | JS-026 | migrated → mprov-ng/mprov_jobserver#184 (https://github.com/mprov-ng/mprov_jobserver/issues/184) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#27 | JS-027 | migrated → mprov-ng/mprov_jobserver#185 (https://github.com/mprov-ng/mprov_jobserver/issues/185) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#28 | JS-028 | migrated → mprov-ng/mprov_jobserver#186 (https://github.com/mprov-ng/mprov_jobserver/issues/186) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#29 | JS-029 | already-upstream-twin → mprov-ng/mprov_jobserver#136 — libgenders: /etc/genders.include is never appended (OPEN) | n/a (not filed) |
| biondogs/mprov_jobserver#30 | JS-030 | migrated → mprov-ng/mprov_jobserver#187 (https://github.com/mprov-ng/mprov_jobserver/issues/187) | Todo ✓ (read-back Todo) |
| biondogs/mprov_jobserver#31 | ADD-001 | fixed-upstream → 5fbdffe (README module docs, merged PR #153) | n/a (not filed) |
| biondogs/mprov_scripts#1 | SCR-001 | migrated → mprov-ng/mprov_scripts#28 (https://github.com/mprov-ng/mprov_scripts/issues/28) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#2 | SCR-002 | fixed-upstream → 4c2f703 (PR #18, closes mprov-ng/mprov_scripts#16; container tests added) | n/a (not filed) |
| biondogs/mprov_scripts#3 | SCR-003 | migrated → mprov-ng/mprov_scripts#29 (https://github.com/mprov-ng/mprov_scripts/issues/29) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#4 | SCR-004 | migrated → mprov-ng/mprov_scripts#30 (https://github.com/mprov-ng/mprov_scripts/issues/30) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#5 | SCR-005 | migrated → mprov-ng/mprov_scripts#31 (https://github.com/mprov-ng/mprov_scripts/issues/31) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#6 | SCR-006 | migrated → mprov-ng/mprov_scripts#32 (https://github.com/mprov-ng/mprov_scripts/issues/32) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#7 | SCR-007 | migrated → mprov-ng/mprov_scripts#33 (https://github.com/mprov-ng/mprov_scripts/issues/33) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#8 | SCR-008 | migrated → mprov-ng/mprov_scripts#34 (https://github.com/mprov-ng/mprov_scripts/issues/34) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#9 | SCR-009 | migrated → mprov-ng/mprov_scripts#35 (https://github.com/mprov-ng/mprov_scripts/issues/35) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#10 | SCR-010 | migrated → mprov-ng/mprov_scripts#36 (https://github.com/mprov-ng/mprov_scripts/issues/36) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#11 | SCR-011 | migrated → mprov-ng/mprov_scripts#37 (https://github.com/mprov-ng/mprov_scripts/issues/37) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#12 | SCR-012 | migrated → mprov-ng/mprov_scripts#38 (https://github.com/mprov-ng/mprov_scripts/issues/38) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#13 | SCR-013 | migrated → mprov-ng/mprov_scripts#39 (https://github.com/mprov-ng/mprov_scripts/issues/39) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#14 | SCR-014 | migrated → mprov-ng/mprov_scripts#40 (https://github.com/mprov-ng/mprov_scripts/issues/40) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#15 | SCR-015 | migrated → mprov-ng/mprov_scripts#41 (https://github.com/mprov-ng/mprov_scripts/issues/41) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#16 | SCR-016 | migrated → mprov-ng/mprov_scripts#42 (https://github.com/mprov-ng/mprov_scripts/issues/42) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#17 | SCR-017 | migrated → mprov-ng/mprov_scripts#43 (https://github.com/mprov-ng/mprov_scripts/issues/43) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#18 | SCR-018 | migrated → mprov-ng/mprov_scripts#44 (https://github.com/mprov-ng/mprov_scripts/issues/44) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#19 | SCR-019 | migrated → mprov-ng/mprov_scripts#45 (https://github.com/mprov-ng/mprov_scripts/issues/45) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#20 | SCR-020 | migrated → mprov-ng/mprov_scripts#47 (https://github.com/mprov-ng/mprov_scripts/issues/47) | Todo ✓ (read-back Todo) |
| biondogs/mprov_scripts#21 | SCR-021 | migrated → mprov-ng/mprov_scripts#48 (https://github.com/mprov-ng/mprov_scripts/issues/48) | Todo ✓ (read-back Todo) |
| biondogs/mash#1 | MASH-001 | fixed-upstream → 413d39c (PR #16, refs mprov-ng/mash#15; tests/test_connect.py) | n/a (not filed) |
| biondogs/mash#2 | MASH-002 | migrated → mprov-ng/mash#23 (https://github.com/mprov-ng/mash/issues/23) | Todo ✓ (read-back Todo) |
| biondogs/mash#3 | MASH-003 | migrated → mprov-ng/mash#24 (https://github.com/mprov-ng/mash/issues/24) | Todo ✓ (read-back Todo) |
| biondogs/mash#4 | MASH-004 | migrated → mprov-ng/mash#25 (https://github.com/mprov-ng/mash/issues/25) | Todo ✓ (read-back Todo) |
| biondogs/mash#5 | MASH-005 | migrated → mprov-ng/mash#26 (https://github.com/mprov-ng/mash/issues/26) | Todo ✓ (read-back Todo) |
| biondogs/mash#6 | MASH-006 | migrated → mprov-ng/mash#27 (https://github.com/mprov-ng/mash/issues/27) | Todo ✓ (read-back Todo) |
| biondogs/mash#7 | MASH-007 | migrated → mprov-ng/mash#28 (https://github.com/mprov-ng/mash/issues/28) | Todo ✓ (read-back Todo) |
| biondogs/mash#8 | MASH-008 | migrated → mprov-ng/mash#29 (https://github.com/mprov-ng/mash/issues/29) | Todo ✓ (read-back Todo) |
| biondogs/mash#9 | MASH-009 | migrated → mprov-ng/mash#30 (https://github.com/mprov-ng/mash/issues/30) | Todo ✓ (read-back Todo) |
| biondogs/mash#10 | MASH-010 | migrated → mprov-ng/mash#31 (https://github.com/mprov-ng/mash/issues/31) | Todo ✓ (read-back Todo) |
| biondogs/mash#11 | MASH-011 | migrated → mprov-ng/mash#32 (https://github.com/mprov-ng/mash/issues/32) | Todo ✓ (read-back Todo) |
| biondogs/mash#12 | MASH-012 | fixed-upstream → ccfe0a9 (refs mprov-ng/mash#9) | n/a (not filed) |
| biondogs/mash#13 | MASH-013 | migrated → mprov-ng/mash#33 (https://github.com/mprov-ng/mash/issues/33) | Todo ✓ (read-back Todo) |
| biondogs/mash#14 | MASH-014 | migrated → mprov-ng/mash#34 (https://github.com/mprov-ng/mash/issues/34) | Todo ✓ (read-back Todo) |
| biondogs/mash#15 | MASH-015 | migrated → mprov-ng/mash#35 (https://github.com/mprov-ng/mash/issues/35) | Todo ✓ (read-back Todo) |
| biondogs/mash#16 | MASH-016 | migrated → mprov-ng/mash#36 (https://github.com/mprov-ng/mash/issues/36) | Todo ✓ (read-back Todo) |
| biondogs/mash#17 | MASH-017 | migrated → mprov-ng/mash#37 (https://github.com/mprov-ng/mash/issues/37) | Todo ✓ (read-back Todo) |
| biondogs/mash#18 | MASH-018 | migrated → mprov-ng/mash#38 (https://github.com/mprov-ng/mash/issues/38) | Todo ✓ (read-back Todo) |
| biondogs/mash#19 | MASH-019 | fixed-upstream → c9608f6 (refs mprov-ng/mash#7) | n/a (not filed) |
| biondogs/mash#20 | MASH-020 | migrated → mprov-ng/mash#39 (https://github.com/mprov-ng/mash/issues/39) | Todo ✓ (read-back Todo) |
| biondogs/mash#21 | MASH-021 | migrated → mprov-ng/mash#40 (https://github.com/mprov-ng/mash/issues/40) | Todo ✓ (read-back Todo) |
| biondogs/mash#22 | MASH-022 | migrated → mprov-ng/mash#41 (https://github.com/mprov-ng/mash/issues/41) | Todo ✓ (read-back Todo) |
| biondogs/mash#23 | MASH-023 | fixed-upstream → 20a4069 + 76bf1d2 + 98c5e8c (ci.yml modernized, dependabot) | n/a (not filed) |
| biondogs/mash#24 | MASH-024 | migrated → mprov-ng/mash#42 (https://github.com/mprov-ng/mash/issues/42) | Todo ✓ (read-back Todo) |
| biondogs/mash#25 | MASH-025 | migrated → mprov-ng/mash#43 (https://github.com/mprov-ng/mash/issues/43) | Todo ✓ (read-back Todo) |
| biondogs/mash#26 | MASH-026 | migrated → mprov-ng/mash#44 (https://github.com/mprov-ng/mash/issues/44) | Todo ✓ (read-back Todo) |
| biondogs/mash#27 | MASH-027 | migrated → mprov-ng/mash#45 (https://github.com/mprov-ng/mash/issues/45) | Todo ✓ (read-back Todo) |
| biondogs/mash#28 | MASH-028 | migrated → mprov-ng/mash#46 (https://github.com/mprov-ng/mash/issues/46) | Todo ✓ (read-back Todo) |

## Dedupe sources (snapshots; copied into `mprov/maint-2026-10-23/oct15-migration/`)

- `snapshots/issues-<repo>.json` — `gh issue list --state all --limit 500` per mprov-ng repo
  taken 2026-10-23 (CC 189, JS 136, SCR 20, mash 11 issues). Wave-2 twins cross-checked:
  CC #309–#313 + #268/#270/#273/#274/#288/#290, JS #141–#146/#155–#166, SCR #20–#27, mash #18–#20.
- `snapshots/prs-<repo>.json` — open PRs per repo (1 each: docs/CI branches, none touching a
  migrated finding's defect).
- `snapshots/live-<repo>.json` + `snapshots/project9-itemlist.json` — post-filing live issue
  lists (duplicate-title audit) and the project-9 item read-back backing the table's
  project 9 column.
- Upstream REVIEW-2026-10.md audit (mprov_control_center, all 224 items closed 2026-10-20):
  Moved-links honored — e.g. CC-009→#272, CC-018→#254, CC-022→#286, CC-025→#280 (audit items
  H-*/D-* refs reused in fixed-upstream rows above). No REVIEW-2026-10.md exists in the
  jobserver/scripts/mash repos; their audits' outputs are their issue lists, covered by the
  snapshot dedupe.
- Today's wave-2 receipts: mprov/maint-2026-10-23/sprint-sync/{relay-receipts,twin-cleanup-receipt}.json
  (27 relayed + 9 skips; those twins are wave-2 findings CC-045..050/JSR2-01..03, not Oct-15 ids).
- Zero duplicate filings: every migrated title was token-matched against all open+closed
  mprov-ng issue titles (`match_twins.py`); every ≥0.4-score candidate was adjudicated
  (result: the 11 already-upstream-twin rows above; remaining candidates rejected as
  feature-request/old-era issues, e.g. CC#37, CC#63, JS#35, mash#1/#3/#8 — verified not twins).

## Filing shape

- Titles `[S<n>] <symptom>` per 2026-10-23 mprov-ng precedent; bodies distilled ≤150 words
  (symptom/evidence file:line at re-verification head/root cause/proposed fix/severity) with
  provenance line back to the fork issue; narrow-scope rows (CC-002/026/028/032/036, JS-030,
  SCR-005/006/015/020 updates) carry explicit partial-fix framing per t_2eae052c/t_412f1a54 sweeps.
- Labels: bug|enhancement + review-found + s1-blocker/s2-functional/s3-robustness/s4-hygiene
  (s2-functional + s4-hygiene created on mprov_control_center to match the sibling-repo
  taxonomy colors/descriptions).
- Filed bodies: card workspace `filing/<repo>-<fid>.md`; results `filing/results.jsonl`.

## Crash-run reconciliation (run 96 → run 103, per butler reconcile-before-filing order)

Run 96 crashed mid-filing. Run 103 reconciled the pack against FRESH live issue lists
`snapshots/live-<repo>.json`, taken 2026-10-23 pre-filing and re-fetched after filing.
56 of 83 pack rows existed live AND in `filing/results.jsonl` (URL-exact); 1 row (SCR-019)
was filed live by run 96 but never logged (adopted as scripts#45 after body byte-match);
0 orphans; the missing 26 were then filed. One transient duplicate of SCR-019
(scripts#46) was created during this reconciliation, detected by the post-filing
duplicate-title audit, and deleted (HTTP 410 confirmed); #45 retained. Titles were also
normalized to the `[S<n>] <symptom>` precedent (51 filed issues renamed via `gh issue edit`;
77 pack rows prefixed) — run 96 had shipped bare register titles for 77 of 83 rows.
A post-filing evidence audit (`evidence_check.py`) re-checked every cited file:line against
the maintenance-clone heads and refreshed 4 bodies (CC-001, CC-004, CC-027, SCR-006) whose
Oct-15 sites had moved upstream (installer scripts removed by DEAD-08/b30a5af; slurm
service script removed by 8134d25; CC url line-shift) — findings themselves survive on the
refreshed sites. CC-032's cited sites verified directly by grep (audit regex artifact).

## Readback

`readback.py` re-viewed every migrated issue with `gh issue view` after final filing:
**83/83 title AND body byte-match vs the filed pack** (`filing/<repo>-<fid>.md` +
updated `dispositions.json` file_title); all OPEN; every URL matches `results.jsonl`.
Repo-wide duplicate-title audit across all four repos (all states, 414 issues):
**zero duplicate titles**.

## Project 9

All 83 filed issues added to org `mprov-ng` project 9 ("2026 Issue Sprint") per butler
scope update (token scopes restored). Verified twice: (1) GraphQL item read-back after add
— 83/83 Status=Todo (`filing/project9.jsonl`); (2) `gh project item-list 9 --owner mprov-ng`
snapshot `snapshots/project9-itemlist.json` — all 83 URLs present, all Status=Todo.
Per-row status in the coverage table's project 9 column.
