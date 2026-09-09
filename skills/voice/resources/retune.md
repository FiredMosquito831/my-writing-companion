# Retune

Adapted from `claude-ghost-writer/skills/retune/SKILL.md` — MIT. Changes: re-scoped from `book.config.json` to vellum's `kb/styles/voice.md` + `kb/styles/baseline.md`; integrated with the drift-check and author-edit harvesting loops; structural references updated to the vellum layout. Core protocol (one criticism at a time, no quality evaluation of the author's raw input, one alignment pass, update the profile from the author's own words) kept verbatim in spirit.

The author reads a draft and says "this doesn't sound like me." Not wrong — *off*. The words are right but the voice isn't theirs. Retune realigns the prose to the author's actual voice using the author's own unguided input as the sample.

This is **not** a structural critique and **not** a demolition. It is a voice realignment only.

## Rules

- **Never evaluate the author's raw input for quality.** It is a voice sample, not a draft. The rougher the better.
- **Never make structural changes.** Content and order stay intact — only voice, rhythm, and word choice change.
- **One pass at a time.** Show the result, ask if it's closer.
- **Update the voice profile from the author's own words** — this is the most important output, not the fixed chapter.

## Phase 0 — Get the chapter and the sample

Ask which chapter feels off. Read it.

Then ask the author to show how they'd say it — don't try to write well, just talk. A few sentences, a voice note transcribed, even how they'd explain it to a friend. **Wait. Do not suggest anything. Do not give examples.** Let them produce something unguided.

If the author doesn't know how to start: pick the part that feels most wrong, read it out loud, then say the same thing in their own words as if telling it at dinner.

## Phase 1 — Analyze the gap

Read the chapter draft and the author's raw input side by side. Identify the specific differences — do not present this analysis to the author, just use it:

- **Sentence length**: is the draft longer and more complex than how they naturally speak, or more clipped?
- **Word choice**: does the draft use more formal, literary, or abstract words than the sample? What specific words did the author use that the draft avoided?
- **Rhythm**: does the draft flow smoothly where their natural voice would land harder? Does it hedge where they're direct?
- **Pronoun distance**: does the draft describe from outside ("one might notice") where the author speaks from inside ("I saw")?
- **Energy**: where does the sample have heat — opinion, impatience, humor, conviction — that the draft flattened into neutral prose?
- **Specificity**: does the sample use concrete details, names, numbers, sensory details that the draft replaced with abstractions?

## Phase 2 — Retune the chapter

Rewrite the chapter preserving all content, all structure, the meaning of every sentence. Change only: word choice (toward the author's vocabulary from the sample), sentence length and rhythm (toward how they naturally speak), level of formality (toward their register), specificity (toward their concrete details where available), energy level (toward their natural heat or directness).

If the author used a specific phrase or expression in the sample that fits, use it verbatim — even if it's rough. Their actual words are the goal, not polished versions of their words.

## Phase 3 — Present the result

Show the retuned chapter without preamble. After it, ask only: "Is this closer?"

- **Yes** → done. Update the chapter file. Harvest the sample into the voice profile (see below).
- **Closer but still off** → ask what's still wrong and show another passage; run another retune pass on the sections still off.
- **No, it's worse** → ask what specifically got worse, point to a sentence; revert to the original for that section and try a narrower retune.

## After a successful retune — harvest the sample

This is the most important output. Update `kb/styles/voice.md`:

- Add new characteristic phrases from the sample to the exemplar passages.
- Note any vocabulary or rhythm patterns the sample revealed that Part 2 missed.
- If specific patterns in the draft were consistently wrong, add them to the anti-exemplars.

Re-measure `kb/styles/baseline.md` if the sample meaningfully changed the author's measured rates (run `vellum style stats` on the new sample set).

Tell the author: the voice profile was updated from their sample; future chapters will use it. Then run a drift check (`drift-check.md`) to confirm the retune landed.
