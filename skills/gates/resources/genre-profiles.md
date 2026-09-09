# Genre Profiles

Mechanism credited to Fablecraft; no source text copied. Changes: re-cast as a vellum numeric-genre reference; aligned with the genre resources in `creative-writing-craft/resources/genre/{fantasy,horror,litfic,mystery,romance,thriller}.md`. Critics and agents cite this file; agents reference the bands, never restate the numbers.

Numeric genre truth the critics (and the muse, when briefing) reference. A judgment that a chapter is "too long" or "too talky" is meaningless without a genre band — a 6k-word thriller chapter and a 6k-word literary chapter are different events. This file sets the bands. It is a **judgment-layer reference**: the deterministic engine does not read it. `vellum wordcount` checks only each chapter's `word-target` ± `word_band` from `kb/project-config.json`; `vellum style stats` compares only against `kb/styles/baseline.md`. The author sets `word-target` per chapter (or `default_word_target` per project) with the genre band in mind; the critics apply this file's bands when scoring.

## The genres

Aligned with `creative-writing-craft/resources/genre/`: fantasy, thriller, mystery, romance, horror, litfic. A project may be a blend — pick the dominant genre for the bands, and note the secondary so critics weight the right axes.

### Fantasy
- **Chapter length**: 3,000–6,000 words (worldbuilding and set-pieces run long; epic fantasy toward the top).
- **Dialogue ratio**: 0.30–0.45 (narration-heavy; exposition and description earn their space).
- **Scene length**: 800–2,000 words; scenes often carry travel, discovery, or magic-system beats.
- **Pace note**: slower burn is genre-appropriate, but clock-drift and prop-custody are unforgivable — the world's internal logic is the contract.

### Thriller
- **Chapter length**: 2,000–4,000 words (short, propulsive; cliffhangers earn shorter).
- **Dialogue ratio**: 0.35–0.50 (interrogations, confrontations, reveals).
- **Scene length**: 600–1,500 words; tight, goal-conflict-disaster.
- **Pace note**: pace is the primary axis. Sags are MAJOR. Put-down points in the first three chapters are disqualifying.

### Mystery
- **Chapter length**: 2,500–4,500 words.
- **Dialogue ratio**: 0.40–0.55 (interviews, alibis, deduction).
- **Scene length**: 700–1,500.
- **Pace note**: information control is the contract. Clues must be visible but not glowing; fair play is non-negotiable.

### Romance
- **Chapter length**: 2,500–5,000 words.
- **Dialogue ratio**: 0.45–0.60 (the relationship is carried in dialogue and gesture).
- **Scene length**: 700–1,600.
- **Pace note**: emotional legibility is the primary axis. Micro-shifts in want/fear/restraint/recognition matter more than plot velocity.

### Horror
- **Chapter length**: 2,000–4,500 words (anticipation does the work; shorter often stronger).
- **Dialogue ratio**: 0.25–0.40 (silence and sensory wrongness over explanation).
- **Scene length**: 600–1,400.
- **Pace note**: dread over shock. Explaining the threat too early is a common failure mode; the unknown is the instrument.

### Literary fiction
- **Chapter length**: 2,000–5,500 words (wide range; sentence-level necessity over velocity).
- **Dialogue ratio**: 0.30–0.50.
- **Scene length**: 600–2,000.
- **Pace note**: perception and pressure of consciousness are the primary axes. "Slow" is not a flaw if every sentence changes attention or understanding.

## How the bands are used

- **Critics and the muse** cite the genre band when scoring structure/pace and when setting or reviewing `word-target` — a "slow" chapter in a thriller is a finding; the same chapter in litfic may be exactly right.
- `vellum wordcount` stays mechanical: it checks each chapter against the per-chapter `word-target` (or `default_word_target`) ± `word_band` from project-config. It does not read the genre; choose targets that sit inside the genre band when you record them.
- `vellum style stats` compares measured rates against `kb/styles/baseline.md`, not the genre bands; critics read the stats output against the dialogue-ratio bands above.
- The genre is recorded in `kb/story.md` (or the project's CLAUDE.md). If no genre is set, critics fall back to the project's own baseline and say so in the review.

## Cross-genre constants

Some things do not vary by genre and are never excused by it:
- Frontmatter completeness (`frontmatter:incomplete`).
- Continuity errors (dead-character reappearances, promise ordering, knowledge anachronism, prop custody).
- Truncation/refusal/placeholder markers.
- Clock non-monotonicity.

Genre adjusts the *bands*; it does not adjust the *invariants*.
