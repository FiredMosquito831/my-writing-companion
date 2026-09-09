---
name: cold-read
description: |
  Load for /vellum:cold-read, after every major editorial program, and before export. The cold-read skill owns the cover-to-cover cold-read protocol: the reader charter, the rolling ledger, the append-only issue log, and the batching/orchestration model. It finds the accumulating-memory defect classes (clock drift, cross-chapter state contradictions, prop custody, promise bookkeeping, knowledge-state slips) that no scanner, chapter reviewer, or continuity query can see.
---

# Cold Read

The cold-read skill owns the cover-to-cover cold-read protocol — a single reader, reading the whole manuscript in order, carrying a rolling ledger, and logging every defect that survives the per-chapter QA. It exists because a class of defect is invisible to every memoryless pass: a linter sees a line, a chapter reviewer sees a chapter, a continuity query sees a query — none of them accumulate reader-state. Clock drift, cross-chapter state contradictions, prop custody, promise bookkeeping at book scale, knowledge-state slips, and audit coverage bias are all *accumulating-memory* defects. The cold read is the only pass that catches them.

## What this skill is

- A **protocol**, not a single prompt. It runs on four files (charter, ledger, issues, batch reports) that together make a multi-sitting read behave like one continuous reader.
- **Assessment-only by default** (rule zero): the read measures; it does not edit the thing it measures. AUTO-FIX is opt-in, narrowly scoped, logged.
- **Batched** for sustainability and context-window safety: 8–11 chapters per sitting, the ledger the only inter-sitting state.
- A **self-contained** reference: it restates the severity taxonomy, the issue format, the batching model, and the orchestration pattern so the agent and the muse can run it without loading other skills. Cross-references to `gates/`, `kb-integrity/`, and `story-ledgers/` are pointers only.

## The document set

| File | Role |
|---|---|
| `work/cold-reads/<YYYY-MM>/charter.md` | Who the reader is, the rules, the batch plan, the severity taxonomy, autonomy tiers. Written once. |
| `work/cold-reads/<YYYY-MM>/reader_ledger.md` | The reader's accumulated memory: NEXT marker, position/clock, promise register, knowledge map, prop custody, do-not-re-explain, PROTECT, tripwires, grades. Updated every batch. |
| `work/cold-reads/<YYYY-MM>/issues.md` | Append-only issue log, one line per issue, fixed format. |
| `work/cold-reads/<YYYY-MM>/batches/batch_X.md` | Per-batch report: what works, grades, seam assessment, "would a paying reader keep going?" |

## Load the resource needed

- `resources/charter.md` — the reader persona ("devoted genre reader who just finished the previous book, with a line-editor's ear; experience first, diagnosis second"), rule zero, the batch plan, the severity taxonomy, AUTO-FIX vs PROPOSE tiers, voice cards, tripwires, PROTECT, deliverables.
- `resources/reader-ledger.md` — the rolling ledger: NEXT marker with WATCH list, position/clock table, promise register (HOT/WARM/COLD), character knowledge map, prop custody, do-not-re-explain register, PROTECT, tripwires, open threads, grades table. "A stale ledger is an amnesiac reader."
- `resources/issue-format.md` — the fixed line format `CR-### | ch:line | SEV | CAT | "quote" | reader-moment | fix direction | SCOPE`, the severity/category vocab, the severity→shared-schema mapping, and the rules (reader-moment mandatory, append-only, continuous numbering).
- `resources/batching.md` — 8–11 chapter batches cut at natural milestones, the per-sitting resume recipe (charter + ledger + last ~40 issues → continue from NEXT), the per-batch procedure, the batch report contents, the orchestration model, and when to run.

## Who runs it

- **Muse** sets up `work/cold-reads/<YYYY-MM>/` from `templates/cold-read/` (via `/vellum:cold-read`), seeds the ledger, and spawns `@cold-reader` per batch.
- **`@cold-reader`** executes one batch: reads charter + ledger + last ~40 issues, continues from NEXT, reads only the batch's chapters, returns (a) append-ready issue lines, (b) ledger section updates, (c) the batch report. Assessment-only; no peeking at outline or editorial notes during a batch.
- For **15+ chapters** muse MAY use the digest pattern from `fiction/agents/review-coordinator.md` (MIT) — spawn per-batch readers, aggregate from summaries, cache per-batch reports on disk.

## How it fits the gates

Cold-read findings are advisory by default; **BLOCKER-class findings block export** until resolved or dismissed-with-author-signoff (the same discipline as `story-ledgers/` exemptions). MAJOR/MODERATE need a triage note. The export readiness checklist (`gates/resources/readiness.md`) cross-checks the cold-read `issues.md` for open BLOCKERs.
