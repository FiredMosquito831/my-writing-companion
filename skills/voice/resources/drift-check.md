# Drift Check

The procedure for catching voice drift — the slow divergence of the manuscript from the author's measured voice. Run every `drift_interval` chapters (default 5, from `kb/project-config.json`) or whenever the author says "this doesn't sound like me." Two passes, always in this order: mechanical first, then LLM.

## When to run

- Every `drift_interval` chapters, as a standing cadence.
- On author request ("this doesn't sound like me").
- After a retune (`retune.md`) — to confirm the retune landed.
- Before a milestone critique (persona panel, blind read) — so the critic is judging against current voice.

## Pass 1 — Mechanical (`style stats --baseline`)

`vellum style stats <chapter-glob> --baseline` computes per-1k rates and diffs them against `kb/styles/baseline.md`. The output is a **bidirectional** drift report (`voice-profile.md`):

- **Over-shoot** (subtraction needed): chapter rate above the author's baseline.
- **Under-shoot** (restoration needed): chapter rate below the author's baseline — the prose has been edited *away* from the voice.

The mechanical pass is deterministic and cheap. It catches: em-dash density, hedge density, tier-1/tier-2 hit rates, dialogue ratio, type-token ratio, burstiness. It does *not* catch whether the prose *sounds* like the author — only whether the numbers moved.

If the mechanical pass is clean, the voice is at least numerically stable. Proceed to Pass 2 to confirm it is also qualitatively stable.

## Pass 2 — LLM (style-creator vs. exemplar/anti-exemplar fork)

The style-creator reads the drifted chapter(s) against `kb/styles/voice.md` Part 2 — specifically the exemplar and anti-exemplar passages. The judgment questions:

- Does the chapter's prose sit with the exemplars, or with the anti-exemplars?
- Has any Part 2 field (tone, rhythm, register, dialogue conventions) shifted?
- Is the shift deliberate (a new register the author is trying) or drift (the model smoothing toward its default)?

The style-creator emits findings in the shared schema (`gates/resources/finding-schema.md`), audit `voice`, with the exemplar/anti-exemplar passages as evidence.

## Resolving the two passes

- **Both clean** → no drift. Record the check date.
- **Mechanical flags, LLM clean** → the numbers moved but the voice didn't. Usually a genre/register shift within the voice (a dialogue-heavy chapter lowers burstiness). Update the baseline's band if the shift is consistent; do not retune.
- **Mechanical clean, LLM flags** → the numbers are stable but the *quality* of the prose has drifted (smoother, more uniform, more "correct"). This is the dangerous kind — it is what the blind-tag test exists to catch. Retune.
- **Both flag** → drift confirmed. Retune, then re-run.

## Output

A drift-check note appended to the chapter's critique record (or a standalone `work/voice-drift-<date>.md` for milestone checks): which pass flagged, the specific axes, the exemplar evidence, and the resolution (none / baseline-band update / retune triggered).
