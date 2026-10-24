# SKIP receipts — impact-retrofit-2026-10-24 / mprov_scripts

Classification pass 2026-10-24 against live GitHub (gh, identity `biondogs`) and
origin/master @ `a44f519` (script files byte-identical to filing commit `eb80617`;
the eb80617..a44f519 diff touches only AGENTS.md, CLAUDE.md, README.md, openwiki/**).

Skipped (no draft written):

- **issue #30** — premise invalid on the current default branch (classification (b)
  analogue: defect verified absent, not fixed-since). Our own freshness-gate comment
  (2026-10-23, biondogs) carries the full receipt: `DiskLayout`'s primary key IS the
  slug string, so `sdisk['slug'] == member['disklayout']` at
  `post-boot/localTempDisk.py:174` matches key-to-key and RAID build does not crash.
  Receipt: `mprov/maint-2026-10-23/oct15-migration/FRESHNESS-SCR-004-RECEIPT-2026-10-23.md`.
  That comment recommends close-as-invalid; close decision belongs to the maintainer
  lane, not this retrofit (bodies-only program).

- **PR #50** — maintainer-engaged (classification (a), by content). 2026-10-24
  comment "if this is accurate how is this working in the production system" is
  addressed TO @biondogs — a maintainer-side reply in discussion under our filing.
  **Identity anomaly flagged:** the comment's API author login is `biondogs`
  (assoc MEMBER) despite addressee-@-mention content; engagement judged by content,
  conservatively skipping. Do not touch.

- **PR #51** — maintainer-engaged (classification (a), by content). 2026-10-24
  comment "LTGM, moves back up from temp to root with reasonable perms, was this
  intended as a back up or just like an intermediate/ running copy?" is addressed
  TO @uberlinuxguy — live design discussion under the filing. **Same identity
  anomaly:** API author login is `biondogs`. Conservative skip; do not touch.

In scope despite linked engaged PRs (issues themselves have zero engagement and the
defects remain on master — PRs unmerged): issue #20 (PR #51), issue #29 (PR #50).

PR #49 in scope: its single review is by `biondogs` (self) — no maintainer engagement.
