---
description: Run the voice retune protocol from a raw author sample.
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents). Run the retune protocol end to end (`voice/resources/retune.md`). $ARGUMENTS = optional chapter number or the author's raw sample.

- The author reads a draft and it doesn't sound like them. Take whatever they give — a few sentences, a ramble, a voice-note transcript, a rough rewrite — as a fresh voice sample. Never evaluate the raw input for quality; it is a sample, not a draft.
- No demolition, no structure critique. Analyze the gap (sentence length, word choice, rhythm, pronoun distance, energy, specificity), make ONE alignment pass preserving all content and structure, and show the result without explaining what changed. Ask "Is this closer?"
- After a successful retune, harvest the sample into the voice record: promote characteristic phrases to exemplars in `kb/styles/voice.md`, update `kb/styles/baseline.md` if the sample reveals a measured rate the profile missed, and route persistent changes to `@style-creator`.
- Retune and drafting must never share a stance-turn.
