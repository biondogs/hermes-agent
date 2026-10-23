# ADR-0007: Authorial voice fidelity in scope; AI-detection evasion permanently out

**Status:** Accepted (operator decision D5 **with rider**, 2026-10-23, via butler chat — comment thread t_77ba5a4b)
**Deciders:** operator (direction + rider verbatim below) · sw-architect (line-drawing) · Card: METATRON-ARCH-1 (t_77ba5a4b)
**Related:** invariant I4 (the human is the author); I2 (attributed history); resolves the June-vs-July values reversal flagged by R1 and DOC-1.

## Context

Metatron's history contains an explicit values reversal. The June module (commits ebae983/c541ceb) was a **Scribbr AI-detection-evasion** tool — detector-facing countermeasures — and it shipped default-on on every branch tip (R1's V1-022 ethics flag: unseeded silent rewriting of academic text by default). The July v2 corpus reversed the values: the voice-profile spec declares the product **"not an authorship-detection evader."** DOC-1 flagged this as the one values decision the rewrite could not inherit silently.

## Operator decision (D5) and rider — verbatim

> *"Option a, but I'd like to keep some of the evasion concepts like avoiding tropes and obvious formatting signs. I still want the product to appear exactly how I would write it and there are actually a number of new humanizer models we could add [to] the research list, we could also plan to make a LoRA from the voice collector."*

(The bracketed "[to]" is the butler relay's insertion.) Operator intent as relayed: the detector-facing evasion module is NOT inherited; the **authorial-voice-fidelity layer IS** — harvesting anti-trope / anti-obvious-AI-formatting concepts as voice-profile features. Target: output indistinguishable from the operator's own natural writing. Contribution ledger applies to all stylometry passes.

## Decision: the line

**The reference target decides the category.** A style feature is voice fidelity when its target and validation are **the author's own writing corpus**. A feature is detection evasion — and out of scope — when its target, success metric, or validation is **a detector's classifier output**.

### IN scope — the voice-fidelity layer (a first-class product goal)

1. **Voice profile from the operator's own corpus** (voice collector): diction, rhythm, structural and formatting habits.
2. **Anti-trope and anti-obvious-AI-formatting, harvested from the June module's concept list** — avoiding clichéd LLM phrasings, formulaic transitions, boilerplate formatting tells (indiscriminate bullet-ification, heading-everything, tic punctuation, the "delve/robust/tapestry" class) — implemented and validated as *style features of the voice profile*. Their justification is fidelity to the author's corpus: text that matches the operator's habits necessarily avoids machine-trope defaults. This satisfies the rider's "I still want the product to appear exactly how I would write it."
3. **Research seed 1:** evaluate current open humanizer / style-transfer models as candidate voice-stylometry passes (research-list entry; any adopted model must pass the same corpus-fidelity validation, not a detector benchmark).
4. **Research seed 2 (planning track, post-v1 scope):** a voice LoRA fine-tune trained on the voice-collector corpus, so generation is native-in-voice rather than post-processed.
5. **The contribution ledger is unconditional:** every stylometry/rewriting pass writes an attributed ledger entry (I4). No silent passes, no default-invisible rewriting — the V1-022 anti-pattern is banned by test.

### OUT of scope — detection evasion (permanently)

1. No module, feature, success metric, test, or benchmark whose purpose is defeating a named or unnamed AI-detection classifier (Scribbr, Turnitin, GPTZero-class).
2. No detector-specific countermeasures; no detector-score optimization loops; no "undetectable" claims in product positioning, docs, or naming.

### Why the line holds (and isn't cosmetic)

- The rider's stated goal is fully achievable on the fidelity side alone: "appear exactly how I would write it" targets the **author**, not a third party's classifier.
- Detector-facing work reintroduces exactly the values problem the July reversal resolved, and chases an adversarial target that changes silently — it cannot be honestly tested, which collides with I7 ("no silent failure") and I3 (trust over fluency) at the product's core.
- Disclosure stays a feature, not a leak (I4): the ledger records what the machine touched even while the prose reads as the author's. Metatron states what it did; it does not claim to be undetectable.

## Alternatives rejected

- **Full option (b) — opt-in "humanize" tool, always ledgered:** retains a permanent, purpose-named detector-facing capability; contradicts the July reversal regardless of opt-in framing.
- **Puritan (a) — discard the anti-trope concepts entirely:** the rider explicitly keeps them, and they are legitimately defensible as corpus-fidelity work; this ADR is what keeps them on the right side of the line.

## Consequences

- P4's voice-profile workstream carries the anti-trope / anti-formatting feature set plus research seed 1; seed 2 (voice LoRA) goes on the research list as a planned future track, not v1 scope.
- Ledger coverage of stylometry passes is a tested invariant (I2/I4 test suite).
- Product docs carry an explicit values note stating this ADR's line.
- Reviewers should treat any PR whose validation references detector outputs as violating this ADR.

## Revisit when (falsifier)

The line is falsified — and must be escalated to the operator before the feature ships — the moment any voice-layer feature's *validation or test metric* depends on a detector's output. Absent that, this decision is not revisited: it is a values statement, not a tradeoff under budget pressure.
