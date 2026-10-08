---
type: component-inventory
title: 'Battle Mode Console, Roster Builder & Dashboard Components'
description: 'Component inventory and responsibilities for the two force-facing modes of apps/web after the Battle Mode rewrite: the Edit Mode Roster Studio (debounced auto-save, static-JSON catalog, enhancements, leader linking, detachment switcher) and the Battle Mode tabletop console (self-contained HUD with command-point generator, interactive phase bar, phase-adaptive statlines, in-card stratagems, single-accordion force org), plus the orphaned CompositeUnitCard/StratagemPanel components and where static /data JSON and localStorage fixtures stand in for API data.'
tags: [webapp, battle-mode, roster-builder, command-points, phase-adaptive, combat-patrol, static-catalog, orphaned-components, fallback]
resource: repo://apps/web/src/app/army/%5Bid%5D/page.tsx
---

`apps/web` splits force construction and force play into two sibling client routes that share
types but never share state: `/army/[id]/edit` (**Edit Mode**, the Roster Studio) and `/army/[id]`
(**Battle Mode**, the tabletop console). Each header renders an explicit `✎ Edit Mode` /
`⚔ Battle Mode` toggle between them, and both mount a `ComplianceDashboard` modal.

The most important thing to know before changing anything here is that the console was rewritten
into a **self-contained Battle Mode HUD**: it no longer imports `CompositeUnitCard` or
`StratagemPanel`, has no wound/health tracking, and no longer substitutes demo units when a roster
is missing. The second is that the catalog the builder and console render is **static JSON shipped
in `apps/web/public/data/`**, not API data — see
[Static Catalog Data Pipeline](../data/catalog-data-pipeline.md).

Routing and the guest session that makes these pages reachable anonymously are covered by
[Web App Shell, Routing & Guest Session](./app-shell-and-guest-session.md); roster reads/writes
still go through [`apps/web/src/lib/api.ts`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/lib/api.ts), whose
swallow-everything fallbacks are documented in
[API Client & Fallback Layer](./api-client-fallback-layer.md). The canonical rules the console
imitates (leader attachment, stratagem gating) live in `@forceorg/rules-engine-11e` — see
[Composite Units & Stratagem Filtering](../rules-engine/composite-units-and-stratagems.md) and
[Roster Validation](../rules-engine/roster-validation.md). Neither route executes that package.

## Component map

| Component | Hosted by | Owns | Data source of truth |
| --- | --- | --- | --- |
| `BattleModeConsolePage` (`/army/[id]`) | route | round/phase/CP state, single-accordion force org, in-card stratagems | `fetchRoster` + `fetchStratagems` + `/data/factions/<id>.json` |
| `RosterBuilder` | `/army/[id]/edit` | roster unit list, catalog drawer, enhancements, leader linking, detachment switcher | `/data/factions/<id>.json` (starts empty) |
| dashboard (`/`) | route | Matched Play vs Combat Patrol tabs, army cards, patrol deploy | `fetchRosters` + `/data/combat-patrol/combat-patrols.json` |
| `ComplianceDashboard` | `/`, `/army/[id]`, `/army/[id]/edit` | rules-audit modal, verdict banner, discrepancy filtering | `auditRoster` result, else arithmetic over props |
| `FactionSelector` | every page header | heraldry palette switch | `ALL_FACTION_PALETTES` (static) |
| `CreateArmyModal` | `/` | faction/subfaction/detachment/name/size form → `createRoster` | `/data/factions/index.json` + per-faction JSON |
| `CompositeUnitCard`, `StratagemPanel`, `PhotoUploadModal` | **none** | orphaned: wound matrix, phase dock, photo upload UI | n/a (no route imports them) |
| `Skeleton`, `ErrorBoundary`/`InlineError` | app-wide | loading and render-failure presentation | n/a |

