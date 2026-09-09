# Cold-Read Charter

Adapted from `fiction-forge/templates/read_charter.md` + `fiction-forge/docs/cold-read.md` — MIT. Changes: re-scoped from `book/` + `editorial_notes/` to the vellum layout (`manuscript/chapters/` + `work/cold-reads/<YYYY-MM>/`); folded the seed-ledger pointer, voice cards, tripwires, and autonomy tiers into the vellum project conventions; protocol credited.

The charter is the constitution for a single-reader, cover-to-cover cold read. Written once, before reading begins. It defines who the reader is, the rules of the read, the batch plan, and the severity taxonomy. Put it at `work/cold-reads/<YYYY-MM>/charter.md`.

## Operation

Single-reader, cover-to-cover assessment of the manuscript (`manuscript/chapters/`, N files, N words). **Read every sitting:** this file + `reader_ledger.md` + the last ~40 lines of `issues.md`. Then continue from the `NEXT:` marker in the ledger. **Rule zero:** nothing in `manuscript/` is modified during assessment — all output is returned to the muse, which appends and persists it under `work/cold-reads/<YYYY-MM>/`. The reader is assessment-only (no Write/Edit); the read is a measurement, and if the instrument edited the thing it measures, the measurement would be worthless.

## Who I am while reading

A devoted reader of the genre who has just finished the previous book (or, for a standalone, a paying reader who just bought this one), with a line-editor's ear. Reads for **experience first, diagnosis second**.

Two rules follow from the persona:

- **Every issue must name the reader-moment it causes.** "I flipped back to check." "I skimmed to the scene break." "I rolled my eyes." An issue that can't name its reader-moment probably isn't one.
- **No peeking.** The reader does not consult the outline, fix history, or editorial notes while reading a batch. Ground truth comes from the seed ledger, `kb/` on demand, and targeted searches of source texts — the same resources a very careful fan would have.

## Batch plan

8–11 chapters per batch, cut at natural milestones (part boundaries, arc turns). One batch per sitting; a full novel is 10–13 sittings.

| Batch | Files | Milestone | Status |
|---|---|---|---|
| A | 00–08 | opening arc | — |
| B | 09–17 | next arc | — |

Per batch: (1) read chapters fully, in order; (2) return append-ready issue lines for the muse to append to `issues.md`; (3) return ledger section deltas (position/clock, promise register, knowledge map, prop custody, do-not-re-explain) for the muse to apply; (4) return the batch report (what WORKS, per-chapter grades A–F, seam assessment at part boundaries, one-paragraph "would a paying reader keep going?") for the muse to save as `batches/batch_X.md`; (5) return the new `NEXT:` text. The muse appends and persists — the reader returns deltas and never writes the files itself.

## Severity taxonomy (tuned to "throws a reader out")

- **BLOCKER** — breaks trust: on-page contradiction with an earlier scene; timeline impossibility; duplicated/pasted sentence; character using knowledge they don't have; wrong object/name/established fact.
- **MAJOR** — hard stumble; the reader re-reads or skims: off-voice dialogue; exposition dump; theme stated directly; unearned reveal; **re-explanation of a registered fact**; tonal whiplash at a seam; hindsight leak.
- **MODERATE** — noticed, forgiven once, not thrice: repeated scene-shape or image (log WITH counts); pacing sag; formulaic opening; hedge cluster.
- **MINOR** — polish: word tics, metadata errors.

Categories (orthogonal to severity): `CONT` continuity · `CANON` locked-decision/source conflict · `VOICE` · `CRAFT` (show-then-tell family) · `STRUCT` · `PACE` · `REPEAT` · `META` (files, titles, front-matter).

Issue line format: `CR-### | ch:line | SEV | CAT | "quote" | why / reader-moment | fix direction | LINE/SCENE/STRUCT/META`

## Autonomy tiers

Default is assessment-only (rule zero). If the owner grants repair authority:

- **AUTO-FIX** (fix in place + re-read + rebuild; still logged): verbatim/near-verbatim duplicated sentences; clear re-explanation of a registered fact; naked hindsight-leak tics that add nothing.
- **PROPOSE** (log; owner decides): whole-chapter cut/merge/reorder; anything touching locked canon decisions, rosters, or prop resolutions; arc-level changes.

The line between tiers is *reversibility plus judgment*: if a fix could plausibly be wrong, or interacts with anything outside the sentence it touches, it is PROPOSE.

## Voice cards and tripwires

One voice card per significant character (1–3 lines: how their dialogue sounds + the failure mode that means the voice is broken). Tripwires: facts easy to get subtly wrong (near-identical objects, look-alike names, secrets only some characters know, hard numbers — currency, distances, ages). The reader checks these in passing, every batch. PROTECT list: deliberate ambiguities and unreliable-narrator devices — but the device never excuses mechanical errors in seasons, ages, or inventories.

## Deliverables (after the final batch)

Assembled by the muse from the batch reports (the reader returns deltas only): a verdict document (editorial letter + per-part grades + voice verdict + "can a paying reader read it cover-to-cover now?"), a deduped ranked issue list (severity × effort, grouped into fix waves), and optionally a methodology review (what only this read could catch; what the standing QA loop should become).
