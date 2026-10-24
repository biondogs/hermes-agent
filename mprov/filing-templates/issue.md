# Issue template — mprov-ng filing

Modeled on uberlinuxguy's Oct-2026 issues (mprov_control_center #347, #346,
#335, #296). The five Rule-C contents (symptom, evidence, root cause,
proposed fix, severity) MUST all be present — as prose, not as labels.

````markdown
<Declarative title: the concrete failure, `fact: mechanism` when a colon
helps. No [Sx] prefix, no trailing period. Sole prefix exception: `[SEC]`
on security ENHANCEMENTS (see Severity model, MPROV-MAINT-POLICY.md). e.g.
"Stateful install never reboots: mprov_boot_init.sh unmounts /proc before
writing /proc/sysrq-trigger">

<Paragraph 1 — symptom as observed, 1–3 sentences. What breaks, on what
setup, with the real error output pasted verbatim if it exists:>

```
<verbatim error text — never paraphrased>
```

<Paragraph 2 — how/where, with evidence woven into the sentence: backticked
`file:line` at minimum, commit-pinned permalink for the defect site
(preferred, e.g. [`mprov_boot_init.sh:337`](https://github.com/mprov-ng/<repo>/blob/<sha>/path#L337)),
and the root-cause mechanism named. Related sightings as `#N` /
`mprov-ng/<repo>#N`.>

**Fix:** <one or two sentences — what to change and what to preserve.>
<Optional extras ONLY when they carry content, his vocabulary: `**Likely
cause:**`, `**To decide:**`, `**Coordinate with:**`, `**Check first:**` —
at most one or two of these per issue.>

Severity: S<N> — <one clause of impact, e.g. "happy path (IPv4) works; IPv6
transport degrades">. Security ENHANCEMENTS (no active breakage) instead
write `Severity: [SEC] — future nice-to-have security enhancement: <one
clause>` and carry the `security` label with NO sN-* label; crisis-tier
security (credential exposure live, break by default) keeps its S tier and
also carries `security`.

Found while <what you were doing> for #<N>. Related: #<N>,
mprov-ng/<repo>#<N>.
````

Rules recap: body ≤150 words is a cap, not a target — his median is 41.
No `## ` headings. No `**Symptom.**`/`**Evidence.**`/`**Root cause.**`
labels. Keep the `review-found`/`sN-*` labels on the ISSUE object (tooling
metadata; under operator adjudication) — they stay off the title and out of
the prose; add the `security` label on every security-classified filing
(Severity model, 2026-10-24). No "Migrated from ..." footer on new filings
unless a real provenance line; when present, keep it to the one closing
sentence.
