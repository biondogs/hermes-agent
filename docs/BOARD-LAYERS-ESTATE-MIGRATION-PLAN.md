# BOARD-LAYERS-ESTATE-MIGRATION-PLAN — Pilot: 5 butler clones → one `butler` role × 5 boards

Status:      PLAN ONLY — no live mutation. Execution is owned by `kanban-board-architect` and requires an explicit operator GO after reading this plan.
Author:      sw-architect (card t_cd36ce51, campaign BOARD-LAYERS)
Date:        2026-11-01 (inventory measured live, read-only, this run)
References:  `docs/BOARD-LAYERS-RFC.md` (50dee6c) · REVIEW t_6bd7f0bc (REQUEST_CHANGES @ f51391c5, findings B1–B7)
             `docs/BUTLER-VERIFY-2026-10-22.md` (verify-matrix pattern) · `docs/BANK-MAP.md` (G-13 bank law)
             `docs/butler-routing-doctrine-2026-10-22.md` (G-02) · `docs/CI-CONTAINERS-GUIDANCE.md` (build/test containers)

---

## 0. Plain-language summary (for the operator)

You are running five nearly-identical butler bots — one per kanban board. I diffed them
line by line. **The five are the same robot five times over**: same brain (~one screen of
genuine per-board text out of a 179-line SOUL), same config except for the board pin,
same skills, same rules, no cron jobs. The only real differences are (a) each one's board
name/description, (b) each one's Telegram bot token (secret), (c) each one's memory bank,
and (d) a few small drift accidents (one butler got a law section the others didn't; one
is missing a memory file; one has an extra skill).

The board-layers feature (built on the `feat/board-layers` branch, currently under
re-review) lets us keep ONE butler profile and compose it with each board at launch — the
board supplies its own context file, memory, secrets, and Telegram identity. Your five
Telegram bots, five chats, and five QR handles stay exactly as they are; only the plumbing
behind them collapses from 5 profiles to 1 role × 5 board layers.

**What this plan proposes, in order:**

1. **Phase 0 (build gate)** — the feature can't be adopted until the 6 blocking review
   findings (B1–B7) are fixed and re-reviewed, the launch-path wiring actually exists
   (today the library has zero consumers — nothing is live), and it's verified in the
   standing containers. Nothing estate-side happens before that.
2. **Phase 1 (pilot)** — create a `butler` role + one small `board.yaml` context file per
   board; move bot tokens into per-board secret files (names recorded here, values never
   printed); re-wire the multiplex gateway so each of the 5 Telegram bots resolves to
   (butler, its board). Roll out one canary board first, then the other four. The five old
   butler profiles are frozen on disk, not deleted — **rollback is "point the gateway back
   at the old profiles," minutes of work.**
3. **Phase 2 (verify)** — rerun the BUTLER-VERIFY-2026-10-22 matrix on the collapsed
   setup (7 checks × 5 boards). One check gets *stricter*: the 2026-10-22 run found the
   board isolation was enforced only by SOUL prose (a butler told to read another board's
   cards could). The code fence in this feature is exactly that missing enforcement — so
   the one BLOCK-PASS cell from 2026-10-22 must become a hard PASS.
4. **Phase 3 (second wave, worker clones)** — the same pattern collapses ~28–30 worker
   clones (ops/watcher/scribe/auditor/planner/orchestrator × 5–6 boards) into ~6 roles.
   This wave is bigger (it touches card assignee names and the shared per-board memory
   banks) and is gated on the pilot's clean verify.
5. **Phase 4 (prose retirement)** — once the fence is code, ~6 lines of "Board Discipline"
   boilerplate in each of 52 worker SOULs and most of each butler's "The One Board" section
   can be deleted — enforced mechanism replaces 57 copies of the same safety paragraph.

**Decision points for you (§9):** state continuity for butler chats (fresh vs adopted — I
recommend fresh; old profiles stay frozen with their histories), canary board choice (I
recommend gargantua01, currently the quietest), and whether worker-wave sequencing starts
with the most-drifted family (g02) or the most-uniform one (skipjack/sjproto).

Estimated effort if GO'd: Phase 1 is a half-day of kanban-board-architect work plus a
gateway restart window; Phase 2 is one verify run (~1 h, pattern exists). No board data,
cards, or histories are modified by the pilot itself.