`CatalogUnit` / `RosterUnit` are exported from
[`RosterBuilder.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx) and imported by the console
for typing, so the builder's payload shape is effectively the roster persistence contract even
though `lib/api.ts` also accepts a leaner offline shape.

## View mode: the Battle Mode console

[`apps/web/src/app/army/[id]/page.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx) is a ~1000-line
self-contained HUD (`BattleModeConsolePage`,
[#L36](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L36)). The header shows the army name, a cyan
**"BATTLE MODE"** badge, and the Edit/Battle toggle
([#L318-L373](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L318-L373)).

**Load path, no fixture army.** On mount it calls `fetchRoster`, then `fetchDatasheets`, then
fetches `${basePath}/data/factions/${normalizedId}.json` (legacy ids normalised, e.g.
`adeptus_astartes` → `imperium-space-marines`) to read the chosen detachment's rules, then
`fetchStratagems({ detachmentId })`
([#L63-L124](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L63-L124)). If `fetchRoster` throws the page
only `console.warn`s and renders with `army = null`: header "Battle Console" and an empty-state
"No units in this battle force. Go to Edit Mode →"
([#L115-L119](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L115-L119),
[#L648-L651](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L648-L651)). The old `DEMO_FALLBACK_UNITS`
army is gone; the remaining fixture in this surface is the dashboard-level `STARTER_DEMO_ARMY`.

**Command-point generator.** HUD state is `battleRound` (starts 1), `commandPoints` (starts 1),
`activePhase` (starts `COMMAND`), `expandedUnitId`, `notification`
([#L50-L54](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L50-L54)). CP rules:
`handleGenerateCP` always +1; `handleSpendCP(amount, name)` refuses with a toast when CP is short;
`handleAdvanceRound` caps at round 5, resets the phase to COMMAND and grants +1 CP
([#L264-L287](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L264-L287)). UI: "+ Next Round (+1 CP)",
a manual CP counter with `−`/`+` buttons, a gold "⚡ Generate Command Phase CP (+1 CP)" button that
only renders while the COMMAND phase is active, and a per-ability "⚡ Generate CP" button whenever
ability text mentions CP/command points
([#L450-L594](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L450-L594),
[#L874-L910](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L874-L910)). Nothing about rounds, phases or
CP is persisted — reload resets the HUD.

**Phase-adaptive datacards.** An interactive five-button phase bar (COMMAND/MOVEMENT/SHOOTING/
CHARGE/FIGHT, [#L513-L560](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L513-L560)) drives the expanded
card: an "Active {phase} Statline" (OC+Leadership in COMMAND, M in MOVEMENT/CHARGE, T+Sv in
SHOOTING/FIGHT) plus full A/BS/WS/S/AP/D rows, with weapon section titles and row highlighting that
change with the phase
([#L719-L858](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L719-L858)).

**In-card stratagems.** Ten hard-coded `CORE_STRATAGEMS`
([#L23-L34](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L23-L34)) are merged, id-deduplicated, with
the detachment rows from `fetchStratagems`
([#L257-L261](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L257-L261)). Per unit, eligibility is a
local filter — phase is `ANY` or equals `activePhase`, and the unit must carry at least one
required keyword (empty list = always eligible) — rendered as "⚡ Legal {phase} Stratagems (N)" with
"Use Stratagem (−X CP)" buttons
([#L657-L663](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L657-L663),
[#L924-L979](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L924-L979)). This mirrors, without calling,
the canonical gate in `stratagem-filter.ts`
([Composite Units & Stratagem Filtering](../rules-engine/composite-units-and-stratagems.md)).

**Single-accordion force org, inline composite merge.** One `expandedUnitId` at a time (first unit
auto-expands, [#L250-L254](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L250-L254)). Leader/bodyguard
pairs are composed **inside the route** (`unitsList` useMemo, merged weapons tagged
`[Leader]`/`[Bodyguard]`, [#L127-L246](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L127-L246)) rather
than through the rules engine or `CompositeUnitCard`. There are **no wound counters or health bars**
and no screen wake lock — both were removed from this route.

**Detachment banner.** A "⚡ ACTIVE DETACHMENT" banner renders `army.detachmentPrimary`, the
detachment rules from the faction JSON, and a "Switch Detachment in Edit Mode →" link
([#L596-L644](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L596-L644)) — switching happens only in
Edit Mode. The `ComplianceDashboard` here receives `dpLimit` and `currentDp`
([#L990-L999](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/page.tsx#L990-L999)).

## Edit mode: the Roster Studio route

[`apps/web/src/app/army/[id]/edit/page.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/edit/page.tsx) is the
only writer of roster payloads. Unlike the console, it **still synthesises a complete Ultramarines
army object** ("Ultramarines Strike Force", Gladius Task Force, 2000 pts, empty units) when
`fetchRoster` rejects
([#L53-L72](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/edit/page.tsx#L53-L72)).

The debounced auto-save loop is unchanged in shape: `handleRosterChange` marks `unsaved` and
restarts a 1200 ms timer; `performSave` PUTs
`{ rosterPayload: { units, totalPoints, detachmentPointsUsed }, factionThemeOverride }` where
`totalPoints = Σ pointsCost` and **`detachmentPointsUsed = Σ catalogUnit.dpCost`**
([#L86-L123](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/edit/page.tsx#L86-L123)). Because `updateRoster`
writes localStorage *before* the PUT, swallows the PUT failure, and the page's `catch` also sets
`saveState = 'saved'`, **the "✓ Saved" pill can be shown while the server never accepted the
roster**.

`handleDetachmentChange` persists `detachmentPrimary` plus a recomputed payload via `updateRoster`
([#L135-L158](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/army/[id]/edit/page.tsx#L135-L158)) — this is how the console's
detachment banner gets its data. `FactionSelector` here is the only place a heraldry choice is
persisted (theme change triggers a save). This host passes `currentPoints` derived from
`currentUnitsRef.current.reduce(...)` — reading a ref during render is not reactive, so the audit's
point total can lag the editor by one render — and unlike the console and dashboard, **no**
`dpLimit`/`currentDp`.

## RosterBuilder: static catalog, enhancements, leader linking, detachment switcher

[`RosterBuilder.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx) is no longer the
demo-catalog component the previous revision described.

**Catalog starts empty and comes from static JSON.** `catalog` initialises to `[]`
([#L110](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L110)) and `loadCatalog` fetches
`${basePath}/data/factions/${normalizedId}.json`
([#L137-L153](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L137-L153)). There is no
`DEMO_CATALOG`, no `catalogSource` state, and no "● Live API Data" / "○ Standby Catalog" badge
anywhere in `src/` any more. `dpCost` maps from `datasheet.detachmentPointsCost`
([#L161](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L161)). Gotcha: `catalogError` is set on
fetch failure but never rendered, so a broken faction file yields a silently empty drawer.

**Subfaction inheritance.** When the faction JSON contains the current `subfactionId`, its
datasheets are appended to the unit list with `dpCost: 0`
([#L175-L200](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L175-L200)). The inheritance rules
themselves are baked into the extraction step, not the UI — see
[Static Catalog Data Pipeline](../data/catalog-data-pipeline.md).

**Enhancements and leaders.** Detachments and their enhancements come from the same JSON
([#L205-L219](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L205-L219)). A character-only dropdown
assigns an enhancement and adds `enh.points` to `pointsCost`, with the header counting "Enhancements
x / 3" ([#L287-L309](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L287-L309),
[#L395-L398](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L395-L398)). `setLeaderAttachment`
plus an "Attach to Bodyguard Unit" select implement leader linking in the browser, and removing a
unit unbinds its attached units
([#L274-L323](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L274-L323),
[#L849-L879](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L849-L879)).

**Detachment switcher strips enhancements silently.** The dropdown + "Apply Changes" button
([#L469-L592](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L469-L592)) calls
`handleApplyDetachment`, which **always clears every assigned enhancement without prompting**
before calling `onDetachmentChange`
([#L326-L358](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L326-L358)).

**What was removed.** `compileWahapediaWargear` is still imported
([#L10](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L10)) but never called; `wargearSelections`
is initialised `[]` and has no UI; the points/DP/Rule-of-Three warning block no longer exists
(`validationErrors` is dead state); `totalDP` is computed
([#L248](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/RosterBuilder.tsx#L248)) but never rendered. Client-side
validation now lives only in `ComplianceDashboard` and, canonically, in
[Roster Validation](../rules-engine/roster-validation.md).

## Dashboard: BeerHammer branding, Combat Patrol, DP tiles

[`apps/web/src/app/page.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx) shows the visible rebrand: the header
is **"BeerHammer"** with subtitle "Command Nexus • 11th Edition"
([#L230-L231](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L230-L231)); the document `<title>` in
`layout.tsx` still says "ForceOrg-40k", and the E2E suite matches either. Two tabs split the hub:
"🏆 Matched Play Rosters" and "⚡ Combat Patrol Mode (Official Wahapedia)", the latter loading
`${basePath}/data/combat-patrol/combat-patrols.json` with an alliance filter
([#L128-L147](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L128-L147),
[#L361-L404](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L361-L404)). "⚡ Deploy Patrol to Battle Mode" creates a
500-point roster with `detachmentPrimary: "Combat Patrol: <rule>"` and navigates straight to
`/army/<id>`
([#L156-L204](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L156-L204)).

Army cards now link **"⚔ Battle Mode"** (`/army/{id}`) and **"✎ Edit Mode"** (`/army/{id}/edit`) —
the old single "Console" label is gone — and show a "DP Cost x/y" stat
([#L456-L519](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L456-L519)). `STARTER_DEMO_ARMY` (three Ultramarines
units) survives solely as the dashboard fallback for an empty/failed `fetchRosters()`
([#L24-L67](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/page.tsx#L24-L67)); the E2E suite's "Captain in Terminator
Armour" assertions are satisfied by this army, not by console fixtures.

[`CreateArmyModal.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/CreateArmyModal.tsx) replaced its hard-coded
four-faction `FACTIONS` list with fetches of `${basePath}/data/factions/index.json` and the selected
faction file ([#L81](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/CreateArmyModal.tsx#L81),
[#L109](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/CreateArmyModal.tsx#L109)). It lists all 27 factions plus
subfactions, shows per-detachment enhancement counts, and still creates rosters with the fixed
`detachmentPointsLimit: 3`
([#L180-L187](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/CreateArmyModal.tsx#L180-L187)).

## Orphaned components: CompositeUnitCard, StratagemPanel, PhotoUploadModal

`CompositeUnitCard.tsx`, `StratagemPanel.tsx` and `PhotoUploadModal.tsx` still exist in
`src/components/` but **no route imports them** (the only remaining import is `CompositeUnitCard` →
`PhotoUploadModal`). Everything the previous revision documented about them — the duplicated
desktop/mobile mounts with independent wound state, `isOpen={true}` phase docks, the
`availableStratagemsCount={6}` literal, the blob-URL photo preview, the unused relative-`/api/.../media`
fetch — is dead code on the current tree. Treat these files as candidate deletions, not integration
points: miniature photo upload has no wired UI entry point until something mounts `PhotoUploadModal`
again ([Media Upload & Object Storage](../api/media-upload-and-object-storage.md)).

The catalog browser ([`apps/web/src/app/catalog/page.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/catalog/page.tsx))
is unchanged in shape: it renders `FALLBACK_CATALOG_DATASHEETS` until `fetchDatasheets` returns a
non-empty array, and `selectedFaction` remains hard-coded to `'adeptus_astartes'`
([#L130-L152](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/app/catalog/page.tsx#L130-L152)) — though `fetchDatasheets` now
normalises that id to `imperium-space-marines` and reads the static JSON first, so the catalog cards
are real extracted catalog data even offline.

## ComplianceDashboard: server audit first, arithmetic second

[`ComplianceDashboard.tsx`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/components/ComplianceDashboard.tsx) owns the
"Rules Audit" modal mounted by all three hosts.

`runAudit` fires whenever `isOpen` becomes true and on every Re-Audit click. It calls
`auditRoster(rosterId)`; only if that **throws** does it compute a client-side audit from props
(`POINTS_SHIFT` when `currentPoints > pointsLimit`, `DP_VIOLATION` when `currentDp > dpLimit`).
In practice [`auditRoster`](https://github.com/fatpat81/BeerHammer/blob/36f00f242ab6d5fe73ee567f7aa43069b2ec0fab/apps/web/src/lib/api.ts) catches its own failure and returns a
synthesised result from the localStorage roster, so the modal shows *some* verdict with no server
at all. Three banners follow — "Battle-Ready (100% Compliant)", "Legal With Advisory Warnings",
"Illegal Roster — Action Required". The "⚡ Sync Active Points (1-Click)" action renders only when
`onAutoFixPoints` is supplied; no host passes it, so the fix button stays unreachable and the
component's `updateRoster` import unused.

Host asymmetry worth remembering: the dashboard and the Battle Mode console pass `dpLimit` +
`currentDp`; the Roster Studio does not, so its DP tile shows `0 / 3` regardless of the roster.

## Working rules for changes here

- The console HUD state (round, phase, CP, expanded unit) is intentionally transient; persisting any
  of it means designing where it belongs, since `rosterPayload` has no field for it and the server
  does not validate the payload at all ([Shared Contracts](../architecture/shared-contracts.md)).
- Catalog/stat/enhancement/detachment facts now have one generated home:
  `apps/web/public/data/factions/*.json` ([Static Catalog Data Pipeline](../data/catalog-data-pipeline.md)).
  The remaining hand-written fixtures are `STARTER_DEMO_ARMY` (dashboard), `FALLBACK_CATALOG_DATASHEETS`
  (catalog page), `CORE_STRATAGEMS` (console), `FALLBACK_CHANGELOG` (changelog) and the literals inside
  `lib/api.ts`. Change both sides or the offline UI will contradict the online one.
- To make wargear choices or wound tracking real again, mount the orphaned components (or port the
  feature) rather than adding state to `RosterBuilder` — and derive `maxWounds` from datasheet
  `wounds`, not the old name-substring heuristics.
- To surface the audit fix, pass `onAutoFixPoints` from each host page; to make DP visible in the
  studio, pass `dpLimit`/`currentDp` the way the console does.
