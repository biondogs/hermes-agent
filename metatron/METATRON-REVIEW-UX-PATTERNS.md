# METATRON-REVIEW-UX: suggestion/review + change-recap patterns from shipped collaborative editors

**Card:** t_75254878 (software-co board) · **Author:** sw-ux · **Date:** 2026-11-02
**Trigger (operator, live W8 re-walk 2026-11-02, verbatim):** the review/suggestion surface *"is not pleasing to use"* — mechanism works (adjudication round-trips fine) but the experience reads unclear: grey low-contrast text, oversized suggestion cards splitting accept buttons across a scroll, cramped pane, weak affordance hierarchy. *"it might be good to find some examples of how this sort of task is accomplished on other collaborative editor systems."*

**Type:** design-research deliverable — no code, no live-instance (:8756) access. This doc is the pattern survey + translation + ranked recommendation set the card asked for, for sw-architect / the next implementation wave.

---

## §0 As-is: what the current Metatron review surface actually does

Verified against `metatron-rewrite/frontend/app` (src/editor.ts, editor.css — read-only inspection, no runs):

| Element | Current behavior | Code basis |
|---|---|---|
| Suggestion list | One pane; **pending rows first, resolved rows after**, all in one scroll | `editor.ts` render loop splits `state.suggestions` into pending/resolved |
| Row anatomy | Full proposed text (`block_id: proposed`) → `why: <rationale>` line → accept/reject buttons **stacked below the text** | `suggestionRow()`: `.sugg-text`, `.sugg-why`, `.sugg-btns` appended in order |
| Resolved-state styling | `.suggestion.accepted { opacity: 0.6 }`, `.suggestion.rejected { opacity: 0.5; text-decoration: line-through }` | `editor.css:286-287` |
| Rationale styling | `.sugg-why` renders at `--text-muted` @ `--f-small` | `editor.css:288` |
| Pending count | Glint strip: "suggestion set: N to adjudicate"; ladder control: "adjudicate — N suggestion(s) need your call" which jumps focus to the first pending row's accept button (`suggestionAnchor`) | `editor.ts` ladder rule + anchor wiring |
| Per-row completion | `accepted/rejected [by <who>]` text line | `suggestionRow()` resolved branch |
| Theme tokens | A real 4-step text ramp with a **documented AA floor** ("muted-on-surface floor, all above the 4.5 floor", 4.81:1 dark) — light and dark sets kept in sync | `editor.css:22-33, 83-86, 149-152` |

**Diagnosis of the operator's four complaints, mapped to mechanism:**

1. **"Grey low-contrast text"** — the token ramp itself is AA-compliant; the violation is *opacity applied on top of tokens*. `opacity: 0.6/0.5` multiplies against the already-muted token and the page background, pushing resolved rows to roughly 2.5–3:1 effective contrast — under WCAG AA 4.5:1 in both themes. Secondary contributor: the *rationale* (the text you need to decide with) renders at the ramp's floor (`--text-muted`), so the decision-critical text is the least legible text on the row.
2. **"Oversized cards splitting accept buttons across a scroll"** — rows render the entire proposed block inline; on any multi-sentence block the `.sugg-btns` row falls below the fold, so *read → scroll → hunt for buttons* per suggestion. No system surveyed does this (see §1 — every shipped system keeps accept adjacent to the summary, not under the payload).
3. **"Cramped pane"** — pending and resolved share one scroll; the resolved backlog (visually near-identical bulk) pushes actionable work out of view; there is no index/summary tier.
4. **"Weak affordance hierarchy"** — accept and reject render as sibling same-weight text buttons; no primary/secondary distinction, no hover-target sizing guidance, and the one "loud" control (Adjudicate) *executes nothing* — it is actually a jump, which mislabels its own weight.

Every one of these has a direct, well-executed precedent in shipped systems. The rest of this doc is that survey.

---

## §1 Pattern survey: where suggestions render and how accept/reject is placed

### 1.1 Google Docs — suggested edits (the "suggestion ribbon" family)

