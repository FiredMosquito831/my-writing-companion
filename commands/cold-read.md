---
description: Set up work/cold-reads/<YYYY-MM> from templates/cold-read and run cold-read batches.
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents). $ARGUMENTS = optional chapter range (e.g. "1-9"); with no range, continue the active read or plan the whole book.

**Setup** (only if `work/cold-reads/<YYYY-MM>/` is missing): create it from `templates/cold-read/` — `charter.md`, `reader_ledger.md`, `issues.md`, `batches/`. Fill the charter with the author: reader persona (devoted genre reader who just finished the previous book, with a line-editor's ear — experience first, diagnosis second), the batch plan (8–11 chapters cut at natural milestones), known failure modes from prior passes, and PROTECT items. Seed the ledger BEFORE reading a word — character states, open promises, prop inventory, do-not-re-explain register, `NEXT:` marker with WATCH list. A thin seed produces false positives in batch A.

**Rule zero: assessment only.** Nothing under `manuscript/` is modified during the read; all output goes to the read folder. AUTO-FIX is opt-in and narrow (mechanical, judgment-free defects only); default NONE.

**Per batch:** spawn `@cold-reader` with the charter + reader ledger + last ~40 issue lines + the batch's chapters ONLY. Never the outline, never editorial notes during a batch. Persist what it returns yourself:

1. Append issue lines to `issues.md` — fixed CR format, every issue names its reader-moment, append-only (never edit a logged line; supersede by appending).
2. Apply the ledger section updates (position/clock, promise register, knowledge map, prop custody, do-not-re-explain register, new `NEXT:`).
3. Save the batch report to `batches/batch_X.md` (what WORKS, grades, seam assessment, "would a paying reader keep going?").

For 15+ chapters you MAY use the digest pattern: spawn per-batch readers, aggregate from summaries, cache per-batch reports on disk.

**After each batch:** report grade, open BLOCKERs, reader trust state. **After the final batch:** summarize; BLOCKER-class findings block export until resolved or dismissed with the author's explicit signoff (`vellum dismiss` with their words). When an issue is resolved, deferred with signoff, or accepted as a limitation, append its triage note to `issues.md` in the machine form from `cold-read/resources/issue-format.md` — a pipe-delimited line within three lines of the issue carrying `| fixed |`, `| deferred-with-author-signoff |`, or `| accepted-limitation |` verbatim (e.g. `CR-005 | triage | fixed | what was done`). `vellum readiness` parses that token; a plain-language note leaves the finding open at export forever. A stale ledger is an amnesiac reader — if the ledger was not honestly updated last batch, say so before continuing.
