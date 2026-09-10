# Revision Plan

Mechanism credited to the editorial-letter reception doctrine taught by BubbleCow (Gary Smailes) and by Windrow; ideas only — no source text copied. Changes: re-cast as the vellum cross-source revision artifact; the row format, statuses, intake protocol, and definition-of-done discipline are written fresh for the vellum loop.

Vellum produces findings in four places — critique lanes, cold-read issues (`CR-###`), demolition logs, and the beta/readiness report — and the reader-sim lane adds a fifth. Nothing else joins them. The readiness report is a scorecard, not a work plan; each report prescribes its own priority order but not a plan across sources. The **revision plan** (`work/revision-plan.md`) is the single triaged, status-tracked work plan that survives between sessions.

## The artifact

`work/revision-plan.md` is **append-only**: one row per finding, never edited or deleted. A row whose status changes gets a new row superseding it (same discipline as the cold-read issue log — history is evidence). The plan is opened by the muse after the first review program of a revision round and kept open across sources and sessions.

The plan has two parts:

1. **Header** — the current round's scope and its **definition of done** (one line, written when the round opens and never edited; a new round appends a new header).
2. **Rows** — the append-only finding log.

## Plan header: per-round definition of done

```
## Round 2026-09 — pass 1 (developmental)
DoD: every open big-picture row in this round resolved or declined; character
rows next; line rows held for the line pass. Exit criterion: cold read over
the revised chapters reports no new STRUCT findings.
```

A round without a definition of done is a list, not a plan. Write it before triaging, in one line: which buckets this round covers, what counts as finished, and how the exit is verified.

## Row format

One line per finding, fixed pipe-delimited format (the engine parses it — `vellum revision status` cross-checks resolved rows mechanically):

```
REV-### | source | location | category | impact | effort | move | status [| note]
```

- `REV-###` — zero-padded, per-plan counter. Never reuse an ID.
- `source` — where the finding came from: `critique:<report file>` | `cold-read:CR-###` | `demolition:chapter-NN` | `beta:readiness-report` | `sim:<report file>` | `author` (self-identified).
- `location` — chapter:line or a short passage anchor.
- `category` — the triage bucket: `big-picture` | `character` | `line`.
- `impact` — the reader cost, one phrase ("reader stops trusting the timeline"). No reader cost, no row — a note that costs the reader nothing is a preference, not a finding.
- `effort` — rough size of the fix: `small` | `medium` | `large` (or free text when uncertain).
- `move` — the structural move the fix needs: `cut` | `move` | `expand` | `combine` | `seed-earlier` | `delay-payoff` | `n/a`.
- `status` — `open` | `in-progress` | `resolved` | `declined`.
- `note` — optional; **mandatory for `declined` rows**: the author's reason, in their own words, verbatim.

## Intake protocol (editorial-letter reception)

The doctrine this file ports is about *receiving* a body of findings without being jerked around by it:

1. **Read everything once, with no pen.** Merge all sources into rows first; do not act while reading. Many apparent problems resolve later in the manuscript; many real problems only become visible in retrospect.
2. **Walk away.** At minimum, end the session between intake and triage. Triage done hot converts every note into an immediate edit, which is how authors polish scenes that restructuring will delete.
3. **Triage into buckets, never item-by-item.** Classify each row `big-picture` (structure, promise, arc, pacing shape), `character` (motivation, voice-of-character, relationship logic), or `line` (sentence-level patterns). Big-picture before character before line — a line polish on a scene that will be cut or moved is wasted work.
4. **Translate to moves, not fixes.** Each row names the kind of structural move (`cut`, `move`, `expand`, `combine`, `seed-earlier`, `delay-payoff`), not replacement prose. The author executes in their own language.

## Merge duty (muse)

After **any** review program — critique fan-out, cold read, demolition, beta read, reader-sim lane — the muse merges all findings from all sources into the plan instead of presenting raw lists. Dedupe across sources: the same weakness found by a critic, a cold-reader, and the beta reader is one row citing three sources, not three rows. Present the author the triaged picture (bucket counts, highest-impact rows first), never a raw dump. The **author triages**; the muse prepares rows and records decisions.

## Declined rows: exemption discipline

A finding the author declines is a decision, not an omission. The row is marked `declined` with the author's reason verbatim in the note field, and the muse **never re-opens it** — the same discipline as `kb/exemptions.json` (the machine never re-litigates a dismissed choice; a re-armed exemption only comes back when the underlying fact changes). Re-litigating declined rows burns the author's trust in the whole review layer.

## Engine cross-check (report-only)

`vellum revision status` prints the plan's status counts and cross-checks rows against their sources: a row marked `resolved` whose source finding is still active in the source artifact (a cold-read `CR-###` line with no terminal triage token — `| fixed |`, `| deferred-with-author-signoff |`, `| accepted-limitation |`) is reported **stale**. A `declined` row without a verbatim reason is reported as a finding. The command writes nothing and is not a gate.
