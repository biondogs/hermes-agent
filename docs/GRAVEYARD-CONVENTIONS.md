> Status: current. Canonical registry entry: hermes-estate/docs/GOVERNANCE.md G-11/G-12 (2026-10-26).

# Graveyard & Tombstone Conventions (fleet decommission parking)

**Status:** doctrine (operator GO 2026-10-24, card t_f50fc845, finding F20 of
KANBAN-SYSTEM-AS-BUILT.md). BANK-MAP-adjacent: this governs *profile-homes*
lifecycle markers; BANK-MAP.md governs *Hindsight banks*.

## 1. What lives where

| Location | Holds | Mechanism |
|---|---|---|
| `~/.hermes/profiles/.deleted/<name>` | 8-byte `deleted\n` tombstones for deleted profiles | Fleet deletion convention (t_0eec511d SWEEP-FOLLOWUP and earlier retirements) |
| `~/.hermes/backups/` | sha256-verified full `tar.gz` copies of deleted profile homes, taken **before** deletion | Deletion protocol (see `husk-deletion-20261024/SHA256SUMS`) |
| `~/.hermes/skill-backups/` | Skill curation/split/pre-evolution copies (`.md` snapshots + tars) | **Separate mechanism** — skill lifecycle, not profile deletion. NOT redundant with `.deleted/` and never a substitute for it. |

Note: the graveyard is at `~/.hermes/profiles/.deleted/` — there is **no**
`~/.hermes/.deleted/`. (The remediation card that prompted this doc assumed the
latter; the census found only the former.)

Purpose of a tombstone: (a) reverse lookup — "why doesn't profile X exist?
it was deleted (mtime = deletion timestamp)"; (b) name-reuse guard — a name
with a tombstone should not be silently re-minted by tooling that auto-creates
profile homes (see the fleet-census re-mint race, as-built §9 errata item 4).

## 2. Current inventory (2026-10-24)

| Tombstone | Deleted | Paired pre-deletion backup |
|---|---|---|
| `coding` | 2026-10-24 | `~/.hermes/backups/husk-deletion-20261024/coding.tar.gz` (sha256-verified) |
| `kworker-muse-probe` | 2026-10-24 | `~/.hermes/backups/husk-deletion-20261024/kworker-muse-probe.tar.gz` (sha256-verified) |
| `sampling-test` | 2026-10-24 | `~/.hermes/backups/husk-deletion-20261024/sampling-test.tar.gz` (sha256-verified; bank hb-sampling-test also deleted per protocol) |
| `unsloth-litellm` | 2026-10-23 | `~/.hermes/backups/unsloth-litellm-decommission-20261023T211940Z/` (full home + MANIFEST) |
| `gaudi-reviewer` | 2026-10-13 | **none found** in `~/.hermes/backups/` (pre-convention retirement; q38p-fleet-archive-2026-10-12 holds the q38p-* fleet only, kba-20261013 is the architect's own snapshot) |

## 3. Retention rule

- Tombstones whose paired backup exists **and** its sha256 verifies may be
  purged after **2026-11-30** if the estate wants hygiene; they cost 8 bytes
  each, so keeping them is also acceptable. Purge is a filesystem delete of
  the tombstone file only — never of the backup.
- `gaudi-reviewer` (no dedicated pre-deletion backup anywhere) is **kept
  indefinitely**: it is the sole marker that the name was retired.
- Tombstones are cheap and load-bearing for name-reuse protection; when in
  doubt, keep.

## 4. Deletion protocol (for future runs)

1. Sweep references first (all board DBs, all cron stores, dispatcher/global
   config, live processes) — zero hits required.
2. Take a full tar of the profile home + record sha256 in the backup dir.
3. Delete the home (guarded — refuse if unexpected files present; watch for
   the census re-mint race and re-verify absence).
4. Write the `deleted\n` tombstone into `~/.hermes/profiles/.deleted/`.
5. Record the retirement in KANBAN-SYSTEM-AS-BUILT.md §3 roster (DELETED
   marker) and in the run receipts.
