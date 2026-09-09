# The Measured Per-1k Voice Profile

Mechanism credited to Fablecraft/Scriptorium; no source text or code copied. Changes: re-cast as a vellum skill resource; numeric profile emitted by `vellum style stats`; bidirectional diff defined; integrated with the tier/cap overrides in `style-guardrails/`.

The measured profile is the answer to "whose voice is this, numerically?" It is the single strongest defense against the mechanical net flattening a real voice: **the author's own rates are the standard the net measures against**, not a generic fiction average.

## What it is

`vellum style stats <file> --baseline` computes per-1,000-word rates for a chapter (or glob) and compares them to `kb/styles/baseline.md`, a numeric table the style-creator builds from the author's own samples:

| metric | author rate (per 1k words) |
|---|---|
| em-dash | 2.1 |
| hedge | 0.8 |
| tier1-hit | 0.0 |
| dialogue-ratio | 0.38 |
| ttr (type-token ratio) | 0.51 |
| burstiness (sentence-len sd/mean) | 0.62 |

The baseline is written by the style-creator during voice capture (`project-setup`) and refreshed from author-edit harvesting. Its frontmatter records which chapters are the sample (`sample-chapters: [1,2,3]`) so its age is visible.

## Bidirectional diff

A drift report lists **both** directions — this is the part generic slop detectors miss:

- **Over-shoot** (subtraction needed): the chapter's rate is *above* the author's baseline. "Em-dashes at 5/1k vs. your 2.1 — cut ~half." This is what most detectors flag.
- **Under-shoot** (restoration needed): the chapter's rate is *below* the author's baseline. "Em-dashes at 0.4/1k vs. your 2.1 — the prose has been edited *away* from your voice." You cannot edit toward a voice you haven't measured. Under-shoot is as much a finding as over-shoot, and it is the one the tier tables alone can never catch.

A drift report that only subtracts is a half-measure. The goal is the author's measured register, not "less."

## How it overrides the tier bans

`style-guardrails/resources/tiers.md` and `structural-caps.md` state the measured-profile law; this file is where the numbers come from. Concretely:

- The **em-dash cap** is the author's baseline rate + band, not a fixed "2 per page."
- A **Tier-1 hit** is measured against the author's own tier-1 rate; only significant over-shoot vs. baseline is a finding.
- **Burstiness** is reported relative to the author's baseline variance — low variance is the finding, high variance is never penalized.

When the baseline says the author *uses* a Tier-1 word at a real rate, that word is not slop in this book — it is the voice. The net adapts; it does not judge.

## Building and refreshing the baseline

1. **Voice capture** (`project-setup`): collect 3–5 author samples → `kb/samples/` → style-creator runs `vellum style stats` on the samples → writes `kb/styles/baseline.md`.
2. **Author-edit harvesting** (`style-creator`): diff author edits against agent drafts, promote characteristic rates, refresh the baseline's `sample-chapters`.
3. **Measured-profile review**: every `drift_interval` chapters, the style-creator re-runs `style stats --baseline` over the whole manuscript and confirms the baseline still represents the author's current voice. If the author's voice has legitimately evolved, the baseline is updated — it measures the author, not a fossil.

## The blind-tag test

A baseline is only as good as the capture that produced it. `blind-tag-test.md` is the falsifiable check: if a fresh critic can't tell the author's prose from the manuscript's at better than 75%, the capture failed and the exemplars need redoing. The baseline's numbers are meaningless if they were measured from the wrong voice.
