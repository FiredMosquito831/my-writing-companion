# Character Dialogue Profiles

<!-- Mechanism credited to quotation-attribution and speaker-identity stylometry research (Michel et al. 2024; Yang et al. 2024; Brei et al. ACL 2026 — see "Research grounding" below); ideas only — no source text or code copied. Changes: adapted as the per-character analog of the author-voice blind-tag test for the vellum voice loop; procedure written fresh. -->

The author-voice blind-tag test (`blind-tag-test.md`) asks whether the AUTHOR'S
voice transferred to the agents. This resource covers the OTHER half of the
same LLM failure mode: characters whose dialogue is indistinguishable from each
other's. The mechanical side is `style stats --dialogue` (per-speaker stats +
pairwise convergence flag); the procedural side is the ~70% per-character blind
attribution test. Both are report-only — findings are suggestions, never gates,
and the measured-profile law (`voice-profile.md`) outranks any mechanical
homogenization flag.

## What it is

A per-character analog of the blind-tag test. For the author, you shuffle
corpus/manuscript passages and see whether a naive reader can tell them apart.
For characters, you strip attribution from a mixed-character scene batch and
see whether a naive reader can name the speaker. Same isolation discipline,
lower threshold.

## The character-page dialogue profile

A dialogue profile is an *optional* body section of a `kb/characters/<id>.md`
page, drafted by `@character-sim` when the page is created and kept in sync by
`@style-creator` / `@kb-lead` as the character's voice shifts. It lives in the
body, not the frontmatter — the engine's frontmatter schema stays fixed.
Skeleton (also in `templates/character.md`):

```markdown
## Dialogue profile

- idiolect-markers: <3-6 checkable habits; what the character never says
  matters as much as what they always say>
- preferred-deflections: <how they dodge direct questions — deflect with a
  question, answer a different one, go silent, joke>
- sentence-length-signature: <typical range, e.g. "clipped: 3-9 words; one
  long sentence only when they are lying">
- top-tokens: <from `style stats --dialogue` output — measure first, then
  tune; never prescribe unmeasured tics>
```

The profile is *descriptive*, not prescriptive: it records what the character
actually does on the page so the simulation and the critics have a target to be
checked against. A character whose measured stats contradict the profile is
either growing or the prose drifted — update the profile rather than forcing
the prose to fit a stale description.

Built by `@character-sim` during setup because the sim is the agent that
inhabits the character; reviewed by the critic because the critic is the agent
that hears the voice from the outside.

## The per-character blind attribution test

### The procedure

1. **Build the deck.** The muse (or style-creator) selects 10–16 dialogue
   lines of similar length (6–40 words each) from a chapter or batch where the
   relevant characters actually speak to each other — scenes where they are
   already in proximity are the hardest, and therefore the most informative.
   Half the lines come from the character you most suspect is being absorbed
   by the group voice. Include 2–3 lines from a different chapter than the rest
   so "sounds like the ch. 5 speaker" is not a cheap signal.
2. **Strip ALL attribution.** Remove dialogue tags, action beats that name
   the speaker ("She set the cup down."), and any surrounding narration that
   names a character. The reader must work from the words alone. Replace names
   *inside* the speech with `<name>` placeholders so "Mira" vs "Mira, Mira..."
   is not the tell. Shuffle. Strip chapter/draft metadata.
3. **Spawn a fresh reader.** A `@critic` with **no project context** — no
   outline, no kb, no style files, no voice.md, not even `kb/story.md`. The
   only inputs are the deck and the cast list for the scene (names + one-line
   role, so the reader has a set to attribute TO). Same isolation discipline
   as the blind-tag test (`blind-tag-test.md`): if the muse cannot honestly
   spawn it without leaking project context, the test is void.
4. **Attribute.** For each line the reader names the speaker (from the cast
   list) and gives one line of evidence.
5. **Score.** Count correct attributions per character, and overall.

### The threshold