- **Render locus:** inline *and* margin. Additions show underlined in the suggester's color, deletions struck through, each with a small **margin card naming the suggester and time** ([CustomGuide](https://www.customguide.com/course/google-docs/track-changes-in-google-docs); [Docs Tips](https://docstips.com/accept-all-suggestions-google-docs/)). The document body stays readable — the suggestion is *markup*, not a card wall.
- **Accept/reject placement:** click the inline change or its margin card → **check / ✕ icons inside the card**, adjacent to the summary, never under the proposed text ([Deckoholic walkthrough](https://www.deckoholic.ai/tutorials/google-docs/track-changes); official mobile flow: tap highlighted text → View comment → **Accept / Reject**, [support.google.com/docs/answer/6033474](https://support.google.com/docs/answer/6033474)).
- **Pending-work surfacing:** a **"Show all comments" side panel lists every open suggestion alongside comments** — an index tier, not a dump ([Deckoholic](https://www.deckoholic.ai/tutorials/google-docs/track-changes)). The file owner gets an email when suggestions arrive. Keyboard walk: `Ctrl+Alt` then `N`,`U` / `P`,`U` jumps suggestion-to-suggestion — **a first-class "jump-to-pending" affordance that is labeled as a jump, not a command** ([SolveYourTech](https://www.solveyourtech.com/switch-viewing-modes-google-docs/)).
- **Batch semantics:** `Tools ▸ Review suggested edits` opens a box with **Accept all / Reject all *plus Preview "Accept all" / Preview "Reject all"*** — you can read the resulting document before committing the batch ([Google support community + Deckoholic](https://www.deckoholic.ai/tutorials/google-docs/track-changes)). The community-documented safe order: *reject the few you disagree with one by one, then Accept all takes the rest.*
- **Completion state:** accepted text becomes plain ink (markup simply *disappears*); rejected text reverts and the card closes. There is **no dimmed graveyard in the body** — closure removes the markup from the reading surface. Undo (Ctrl+Z) covers mis-clicks; version history covers late discovery.
- **Density/contrast:** suggester color is an accent on normal-contrast text; resolved suggestions leave no low-contrast residue.

### 1.2 Microsoft Word — Track Changes

- **Render locus:** inline markup with **margin balloons** (or all-inline), plus a **markup-view switch: Simple / All / No / Original** — a *density dial* over the same data ([Microsoft support: Track changes](https://support.microsoft.com/en-us/office/track-changes-in-word-197ba630-0f5f-4a8e-9a77-3712475e806a)). "No Markup" = glance at the accepted-result document — the desktop-app analogue of Docs' preview.
- **Accept/reject placement:** clicking a change opens a **card with the reviewer's name and accept/reject options** right there; plus a **sequential review loop**: `Review ▸ Next` → Accept / Reject → auto-advance ("Accept and Move to Next" as the literal button label) ([Microsoft support](https://support.microsoft.com/en-us/word/training/track-changes-in-word)). The ribbon-level Accept/Reject menu carries the batch variants: *Accept This Change / Accept and Move to Next / Accept All Changes Shown / Accept All Changes / Accept All Changes and Stop Tracking* — the "Shown" variant respects the current filter.
- **Pending-work surfacing:** the **Reviewing Pane** (vertical or horizontal) lists every tracked change and its **"summary section at the top … displays the exact number of visible tracked changes and comments that remain"** — an explicit remaining-work counter tied to the active filter ([Microsoft support](https://support.microsoft.com/en-us/office/track-changes-in-word-197ba630-0f5f-4a8e-9a77-3712475e806a)). Margin bars (the "revision bar" gutter strip) mark changed paragraphs without any card at all.
- **Completion state:** accepting/rejecting removes the markup; the Reviewing Pane shrinks; the summary count goes to zero — *the count IS the completion state*.
- **Note the inversion Word enforces:** the pane is for *finding* changes, not *fixing* them — "make all editorial changes in the document" ([Microsoft support](https://support.microsoft.com/en-us/office/track-changes-in-word-197ba630-0f5f-4a8e-9a77-3712475e806a)). Index navigates, body acts.

### 1.3 Notion — suggested edits

- **Render locus:** suggested text shows **in place on the page** (insertions/deletions marked) with a **suggestion list on the side of the page** ([Notion help: Suggested edits](https://notion.com/help/suggested-edits)).
- **Accept/reject placement:** **hover the suggestion → ✔️ accept / ❌ reject** inline on the suggestion itself; the suggestion is also a comment thread — click to reply, emoji-react. Accept/reject are *hover-adjacent micro-actions*, not stacked buttons under a payload.
- **Pending surfacing:** **inbox notification when someone suggests on your page**; the mode chip ("Suggesting" with an ✕) marks the session state. No accept-all exists — per-suggestion only.
- **Completion state:** rejected suggestion "will disappear"; accepted contents update — again, closure **removes**, never dims.
- **Relevance to Metatron:** Notion is the closest *layout* precedent for a pane-based surface: inline body + side rail of suggestions, micro-actions on the rail item.

### 1.4 Figma — comment/suggestion pins

- **Render locus:** **numbered pins on the canvas** at the exact point/region, plus a **right sidebar list when comment mode is on** ([Figma help: Guide to comments](https://help.figma.com/hc/en-us/articles/360039825314-Guide-to-comments-in-Figma)).
- **Index↔body navigation is the core mechanism:** clicking a sidebar item **navigates the canvas to that comment's location** ([Figma help: View and manage comments](https://help.figma.com/hc/en-us/articles/360041547593-View-and-manage-comments)); `⇧C` hides all pins for a clean read; sort/filter by **Open vs Resolved** and by file/page.
- **Completion state:** **Resolve** — resolved threads leave the Open view entirely (filtered away, still retrievable). The default canvas view is *actionable-only*; the resolved history is opt-in.
- **Why it matters here:** Figma is the canonical proof that **"jump-to-pending with a visible count"** works as *the* navigation affordance for pending review work, and that resolved items should exit the primary view rather than linger at 50% opacity.

### 1.5 Grammarly — correction card flow

- **Render locus:** inline underline (severity/category color-coded; documented colorblind mode exists — category is never color-only) + **correction cards to the right of the text** ([Grammarly support: Apply corrections](https://support.grammarly.com/hc/en-us/articles/115000091451-Apply-corrections)).
- **Accept is ONE click on the suggestion itself** — "Click on a suggested correction to apply the change in the text" — there is no separate Accept button. Dismissal is a trash icon; cards are **collapsed by default and expand for the explanation** ("View a detailed description of the highlighted mistake") ([Grammarly support](https://support.grammarly.com/hc/en-us/articles/115000091451-Apply-corrections), [Editor user guide](https://support.grammarly.com/hc/en-us/articles/360003474732-Grammarly-Editor-user-guide)).
- **Bidirectional sync:** clicking a card locates the underlined phrase in the text; clicking the underline highlights the card ([Editor user guide](https://support.grammarly.com/hc/en-us/articles/360003474732-Grammarly-Editor-user-guide)).
- **Batch dismissal is per-category:** the trash icon next to a category heading ("Spelling") **ignores all suggestions in that category at once** ([Grammarly blog: new editor](https://grammarly.com/blog/product/new-grammarly-editor)).
- **Density:** the list is a queue of one-line actionable cards; the *payload* (explanation, variants) hides behind expand. Ignored cards **leave the list** ("Cards you ignore are removed from the list").

### 1.6 LanguageTool — rule-popup flow

- **Render locus:** squiggly underline in the editor + **popup dialog at the highlight** listing replacements; **Ignore** in the dialog dismisses (temporarily disables the rule for that instance) ([LanguageTool: rules on/off](https://languagetool.org/insights/post/enabling-and-disabling-rules/)). Same shape as Grammarly minus the card rail: popup applies a replacement with one click, everything else is a rule-management escape hatch. Lower UI sophistication than Grammarly but same law: **apply is one click, adjacent to the highlighted text; dismissal is cheap and rule-scoped.**

### 1.7 GitHub — review-suggestion blocks

- **Render locus:** suggestions live **in the diff/thread as ` ```suggestion ` blocks rendered as a mini-diff**, authored via "Make a Suggestion" on selected lines ([GitHub docs: Reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request)).
- **Accept/reject placement:** below the suggestion block, **"Commit suggestion"** (apply as its own commit) or **"Add suggestion to batch"** → accumulate many suggestions → **"Commit suggestions"** applies the whole batch **as a single commit** with co-author attribution per suggester ([GitHub docs: Incorporating feedback](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/incorporating-feedback-in-your-pull-request)). Note the *naming discipline*: the button states the consequence ("Commit"), not the verdict ("Accept").
- **Thread lifecycle:** **"Resolve conversation"** collapses the whole thread and marks it resolved — "makes it easier to find conversations that still need to be addressed" ([GitHub docs: Commenting on a PR](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request)); a Conversations menu indexes all threads; out-of-scope suggestions can be **deflected into a tracking issue** instead of accepted/rejected.
- **Completion state:** resolved threads collapse out of the active view; unresolved ones dominate; review decision (Approve / Request changes) is a separate, higher-weight control than any individual suggestion.
- **Newest precedent (AI in the loop):** review comments can now be **delegated to Copilot** — a third disposition beyond accept/reject/defer ([GitHub docs](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/incorporating-feedback-in-your-pull-request)).

### 1.8 Cross-system comparison table

| System | Render locus | Accept placement | Batch semantics | Pending count | Completion state |
|---|---|---|---|---|---|
| Google Docs | inline markup + margin card | check/✕ in card, beside summary | Accept/Reject-all **with preview** | side panel list; email | markup removed; count absent because backlog is gone |
| Word | inline + balloons + gutter bars | card on click; ribbon sequential loop | Accept/Reject all, all-shown, +move-to-next, +stop-tracking | Reviewing Pane summary count | count → 0 |
| Notion | in-place + side suggestion list | hover ✔️/❌ on the item | none (per-item only) | inbox notification | item disappears on resolve |
| Figma | canvas pins + sidebar list | (resolve on thread) | resolve per thread | Open/Resolved filter, pin numbers | resolved exit default view |
| Grammarly | underline + right card rail | **one click on the correction** | ignore-all-per-category | alert list queue | card leaves list |
| LanguageTool | underline + popup | one click on replacement | ignore-per-rule | squiggle count implicit | highlight leaves |
| GitHub | diff thread suggestion block | "Commit suggestion" under block | **add-to-batch → one commit** | unresolved-conversation count | resolve collapses thread |

**The three laws every shipped system obeys (Metatron violates all three today):**

1. **The action never hides below the payload.** Accept/reject sit on the summary row (Docs card header, Notion hover, GitHub under the mini-diff, Grammarly one-click). Payload detail (full proposed text, explanation) is collapsed *behind* expand — the inverse of Metatron's row.
2. **Resolved work exits the primary view.** Nobody keeps a struck-through, half-transparent backlog above/below the actionable queue. Resolution = collapse (GitHub), filter out (Figma), remove (Grammarly/Notion), or vanish-the-markup (Docs/Word).
3. **Batch accept is previewable and/or granular.** Accept-all never means "blindly commit everything": Docs previews the result; GitHub batches only what you explicitly added; Word's "All Shown" respects the filter; Grammarly batches only within the category you aimed at.

---

## §2 Change-recap timeline patterns

(Operator praised the recap-timeline idea unprompted; Metatron's contribution ledger already stores `{seq, ts, actor: human|agent|system, action, surface, target, summary, rationale?}` — ADR-0011 §4 — so the question is purely the render precedent.)

### 2.1 Google Docs / Drive version history
Right-panel timeline of timestamps; **each editor gets a stable color shown next to their name**, so per-actor authorship is scannable without reading names; **"Name this version"** pins milestones (cap 40/document) and an **"Only show named versions" toggle collapses the noise** ([support.google.com/docs/answer/190843](https://support.google.com/docs/answer/190843?hl=en)). *The named-version toggle is the pattern to steal: a signal/noise dial over the same timeline.*

### 2.2 Notion page/version history
Revisions + comments interleaved in one "Updates" dropdown; snapshots coalesced (every 10 min active, 2 min after idle); selecting a version shows **"highlights of what changed" — added/removed text, added/deleted blocks — so you review "without manually comparing two versions side by side"** ([Notion help: duplicate, delete & restore](https://notion.so/help/duplicate-delete-and-restore-content)). *Best-rendered precedent for "each timeline entry carries its own diff summary."*

### 2.3 Word Reviewing Pane
Flat list of all changes grouped per reviewer, **top summary = exact remaining counts** ([Microsoft support](https://support.microsoft.com/en-us/office/track-changes-in-word-197ba630-0f5f-4a8e-9a77-3712475e806a)). *Precedent for the ledger header-line: "this run: 7 agent changes, 2 accepted, 1 rejected, 4 pending."*

### 2.4 GitHub timeline + bot attribution
Reviews, comments, commits and *system events* share one conversation timeline, distinguished by identity treatment, not separate feeds: bots render with the **`[bot]` suffix and a "bot" badge** (e.g. `dependabot[bot]`, verifiable on any dependabot commit list, e.g. [dependabot-core commits](https://github.com/dependabot/dependabot-core/commits)); AI-assisted commits surface as **co-author identity — "brettfo and Copilot committed …"** — the same multi-avatar co-author mechanism humans use ([SSW attribution rule](https://www.ssw.com.au/rules/attribute-ai-assisted-commits-with-co-authors) documents the `Co-authored-by:` agent convention across Claude Code/Codex/Copilot). Resolved threads collapse *in place* — history stays contiguous while active work stands out.

### 2.5 Gemini-in-Docs comment workflows (the AI-in-review precedent)
Google's July-2026 direction: Gemini **summarizes comment threads, finds unresolved issues, and "generates suggested edits for you to review, approve, and apply"** — AI output deliberately lands in the *same* suggested-edits substrate as human suggestions, keeping the human as approver ([Workspace Updates, 2026-07-28](https://workspaceupdates.googleblog.com/2026/07/streamline-collaboration-in-google-docs-with-Gemini-powered-comment-workflows.html)). *This is the closest shipped analogue to Metatron's model — AI suggestions inheriting the human suggestion UI wholesale, with review/approval preserved.*

**Human-vs-system distinction, ranked by render quality for Metatron:**
1. **GitHub** — one timeline, actor identity + badge does the work; machine entries never get a special lane. Best fit: Metatron's ledger is already one timeline with `actor` on every entry.
2. **Notion** — per-version "highlights of what changed" beats bare timestamps.
3. **Docs** — stable per-actor color + named-version filter (two actors only: *Metatron* and *me* — color works trivially at n=2).
4. **Word** — count header as the at-a-glance summary line.

---

## §3 Metatron translation: what transfers, what needs the AI twist

Metatron's structural difference: **the counterpart is an AI running in bursts, not a human colleague typing continuously.** That flips two assumptions almost every precedent makes.

### Transfers directly (adopt as-is)
- **Two-tier layout: index rail + inline markup.** Every pane-based system (Notion rail, Grammarly card rail, Figma sidebar, GitHub file list) pairs a *compact index* with *body context*. Metatron's single full-text dump is the outlier.
- **Action-adjacent-to-summary rows; full proposed text behind expand** (Grammarly's collapsed cards; GitHub's mini-diff beats Docs' full-paragraph markup for machine suggestions precisely because diffs beat payloads).
- **Jump-to-pending + explicit count** (Figma sidebar→canvas, Docs N/U walk, Word Next loop, Reviewing Pane count).
- **Resolved items exit the actionable view** (Figma Open/Resolved filter; GitHub resolve-collapse), with an explicit toggle to reveal them.
- **Accept-all with preview** (Docs) and **per-batch/per-category accept** (GitHub batch; Grammarly category) — see twist #3 before shipping accept-all.
- **Consequence-named buttons** (GitHub's "Commit suggestion" > "Accept"): the Metatron label should state what happens to the text ("apply to document"), which also serves the trust story.

### Needs the AI twist
1. **Suggestion density per burst, not per human.** A human reviewer dribbles 3–12 suggestions; a Metatron run lands a *set* (the glint already says "suggestion set"). Every system above assumes low arrival rate; the batched-accept mechanics (GitHub batch, Grammarly category-dismiss, Docs preview-then-accept-all) are not garnish for Metatron — they're **mandatory scale controls**. Recommendation: suggestions render grouped **per run** ("Draft run · 4 suggestions"), and the batch primitives are first-class from day one.
2. **Per-suggestion provenance replaces per-author color.** In Docs/Word the author name+color *is* the trust cue; with a single AI counterpart the interesting variable is **why the machine proposed this**: rationale (already served as `s.proposed`/`s.rationale`), source/basis, model+run identity. The ledger already stores `rationale`, `surface`, `target` (ADR-0011 §4) — the row should show one-line rationale at normal contrast (not `--text-muted` floor) and expand to full provenance. This is also what satisfies the project's served-truth law: the provenance shown must be served facts, never invented.
3. **Accept-all meets automation bias.** With a human suggester, accept-all is safe-ish (you can tell their good takes from bad in bulk). With an AI, bulk-accept invites rubber-stamping — and the operator's invariants (I3 trust over fluency, I4 the human is the author) make that a product risk, not just a UX nit. The twist: **preview-gated batch accept** (Docs' Preview "Accept all" as a required intermediate screen showing the resulting document) *and* biased friction — one-by-one for a first run; batch becomes natural once the operator trusts the stream. (No surveyed product solves this; Gemini-in-Docs keeps explicit human approve even for AI suggestions — the closest precedent for "AI never self-approves.")
4. **Trust cues are content, not chrome.** GitHub resolves AI-vs-human trust by making the *identity visible everywhere* (badge, co-author avatar), not by styling AI output differently. Metatron: the actor badge ("Metatron" vs "you") on every ledger/summary entry + the recap timeline (§4b) *is* the trust surface. No special "AI" warning styling per suggestion — the recap timeline gives the audit trail instead.
5. **No notification story needed.** Docs/Notion notify the *author* when suggestions arrive; in single-user Metatron the operator *is* the suggester's counterpart — arrival surfacing collapses into the pending-count badge and the run receipt. Drop any plan for notification affordances.

---

## §4 Ranked recommendations (for sw-architect / next wave)

Ordered by operator-pain-per-effort. (a) is the W8 re-walk fix; (b) is the surface the operator praised; (c) is cheap policy cleanup that should ride with (a).

### (a) Suggestions pane redesign — P0

1. **Row anatomy inversion (fixes complaints #1+#2 together):** compact summary row = one-line **diff summary** (changed block id/section + short before→after or `+N/−N` for paragraph-scale suggestions) with **accept + reject pinned at the row's trailing edge, same line as the summary** — never stacked below the payload (Grammarly/Notion/Docs-card law). Full proposed text, rationale, and provenance move behind a per-row **expand** (Grammarly collapsed-card pattern). A row is actionable without scrolling *inside* the row, at every suggestion size.
2. **Resolved backlog leaves the default view (fixes #3):** pending-only list by default; resolved entries collapse into a "Resolved (N)" fold or Open/Resolved filter (Figma). No opacity games: the token ramp's AA floor is already documented in `editor.css` — **ban `opacity` on resolved states**, use the existing `--text-soft`/`--text-dim` tokens explicitly if any resolved text must remain visible, keeping effective contrast ≥ 4.5:1 in *both* theme sets. Rationale/why text steps up from `--text-muted` to at least `--text-dim` (decision-critical text never sits at the ramp floor).
3. **Affordance hierarchy (fixes #4):** accept = the row's single primary action (filled/accent treatment); reject = quiet secondary; expand = tertiary text button. Accept/reject labels name the consequence ("apply", "dismiss" or equivalent) per GitHub's discipline. Busy state stays as-is (the mechanism earned the operator's praise; don't touch the wire contract).
4. **Header = Word's Reviewing Pane summary line:** "N pending · M resolved" computed from the served set (already computed client-side today), plus **Accept-all-with-preview** gated per twist #3 — preview shows the resulting document before committing the batch (Docs). Ship per-run grouping in the same pass ("suggestion set" is already the served unit).

### (b) Recap timeline as the first contribution-ledger surface — P1

Build on the existing `contributions` read (ADR-0011 §4; the ledger already records actor/summary/rationale — **no new data substrate needed**). Precedent stack: GitHub's single-timeline-with-actor-badges (§2.4) + Notion's per-entry "highlights of what changed" (§2.2) + Docs named-version milestones (§2.1):

- Reverse-chronological timeline, **grouped by day and by run**; entries: actor badge (**"Metatron" / "You" / system** — stable color each, n=2 makes Docs' color-coding cheap), action + target + one-line summary (all served fields).
- **Docs-style named milestones:** stage transitions / gate verdicts render as pinned named separators ("v1 draft complete", "cite gate passed"); a **"Milestones only" toggle** collapses routine churn (the Docs named-version filter).
- **Actor filter** (all / me / Metatron) — the "AI-vs-me recap" the operator praised; each accepted/rejected suggestion links back into the suggestion fold so recap → detail navigation exists (Figma sidebar→canvas jump, one mechanism reused).
- Honest empty state already specced in ADR-0011 (pre-feature history lives in history/revisions) — keep it.

### (c) Keep/remove decisions for existing affordances — P0/P1 policy

| Affordance today | Decision | Rationale |
|---|---|---|
| **Adjudicate button** (functional, jumps to first pending accept) | **KEEP MECHANISM, RELABEL + RESHAPE → jump-to-pending with count badge**: "Adjudicate — N" → "↓ N to review" | It is a jump mislabeled as a command; every precedent labels navigation as navigation (Docs Ctrl+Alt+N/U, Figma sidebar click). The count badge doubles as the pending surfacing (Word summary-line law). Keep it as the *ladder* control the W8-signal spec froze; only its visual identity changes. |
| Glint strip "suggestion set: N to adjudicate" | **FOLD into the pane header count line** (recommendation a.4) | Two count surfaces (glint + ladder) say the same served fact; one wins. |
| Resolved rows with `opacity .5/.6` + strikethrough inline in the list | **REMOVE → collapse/resolve pattern** (recommendation a.2) | Violates the token ramp's own AA floor; no precedent keeps a struck-through backlog in the actionable view. |
| accept/reject sibling text buttons | **KEEP actions, REWEIGHT** (a.3) | Mechanism praised; hierarchy is the complaint. |
| Per-row `resolved_by` line | **KEEP, move into the Resolved fold's entry meta** | Audit-relevant, not actionable-view content; the ledger/b becomes its permanent home. |

**Suggested acceptance bar for the wave's QA walk** (breaks into cards at sw-architect's decomposition): (1) at 1080p with a 5-suggestion set from the W8 fixture run, **zero intra-row scrolling** — accept visible on every collapsed row; (2) computed-contrast sweep (the W8 fill-invariant harness pattern can carry over to color) asserting every suggestion-view text pairing ≥ 4.5:1 in both theme sets, with `opacity` banned inside `.suggestion`; (3) pending→resolved transition moves the row into the fold in one repaint; (4) jump-to-pending focuses the first actionable row's accept control; (5) recap timeline renders from a real `contributions` reply with actor badges and survives the empty state.

---

## §5 Source register

Suggestion/review mechanics:
- Notion — *Suggested edits* — https://notion.com/help/suggested-edits
- Microsoft — *Track changes in Word* — https://support.microsoft.com/en-us/office/track-changes-in-word-197ba630-0f5f-4a8e-9a77-3712475e806a and https://support.microsoft.com/en-us/word/training/track-changes-in-word
- Google — *Suggest edits in Google Docs (iPhone & iPad)* — https://support.google.com/docs/answer/6033474 (desktop answer pages 404 to non-browser fetch; desktop mechanism corroborated below)
- CustomGuide — *Track Changes in Google Docs* — https://www.customguide.com/course/google-docs/track-changes-in-google-docs
- Deckoholic — *How to Track Changes in Google Docs* (margin cards, side panel, Accept/Reject-all preview, Ctrl+Alt N/U walk) — https://www.deckoholic.ai/tutorials/google-docs/track-changes
- SolveYourTech — *Switch Editing/Suggesting/Viewing modes* (mode/shortcut/panel detail) — https://www.solveyourtech.com/switch-viewing-modes-google-docs/
- Grammarly — *Apply corrections* — https://support.grammarly.com/hc/en-us/articles/115000091451-Apply-corrections ; *Editor user guide* — https://support.grammarly.com/hc/en-us/articles/360003474732-Grammarly-Editor-user-guide ; *What's new with the Grammarly editor* (category ignore-all) — https://grammarly.com/blog/product/new-grammarly-editor
- LanguageTool — *How to turn rules on and off* (dialog + Ignore) — https://languagetool.org/insights/post/enabling-and-disabling-rules/
- GitHub Docs — *Reviewing proposed changes in a pull request* — https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request ; *Incorporating feedback* (Commit suggestion / batch) — https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/incorporating-feedback-in-your-pull-request ; *Commenting on a pull request* (Resolve conversation) — https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request
- Figma — *Guide to comments* — https://help.figma.com/hc/en-us/articles/360039825314-Guide-to-comments-in-Figma ; *View and manage comments* — https://help.figma.com/hc/en-us/articles/360041547593-View-and-manage-comments

Recap timelines & attribution:
- Google — *See what's changed in a file* (version history, per-editor colors, named versions + filter) — https://support.google.com/docs/answer/190843
- Notion — *Duplicate, delete & restore content* (version history, change highlights, snapshot cadence) — https://notion.so/help/duplicate-delete-and-restore-content
- Google Workspace Updates — *Gemini-powered comment workflows in Google Docs* (AI suggestions in the human suggestion substrate) — https://workspaceupdates.googleblog.com/2026/07/streamline-collaboration-in-google-docs-with-Gemini-powered-comment-workflows.html
- GitHub — dependabot commit history (bot identity in timeline) — https://github.com/dependabot/dependabot-core/commits ; SSW — *Attribute AI-assisted commits with co-authors* — https://www.ssw.com.au/rules/attribute-ai-assisted-commits-with-co-authors ; OpenAI Codex discussion #2807 (co-author trailer prior art) — https://github.com/openai/codex/discussions/2807

Metatron as-is: `/local/projects/metatron-rewrite/frontend/app/src/editor.ts` (`suggestionRow`, ladder/adjudicate wiring), `editor.css` (`:285-288` suggestion states; `:22-33` token ramp + AA-floor note), `docs/adr/0011-voice-profile-and-contribution-ledger.md` §4–§5 (ledger entry shape, contributions pane posture).

*Caveats: Google Docs desktop behavior cited via the official mobile answer + two corroborating walkthroughs because the support.google.com desktop answers reject headless fetches (404 to non-browser clients); descriptions were cross-checked between the two sources and match Notion's help-page wording patterns for the same shared-doc mechanics. Figma "suggestion pins" are surveyed as the comment-pin/resolve pattern the card named; Figma has no accept/reject-edit primitive — that's why it contributes navigation & resolve mechanics only.*
