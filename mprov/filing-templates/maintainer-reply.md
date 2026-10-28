# Maintainer-reply template — thread comments on mprov-ng

Modeled on uberlinuxguy's own comment corpus (median 18 words, 0% headings)
and on our standing maintainer-engagement rule (never post an untested
opinion — every claim carries a receipt). His shape + our receipts:

```markdown
<Public reply — must pass the cold-reader test (FS10, 2026-10-28): a reader
who has NOT followed the internal thread understands on first read. Required
shape: (1) context clause naming the artifact/behavior, (2) finding/claim in
complete subject-verb-object sentences (no telegraphic noun-chain fragments),
(3) consequence — what this means for the reader / what changes. Minimum
3 full sentences; corrections restate BOTH the original (wrong) claim and the
corrected finding in full. No unexpanded shorthand. Internal board traffic
exempt. Then: stance/verdict first, first person, soft ask form when asking
("I would prefer ...", "I don't think ... is the right shape because ...").
Receipts woven inline: sha/file/test names backticked, issue/PR refs as `#N`
or `mprov-ng/<repo>#N`, one or two hard numbers. No headings, no bold labels,
no bullet lists unless ≥3 true list items.>
```

Per-situation openers he actually uses (adopt verbatim shapes):
- Preference on a PR: `I would prefer to see <X> renamed to <Y> for <reason>.`
- Declining a design: `This is an interesting idea but I would prefer <alt>.
  The point was <goal>, and <cost>.`
- Closure: `Closing as won't fix: replaced by #N. <provenance: what is
  already on main, which sha survives, what the replacement adds>.`
- Already fixed: `Already fixed by `<sha>` (<context>, merged to `main` on
  <date>). <one-sentence mechanism>; <test file> covers it.`
- Ordering: `Blocked by mprov-ng/<repo>#N (<one-clause why>). That has to
  reach <`:dev`/release> before this merges.`
- Tested verdict on a claim (our rigor inside his shape): `<Verdict in
  five words: "Did not reproduce on current main" / "Confirmed on
  `<sha>`"]. <what was run, on which head> — <result numbers>; <test file
  or script name> covers it. <next step / ask>.`
- Correction (FS10 extra rule): restate BOTH claims in full. Open with
  context ("Correction to my previous comment: I originally said ... That
  was wrong."), then the corrected finding with mechanism, then the
  consequence ("Escaping is not involved; the fix addresses ...").

BAD — telegraphic fragment, no context, no restated prior claim, <3 sentences:
`Corrected the description: null projection from the levels a real payload
carries no Ansible keys on, plus the whole-array select — not the escaping.`

GOOD — context → both claims → consequence, ≥3 full sentences:
`Correction to my previous comment: I originally said the failure came from
shell escaping of the payload. That was wrong. The real causes are (1) the
projection returns null because the levels our real payload carries contain no
Ansible keys at all, and (2) the whole-array select grabs entries it shouldn't.
Escaping is not involved; the fix addresses (1) and (2).`

Keep (content rigor, unchanged): run it before you say it; per-claim
verdicts with receipts; mark un-runs honestly; verify your own comment
landed (read back id/author/length via API). Public replies add FS10's
clarity floor (≥3 sentences, cold-reader test) — FS6's "mirror their
length" still applies but is bounded below by that floor. Security claims
in replies follow the Deployment threat model (controlled deployments,
MPROV-MAINT-POLICY.md, 2026-10-25): state harms that survive with no
untrusted network actor; concede working-as-intended where the maintainer's
design intent says so, without backpedaling on verified evidence.
