# Cold-Read Issue Format

Adapted from `fiction-forge/docs/cold-read.md` + `fiction-forge/templates/issues.md` — MIT. Changes: re-scoped to the vellum layout; the fixed line format and severity/category vocab kept verbatim (tooling and later fix-waves depend on the exact format); integrated with the shared finding schema (`gates/resources/finding-schema.md`) — cold-read issues use the CR-### id scheme and the CAT/SEV vocab, which map onto the shared schema's `technique` and `severity`.

The issue log (`work/cold-reads/<YYYY-MM>/issues.md`) is **append-only**: one line per issue, fixed format, never edited or deleted. If an issue is fixed or superseded, append a note. The last ~40 lines of this file are part of every sitting's resume context, and the final ranked issue list is generated from it — so the format must stay exact.

## The line format

```
CR-### | ch:line | SEV | CAT | "quote" | why / reader-moment | fix direction | LINE/SCENE/STRUCT/META
```

- `CR-###` — zero-padded 3-digit, per-ledger counter, continuous across batches. Never reuse an ID.
- `ch:line` — chapter and line, anchoring the finding.
- `SEV` — `BLOCKER | MAJOR | MODERATE | MINOR` (see `charter.md` §Severity taxonomy).
- `CAT` — `CONT | CANON | VOICE | CRAFT | STRUCT | PACE | REPEAT | META`.
- `"quote"` — a short verbatim quote.
- `why / reader-moment` — **mandatory.** Name the reader-moment ("flipped back to check", "skimmed to the scene break"). No reader-moment, no issue.
- `fix direction` — a direction, not a patch. Prefer subtraction (the most common failure mode of AI-assisted prose is over-explanation).
- Final field = fix scope: `LINE` (one sentence) / `SCENE` (one scene) / `STRUCT` (crosses chapters) / `META` (files/metadata, not prose).

## Severity → shared-schema mapping

Cold-read severities map onto the shared finding-schema severities (`gates/resources/finding-schema.md`):

| Cold-read SEV | Shared-schema severity | Blocks export? |
|---|---|---|
| BLOCKER | blocker | Yes — must be resolved or dismissed-with-author-signoff |
| MAJOR | warning | Needs a triage note (fixed / deferred / accepted-limitation) |
| MODERATE | suggestion | Advisory |
| MINOR | note | Advisory |

## Rules

- **The reader-moment field is mandatory.** An issue that cannot name the moment it throws a reader out is not an issue.
- **Fix direction is a direction, not a patch.** Point at the problem and the kind of intervention; do not write the fix.
- **If an AUTO-FIX was applied** (per the charter's autonomy tier), append a triage line rather than editing history. The line stays; the fix is noted.
- **Triage notes are pipe-delimited lines** (the engine parses them mechanically — `vellum readiness` scans for them within three lines of the issue). Append, within three lines of the issue line, a line carrying one of these tokens verbatim: `| fixed |`, `| deferred-with-author-signoff |`, or `| accepted-limitation |`, e.g.:

  ```
  CR-005 | triage | fixed | <one line: what was done / who signed off / why accepted>
  ```

  A plain-language note ("fixed in the ch7 revision pass") without the pipe token is invisible to the engine — the finding stays open at readiness forever.
- **Number continuously across batches.** Never reuse an ID. A renumbering breaks every `ch:line` reference — if you renumber chapters, regenerate the mappings immediately.
- **REPEAT category: always log counts.** "Repeated scene-shape" without a count is not actionable.
- **Pre-queued section:** issues found while building the read folder (stale metadata, title/filename drift, numbering inconsistencies) go in the pre-queued section so batch reading starts clean.
