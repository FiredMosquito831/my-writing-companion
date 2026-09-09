---
name: voice
description: |
  Load for project-setup voice capture, every drift_interval chapters, or when the author says the prose does not sound like them. The voice skill owns the voice lifecycle: capture, measured profile, exemplars/anti-exemplars, drift checks, the blind-tag falsification test, and retune. It is the strongest signal the style-creator and critics have — and the reference the mechanical net defers to.
---

# Voice

The voice skill owns the full lifecycle of a project's prose voice: how it is **captured** from the author, **measured** into a numeric profile, **calibrated** against exemplar passages, **checked** for drift, **tested** for whether the capture worked at all, and **retuned** when the author says it is off. It is the reference the mechanical net (`style-guardrails/`) defers to via the measured-profile law, and the primary lens the style-creator and critics use.

## What this skill is

- The **single source of truth** for the project's voice: `kb/styles/voice.md` (the document these resources describe how to build and maintain).
- The **measured-profile law** made numeric: `kb/styles/baseline.md` is the author's own per-1k rates, and the net measures against them instead of a generic average.
- A **self-contained** reference: it restates the measured-profile law, the drift/retune loop, and the blind-tag test so the style-creator can act without loading other skills. Cross-references to `style-guardrails/` and `creative-writing-craft/` are pointers only.

## Load the resource needed

- `resources/voice-template.md` — the two-part `kb/styles/voice.md` structure: Part 1 guardrails (restated inline) and Part 2 identity scaffold (tone, sentence rhythm, vocabulary register, POV/tense, dialogue conventions, exemplar passages, anti-exemplars). How it is built, used, and maintained.
- `resources/voice-profile.md` — the measured per-1k voice profile: what it is, how `vellum style stats --baseline` emits it, the **bidirectional diff** (over-shoot vs. under-shoot), how it overrides the tier bans, how the baseline is built and refreshed, and the blind-tag test that validates the capture.
- `resources/blind-tag-test.md` — the falsifiable check that voice capture worked: shuffle author-corpus and manuscript passages, strip tags, sort with a fresh project-naive critic; < 75% correct attribution means the capture failed and the exemplars need redoing.
- `resources/drift-check.md` — the two-pass drift procedure (mechanical `style stats --baseline` + LLM exemplar/anti-exemplar comparison), when to run it, and how to resolve the two passes.
- `resources/retune.md` — the voice realignment protocol: take the author's unguided sample, analyze the gap, one alignment pass (no structural changes, no quality evaluation of the sample), present, and harvest the sample back into the voice profile.

## How the voice lifecycle fits the chapter loop

1. **Setup** (`project-setup`): collect 3–5 author samples → style-creator builds `kb/styles/voice.md` + `kb/styles/baseline.md` → run the blind-tag test once to confirm the capture.
2. **Drafting**: writer loads voice Part 1 + Part 2 + one exemplar (§9 recipe slot 6). Mechanical net (`style-guardrails/`) runs silently, defers to the measured profile.
3. **Drift check** every `drift_interval` chapters or on author request: mechanical + LLM passes. Clean → continue. Drift → retune.
4. **Retune** on "this doesn't sound like me": author sample → one alignment pass → harvest into voice.md + baseline.md → drift check to confirm.
5. **Author-edit harvesting** (style-creator, ongoing): diff author edits against agent drafts, promote characteristic choices into exemplars — the strongest available voice signal, free.
6. **Milestone**: critics judge execution against exemplars/anti-exemplars; blind-tag test re-run after any major retune.

## The measured-profile law (restated)

The author's own measured rates are the standard. `style-guardrails/` states the law; this skill provides the numbers. Caps adapt to `kb/styles/baseline.md`; only statistically significant over-shoot vs. the author's baseline is a finding; under-shoot is reported too. A word the author genuinely uses is never slop in this book.
