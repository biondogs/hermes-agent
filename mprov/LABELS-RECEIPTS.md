# mProv Review Program — Label Creation Receipts

Created: 2026-10-15T14:45Z by charter card t_a6e7e859 (sw-pm), via
`gh label create` with gh auth as account **biondogs** (scopes: repo,
read:org, workflow, gist — verified live before creation).

Reused GitHub defaults, untouched: `bug` (#d73a4a), `enhancement` (#a2eeef).

New labels created (5) on ALL FOUR forks — verified by read-back
(`gh label list`) immediately after creation, 20/20 present:

| Label | Color | Description |
|---|---|---|
| s1-blocker | #b60205 | Severity S1: security hole or data-loss path; release blocker |
| s2-functional | #d93f0b | Severity S2: functional bug in normal operation |
| s3-robustness | #fbca04 | Severity S3: robustness/edge-case weakness or missing protective feature |
| s4-hygiene | #c2e0c6 | Severity S4: hygiene only, no behavioral risk |
| review-found | #c5def5 | Found by 2026-10 comprehensive mProv review |

Repos verified (read-back at 2026-10-15T14:45Z, all 5 labels confirmed):
- [x] biondogs/mprov_control_center
- [x] biondogs/mprov_jobserver
- [x] biondogs/mprov_scripts
- [x] biondogs/mash

No issues were filed from the charter card. Raw create-run log: .label-run.log.
