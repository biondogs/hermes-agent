# t_6f44a15a receipts — AS-BUILT-REMEDIATION-1 (F1 distiller, F2 sw-ux)

Date: 2026-10-24 (backups stamped 2026-10-23 23:00:10 host-local as archived).
Operator GO: "Fix both descriptions in one architect card now" (interactive decision prompt).

- Backups of pre-edit config.yaml: `~/.hermes/config-backups/desc-fix-20261023-230010/`
- Method: guarded single-line splice of `agent.description` only (reversible-splice assertion: rest of file byte-identical; line counts preserved; post-write readback verified).
- receipt: distiller rc=0, sw-ux rc=0 (hermes -p <p> config check, config version 51 ✓ both)
- fleet uniqueness check: 57 config-bearing agent.description values; collisions on full-text / first-80 / first-40 = NONE
- No gateway restart (config/description read at next session spawn).
- Scripts: fix_descriptions.py + check_uniqueness.py (workspace t_6f44a15a).
- Diff files: distiller-config-description.diff sw-ux-config-description.diff