---

## 1. Measured inventory (read-only, taken this run)

Everything below was measured against the live estate 2026-11-01, read-only. No profile,
board, config, or secret value was written or printed.

### 1.1 The five butlers: role vs board

Profiles: `g01-butler`, `g02-butler`, `gaudi-butler`, `swco-butler`, `sjproto-butler`.
Boards served: gargantua01, gargantua02, gaudi, software-co, skipjack-prototype.

| Layer | Verdict | Evidence |
|---|---|---|
| **config.yaml** | **ROLE, except 3 keys** | 80 flattened keys; 77 byte-identical across all five. Differences: `agent.description` (board text), `kanban.board` (board pin — the fleet hotfix pin), and `onboarding.seen.profile_build_offered` (g01-only **drift artifact**, meaningless). |
| **SOUL.md** | **ROLE + one board block + drift** | 179 lines each. After substituting board/fleet/bot tokens, differences reduce to: header line; the "The One Board" board tokens; the "Estate context" block (board description, fleet vocabulary, live lanes — ~4 lines, pure board context); plus genuine drift: g02-butler carries the G-07 External Comms Law section **the other four lack**; 4-of-5 carry a "memory bank" line g01 lacks; swco-butler's intake note #5 differs *correctly* (software-co receives standing-container work; the others route it away) — that is real board content, not drift. |
| **.env** | **identical NAMES, per-board values** | All five export exactly the same 9 names: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_FALLBACK_IPS`, `TELEGRAM_HOME_CHANNEL`, `KANBAN_STREAM_BOT_TOKEN`, `KANBAN_STREAM_ALLOWED_USERS`, `KANBAN_STREAM_OPS_CHAT_ID`, `ORB_API`, `ORB_API_KEY`. Values differ (per-board bots/chats) — values were not read; per `secret-provisioning-no-leak` only names appear anywhere in this plan. |
| **skills/** | **ROLE + 1 board accident** | 42 identical files per butler. swco-butler additionally has `devops/ci-standing-containers/SKILL.md` (pushed 2026-11-01 to 9 profiles fleet-wide — on butlers it is arguably noise; decide at authoring). g02-butler has only `.usage.json` bookkeeping locks. |
| **memories/** | **ROLE + 1 drift** | `MEMORY.md` everywhere; `USER.md` missing on g01-butler (drift, recreate at cutover). |
| **cron/** | **ROLE — empty** | Zero cron jobs on all five (executions table 0 rows everywhere). No cron migration needed in the pilot. |
| **profile.yaml / description** | **BOARD** | Description text only differs by board/bot/fleet names (verified structurally identical). |
| **hindsight bank** | **BOARD-attached** | `hindsight/config.json bank_id == <butler>` on each (g01-butler, …) — 5 dedicated banks, per BANK-MAP §1.4. |
| **session/state** | **BOARD-attached, asymmetric** | state.db sizes: 1.7 MB (g01) / 26.7 MB (g02) / 29.1 MB (gaudi) / 83.5 MB (swco) / 19.1 MB (sjproto). Session transcripts + gateway routing indexes are the only heavy state. |
| **subscriptions** | **3 rows fleet-wide** | `kanban_notify_subs.notifier_profile` is keyed by profile name: 1 row on gargantua01 (`g01-butler`), 2 on gargantua02 (`g02-butler`), none elsewhere. Re-pointing surface is 3 rows. |

**Butler drift register (must be reconciled at cutover, §3.4):** g02-only G-07 section;
g01 missing USER.md + memory-bank line; g01 onboarding artifact; swco extra skill;
swco inbound-routing note (keep, as board content).

### 1.2 Worker clone families — second-wave estimate

Families measured (post board-token normalization, SOUL similarity ratio; config-diff keys;
env names identical within each family):

| Family | Clones | Similarity range (vs family base) | Config keys differing | Notes |
|---|---|---|---|---|
| ops | 4 (g01,g02,sj,sjp) | 0.62–0.97 | `agent.description` only | g02-ops drifted hard (absorbed G-07 law + rewrite ≈ 92 lines); sjp-ops carries GPU-MULTICAST SAFE-RESTART rule (board law); sj-ops nearly clean (8 lines). |
| watcher | 5 (+gaudi) | 0.68–0.97 | description + 1 onboarding drift | gaudi-watcher is an older "seed SOUL" (BOARD-DEV-4 shape, 34 changed lines, 6 extra skills). |
| scribe | 5 (+gaudi) | 0.52–0.97 | 4 — description **+ `fallback_model`/`model.default` + muse ctx pin** | gaudi-scribe is a seed SOUL (154 changed lines). The scribe-family model drift is exactly the class §9.3 forbids boards from re-introducing — collapses away. |
| auditor | 5 | ~0.97 | description only | cleanest family. |
| planner | 5 | 0.76–0.97 | description only | gaudi-planner is a *different role* in practice ("campaign scientist") — role specialization (RFC §15.1), not a clone. |
| orchestrator | ~6 (g01,g02,gaudi,sj,sjp,+kanban-orchestrator) | not yet diffed (wave-2 task) | — | default-board orchestrator is a distinct meta role. |

**Estimate:** ops/watcher/scribe/auditor/planner across boards ≈ **24–28 clones → 5 roles**;
orchestrator needs a scoping decision first (role boundary between "board orchestrator"
and the default/kanban meta-orchestrators). Worker .env carries only 5 names
(`ORB_API`, `ORB_API_KEY`, `KANBAN_STREAM_BOT_TOKEN`, `KANBAN_STREAM_ALLOWED_USERS`,
`KANBAN_STREAM_OPS_CHAT_ID`) — all model/stream credentials, which stay role-side;
**worker board layers will have empty env manifests** — their per-board context is the
soul fragment + memory bank, not secrets.

**Bank law interaction (G-13):** workers today share a per-board *environment bank*
(e.g. `g01-infra` across the g01 fleet) — an explicit operator axis ruling. RFC §8.3's
derived default (`board-<slug>-<role>`) would **split** those shared banks per role. The
wave-2 board.yaml MUST pin `memory.bank: <environment bank>` per board to preserve the
operator's environment-axis law. This is the one place the layering feature must be
configured *against* its default, and it is fully supported (`memory.bank` override, §8.3).

### 1.3 "Board Discipline" prose: what the code fence retires

Measured: **52 of 59** profiles carry the identical "## Board Discipline" section (the
RFC's "53" was the pre-retirement count; drift since). The five butlers carry "The One
Board" instead; `kanban-board-architect`, `kanban-orchestrator` carry none.

The worker BD paragraph has 6 bullets. Post-fence dispositions (Phase 4):

| BD bullet | Disposition |
|---|---|
| 1. Work only on the dispatcher-pinned board; every kanban call carries explicit `board=` | **Retired.** Fence refuses cross-board resolution pre-connect (RFC §10.1); the env pin + claim-time validation make it mechanical. The "always pass board=" belt-and-suspenders practice can drop once fence verified. |
| 2. Follow-up cards on the SAME board, explicit `board=`; never touch other boards' cards | **Retired.** Same mechanism — cross-board create/comment/complete is refused at the client layer, all launch paths. |
| 3. No Telegram/chat intake; butler owns intake | **Stays** (role law, nothing to do with the fence). Moves to role SOULs once; no longer N-times-cloned. |
| 4. Cross-board references are text-only, never link edges | **Halved.** The enforceable half (cross-board `kanban_link`) is fence-refused; the style half ("paste ids as text") stays as one line of role prose. |
| 5. GATE-WAIT PATTERN (link-before-block) | **Stays** (workflow law; orthogonal to boards). |
| 6. NO-SELF-GATE (independent gate profiles) | **Stays** (assignment/auth law; orthogonal). |

Butler "The One Board" bullets: the explicit-`--board` mandate, the stop-and-refuse rule,
the archived-board fallback, and the "other boards do not exist for you" bullet are all
**retired by the fence** — the section collapses to a one-line scope statement carried by
the board fragment. The existing "ENFORCED IN TOOLING" bullet (2026-10-23 hotfix pin)
becomes the fence's user-facing description. Note: the live hotfix pin *silently swallows*
an explicit foreign `--board` under a pin — the RFC's fence turns that into a **refusal**
(review finding B3 is the fix card; BUTLER-VERIFY-2026 check 3 then upgrades from
BLOCK-PASS to hard PASS).

**Prose deleted at Phase 4:** ~6 BD lines × 52 SOULs + ~6 One-Board lines × 5 butler
SOULs ≈ 342 boilerplate lines, and every future law edit (LITELLM-YAML, G-07, DECISION-NUDGE
…) propagates to 1 role SOUL instead of N clones — today every identical law block is
already duplicated 5×/family.

---

## 2. Phase 0 — build gate (preconditions; nothing estate-side)

The feature is NOT adoptable at tip: t_6bd7f0bc verdict REQUEST_CHANGES @ f51391c5.

1. **Landing set**: all 6 FIX cards (t_ed77dd7f, t_2d010193, t_b8d6a39f, t_ff349eaa,
   t_470b20ba, t_72f33d7a) merged — must include B5 (launch-path composition wired:
   dispatcher child start, gateway session construction, cron scope, env/skills/SOUL/state
   consumers, D9 grant-only `boards:all`, D11 claim-time validation) and B1 (fence
   zero-change discriminator fixed; upstream corpus 3 pre-existing failures → 0).
2. **REVIEW-R2 PASS** with a standing-container receipt: branch suites via
   `ci/hermes-upstream/run-branch.sh` (hermes-upstream:fresh), NOT the campaign-local
   harness image (R2 finding).
3. **Estate-shape regression**: rebase feat/board-layers onto the live hotfix line
   (`local/hotfix-carried-2026-11-01-0935`, a0107dcf90,
   v0.22.5+canary.20261101T064348Z-38-ga0107dcf90 — install
   `/home/arch/.hermes/hermes-agent`) and run `twin-test`/`twin-rebase-check` in
   **hermes-estate-twin** (per CI-CONTAINERS-GUIDANCE; never the live estate).
4. **Version pin**: the deployable build is an exact git commit sha on the hotfix-carried
   line; the sha is recorded in the operator-GO card and in the deploy receipt. Deployment
   follows the standing hotfix-rebase procedure (estate-shape container first).
5. **Zero-change sanity on the live shape**: unlayered profiles/boards byte-identical
   behavior — the pilot's own Phase-2 zero-change check doubles as the estate gate (§4).

**Risk (P0):** none estate-side — Phase 0 is container work only. Falsify/revisit: if R2
finds new blocking issues, the pilot waits; this plan does not depend on dates.

---

## 3. Phase 1 — pilot: `butler` role × 5 boards

Owner on GO: `kanban-board-architect` (architect does not mutate the live estate).

### 3.1 Author the role (once)

- New profile `~/.hermes/profiles/butler/`: SOUL = today's common butler body (intake
  protocol, escalation, ARCHIVE-GC, LITELLM-YAML laws, LONG-JOB DETACH, DECISION-NUDGE,
  role/no-go sections) with the 4-line "Estate context" block removed and "The One Board"
  reduced to the one-line scope statement. **No `{{board.*}}` slots required** for the
  pilot — the board fragment carries all board prose (slots enter with wave 2/3 when
  workers need inline host facts).
- config.yaml = the verified-identical 77-key common config with `kanban.board` REMOVED
  (the binding comes from composition; a configured pin on the role would fight the
  composer), `agent.description` de-boarded.
- `.env` keeps role-side credentials ONLY: `ORB_API`, `ORB_API_KEY` (model creds must stay
  role-side — RFC §7 flags credential-sounding exports in board manifests; do not move).
- skills = the common 42 files. Decide the swco extra (recommend: leave
  ci-standing-containers on the software-co BOARD layer via `skills.add:` — butler usage is
  advisory; keeping the role minimal wins).
- `boards.pin`: none. Butler is composed per board; no `capability: all` (each composed
  instance is board-pinned — that's the point).

### 3.2 Author the board layer (once per board; 5×)

Per board `<slug>` in `~/.hermes/kanban/boards/<slug>/`:

| File | Content |
|---|---|
| `board.yaml` | `version: 1`; `roles: [butler]` (pilot allowlist — extend per wave); `memory.bank: <existing butler bank>` (g01-butler… — **pilot decision D-banks**, keeps banks continuous, no server-side renames, RFC §8.3 explicit override); `meta.maintainers: operator`. No skill/toolset/model deltas. |
| `SOUL.md` (fragment) | The board's "Estate context" block (description, fleet vocabulary, live lanes) + the swco-style inbound routing note where applicable + G-07 section reconciled fleet-wide (drift register item — see 3.4). |
| `env/manifest.yaml` | Names only: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_FALLBACK_IPS`, `TELEGRAM_HOME_CHANNEL` (+ `KANBAN_STREAM_*` if values prove per-board — see D-stream). |
| `env/secrets.env` | 0600 values, written ONCE directly at the board path per skill `secret-provisioning-no-leak` (never staged via scratch; names-only receipts; post-move audit grep). Source: the frozen clone's `.env` — value is *moved*, not copied-and-left, at cutover time only. |

