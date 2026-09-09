# Cold-Read Batching

Adapted from `fiction-forge/docs/cold-read.md` §Batching + `fiction-forge/templates/batch_report.md` — MIT. Changes: re-scoped to the vellum layout (`work/cold-reads/<YYYY-MM>/batches/`); the 8–11-chapter batch size and per-sitting recipe kept verbatim; integrated with the vellum cold-read command (`/vellum:cold-read`) and the subagent orchestration in the skill.

Batching is what makes a cover-to-cover read sustainable across sittings — and across context windows when the reader is a subagent. One batch per sitting; the ledger is the only state that carries between them.

## Batch size and cutting

- **8–11 chapters per batch.** Smaller than a full book (no single sitting can hold a 290k-word manuscript in context), larger than a chapter (the reader needs to carry cross-chapter state to find clock drift, prop custody, promise bookkeeping — the defect classes that survive per-chapter QA).
- **Cut at natural milestones**: part boundaries, arc turns, time jumps. Never cut mid-arc — the reader loses the thread's heat.
- **One batch per sitting** is the sustainable pace. A full novel is 10–13 sittings.

List the batches in the charter (`work/cold-reads/<YYYY-MM>/charter.md`) with a status column; mark complete as each is read.

## The per-sitting recipe

This is the entire resume state — what makes the protocol work across sessions:

```
Read: the charter + reader_ledger.md + the last ~40 lines of issues.md.
Then continue from the NEXT: marker in the ledger.
```

That is everything. The ledger *is* the reader's memory; if it is updated honestly every batch, any sitting — human or subagent, today or next month — picks up exactly where the last one left. This is also why ledger discipline is non-negotiable.

## Per-batch procedure

1. **Read the charter + ledger + last ~40 issues.** Continue from `NEXT:`.
2. **Read the batch's chapters fully, in order.** No peeking at outline or editorial notes.
3. **Append issues to `issues.md` as found.** One line each, fixed format (`issue-format.md`); name the reader-moment.
4. **Update every ledger section** — position/clock, promise register, knowledge map, prop custody, do-not-re-explain, open threads, grades. An unupdated ledger invalidates the next batch.
5. **Write `batches/batch_X.md`** — what WORKS, per-chapter grades A–F, seam assessment at part boundaries, and one paragraph answering "would a paying reader keep going?"
6. **Set the `NEXT:` marker** in the ledger (with the WATCH list for the coming span).

## What the batch report contains

`batches/batch_X.md` (adapted from `fiction-forge/templates/batch_report.md`, MIT):

- **Reader log** — one entry per chapter: title, letter grade, 1–3 sentences of honest reader experience with the specific beat or line named. Praise what works; the read loses calibration if it only logs defects.
- **Big findings** — the batch's 1–4 conclusions larger than any single issue line (confirmed structural patterns, missing scenes, discovered devices), numbered, cross-referenced to issue IDs.
- **Seam assessment** — only at part boundaries; delete otherwise.
- **Batch verdict** — one paragraph: the batch grade, the state of the reader's trust, and a straight answer to "would a paying reader keep going?"
- **Ledger-updates checklist** — confirm every section was touched before ending the sitting.

## Orchestration (skill, not agent)

Orchestration lives in the skill, not the agent: muse spawns `@cold-reader` per batch, persists ledger/issues updates itself. For 15+ chapters muse MAY use the digest pattern from `fiction/agents/review-coordinator.md` (MIT) — spawn per-batch readers, aggregate from summaries, cache per-batch reports on disk. The agent executes one batch; the skill coordinates many.

## Grade what works

The batch report's "what WORKS" section and the grades keep the read honest. A read that only logs defects drifts into fault-finding and loses calibration. Name what earns the reader's time, not just what costs it.

## When to run

- After every major editorial program (especially parallel-agent waves, which introduce exactly the cross-chapter defects this read exists to catch).
- Before export (a final cold read is the last gate — if it finds BLOCKERs, you weren't ready).
- Not as a substitute for the scanners (`kb-integrity/`) — run the deterministic checks first and fix what they flag; don't spend cold-read attention on defects a script can find.
