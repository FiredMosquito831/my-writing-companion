---
name: series-bible
description: >
  Schemas and conventions for the series bible (`series/bible.json`) and the
  rest of the library layer's JSON state, plus how book kb maintenance maps
  onto series canon. Load when inspecting or planning changes to bible
  entities and fields, deciding between a `value` and a `by-book` encoding,
  setting `scope` or `iron`, resolving what a field's effective value is at
  a given book ordinal, choosing or checking `series-id:` join keys on kb
  entity frontmatter, routing captured story knowledge into series scope,
  or writing kb pages about series-shared characters, props, promises,
  questions, and world knowledge. Use alongside the series skill, which owns
  the `library` command surface; this skill owns the data dialect. Findings
  are advisory-only — the series layer never adds a fourth gate.
---

# Vellum: Series Bible

The series-bible skill is the data-dialect reference for the library /
series layer: the JSON schemas, the encoding conventions, and the boundary
between book kb maintenance and series canon. For the command surface
(`library init/link/bootstrap/retcon-check/...`), load `/series` instead.
For book-local ledger schemas, load `/story-ledgers` — they are unchanged
by the series layer.

## The single-source-of-truth rule

All series-canonical state lives in `series/bible.json`, written **only**
by the engine (`library bootstrap --apply`, `library retcon --apply`,
`library init` for the empty skeleton). Agents and authors never write
bible state by hand, and book kb files never get a `canon:` mirror. The
only series-related field an agent may write in a book kb file is the
opt-in `series-id:` join key on entity frontmatter — and only via
`library bootstrap --apply` after human resolution of an ambiguity row, or
by the author by hand. All machine state is JSON; markdown files in the
library are human-facing reports only, never parseable state.

## Library file map

```
<library-root>/            # never inside a book project
  library.json             # manifest — engine-written only
  series/
    bible.json             # series canon — single source of truth
    retcons.jsonl          # append-only retcon audit log (audit only)
    exemptions.json        # series-scope dismissals — engine-written
    errata.md              # printed-vs-canon decisions — human-owned
  reports/                 # generated plans (retcon-plan-<ts>.md)
  handoff/                 # generated handoff-<ordinal>.md
  .lock                    # advisory lockfile during engine writes
```

## Manifest — `library.json`

Strict shape: unknown top-level keys are rejected (exit 2), so a future
engine cannot silently mis-read an old file. Required `kind:
"vellum-library"`.

- `schema_version` — integer, currently `1`.
- `series` — `{ title, created, next_event_id, next_retcon_id }`; the two
  counters are monotonic and only ever increase.
- `books[]` — `{ book_uuid, title, path, ordinal, status, linked_at,
  unlinked_at, engine_min_version, kb_entity_count, story_hash_at_link }`.
  `path` is relative to the library root with forward slashes; books are
  matched by `book_uuid`, never by realpath. `book_uuid` lives in the
  manifest and the book-side sidecar only — never in `kb/story.md`.
- `books[].status` ∈ `draft | published | archived`. See the freeze
  doctrine in `/series`: published canon is frozen (retcon-record-required
  default, never later-wins); archived is fully quiet.
- `engine_min_version_global` — minimum book engine version the library
  works against.

The book-side counterpart is the inert `.vellum/series-link.json` sidecar
(`series_root`, `book_uuid`, `ordinal`, `status`, `engine_min_version`).
It is never a source of truth; `library validate` regenerates stale
sidecars.

## Bible entities — `series/bible.json`

```
{
  "series_id": "<slug>",
  "schema_version": 1,
  "entities": {
    "char:lena-popescu": {
      "type": "character",
      "series_id": "char:lena-popescu",
      "name": "Lena Popescu",
      "aliases": ["Lena", "Lena P."],
      "fields": { ... },
      "established-in": ["1:chapter-03"],
      "scope": "shared",
      "entity_hash": "sha256:...",
      "last_touched": "R002"
    }
  },
  "timeline": { "events": [ { "eid": "E001", "when": "2011-07", ... } ] }
}
```

- **Entity ids** are typed slugs: `char:`, `prop:`, plus entity types
  `character | prop | promise | question | knowledge`.
- **Required keys**: `type`, `series_id`, `name`, `fields`,
  `established-in`, `scope`. Optional: `aliases`, `entity_hash`,
  `last_touched`.
- **`established-in`** — list of `ordinal:chapter-NN` coordinates
  (`1:chapter-03`); each must resolve to a real chapter file in the linked
  book, otherwise it is a finding (`series:established-ref-missing`), not
  a crash.
- **`scope`** — `shared` (visible to all books) or `local` (single-book
  only; local entities still get by-book maps but are flagged when another
  book references them).
- **`entity_hash`** — sha256 of the book kb entity's canonical frontmatter
  at last capture. Drives the uniform staleness rule: any author edit to
  that kb page flips the hash, stale series exemptions bound to it, and
  re-fires the finding. This is intentional — direct kb edits to canon
  must be re-reviewed.
- **`last_touched`** — the last retcon id that mutated the entity, or
  `"bootstrap"`.
