# FRESHNESS GATE RECEIPT — SCR-004 / mprov-ng/mprov_scripts#30

Date: 2026-10-23 · Card: kanban t_2500e704 · Worker: sw-dev-b · gh identity: biondogs (allowlisted)

**Verdict: DEFECT DOES NOT REPRODUCE — filing premise factually wrong (slug primary key, not integer PK). NO PR opened. Issue commented; close decision deferred to maintainer.**

## Freshness gate
- Repo: https://github.com/mprov-ng/mprov_scripts (default branch `master`, no `main`)
- Base sha re-verified live: `a44f519e0c035270e092feb67d3d97533775aca4`
- Cited code present and unchanged since filing: `post-boot/localTempDisk.py:174` `if sdisk['slug'] == member['disklayout']:` — last touching commit `419f8bd` (2022-11-04); `git log eb80617..origin/master -- post-boot/localTempDisk.py` empty → byte-identical to the filing evidence sha `eb80617`.

## Why the premise is wrong
Issue claims the serialized RAID member `disklayout` is "an integer primary key" (PrimaryKeyRelatedField ⇒ int). It is a PrimaryKeyRelatedField, but:

1. `mprov_control_center/disklayouts/models.py`: `slug = models.SlugField(primary_key=True, unique=True, blank=True)` — **`DiskLayout`'s PK is the slug**; no integer id exists on the model.
2. Initial migration `disklayouts/migrations/0001_initial.py` (2022-08-04): `('slug', models.SlugField(primary_key=True, serialize=False))` — slug has been the PK since inception; no migration ever introduced an int PK on DiskLayout.
3. DRF `PrimaryKeyRelatedField.to_representation()` → `str(value.pk)` → for `DiskLayout` that is the slug string.

## Empirical verification (not serializer-reading alone)
Faithful replica of `DiskPartitionAPISerializer` (`disklayouts/serializers.py:6-11`: explicit `disklayout = PrimaryKeyRelatedField(...)`, `fields='__all__'`, `depth=2`) run against in-memory sqlite at mPCC's pinned stack (`requirements.txt`: `django>=4.2,<5`; resolved Django 4.2.30 / djangorestframework 3.17.2). Probe: `drf_slugpk_probe/settings_probe.py` (sw-dev-b scratch). Output:

```text
serialized member disklayout: 'local-sda' str
disk entry slug: 'local-sda'
slug == member disklayout: True
list-serialized member disklayout: 'local-sda'
```

Data path confirmed end-to-end: `localTempDisk.py::_getDiskLayout` → `systems/?self` (nested details ⇒ `SystemDetailSerializer.disks = DiskLayoutAPISerializer(many=True)`) → `getMembers()` → `DiskPartitionAPISerializer(...).data` ⇒ member `disklayout` = **slug string**. Therefore the live comparison in `buildRAIDs` is slug-vs-slug and matches key-to-key exactly as-is; RAID build does not crash on this line. (The explicit `PrimaryKeyRelatedField` declaration is honored over `depth`, which is why the PK representation — the slug — is what lands on the wire.)

## Actions taken
- Comment on mprov_scripts#30 with the above evidence: https://github.com/mprov-ng/mprov_scripts/issues/30 (verify below). No close action taken — maintainer's call.
- No branch, no commits, no PR opened (per card's fixed/does-not-reproduce branch: "open NO PR").
- No distiller pre-publication gate created — the gate exists only ahead of PR publication, which did not occur.

## Reporting fields
- issue: mprov-ng/mprov_scripts#30 (left OPEN, evidence comment posted)
- base sha: a44f519e0c035270e092feb67d3d97533775aca4
- head sha: n/a (no fix — nothing to fix)
- test-before/after: n/a (no fix); RED/GREEN gate N/A because the defect does not exist on base — probe above is the negative evidence
- PR URL: none (by design)
- reviewer: n/a
- CI state: n/a
- Overlap: sibling card t_01679e4f (#29, localTempDisk.py non-RAID mount) untouched by this finding — different code block; note for the PM: if other openwiki-wave filings claim "PrimaryKeyRelatedField ⇒ integer" against DiskLayout FKs, they share this incorrect premise.