**Board.yaml is the marker**: a board without board.yaml behaves byte-identically to today
(RFC §12), so authoring files into a board dir before the build flip changes nothing.

### 3.3 Gateway re-attach (Topology-B multiplex preserved)

- Topology-B invariant: 5 Telegram bots, 5 tokens/QR handles, 5 operator DMs — unchanged.
- The multiplex gateway gains the RFC §11 routing: inbound bot token → match the board env
  layer exporting `TELEGRAM_BOT_TOKEN` → session composes (role=butler, board=<slug>),
  session-tagged with the board so `/resume`/`/new` keep the pin; banner surfaces
  `role=butler board=<slug> fencing=pinned`.
- Restart window: one multiplex-gateway restart (same class as the 2026-10-22 14:58Z
  restart; ~1 min connect drain, then five `✓ telegram connected` receipts — but now five
  *composed* sessions).
- **Canary sequencing (D-canary):** recommended order — gargantua01 first (quietest board,
  1 sub row, smallest state.db), hold 24 h, then gaudi + skipjack-prototype, then
  gargantua02 + software-co (heaviest state, most subs). Each step's old profile stays
  frozen (below) so any single-board revert is instant.

### 3.4 Cutover mechanics (per board)

1. Freeze the clone: stop gateway routing to it, rename nothing on disk (frozen in place;
   `.env` values preserved as the rollback copy — **do not delete during pilot**).
