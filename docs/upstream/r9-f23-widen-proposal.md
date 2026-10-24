# R9 addendum — F23 (kanban stream auto-subscribe WIDEN): proposal only, no PR prepared

Per the PERF-PORTABILITY-STUDY R9 item, the optional F23 WIDEN (local hotfix
37d4c9ed89: auto-subscribe every open card to the kanban event stream,
terminal events only, config-pinned destination) is **upstream-able-as-feature**
and could ride the kanban-stream plugin instead of core.

**Proposal (do NOT file yet):** keep carrying 37d4c9ed89 as a local hotfix for
now. If and when the two R9 bugfix PRs land and the kanban-stream plugin has
proven its shape upstream, offer the widen as a follow-up *plugin* feature:
`auto_subscribe_open_cards` behind a default-off config knob, terminal-kind
events only, stamped with the board's owning profile. Filing it as core
scheduler/notifier behavior now would couple an estate-deployment convention
(nevery-card stream coverage) to upstream semantics that maintainers have not
asked for — high review friction for zero bug relief. The two bugfix PRs are
the whole carry-reduction payload of R9; F23 carries no reduction value until
upstream wants the feature at all.

Shepherd list for R9 (status 2026-10-24):
- PR #143372 (kanban_archive tool): OPEN, no checks yet, awaiting maintainer
  review. Shepherding = watch for review comments and answer same-day.
- new: chat -q source labels PR (branch fix/chat-oneshot-source-labels) —
  cross-linked with rival implementation #142456; operator decides Go/No.
- new: cron suppressed-session-rows PR (branch fix/cron-suppressed-session-rows)
  — Fixes #140222 + #143785; no rival PR found.
