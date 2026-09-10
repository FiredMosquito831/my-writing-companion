# Genre Profiles

Mechanism credited to Fablecraft; no source text copied. Changes: re-cast as a vellum numeric-genre reference; aligned with the genre resources in `creative-writing-craft/resources/genre/{fantasy,horror,litfic,mystery,romance,thriller}.md`. Critics and agents cite this file; agents reference the bands, never restate the numbers. The Obligatory scenes & conventions section below is credited to Shawn Coyne (*The Story Grid*) — ideas only; no source text copied.

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

## Obligatory scenes & conventions

Ideas-only: the obligatory-scenes-and-conventions concept is credited to Shawn Coyne (*The Story Grid*); no source text copied — every item below is rewritten as an original checkable question for vellum. This section carries only the checklist; the reader-expectation prose for each genre lives in `creative-writing-craft/resources/genre/<genre>.md` and is not duplicated here.

Obligatory moments are scenes that must happen **on the page** — dramatized, not reported. A genre moment summarized in a paragraph is a miss. Conventions are the reader's standing expectations; a book may consciously subvert one, but the subversion must be visible enough to name. All of it is advisory: the outliner checks these at outline time, the beta reader verifies dramatization before PASS, and the author may deliberately override any item.

### Fantasy

Obligatory moments:
- Does the story contain the scene where the extraordinary first irrupts into the ordinary — and the protagonist must choose to engage with it?
- Is the magic's cost paid on the page at least once before the climax depends on it?
- Is the protagonist's commitment to the central quest dramatized as a threshold scene, not narrated in retrospect?
- Is there a scene of earned wonder — a set piece that delivers the genre's core promise and could only happen in this world?
- Does the climactic confrontation turn on what the protagonist learned or became, not on power arriving unearned?

Conventions:
- A magic or power system with limits and costs, consistent when it returns.
- Worldbuilding delivered through action and consequence, not lecture.
- Stakes that scale from personal to world-level without losing the personal.
- A villain force embodied on the page — a face, a voice, or a presence the reader meets.

### Thriller

Obligatory moments:
- Is the inciting crime or act on the page, and does it signal a master villain at work — larger than the hero's ordinary problems?
- Is there a scene where the hero is at the mercy of the villain — physically, socially, or informationally — and the villain's full power is demonstrated?
- Is there a false ending — the apparent resolution near the close that turns out to be the villain's last move?
- Does the climactic confrontation resolve through something the story established earlier (a flaw in the villain's plan, a skill or truth the hero paid to learn)?

Conventions:
- A MacGuffin — the object, secret, or person both sides pursue — defined and driving the plot.
- Red herrings: misdirection that is fair on reread.
- Making it personal: the stakes shift from professional duty to the hero's own.
- A ticking clock: a deadline that converts every delay into loss.

### Mystery

Obligatory moments:
- Is the crime presented on the page (committed or discovered), so the puzzle is actually posed to the reader?
- Does the sleuth interview or confront at least one lying suspect on the page, with the lie load-bearing?
- Is each significant clue shown to the reader where the sleuth finds it — visible but not glowing?
- Is there a scene where the sleuth's working theory is falsified — a wrong accusation, a dead end — so difficulty is demonstrated?
- Does the solution scene walk the reader through the reasoning on the page, accounting for every clue planted?

Conventions:
- Fair play: every fact needed for the solution is available to the reader before it is revealed.
- Suspects with means, motive, and opportunity shown on stage.
- A sleuth with a distinctive method the reader can recognize.
- Misdirection that survives a reread without cheating.

### Romance

Obligatory moments:
- Is the first meeting of the central pair on the page — and charged (want, fear, restraint, or recognition)?
- Is there a scene where attraction is acted on — a kiss, a confession, an intimacy beat — that changes the relationship's terms?
- Is there a dark moment on the page: the scene where the relationship breaks under the internal conflict?
- Does a proof-of-change scene show one partner demonstrating the change the dark moment demanded, with a gesture costly to them?
- Does the ending land as an on-the-page scene establishing the committed state, not an inference?

Conventions:
- Internal conflict on both sides: each has a reason love seems impossible, and it is dramatized, not stated.
- An external obstacle or force pressuring the pair from outside.
- Chemistry carried in micro-gesture and dialogue, not asserted by narration.
- Emotional turning points dramatized in scene, never summarized.

### Horror

Obligatory moments:
- Is the first contact with the threat on the page, at reading pace — the moment the ordinary world cracks?
- Is there an escalating demonstration scene that partially reveals the threat's rules (what it can and cannot do)?
- Does the safe place fail — the haven, plan, or authority the characters trusted is destroyed on the page?
- Is there a moment of fullest visibility (or deliberate obscurity) of the threat, placed where it costs the most?
- Does the final confrontation turn on something established earlier — a rule, a cost, a weakness already shown?

Conventions:
- Dread before shock: anticipation scenes precede the violence or the reveal.
- Sensory wrongness over explanation; the unknown does the work.
- Isolation — physical, social, or epistemic — that removes easy exits.
- A price paid before the climax that proves the stakes are real.

### Literary fiction

Obligatory moments:
- Is there an inciting disturbance on the page — however quiet — that destabilizes the protagonist's self-understanding?
- Is at least one scene where interiority changes under pressure dramatized through perception and detail, not narrated as summary?
- Is there a scene where the protagonist's old coping visibly fails — the internal false belief meets evidence against it?
- Is the moment of changed understanding rendered in the world (action, image, gesture) rather than stated as thesis?
- Does the ending dramatize the changed (or deliberately unchanged) consciousness rather than announcing it?

Conventions:
- Interiority as the engine: pressure of consciousness carries the causality.
- Meaning carried through image and motif rather than plot mechanics.
- Voice itself as instrument — the telling is part of the story.
- Earned ambiguity: what is left unresolved is a choice, not an omission.

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