2. Reconcile the drift register §1.1 (fleet-wide G-07 into the role; USER.md recreated in
   the board state root; swco extra skill to board layer; g01 onboarding artifact ignored).
3. Move secrets (3.2), author board layer, dry-run `hermes profile effective --profile
   butler --board <slug>` (names-only output; exit-code contract 0/1/2), flip gateway
   routing to composition.
4. Re-point subs: update `kanban_notify_subs.notifier_profile` for the 3 live rows
   (host-side by the executing architect; values/rows: 1× gargantua01, 2× gargantua02).
5. Operator smoke-check in the board's chat (one status query, one intake create on a
   tagged test card — same shape as BUTLER-VERIFY checks 1–2).

**State decision (D-state, operator):** composed instances get FRESH state roots
(`<board>/state/butler/` — young state.db, new sessions/, MEMORY.md/USER.md born there;
hindsight banks carried over via `memory.bank` pin). One cost: `/resume` continuity into
the old clone's session history is unavailable until the RFC §15.2 adopt-profile helper
exists (roadmap; NOT a Phase-1 dependency). Rollback restores full old history because
nothing was migrated. **Recommendation: fresh.**

### 3.5 Pilot risks / rollback

| Risk | Mitigation |
|---|---|
| Gateway routing regression (largest wiring surface — review B5 called the gateway leg out) | Canary-first sequencing; old profiles frozen; gateway flip is per-bot reversible; Phase-2 check 7 gates expansion. |
| Secrets handling during the move | `secret-provisioning-no-leak` procedure verbatim: direct single write, 0600, names-only receipts, post-move audit; old `.env` retained frozen until Phase-3 sign-off. |
| Composed SOUL renders wrong (fragment/slot/strictness) | `profile effective` dry-run BEFORE flip on every board; strict-at-launch means a bad composition fails the session build loudly, not silently. |
| Notify subs / cron edge cases | 3 sub rows re-pointed same window; butlers have zero cron (measured), so no cron scope to carry in the pilot. |
| Operator chat disruption | One restart (~1 min) + per-board canary; the bot identity/threads are unchanged, so Telegram side sees nothing but a brief reconnect. |

