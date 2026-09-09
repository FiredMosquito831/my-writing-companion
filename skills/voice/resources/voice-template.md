# Voice Template — `kb/styles/voice.md`

Mechanism credited to NousResearch/autonovel (`voice.md`); no source text copied. Changes: rewritten as a two-part fiction voice document; Part 2 scaffold fields re-derived and expanded; integrated with the measured-profile law and the drift/retune loop.

`kb/styles/voice.md` is the single source of a project's voice. The style-creator builds it during the voice-capture interview (`project-setup`) and refreshes it from author samples and author-edit harvesting. It has two parts.

## Part 1 — Guardrails (restated inline)

A short, self-contained restatement of the tier summary from `style-guardrails/resources/tiers.md` so a writer can draft against the guardrails without loading that skill. Include:

- The **measured-profile law**: caps adapt to `kb/styles/baseline.md`; the author's own rates override the bans.
- The **Tier-1 headline**: the five to ten words most toxic to *this* project's voice (drawn from the author's samples — the words the author never uses but the model reaches for).
- The **escape hatch**: `<!-- voice:skip -->` suppresses tier-1 debt for a chapter.

Part 1 is the same for every project; Part 2 is where this novel's voice lives.

## Part 2 — Identity scaffold

Discovered during the voice-capture interview, written as tendencies (not rules), and calibrated against exemplar passages throughout drafting. Every field below is a *lens*, not a constraint — fill only what the samples support; leave the rest marked "undetermined from current samples."

### Tone
The felt register of the prose. Not a genre label — a sensory description. Examples the style-creator might propose: "mythic and weighty, like stone tablets read aloud"; "spare and cold, sentences like knife cuts"; "warm and breathless, like a traveler talking by firelight." Anchored to a specific author sample.

### Sentence Rhythm
Tendencies, not rules. Where does the prose speed up, and where does it slow? "Long sentences for worldbuilding, short for violence." "Dialogue clipped; narration flows." Marked "undetermined" until the samples show a pattern.

### Vocabulary Register
The word-hoard for this world. Anglo-Saxon blunt, Latinate baroque, colloquial modern, a mix? What does this world *sound like*? Note recurring words the author reaches for and words the author conspicuously avoids.

### POV and Tense
Third limited, first, rotating, omniscient? Past, present, shifting for effect? Locked here so the writer and the continuity-checker (`pov:` frontmatter) agree.

### Dialogue Conventions
Tags ("said" only, action beats, none)? How do characters sound distinct from each other? Subtext rules — do characters say what they mean? Anchored to samples.

### Exemplar Passages
3–5 paragraphs that *are* the voice, written during the capture interview from the author's own prose. The tuning fork: the style-creator calibrates every chapter against these. Each passage is cited (source file + context) so it can be re-checked.

### Anti-Exemplars
3–5 paragraphs showing what this voice is *not*. Not the generic anti-slop list — specific to this novel. "This is too flowery for our tone." "This is too modern." "This explains what the narrator would show." These are the strongest signal the style-creator has, because knowing what a voice refuses is often clearer than knowing what it accepts.

## How the scaffold is used

- **Writer** loads Part 1 + Part 2 + one exemplar when drafting (slot 6 of the §9 context recipe).
- **Style-creator** runs drift checks (`drift-check.md`) every `drift_interval` chapters or on "this doesn't sound like me."
- **Critics** compare execution against the exemplars/anti-exemplars, not against the tier tables alone.
- **Blind-tag test** (`blind-tag-test.md`) falsifies whether the capture worked at all.

## Maintenance

The scaffold is a living artifact. It is refreshed from:
1. **Author samples** collected during `project-setup` (the foundation).
2. **Author-edit harvesting**: when the author edits an accepted chapter, the style-creator diffs the author's text against the prior agent draft (`work/drafts/`) and promotes characteristic choices into exemplars — the strongest available voice signal, free.
3. **Retune** (`retune.md`): when the author says the prose doesn't sound like them.
