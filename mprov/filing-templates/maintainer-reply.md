# Maintainer-reply template — thread comments on mprov-ng

Modeled on uberlinuxguy's own comment corpus (median 18 words, 0% headings)
and on our standing maintainer-engagement rule (never post an untested
opinion — every claim carries a receipt). His shape + our receipts:

````markdown
<Single paragraph. VERDICT or stance in the first sentence, first person,
soft ask form when asking ("I would prefer ...", "I don't think ... is the
right shape because ..."). Then the reason, with receipts woven in inline:
sha/file/test names backticked, issue/PR refs as `#N` or
`mprov-ng/<repo>#N`, one or two hard numbers. No headings, no bold labels,
no bullet lists unless ≥3 true list items. Mirror their length: a one-line
question gets a two-line answer.>
````

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

Keep (content rigor, unchanged): run it before you say it; per-claim
verdicts with receipts; mark un-runs honestly; verify your own comment
landed (read back id/author/length via API). Change (look only): one
paragraph, stance first, receipts inline, ≤~80 words when the maintainer's
ask fits in one.
