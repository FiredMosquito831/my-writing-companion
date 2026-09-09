<!-- Adapted from oh-story-claudecode (skills/story-long-write, state-card design) — MIT. Changes: rewritten in English for vellum's fixed 7-section layout; skeleton only — the engine writes the real card. -->

# State Card (skeleton)

Machine-authoritative: `vellum state rebuild` generates the real file at `state/state-card.md` from `kb/` + `manuscript/` + ledgers. **Never hand-edit it** — the hash check flags hand edits (`state:hand-edited`) and `state rebuild` repairs. Hard cap 12 KB; if content overflows, the engine refuses and reports. This skeleton documents the fixed 7-section order the engine emits; fill nothing here. Placeholders in `<angle brackets>`.

## Story position
<2–4 lines: where the book is — current chapter, arc position, the pressure in play, what the next chapter must do>

## Open promises & questions (top N by age)
<oldest first; id, one-line state, target-by if set>
- <promise-… — planted ch NN; unfired past target-by ch NN>
- <question-… — raised ch NN; open>

## Active cast state (one line each)
<one line per live character: name — status, want, last state change>
- <character-… — alive; want: …; last changed ch NN>

## Knowledge boundaries
<who knows what that could be misused — facts with limited holders, as of the last accepted chapter>
- <character-… knows <fact> as of ch NN; does NOT know <fact>>

## Props & clock
<prop custody one-liners; clock threads with readings>
- <prop-… — holder/location, status (last confirmed ch NN)>
- <thread — position as of ch NN; clock reading>

## Next beats with word quotas
<this chapter's beats, quota each, POV, `verbatim:` lines owed>
1. <beat — quota NNN — POV …>

## Flags
<exemptions digest (active keys + one-line reasons); do-not-re-explain register; pivotal chapters awaiting blind artifacts; `<!-- voice:skip -->` chapters>
- <flag>