**Below ~70% correct attribution = a homogenization finding** (severity
`suggestion`, key `voice:dialogue-convergence-<a>-<b>` — the same key the
mechanical convergence flag emits, never a gate). The
complementary rule holds too: a character whose lines the reader attributes to
*another* character at above-chance rate is the one being absorbed — that
direction matters for the retune brief.

- >= 70% overall: the characters are distinct enough to pass unaided. Note
  the score and date in the affected character page's dialogue profile.
- 55–70% overall: marginal. Run the retune brief on the character with the
  lowest per-character rate; the evidence lines from the test are the brief.
- Below 55%: the characters are functionally the same voice. The measured
  profile (`voice-profile.md`) has the strongest signal — use it to rebuild
  the absorbed character's idiolect markers and re-sim.

### Confidence note

The ~70% threshold is a floor for a 10–16 line deck at the stated length.
Casts of 2 characters have a higher chance baseline (50%) than casts of 4+
(25%); small decks widen the confidence band. Treat the band, not the point.
The mechanical convergence flag (below) lowers this to a check on a signal the
metrics can already see — it is the trigger, the blind test is the verdict.

## The mechanical companion

`style stats <file|glob> --dialogue` implements the mechanical half:

- Parses BOTH dialogue conventions: dash-introduced lines (`— …`) and quoted
  speech (straight `"…"` and curly `"…"`/`"…"`).
- **Speaker attribution is nearest-narration ONLY:** a speech-verb tag inside
  the dialogue paragraph, else the nearest narration paragraph naming exactly
  one cast member. Lines the metric cannot attribute are excluded from
  per-speaker stats and reported as an `unattributed` count — never guessed,
  never attributed to "whoever is nearby".
- Per-speaker stats: attributed line count, word count, mean utterance length,
  type-token ratio, top idiolect tokens (with the stopword table below
  excluded).
- **Pairwise convergence flag:** when two named characters both have >=
  8 attributed lines AND both the mean-utterance-length delta AND the TTR
  delta sit at/below the convergence deltas, emit a suggestion finding
  (`voice:dialogue-convergence-<a>-<b>`). Report-only; convergence flags never
  auto-block and are dismissed through the same exemption protocol as any
  other finding — the author's measured profile always wins.

The convergence deltas are defaults (mean-utterance delta <= 1.0 word, TTR
delta <= 0.05). They are a tripwire, not a standard — a character whose
idiolect genuinely clusters tight is the author's choice.

## When to run

- When a character page is first created (build the dialogue profile from the
  sim's first pass, then verify with the mechanical stats).
- After any chapter where a character speaks a lot — the mechanical stats are
  cheap; run them every chapter in the character's presence.
- When a critic flags homogenization in the `prose-critique/voice.md`
  "Character Simulation Distinction" lens — run the mechanical stats first to
  quantify, then the blind test to confirm before editing.
- When the blind-tag test passes but the book still "sounds samey" — the
  author voice transferred, but the characters didn't.

## Interpretation notes

- The reader's evidence lines matter more than the score. *Which* lines were
  misattributed, and what told them apart, is the retune brief.
- If the reader attributes a character's lines to the SAME character but
  consistently on the wrong-chapter lines, the idiolect shifts between chapters
  — that's drift, not homogenization; use the drift-check loop instead.
- The sim (`@character-sim`) is your strongest discovery tool: ask it to speak
  as the absorbed character across three emotional registers. If the three sound
  alike, the character has one gear, not three — rebuild the deflections and
  the tic table before touching the prose.

## Research grounding

- Michel et al. 2024 — quotation attribution via stylometry: speakers are
  recoverable from the surface statistics of their own speech across a corpus.
- Yang et al. 2024 — speaker-identity drift when a role-played LLM juggles
  multiple named speakers in one context.
- Brei et al. ACL 2026 — reduced lexical variety in character dialogue in
  LLM-generated fiction relative to human-written baselines.

Mechanisms credited; no source text or code copied.
