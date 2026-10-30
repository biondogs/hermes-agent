#!/usr/bin/env python3
"""Converge the 'upstream-hermes-filing' skill into every filing-lane skill root.

Carrier pattern (mirrors provision-sdlc-review-fleet.py, t_6fa405f5 policy):
per-profile byte copies from the canonical bundle in the management repo, NOT
skills.external_dirs coupling. Bundled here because force-loading a filing
checklist across lanes (distiller, sw-dev-a/b, sw-docs, default) must not
depend on the shared tree's skill-resolution tiers.

SCOPE (t_1a63e305): filing lanes ONLY — default, distiller, sw-dev-a,
sw-dev-b, sw-docs. This is deliberately NOT a fleet sweep (G-30 territory);
extending to more profiles needs its own fleet-change card.

Canonical bundle (source of truth):
  /local/projects/software-co/skills/upstream-hermes-filing/SKILL.md
Doctrine text of record (do not restate rules in the skill):
  /local/projects/software-co/docs/UPSTREAM-HERMES-FILING-2026-10-30.md  (G-34)

Convergent + idempotent: a profile dir is touched only when the SKILL.md bytes
differ from the bundle; --check reports drift only. Skills are scanned per
worker spawn: no gateway restart needed.

FLEET PROFILE CENSUS LAW (t_881a0e4b) + HUSK LAW (t_9bd09e02): REAL profiles
only (config.yaml present); husks logged "husk, skipped", never touched.

Usage: python3 provision-upstream-hermes-filing.py [--check]
"""
from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
from fleet_profiles import husk_note, real_profile_dirs  # noqa: E402

BUNDLE = Path("/local/projects/software-co/skills/upstream-hermes-filing")
PROFILE_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_HOME = Path.home() / ".hermes"
SKILL_REL = Path("skills/upstream-hermes-filing")
SKILL_FILES = ["SKILL.md"]


def homes() -> list[Path]:
    roots = [DEFAULT_HOME]
    real, husks = real_profile_dirs(PROFILE_ROOT)
    for h in husks:
        print(husk_note(h.name))
    filing_lanes = {"distiller", "sw-dev-a", "sw-dev-b", "sw-docs"}
    roots += [h for h in real if h.name in filing_lanes]
    return roots


def provision(home: Path, check_only: bool) -> str:
    dst = home / SKILL_REL
    label = home.name if home != DEFAULT_HOME else "default(@@/.hermes)"
    if (home != DEFAULT_HOME and not (home / "config.yaml").exists()):
        return f"husk, skipped: {label}"
    drift = []
    for f in SKILL_FILES:
        src = BUNDLE / f
        tgt = dst / f
        if not tgt.exists() or not filecmp.cmp(src, tgt, shallow=False):
            drift.append(f)
    if not drift:
        return f"in sync: {label}"
    if check_only:
        return f"DRIFT {drift}: {label}"
    dst.mkdir(parents=True, exist_ok=True)
    for f in drift:
        shutil.copy2(BUNDLE / f, dst / f)
    return f"provisioned {drift}: {label}"


def main() -> int:
    check = "--check" in sys.argv
    for home in homes():
        print(provision(home, check))
    return 0


if __name__ == "__main__":
    sys.exit(main())
