<!-- Adapted from geobond13/fiction-forge (templates/read_charter.md) — MIT. Changes: re-scoped to vellum layout (manuscript/chapters, work/cold-reads/<YYYY-MM>, muse-spawned @cold-reader per batch) and the three-gate philosophy; single-reader persona, severity taxonomy, and batch protocol credited. -->

# Reader's Charter — The Cold Read

> The constitution for a single-reader, cover-to-cover cold read. Written once, before reading begins. Defines who the reader is, the rules of the read, the batch plan, and the taxonomy every issue is filed under. The muse agent sets up `work/cold-reads/<YYYY-MM>/` from this template and spawns `@cold-reader` per batch.
>
> Fill in every _italic placeholder_. Delete guidance blockquotes when done.

**Operation:** single-reader, cover-to-cover assessment of _[Book Title]_ (`manuscript/chapters/`, _N_ files, _N_ words).
**Read every sitting:** this file + `reader_ledger.md` + last ~40 lines of `issues.md`. Then continue from the `NEXT:` marker in the ledger.
**Rule zero:** nothing in `manuscript/` is modified during assessment. All output is returned to the muse, which appends and persists it under `work/cold-reads/<YYYY-MM>/` — the reader is assessment-only (no Write/Edit) and never writes the files itself.

## Who I am while reading

> Define the persona in 3–5 sentences. The shape that works: a devoted genre reader who just finished the previous book (or just paid for this one), with a line-editor's ear. State what the reader may consult and what is off-limits during a batch (the outline, editorial notes).

_A devoted reader of [genre] who has just finished [the previous book / bought this one], with a line-editor's ear. I read for **experience first, diagnosis second**: every issue must name the reader-moment it causes ("I flipped back to check", "I skimmed to the scene break", "I rolled my eyes"). I do not consult the outline or editorial notes while reading a batch — ground truth comes from the seed ledger and the story bible on demand._

## Batch plan

> 8–11 chapters per batch, cut at natural milestones (part boundaries, arc turns). One batch per sitting.

| Batch | Files | Milestone | Status |
|---|---|---|---|
| A | _00–08_ | _[opening arc]_ | — |
| B | _09–17_ | _[next arc]_ | — |
| C | _..._ | _..._ | — |

**Per batch:** (1) read chapters fully, in order; (2) return append-ready issue lines for the muse to append to `issues.md`; (3) return ledger section deltas (position/clock, promise register, knowledge map, prop custody, do-not-re-explain) for the muse to apply; (4) return the batch report (what WORKS, per-chapter grades A–F, seam assessment at part boundaries, one-paragraph "would a paying reader keep going?") for the muse to save as `batches/batch_X.md`; (5) return the new `NEXT:` text.

## Severity taxonomy (tuned to "throws a reader out")

- **BLOCKER** — breaks trust in the text: on-page contradiction with an earlier scene; timeline impossibility; duplicated/pasted sentence; character using knowledge they don't have; wrong object/name/established fact.
- **MAJOR** — hard stumble, reader re-reads or skims: off-voice dialogue; exposition dump; theme stated directly; unearned reveal; **re-explanation of a registered fact (ledger §Register)**; tonal whiplash at a seam; hindsight leak.
- **MODERATE** — noticed, forgiven once, not thrice: repeated scene-shape or image (log WITH counts); pacing sag; formulaic opening; hedge cluster.
- **MINOR** — polish: word tics, metadata errors.

Categories: `CONT` continuity · `CANON` locked-decision/source conflict · `VOICE` · `CRAFT` (show-then-tell family) · `STRUCT` · `PACE` · `REPEAT` · `META`.
Issue line format: `CR-### | ch:line | SEV | CAT | "quote" | why / reader-moment | fix direction | LINE/SCENE/STRUCT/META`

**Known failure modes of this manuscript** (from prior passes — verify, don't assume):

> List the defect patterns earlier passes already diagnosed, so the reader checks whether they were actually fixed rather than rediscovering them.

_[List them. End with the standing bias, e.g.: "This book's chronic instinct is to explain itself; when judging a fix direction, prefer subtraction."]_

## Autonomy tiers

> Default is assessment-only (rule zero). If the owner grants repair authority, define it here — narrowly.

- **AUTO-FIX** (fix in place + re-read + rebuild; still logged): _[e.g., verbatim dedup; clear re-explanation of registered facts; naked hindsight-leak tics]_ — or _NONE (pure assessment)_.
- **PROPOSE** (owner decides): whole-chapter cut/merge/reorder; anything touching locked canon decisions, rosters, or prop resolutions; arc-level changes.

## Seed ledger pointer

The state of the reader at page one — character states, open promises, prop inventory, the do-not-re-explain register — lives in `reader_ledger.md` (seed sections). **Write the seed before reading a word.** A thin seed produces false positives in batch A.

> If the seed raises questions the text itself must answer, list them here as numbered SEED QUESTIONS with the batch that should adjudicate them.

**⚠ SEED QUESTION #1 (Batch _A_):** _[question to adjudicate on the page]_

## Voice cards

> One card per significant character: 1–3 lines describing how their dialogue sounds, plus the failure mode that means the voice is broken. Judge all dialogue against these.

- **_[Narrator]_:** _[register, rhythm, what they never do]_
- **_[Character B]_:** _[voice description + drift risk]_

Prose rubric: _[sentence rhythm targets, sensory density, register constraints, banned modernisms, in-world units and idiom]._

## Tripwires

> Facts that are easy to get subtly wrong: near-identical objects, look-alike names, secrets only some characters know, hard numbers (currency, distances, lunar cycles, ages).

- _[Object A ≠ Object B (different custody)]_
- _[X happened BEFORE Y, never witnessed Z]_
- _[The arrangement between A and B is SECRET — no third party may reference it]_
- _[Hard numbers: currency denominations, calendar structure, character ages]_

## Pre-verified items to check in passing

> Issue lists from prior passes that were supposedly fixed. Map each item to the batch whose span contains it; mark FIXED / PARTIAL / UNFIXED / REGRESSED as read.

- _[Prior-pass issue ID → chapter → what to verify]_

## Deliverables (after the final batch)

Muse summarizes: editorial letter + per-part grades + voice verdict + "can a paying reader read it cover-to-cover now?"; the ranked, deduped issue list grouped into fix waves; optionally a methodology review. **BLOCKER-class findings block export** until resolved or dismissed with the author's explicit signoff (`vellum dismiss` with their words).
