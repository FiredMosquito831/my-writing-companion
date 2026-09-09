# Cold-Read Rolling Ledger

Adapted from `fiction-forge/templates/reader_ledger.md` — MIT. Changes: re-scoped to the vellum layout (`work/cold-reads/<YYYY-MM>/`); the NEXT marker, WATCH list, and per-section update discipline kept verbatim in spirit; integrated with the vellum knowledge/prop/clock ledgers in `kb/`.

The reader's accumulated memory, persisted to disk. This file is what makes a multi-sitting read behave like one continuous reader: every sitting reloads it, every batch updates it. **A stale ledger is an amnesiac reader** — you are back to memoryless QA. Seed the marked sections BEFORE reading a word; update EVERY section at the end of every batch.

## NEXT: (the resume marker — always current)

State the next batch and file range, plus a WATCH list: the specific promises, seams, and prior-issue verifications that fall inside the upcoming span.

**Batch A — read files 00–08.** WATCH: promises expected to advance; seams to assess; tripwires and prior-pass fixes in this span.

## Position / Clock table

One row per span read (seed rows first). This table catches clock drift — season, calendar, ages — cross-checked every batch. (Cross-references `kb/clock.md`, which is the canonical clock source; the ledger holds the reader's running view.)

| Chapters | Thread | Story-day | Season | Notes |
|---|---|---|---|---|
| (book start) | main | day/date | season | protagonist age, location, situation at page one |
| 00–08 | ... | ... | ... | one dense line per chapter: what happened, when, key state changes |

## Promise register (open promises — HOT / WARM / COLD)

Number every promise and sort by heat. HOT = the reader is actively leaning forward; WARM = remembered when prompted; COLD = long-fuse. (Cross-references `kb/promises/`; the ledger is the reader's running view of heat.)

**HOT:** P1 ... · P2 ...
**WARM:** P10 ... · P11 ...
**COLD (long-fuse):** P20 ... · P21 ...

A promise that never pays is a finding; a payoff that arrives unearned is a finding too.

## Character knowledge map (who knows what)

Only track knowledge that could be misused: secrets, things learned off-page, things the reader knows but a character doesn't. (Cross-references `kb/knowledge/`.) A character acting on unheld knowledge is a BLOCKER.

- Character A knows X as of Ch NN; does NOT yet know Y.
- Reader knows Z; protagonist has not connected it aloud.
- Secret S is held by A and B only — no third party may reference it.

## Prop custody

Where every significant object is, who holds it, and its state. (Cross-references `kb/props/`.) Seed the full inventory; append NEW props per batch. Flag collisions (two objects filling one slot) as issues.

- Object — location/holder, state, chapter last confirmed.
- NEW props (Batch A): object (ch NN, role/plant).
- Money/resources: amounts, debts, deadlines.

## Do-not-re-explain register

A fact goes on this register the first time the book explains it. Re-explaining any registered fact = MAJOR. This catches the over-explanation habit. Seed with everything the previous book or the opening chapters established; append per batch.

- ADDED thru Ch NN: fact (established ch NN — do not re-run).

## PROTECT (deliberate design — do NOT flag as defects)

Intentional ambiguities, unreliable-narrator devices, deliberately open threads. The device only covers what a storyteller would plausibly fudge — it never excuses mechanical errors (seasons, ages, inventories).

## High-risk tripwires (mirror of charter, grows during read)

Object A ≠ Object B · secret arrangement · hard numbers · ...

## Open threads by batch (watch for payoff)

Per batch, list the new threads opened in that span so later batches check for their payoff. Promote to the promise register if they carry real heat.

**Batch A:** thread (ch NN) — what payoff it demands.

## Grades table (running verdict data)

Filled per batch. Letter grades A–F. At part boundaries, add a part grade and a seam assessment. Keep a one-line running thesis — the verdict document assembles from here.

| Batch | Files | Grade | One-line verdict |
|---|---|---|---|
| A | 00–08 | — | ... |

**Part grades:** I: — · II: — · ...
**Running thesis:** what the book is doing well; the one or two persistent weaknesses; whether they're fixable by subtraction.

*Batches completed: A (files, n issues, grade) · B (...). Issues logged: CR-001…NNN.*
