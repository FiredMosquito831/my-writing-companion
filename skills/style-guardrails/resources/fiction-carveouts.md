# Fiction Carveouts

<!-- Adapted from hardikpandya/stop-slop + conorbronsdon/avoid-ai-writing — MIT. Changes: this file is the fiction filter applied to those nonfiction-tuned lists; the exemption rubric is written fresh for fiction; no source text copied. -->

Attribution: supplemental lists in `tiers.md` and `structural-caps.md` draw on `hardikpandya/stop-slop` (MIT) and `conorbronsdon/avoid-ai-writing` (MIT), both of which are tuned primarily for nonfiction and business prose. This file is the filter that keeps the mechanical net from flattening fiction voice. Changes: exemption rubric written fresh for fiction; no source text copied.

Stop-slop's rules assume the text is an argument. Fiction is not an argument. A rule that improves an essay can destroy a novel: fictional narrators lie, hedging can be a *voice*, and "would a reader think AI wrote this?" is answered differently for a first-person teenage narrator than for a neutral omniscient one.

## When a "tell" is a voice

Exempt a flagged pattern when it is **deliberate voice register**. The test is not "does the pattern appear" but "does the pattern characterize":

- **Unreliable-narrator diction**: a narrator who hedges, embellishes, or contradicts is *supposed* to. "I did not look back" as a tic of denial is character work; the same sentence in five narrators' mouths is slop.
- **Period dialogue**: "It's not that I'm afraid — it's that I know the cost" is how a 19th-century gentleman *talks* in fiction. Binary contrasts, balanced antithesis, formal constructions — all period-accurate. Do not flag in dialogue.
- **Regional / class register**: adverbs, intensifiers ("really," "just," "literally"), and filler in dialogue can be exactly how the character speaks. Stop-slop's "kill all adverbs" is a *narration* rule; dialogue is exempt where the voice earns it.
- **Close psychic distance**: deep-POV narration shares the character's diction — fragments, present-tense immediacy, "your collar, your miserable soul" (Gardner's rung 5). What looks like a "subjectless fragment" is often the dial turned all the way down. See `creative-writing-craft/resources/psychic-distance.md`.
- **Stylized narration**: hard-boiled staccato, lyrical long sentences, irony that leans on "not X, but Y." If the *voice resource* (`kb/styles/voice.md`) names it as a tendency, it is protected.

The distinguishing question: **would the author defend this as intentional?** If yes — and the author's word is the ground truth (GR-09) — it is not a finding. If the pattern appears in narration that has no characterized narrator, it is a finding.

## The mechanical net's escape hatch

`<!-- voice:skip -->` anywhere in a chapter suppresses tier-1 debt accrual for that chapter. Use it when the chapter's register legitimately trips the tables (period piece, narrator voice exercise, epistolary chapter). The net still logs structural caps (duplicated lines, truncation markers) — those are errors, not voice.

## What the carve-outs never excuse

Some things are *never* voice, because no storyteller would defend them:

- **Truncation markers, model-refusal phrases, placeholder text** (`[TODO`, `[INVENTED]`, `[VERIFY]` left in an accepted chapter) — process artifacts, not prose.
- **Verbatim or near-verbatim duplicated lines** — revision accidents.
- **Tier-1 slop in *narration*** at rates far above the author's measured baseline — the measured-profile law exists so the author's own register is never flagged, not so slop rides along with it.
- **Structural slop applied to the book as a whole**: every chapter ending the same way, every scene the same shape, every character speaking in the same balanced antithesis. Uniformity across chapters is not voice; it is the machine's fingerprint.

## Dismissal, not deletion

When the author declares a flagged pattern intentional, the finding is *dismissed* (keyed `<category>:<entity_id>`, via `vellum dismiss`), not deleted. The net stops raising it; the exemption records the author's words. If the underlying fact later changes (voice profile re-measured, narrator rewritten), the exemption goes `stale` and re-arms once — the author re-decides. See `story-ledgers/resources/ledger-files.md` for the exemption format.