**Pilot rollback (any board, ≈ minutes):** gateway re-points the bot token at the frozen
clone profile; delete/rename that board's `board.yaml` (marker-off = board unlayered,
byte-identical legacy behavior); old profile resumes with full state. Nothing else was
mutated — banks were carried (not moved), no board DB touched. Full-pilot rollback = same
step ×5 + build unpin (redeploy previous hotfix-carried commit).

---

## 4. Phase 2 — verification matrix (BUTLER-VERIFY-2026 pattern, adapted)

One verify run by the architect/board-architect on the collapsed fleet; every check × 5
boards, receipts on the verify card. Inherited checks keep their 2026-10-22 shapes:

| # | Check | PASS criterion (changed vs 2026-10-22 in **bold**) |
|---|---|---|
| 1 | Scoping | SOUL composition provenance clean (`profile effective` exit 0, fragment + slot fills attributed); live one-shot "what board are you scoped to" answers the board verbatim; **banner shows composed pair**. |
| 2 | Board write test | Tagged card through composed butler lands only on own board (sqlite readback of all boards). |
| 3 | Cross-board refusal — **TOOL LAYER** | Instructed attempt with foreign `board=`/`--board` must be **refused by the fence pre-connect** on the CLI, kanban tools, and gateway surfaces. The 2026-10-22 BLOCK-PASS (tool layer did not fence; gaudi probe read 16 foreign summaries) **must become a hard PASS** — this is the feature's headline claim. |
| 4 | Bank isolation | Canary retain/recall through each composed instance → existing `<fleet>-butler` bank (continuity proven: canary retrievable), zero cross-bank leaks (scan all banks). |
| 5 | Model wiring | `config check` rc=0; litellm/ORB one-shot exact-echo; ctx pins hold through composition. |
| 6 | Env hygiene | **Names-only proof**: `profile effective` env section lists the 4–7 board names, never a value; secrets file 0600; placeholder scan; role `.env` retains only ORB names. |
| 7 | Gateway registration | Multiplex restart receipt; 5× `✓ telegram connected (profile: butler, board: <slug>)`-class lines; `getMe` on all five tokens → same bot ids/usernames as 2026-10-22 (8522272075 / 8948894256 / 8825019300 / 8892444888 / 8646424684); subscriptions deliver (`notify+wake` row re-pointed and observed). |
| 8 | **Zero-change regression (new)** | Unlayered boards (default, skipjack, software…) and every non-butler profile byte-identical: pick 2 canary workers, byte-compare effective SOUL/config/skill-list/env names pre/post build flip; upstream corpus green in estate-twin. |
| 9 | Rollback drill (new) | On the canary board only: execute §3.5 rollback once, re-verify checks 1/2/7 against the frozen clone, then re-flip. A rollback path proven once beats one never exercised. |

