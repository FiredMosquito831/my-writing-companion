# The Blind Tag Test

Mechanism credited to Fablecraft/Scriptorium; no source text or code copied. Changes: re-cast as a falsifiable voice-capture check for the vellum voice loop; procedure written fresh.

Voice capture is the foundation everything else stands on — exemplars, baseline, drift checks. If the capture failed (wrong samples, wrong reading of them), every downstream artifact is confidently wrong. This test makes failure *visible* instead of assumed-good.

## What it is

A falsifiable check that voice capture worked: shuffle author-corpus passages with manuscript passages, tags stripped, and have a fresh reader sort them. If the reader cannot tell which is which, the voice has transferred. If they can, the capture failed.

## The procedure

1. **Build the deck.** The style-creator (or muse) selects 10–14 passages of similar length (150–300 words): half from the author's corpus (`kb/samples/` + author-edited passages the style-creator harvested), half from manuscript chapters the agents drafted. Shuffle and strip all identifying metadata — no filenames, no chapter numbers, no dates.
2. **Spawn a fresh reader.** A `@critic` with **no project context**: no outline, no kb, no style files, no voice.md. The only input is the deck. (If muse cannot honestly spawn it without leaking project context, the test is void — same discipline as the blind read.)
3. **Sort.** The reader tags each passage "author" or "manuscript," with one line of evidence per passage.
4. **Score.** Count correct attributions.

## The threshold

**< 75% correct attribution = voice capture failed.** Redo the exemplars: re-interview, re-harvest author edits, rebuild `kb/styles/voice.md` Part 2 and re-measure `kb/styles/baseline.md`. (Chance is 50%; a *failed* capture means the manuscript's voice is distinguishable — usually because it is smoother, more uniform, or more "correct" than the author's.)

At or above 75%: the capture holds. Note the score and date in `kb/styles/voice.md` frontmatter so the next drift check can compare.

## When to run

- After the initial voice-capture interview (once).
- After any major retune (`retune.md`).
- When drift checks keep flagging the same axis and the style-creator suspects the baseline, not the prose.

## Interpretation notes

- The reader's evidence lines matter more than the score: *which* passages were misattributed, and what told them apart, is the retune brief.
- If the reader attributes author passages to the manuscript, the manuscript is out-writing the author's register — check whether the samples were unrepresentative (early drafts, different genre) before touching the manuscript.
- A fresh reader is required every run. Reusing a reader who has seen the corpus biases the sort.
