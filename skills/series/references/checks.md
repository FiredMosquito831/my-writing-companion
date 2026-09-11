# Series Retcon Detection Catalog

Agent-facing copy of the §10 detection catalog. `library retcon-check` runs
these deterministically and emits only judgments for the rows marked
`resolution: judgment`. Judgment-flagged rows are never engine-resolved;
they are routed to muse/kb-lead.

Exit codes from `library retcon-check`: **0** clean · **1** findings ·
**2** unreadable/unlinked.

## Shared finding schema (no version bump)

The series layer adds findings using the existing shared finding schema
(`gates/resources/finding-schema.md`) without a version bump. The two new
fields are additive and optional:

- `book` — the book ordinal the finding pertains to.
- `series_scope: true` — marks the finding as series-layer (vs. book-local).

Deterministic checks are counted separately from judgment-flagged rows in
the summary line:

```
library retcon-check: 7 deterministic findings, 2 judgment-flagged
  (muse/kb-lead review)
```

## Coordinate convention

All series coordinates use the form `book-<ordinal>/chapter-<NN>` (e.g.
`1/chapter-09`). The book ordinal may be omitted only when the coordinate
refers to the *current* (probing) book; such bare `chapter-<NN>` in a
`series/` file is itself a finding (`series:unqualified-ref`).

Inside `series/bible.json` internals, `established-in` uses the short
`ordinal:chapter-NN` form (`1:chapter-03`). Retcon/handoff reports use
the slash form `1/chapter-03` in markdown. Both parse to the same key.
`library validate` rejects any other shape.

## Deterministic checks

### `series:deceased-as-of-start`

A `scope: shared` character with `status.by-book[current-1]` = `deceased`
is listed in the current book's chapter frontmatter `characters:`
(`mentions:` is exempt).

- Resolves via the `by-book` map at ordinal = current − 1.
- `mentions:` is always exempt: referenced/remembered/dead characters are
  fine to mention — the finding fires only when a deceased character appears
  in `characters:` as a present participant.
- **Exempt list (per-key dismissals):** for an intentionally recurring
  apparition ("He is a ghost; the apparition is intentional") dismiss the
  wildcard form `series:deceased-as-of-start:<series-id>:*` once — it
  suppresses the character's finding in every chapter for the life of the
  series, without dismissing other characters' findings. Per-chapter exact
  keys also remain available.
- Deterministic. Not judgment-flagged.

### `series:open-thread-carry`

A `kb/promises/` or `kb/questions/` entry with `status: open` and
`resolved-in: null` is referenced by a `series:established-in` value from
a published book and is still listed as unresolved in the current book's
state.

- Deterministic. Not judgment-flagged.

### `series:knowledge-anachronism`

A world-level `kb/knowledge/` fact whose `audience-learned-in` coordinate
claims the audience learned it in a **later** book than the book using it as
active canon (e.g. learned `3:chapter-01` but carried as canon in book 2).
A fact legitimately carried forward from an earlier book never fires.

- A bare `chapter-NN` coordinate means the current book — never
  anachronistic.
- Limited to **world-level** facts only (no character `holders`). Per-book
  character/prop knowledge carve-out stays in book scope (handled by
  `vellum ledger check`).
- **Planned reveals are opt-out:** a deliberately seeded cross-book
  reveal/mystery (the reader learns it in a later book on purpose) carries
  `reveal-planned: true` in the knowledge frontmatter and never fires this
  check.
- Deterministic for world facts. Not judgment-flagged.

### `series:canon-divergence`

A `scope: shared` fact's value in the current book kb differs from the
`by-book` value at this ordinal in the bible.

- Elevated severity if the bible field has non-empty `iron:` (marked with
  the `series:iron-clash` key; the shared finding schema's severity stays
  `warning` — the key is the elevation marker). The iron literals are
  compared too: for an immutable `value`-encoded fact whose kb value
  matches canon but contradicts the field's iron literal, the row is
  elevated the same way.
- Against a `published` book, emitted as `resolution: judgment` with
  default "retcon record required". The author must explicitly approve a
  change to frozen canon.
- Deterministic detection; judgment resolution for published books.

### `series:unqualified-ref`

Any `series/` file or retcon plan contains a bare `chapter-NN` (no
`book-N/` prefix) where a `book-N/chapter-MM` is expected.

- Schema-level, deterministic. Rejected or flagged as a finding; the
  slash form is mandatory in markdown tables.
- Not judgment-flagged.

### `series:orphan-book-ref`

`series/bible.json` entities carry `by-book` entries for an ordinal whose
book is `unlinked_at` non-null or missing.

- Detected after `library unlink`; canon remembers detached books.
- Deterministic. Not judgment-flagged.

### `series:id-mismatch`

A book kb entity joined by alias (not exact `series-id`) has a different
internal kb id from the bible `series_id`.

- Advisory, not a failure. Author confirms or reclassifies.
- Deterministic detection; advisory severity.

### `series:half-linked`

Detected by `library validate` when `.vellum/series-link.json` exists but
the manifest entry is missing (or vice versa).

- Deterministic. Not judgment-flagged.
- `library link` is idempotent-completing: re-running finishes the
  manifest entry after a crash between the two writes.

### `series:retcon-log-orphan`

A `retcons.jsonl` row references a `field` that contains a `rid`
last-touched value, but `bible.json` shows an older `last_touched`.

- Flag for corrective reapply.
- Deterministic. Not judgment-flagged.

### `series:established-ref-missing`

An `established-in` coordinate does not resolve to a chapter file in the
linked book.

- Missing file → finding, **not crash**.
- Deterministic. Not judgment-flagged.

## Judgment-flagged rows (engine emits, does not resolve)

### `series:unlinked-cast` (advisory, routed to kb-lead)

A series canon entity that appears in a chapter frontmatter `characters:`
cast but carries **no** `series-id:` in the book kb entity.

- Advisory, not a finding emitted by the engine as resolved. Routed to
  kb-lead for the author to confirm or add the `series-id:` join key.
- Closes the silent-gap hole: a series entity referenced in a chapter
  cast without a book-side join key is visible to the kb-lead.

### Projekt-2 animation concern (judgment row)

A timeline event titled as past is referenced in a later book's prose
without `established-in` in the earlier book.

- Cross-checked as a check #9 variant on timeline events.
- Judgment row; routed to muse/kb-lead.

### Author-owned kb edit staleness (uniform rule)

Every entity-bound finding's dismissal is bound to its `entity_hash`.
A direct canon/kb edit flips matching exemptions stale uniformly.

- The engine does not re-flag for non-entity-bound judgments.
- This is a uniform rule: whether the hash change came from capture or a
  manual kb edit, the dismissal goes stale and the finding re-fires.

## Iron facts

When a bible field has a non-empty `iron:` list (per-field `iron:`
literals), any proposed divergence against that literal is elevated and
marked with the `series:iron-clash` finding key. Severity stays inside the
shared finding schema's enum (`warning`); the iron-clash key is the
elevation marker downstream consumers match on.

- `iron:` is per-field, not per-entity (§4.1).
- `iron:` is the per-field tier for LitMemo shared-no-change facts.
- The do-not-re-explain register surfaces iron facts in the series state
  card (§8.8 section 4).