Gate: all PASS (no BLOCK-PASS permitted — the 2026-10-22 guardrail gap is what this
feature closes) before Phase 3 even schedules. Failures route to fix cards, not to prose
patching of SOULs.

---

## 5. Phase 3 — second wave: worker families (after pilot green)

Sequenced per family (not all at once); each family gates on the previous one's green verify.

1. **Family choices (D-wave-order):** recommended order = auditor (cleanest, 0.97) →
   planner → watcher/scribe (absorb the gaudi seed-SOUL divergence as role refresh) →
   ops (g02-ops absorbed the G-07 law + rewrite; sjp-ops carries the GPU-multicast board
   rule into the board fragment) → orchestrator last (needs the role-boundary decision:
   board orchestrator vs default/kanban meta-orchestrator; gaudi-planner "campaign
   scientist" gets its own role — specialization, RFC §15.1).
2. **Assignee-name migration (the wave's real cost).** Cards carry profile-name assignees
   (`g01-ops`). Under composition the assignee becomes the ROLE (`ops`) + the card's own
   board as binding. Per board+family at a quiescent point: update the board's fleet
   vocabulary (butler fragment), stop dispatching the clone, and let in-flight cards
   either finish under the frozen clone or be reassigned in one scripted pass. Because
   unlayered profiles remain fully functional under the new build (zero-change guarantee),
   both namespaces can coexist on a board during transition — but one board × one family
   at a time keeps the dispatcher view sane. Frozen clones retire (delete) only at
   Phase-4 sign-off, after two clean weeks.
3. **Bank/pin configuration:** each worker-wave `board.yaml` sets
   `memory.bank: <environment bank>` (g01-infra, g02-infra, skipjack-infra,
   skipjack-prototype-infra, gaudi-hpu*) — REQUIRED to preserve the G-13 environment-axis
   law against the §8.3 per-role default. Worker env manifests stay empty (§1.2); soul
   fragments carry the Estate-context blocks; scribe-family model drift (fallback_model /
   muse pin) dissolves — roles own models, boards cannot re-add them (§9.3).
4. **Cron:** any worker cron jobs (butlers had none; check per board at authoring) migrate
   via the `board:` job field (RFC §11 cron row); in-process fire paths must see the
   declared board — tracked in review non-blocking findings, verify in R2.

Estimated collapse: ~24–30 profiles → 5–6 roles; every future law/model/skill edit lands
once per role.

---

## 6. Phase 4 — prose retirement + steady state

- Delete the retired Board-Discipline bullets (§1.3 table) from all role SOULs; collapse
  butler One-Board sections to the one-line scope statement.
- Adopt the RFC §15 roadmap items as wanted: `board adopt-profile` helper (makes D-state
  adoptable later), board dashboards, board-scoped token rotation (the manifest's file
  source already makes butler-token rotation a board-local act — nice-to-have now, trivial later).
- GOVERNANCE.md rows for anything operator-ratified here (canary, wave order, bank pins).

**Falsify/revisit this plan when:** upstream lands per-board policy fields that overlap
(RFC §14 tracker) — re-map layers; if R2's verdict changes the composition contract, §3.2
authoring changes with it; if the pilot shows composed-session overhead (context/token
cost of fragment append) materially different from today, re-measure before wave 2.

---

## 7. Consolidated verification checklist (deliverable of every phase gate)

- [ ] Phase 0: R2 PASS + run-branch.sh receipt (upstream:fresh) + estate-twin twin-test on rebased hotfix line + pinned sha recorded
- [ ] Phase 1 (per board): `profile effective` exit 0, provenance attributed, env names-only; secrets 0600 single-write + audit grep; dry-run before flip; old clone frozen with `.env` intact
- [ ] Phase 2: 9-check matrix × 5 boards all PASS (check 3 hard-PASS at tool layer; check 8 zero-change; check 9 rollback drill) — receipts on verify card
- [ ] Phase 3 (per board×family): quiescence check, assignee pass script dry-run then run, `memory.bank` pinned to environment bank, dispatch smoke, 2-week freeze before clone deletion
- [ ] Phase 4: grep proves zero retired-prose lines remain (`grep -l "explicit board argument" */SOUL.md` → butler role only); GOVERNANCE rows filed

## 8. Explicit out of scope (fences)

- No live profile/board/config mutation in this card — this document is the deliverable.
- No kanban data-model changes, no cross-board memory federation (RFC §2 non-goals carry over).
- No upstream/public filing of this plan (that chain has its own gates).
- Not adopting `boards: all` anywhere; the pilot needs no meta roles.
- Software-co's own lanes (sw-*) are role-only (no clones) — unaffected by every wave.

## 9. Operator decision points

| # | Decision | Recommendation |
|---|---|---|
| D-state | Butler chat/session history: fresh composed state roots vs adopt (needs §15.2 helper, later) | **Fresh** — rollback stays trivial, banks carry continuity, adoption can happen later without redoing anything |
| D-canary | Canary board order | gargantua01 → {gaudi, skipjack-prototype} → {gargantua02, software-co} |
| D-banks | Butler hindsight banks: keep `<fleet>-butler` ids via `memory.bank` pin vs rename to `board-<slug>-butler` | **Keep** for pilot (no server mutation); rename is cosmetic and can ride a later wave |
| D-stream | `KANBAN_STREAM_*` values shared estate-wide vs per-board (values not read in this pass) | Board-architect cmp-verifies value identity at authoring: shared → role `.env`; per-board → board manifest |
| D-wave-order | Worker family order | auditor → planner → watcher/scribe → ops → orchestrator-last (with the orchestrator role-boundary decision taken first) |
| D-swco-skill | ci-standing-containers skill on butler role vs software-co board layer | Board layer (`skills.add:` on software-co only) — keep the role minimal |

Any follow-on work routes via `kanban-board-architect` + operator GO; this card is a plan,
not a request for that GO.
