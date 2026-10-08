---
type: Documentation Index
title: "Webapp"
description: "Files and subdirectories in Webapp."
---

# Files

- [Api client fallback layer](api-client-fallback-layer.md)
- [Web App Shell, Routing & Guest Session](app-shell-and-guest-session.md) - How the Next.js 14 App Router frontend in apps/web is wired: the root shell that wraps every route in ErrorBoundary + AuthProvider, the client-only route table, and the callsign guest session that persists in localStorage under forceorg_local_user while Supabase remains an optional legacy path.
- [Battle Mode Console, Roster Builder & Dashboard Components](console-and-builder-components.md) - Component inventory and responsibilities for the two force-facing modes of apps/web after the Battle Mode rewrite: the Edit Mode Roster Studio (debounced auto-save, static-JSON catalog, enhancements, leader linking, detachment switcher) and the Battle Mode tabletop console (self-contained HUD with command-point generator, interactive phase bar, phase-adaptive statlines, in-card stratagems, single-accordion force org), plus the orphaned CompositeUnitCard/StratagemPanel components and where static /data JSON and localStorage fixtures stand in for API data.
- [Faction Theme System & Chapter Heraldry](ui-theme-and-heraldry.md) - How @forceorg/ui-theme turns a roster.factionThemeOverride key into a Dawn of War 4-channel colour palette and chapter SVG insignia: the FactionPalette and ChapterPathDefinition contracts, ThemeProvider controlled/uncontrolled themeKey and CSS custom-property injection, and the palette/heraldry registries every apps/web page consumes.
