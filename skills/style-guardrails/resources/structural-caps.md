# Structural Caps

Mechanism credited to NousResearch/autonovel (`ANTI-PATTERNS.md`); no source text copied. Detector-mechanics taxonomy rewritten for fiction; the machine-readable categories are implemented in `prose_core.py`, adapted from `conorbronsdon/avoid-ai-writing/detector/patterns.js` (MIT). Changes: re-cast as a fiction-prose structural-cap reference; numeric thresholds tuned to the measured author profile (`voice/resources/voice-profile.md`); caps adapt to `kb/styles/baseline.md` rather than judging the author's voice a violation.

These are the numeric and structural thresholds for fiction prose. Some are **net-enforced** mechanically (`prose_core.py` implements: tier-1 vocabulary, filler, tier-2 clusters-of-three, em-dash density, near-verbatim duplicated lines); the rest are **judgment-layer diagnostics** — critics apply them by reading, and the report-only metrics (`vellum style stats`: burstiness, opener variety, paragraph entropy) measure where applicable. Every cap is a *default* — the measured-profile law (`tiers.md`) overrides any cap that conflicts with the author's own rates.

## Em-dash density

- Default cap: ~2 em-dashes per 1,000 words (the `prose_core.py` default; the net flags above it as advisory). For a dash-light voice, the author sets a tighter target and the critics hold the prose to it — the engine's floor stays at the default.
- Carve-out: an em-dash acting as the separator in a bulleted/numbered list item that opens with a bolded lead term or a markdown link (`- **Term** — description`) is typography, not a prose splice — it does not count toward the rate.
- Measured override: if `kb/styles/baseline.md` carries an em-dash rate, the net's cap adapts to the author's measured rate × 1.25 (a 4/1k author is flagged only past 5/1k).

## Hedges per page

- Default: one hedge cluster per page, max. Hedge words: *may, might, could, possibly, perhaps, it seems, one might*.
- Stacked hedges ("may potentially", "could possibly") count double.
- Measured override: author baseline + band.

## Sentence-length variance (burstiness)

- Measured as coefficient of variation (sd/mean) of sentence lengths. Human prose is bursty — short punchy sentences mixed with long winding ones.
- A flat band (every sentence 15–25 words) is the signature of synthetic prose. **Judgment-layer metric**: `vellum style stats` reports burstiness as a number; the net does not flag it. Critics read the report against this cap.
- Floor: flag *low* variance, never high — varied rhythm is the goal.

## Consecutive paragraph-opener repetition

- Three or more consecutive paragraphs opening with the same construction (transition word, "And", "But", wh- word, or identical grammatical shape) → a judgment-layer finding (opener *variety* is a report-only metric in `vellum style stats`; the net does not flag it).
- The fix is to vary openings: subject, action, dialogue, sense detail, temporal anchor.

## Paragraph-length uniformity

- Three or more consecutive paragraphs of similar length → a judgment-layer finding. Vary deliberately: some one-sentence paragraphs, some longer. (Paragraph-shape entropy is reported by `vellum style stats`; no net detector exists for this cap — the critic's read is the instrument.)

## Negative-setup / positive-flip sentence shape

- The "not X — it's Y" / "not just X, but Y" construction. Max one per piece unless it serves the argument; the multi-negation countdown ("It's not the price. It's not the features. It's the trust.") is the same move inflated.
- Split-sentence form (negation and correction in two separate sentences) is flagged the same way.

## Triadic listing

- AI defaults to groups of three. More than two triadic fragments / three-item "and" joins per chapter is a pattern. **Judgment-layer cap** — no net detector; the critic counts. Vary: two items, four, a full sentence.

## Negative-assertion repetition

- "He did not look back." / "He did not think about..." — one per chapter is fine; five is a tic. **Judgment-layer cap** (net checks near-verbatim duplicated lines only). Replace with active alternatives or cut.

## Simile crutch

- "the way X did Y" used 4–8 times per chapter. Max ~2 per chapter; vary the construction ("like", direct metaphor).

## Section-break as rhythm crutch

- A chapter with 5 "---" breaks is 5 vignettes, not a chapter. Max ~2 per chapter, for genuine time/location jumps.

## Predictable emotional arcs

- Beats arriving exactly on the outline's schedule with no deviation. The fix: one moment per chapter that surprises — a character saying the wrong thing, an emotion arriving early, a beat that interrupts another.

## Repetitive chapter endings

- No two chapters end with the same structural move. Each ending belongs to that chapter specifically.

## Balanced antithesis in dialogue

- "I'm not saying X. I'm saying Y." / "Not X, but Y." / "There's a difference." — if multiple characters share this sentence structure, they are not distinct.

## Dialogue as written prose

- Characters speaking in complete, polished sentences with no false starts, interruptions, trailing off, or slightly-wrong words. At least one imperfect line per scene.

## Scene-summary imbalance

- 70%+ of each chapter should be in-scene (moment by moment, with dialogue and action). Summary is for time compression only.

## Over-explain (the #1 structural problem)

- The narrator restating what a scene already showed. After every emotional beat, check: does the next paragraph explain what just happened? If yes, cut it. If a scene shows it, the narrator does not say it.

## Cataloging-by-thinking

- "He thought about X. He thought about Y. He thought about Z." → replace with the thought itself as a fragment, a physical action, or dialogue. Real interiority is messier.

## The treadmill test (information density)

- Read each paragraph and ask "what's actually new here?" If you could cut 40–60% and lose no information, the structure itself needs rewriting, not patching.

## The paragraph-reshuffle test

- Can you swap two body paragraphs without breaking the piece? If the order doesn't matter, you've written a list of points, not an argument that builds. Each paragraph should depend on the one before it.
