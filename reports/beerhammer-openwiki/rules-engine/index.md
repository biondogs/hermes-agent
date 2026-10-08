---
type: Documentation Index
title: "Rules Engine"
description: "Files and subdirectories in Rules Engine."
---

# Files

- [Composite Units & Stratagem Filtering](composite-units-and-stratagems.md) - How packages/rules-engine-11e merges a leader datasheet into a bodyguard datasheet (attachment validity, effective toughness, keyword/weapon/ability merge, wound allocation) and how stratagems are gated by battle phase, unit keywords and detachment identity — plus how the Tabletop Console mirrors (and currently diverges from) those canonical rules.
- [roster-validation](roster-validation.md) - The matched-play compliance checks in packages/rules-engine-11e/src/detachment-validator.ts (points limit, DP budget, Rule of Three, orphan attachments), how apps/api/src/routes/audit.ts maps their codes/severities into RosterDiscrepancy plus its own point-shift detection, and how ComplianceDashboard degrades to a purely local audit.
- [Rules Engine 11E: Public API, Consumers & Tests](rules-engine-overview.md) - Orientation to @forceorg/rules-engine-11e: its four pure modules and exported surface, which apps actually import them today (only validateRoster in the API audit route; the RosterBuilder wargear import is dead and the web components duplicate the logic inline), which are test-only, and how the 53-test vitest suite plus the CI coverage gate guard the rules semantics.
- [Wargear AST Compiler](wargear-ast-compiler.md) - How packages/rules-engine-11e/src/wargear-parser.ts compiles natural-language Wahapedia wargear prose into WargearRuleAST nodes, the five regex line patterns and helper semantics, and where the resulting ASTs live (transient UI state in RosterBuilder, never the conditionTree JSON column).