- **`timeline.events[]`** — `{ eid, when, summary, established-in }`.
  `eid` is a stable `E###` id that is never renumbered; `when` must parse
  as ISO-8601 (structured dates, never prose — unparseable `when` is
  flagged).

### Field encoding — the two encodings

Each canonical field uses **one** of two encodings, never both:

- `{ "value": <literal> }` — immutable, book-independent fact (`born`).
- `{ "by-book": { "<ordinal>": <literal> } }` — value indexed by book
  ordinal, keys are ordinal **strings**, exactly one entry per book
  (`status`, `location`). This materialized map is the queryable truth;
  it is authored only by `bootstrap --apply` / `retcon --apply` and never
  reconstructed.

Optional third key inside the field object: **`iron`** — a list of
literal shared-no-change facts. When present and non-empty, any proposed
divergence against that literal is elevated and marked with the
`series:iron-clash` finding key; shared finding severity remains `warning`
(the key carries the elevation without changing the shared schema).

### Effective-at-N resolution

The effective value at book ordinal N is a dict lookup on the by-book map
— no log walking, no ties, no ordinal-order dependency:

```
value = bible.entities[<id>].fields[<field>].by-book.get(str(N),
        bible.entities[<id>].fields[<field>].value)
```

Time indexing covers all `by-book` fields, not only character status.

### Coordinate convention

- Bible internals: short form `ordinal:chapter-NN` (`1:chapter-03`).
- Markdown reports (plans, handoff): slash form `1/chapter-03`.
- Both parse to the same key; any other shape is rejected. A bare
  `chapter-NN` where a qualified coordinate is expected is itself a
  finding (`series:unqualified-ref`).

## Retcon log — `series/retcons.jsonl`

Append-only, one JSON object per line, never rewritten or compacted. Each
row carries `rid` (monotonic `R<int>`), `at` (ISO-8601 UTC),
`author_words` (verbatim, never edited), `kind` (`fact-change |
reanimation | scope-change | established-before | errata`), `entity`,
`field`, `from_book`, `old_by_book` / `new_by_book`, `proposed_by`. The
log is the audit trail only — `retcon-check` never reads it to compute
truth; the bible's by-book maps are the truth.

## Series exemptions — `series/exemptions.json`

Each dismissal targets exactly one finding id, not a whole entity:

```
{ "dismissals": [ { "finding_id": "series:deceased-as-of-start:...",
  "reason_author_words": "...", "at": "...",
  "expires_on_entity_hash": "sha256:...", "scope": "series" } ] }
```

Series-scope dismissals live and die in the library — they are never
written to a book's `kb/exemptions.json`, and existing book-scope
dismissals are never auto-migrated. `library dismiss` requires the reason
in the author's own words. The `expires_on_entity_hash` binding makes the
staleness rule uniform for author-owned kb edits.

## KB-management integration

The book kb remains the book's memory; the series bible is the
cross-book canon. The boundary:

- **Capture flow is unchanged book-side.** Chapter close-out → kb-lead
  writes/updates book kb pages exactly as in `/story-ledgers` and
  `/kb-management`. Series canon changes do **not** flow through kb page
  edits — they enter the bible only via `library bootstrap --apply`
  (initial capture) or an approved `library retcon --apply` plan. Never
  hand-edit `bible.json`, and never paste bible values into kb pages as a
  `canon:` block.
- **Join key.** A kb entity page joined to the series carries `series-id:
  <entity-id>` (e.g. `series-id: char:lena-popescu`) in its frontmatter.
  Absent = invisible to the series layer. The key is written by
  `bootstrap --apply` for resolved rows or by the author by hand; new
  entities get joined by running bootstrap again (its `[?]` ambiguity rows
  need the author's words before anything is written).
- **Editing a joined page is a canon event.** Because `entity_hash` is
  bound into series exemptions, editing a joined kb page makes its series
  dismissals stale and re-fires their findings. Route deliberate
  series-level fact changes through a retcon plan, not a silent kb edit.
- **Do-not-re-explain.** The series state card's register ("Established
  before this book — do not re-explain") applies to kb pages too: a page
  about a shared entity states what the series has committed to; it does
  not re-derive or re-litigate canon established in an earlier book.
  Cross-book questions belong in a retcon plan or `series/errata.md` for
  published books.
- **Vocab overlap.** Series-wide term decisions belong in the bible
  (`name`, `aliases`); book-local vocab pages stay book-local. When they
  disagree, the bible wins for `scope: shared` entities and the kb page
  should be corrected or a retcon planned.
- **Advisory-only.** Nothing here blocks a gate. The three hard gates
  (`/gates`) are unchanged; series findings are informational (exit 0/1/2,
  never a gate exit).

## Cross-references

- **`/series`** — the operator's manual: subcommands, retcon lifecycle,
  detection catalog (`references/checks.md`), freeze doctrine, migration
  path for existing projects.
- **`/story-ledgers`** — book-local ledger schemas (unchanged) and the
  `series-id:` frontmatter convention.
- **`/kb-integrity`** — when a book is linked, `library retcon-check` and
  `library state` are the series companions to the book-local engine.
- **`/gates`** — no fourth gate; findings are advisory-only.
