# Smell Tests

Mechanism credited to NousResearch/autonovel; no source text copied. Changes: rewritten as four named fiction-prose tests with concrete procedures; integrated with the post-write net and the critic persona panel.

Four tests to run on any passage — in the writer's own head, in a critic's report, or as a demolition check. A passage that fails more than one needs a rewrite, not a patch.

## Test 1 — Read aloud

Read the passage out loud (or mouth it). Does it sound like a person talking, or like a press release?

- Listen for: transition-word chains, hedge clusters, sentences that all land on the same rhythm.
- The ear catches what the eye skips. If you stumble reading it, a reader will stumble too.
- This is the single highest-signal test. It costs nothing and finds the defects no word-list catches.

## Test 2 — Surprise

Is there a single surprising sentence? Human writing surprises — an unexpected word, a turn the reader didn't see coming, a detail that estranges the familiar.

- Slop never surprises. If every sentence is the one the reader predicted, the passage is synthetic.
- One surprising beat per page is enough. It does not have to be loud — a quiet precision counts.
- If the passage is competent but unsurprising, it is "fine" — and "fine" is the enemy.

## Test 3 — Specificity

Does it say something specific? The swap test: could you replace the topic and the same words would still work?

- "The city pulsed with a vibrant energy" — swap "city" for any city, "energy" for any noun, and the sentence survives. That is slop.
- "The city smelled of diesel and overripe melons" — try swapping that. It is anchored. That is prose.
- Specificity is the antidote to slop. Names, numbers, sensory details, the concrete instance behind the abstract noun.

## Test 4 — "AI wrote this?"

The honest verdict. Would a careful reader — one of the four beta readers, a genre professional, a skeptic looking for proof — flag this passage as machine-written?

- If yes, rewrite. Do not argue with the verdict.
- The tells that trigger it: Tier-1 vocabulary (`tiers.md`), structural uniformity (`structural-caps.md`), over-explanation, symmetry, the absence of a voice.
- This test is judgment, not regex. It is the last gate the others cannot replace.

## How the tests map to the mechanical net

The post-write net (`check-prose-after-write.sh` / `prose_core.py`) catches the *mechanical* correlates of these tests — Tier-1/tier-2 vocabulary, em-dash density, burstiness, opener repetition, duplicated lines. The tests catch what the net cannot: whether the passage *works*. Run the net first (it is cheap and deterministic); run the tests after (they are the reason the net exists).
