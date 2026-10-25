# maintainer ruling — mcc#318 comment 6393012139 (full text)

- author: uberlinuxguy (Jason Williams)
- filing: mprov-ng/mprov_control_center#318
- comment id: 6393012139
- posted: 2026-10-25T03:35:02Z
- capture: paginated full-text fetch (watcher-fulltext rule, 4/4 issue
  comments fetched; raw capture: mcc318_thread_full.json.gz on kanban card
  t_bf6277f2, gunzip sha256-verified)

Verbatim body:

> Your context for implementation is flawed.  This system is in a tightly
> controlled setting where an admin would have cabled a system in a
> deliberate way to use the port match function in NADS.  Systems not cabled
> deliberately, would fall into the auto detection section of the UI and
> require manual intervention by an admin.  Unless I am missing something,
> the code functions as intended.
>
> I would suggest you restructure your security model around this and
> reassess all your open security issues and PRs

Thread context (same thread, earlier turns):

- 6379587347 uberlinuxguy 2026-10-24T03:59:38Z — "Flagged **client-api-change**:
  an enrollment token on `/systems/register` needs the jobserver's `nads`
  plugin to send it, and a way to get it into the public N.A.D.S. image. See
  PR #336."
- 6392641938 uberlinuxguy 2026-10-25T02:50:05Z — "Explain further the attack
  vector.  I do not understand how an attacker can \"bind a mac to any
  system\""
- 6392659997 biondogs 2026-10-25T02:52:17Z — our attack-vector answer
  (superseded by the ruling below)
- 6393165133 biondogs 2026-10-25T03:54:36Z — our distiller-gated
  acknowledgment (sha256 ebecbc67…08c0f, verified on-thread): concedes the
  controlled-deployment model code-verified at origin/main a69f5a0, keeps
  the queue-pollution residual, commits to the item-by-item reassessment.
