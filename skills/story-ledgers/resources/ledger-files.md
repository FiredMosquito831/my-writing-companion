# Ledger Files

Adapted from `story-skills/skills/plot-structure/references/{promise,question}-template.md` — MIT. Changes: re-scoped to the vellum kb/ layout; promise schema extended with `reinforced:` + `planned` status and `target-by`; knowledge (3-level certainty) and prop custody schemas added (mechanism from fiction-forge's cold-read knowledge map and prop custody, MIT); clock table adapted from `fiction-forge/templates/reader_ledger.md` (MIT); exemption format and keying re-derived from Novel-OS `core/continuity_engine.py` `Finding.key` design (MIT). Full prose guidance follows each schema.

The ledgers are the deterministic continuity layer: machine-checkable YAML frontmatter that `vellum ledger check` validates against the manuscript. Prose below the frontmatter carries the human context. Every schema is a *minimum* — extra fields are allowed, missing required fields fail loudly.

## `kb/promises/<id>.md` — promises and payoffs

Schema adapted from `story-skills/skills/plot-structure/references/promise-template.md` (MIT), extended:

```yaml
---
id: promise-ring-of-oath
type: promise
title: "The ring must be returned to the House"
status: planned|planted|reinforced|paid-off|abandoned
planted-in: chapter-03
reinforced: [chapter-09]
payoff-in: null          # chapter-NN once paid
target-by: chapter-20    # soft deadline; ledger check flags unfired setups past target
abandoned-reason: null
---
```

Prose below the frontmatter: the promise as the reader experiences it, and what payoff should feel like.

- `status: planned` means the setup is written but not yet on the page; `planted` means it is on the page; `reinforced` means it has been worked at least once after planting; `paid-off` / `abandoned` close it (with `abandoned-reason`).
- `target-by` is a soft deadline — the ledger flags unfired setups past it (Novel-OS overdue-thread check, MIT, adapted).
- Dormant promises (no reinforcement for > 3 chapters) are flagged as `dormant` findings (Novel-OS dormant-thread check, MIT, adapted).

## `kb/questions/<id>.md` — open questions

Schema adapted from `story-skills/skills/plot-structure/references/question-template.md` (MIT):

```yaml
---
id: question-who-burned-the-annex
type: question
title: "Who burned the annex?"
status: open|answered|dormant
raised-in: chapter-02
answered-in: null
answer: null
---
```

Prose below: what needs answering, known clues and constraints, and the resolution plan.

## `kb/knowledge/<id>.md` — who knows what, with certainty

3-level certainty; mechanism from fiction-forge's cold-read knowledge map (MIT) + per-holder query (Novel-OS-style `knowledge --as-of` design). Queryable via `vellum knowledge <character-id> --as-of N`:

```yaml
---
id: knowledge-tom-faked-his-death
type: knowledge
title: "Tom faked his death"
statement: "Old Tom is alive; the funeral was staged."   # canon fact prose
holders:
  - character: character-mira-tarn
    learned-in: chapter-09
    certainty: knows          # knows | half-glimpse | audience-only
audience-learned-in: chapter-09   # when the READER learns it (dramatic-irony queries)
superseded-by: null
---
```

- `certainty: knows` — the character holds the fact and can act on it.
- `certainty: half-glimpse` — the character suspects or has partial evidence; acting on the *full* fact is a knowledge anachronism.
- `certainty: audience-only` — the reader knows; no character does. Dramatic irony.
- `audience-learned-in` enables the dramatic-irony query (`vellum knowledge <character-id> --as-of N --audience`): what the reader knows vs. what characters do as of chapter N.
- What `ledger check` mechanically validates: every `learned-in` references an existing chapter, and the holder appears in that chapter's `characters:` (they were in scene when they learned it). There is no per-chapter usage marker, so *using* a fact in prose before its `learned-in` is not machine-detectable — that anachronism class is what the cold read and the critics catch; `vellum knowledge <character-id> --as-of N` gives them the holder's fact list to check against.

## `kb/props/<id>.md` — prop custody

Custody mechanism from fiction-forge's prop custody (MIT):

```yaml
---
id: prop-ring-of-oath
type: prop
title: "Ring of Oath"
introduced-in: chapter-01
custody:
  owner: character-mira-tarn   # or null
  location: "Mira's coat pocket"
  status: in-play              # in-play | destroyed | lost | resolved
history:
  - {chapter: 3, change: "Given to Mira by Tom"}
---
```

`ledger check` validates chapter `custody:` frontmatter mechanically: a reference to an unknown prop, or to a prop whose recorded status is `destroyed` / `lost` / `resolved`, is a finding. Two props filling one symbolic slot, or a prop's location contradicting what the chapter shows, are judgment findings — the cold read and the critics surface those; the engine only fences the mechanical contradictions.

## `kb/characters/<id>.md` — characters

```yaml
---
id: character-old-tom
type: character
name: "Old Tom"
status: alive            # alive | deceased | unknown
died-in: null            # chapter-NN when status: deceased
aliases: ["Thomas Reave"]
pov-eligible: true
---
```

Dead-character reappearances: `status: deceased` + `died-in` vs. chapter `characters:` lists (`mentions:` is exempt — referenced/remembered/dead characters are fine to mention).

## `kb/clock.md` — threads and clocks

One table; rows are threads. Position/clock rows adapted from `fiction-forge/templates/reader_ledger.md` (MIT):

```markdown
| thread | started | position as of | clock reading | last chapter |
|---|---|---|---|---|
| siege-countdown | ch 4 | day 9 of 30 | 21 days remain | 7 |
```

`ledger check` validates each thread row mechanically: `started` must not be after the row's `last chapter` (a thread running backwards is a finding). The `clock reading` cell is free-form prose the engine does not parse — cross-batch regressions in the reading itself (a countdown growing, a clock slipping backwards between updates) are reader-state drift, which is what the cold read's reader ledger exists to catch.

## `kb/exemptions.json` — dismissed findings

```json
{
  "schema_version": 1,
  "exemptions": [
    {"key": "continuity:character-old-tom-seen-after-death",
     "reason": "Ghost sightings are intentional (author words here)",
     "dismissed_at": "2026-09-09", "chapter": "chapter-09",
     "status": "active", "stale_note": null}
  ]
}
```

- `status: active|stale`. Every check loads this file and drops findings whose `key` matches an active entry. `stale` entries re-arm once.
- **Key format**: `<category>:<entity_id>` where category ∈ `continuity|canon|voice|craft|structure|pace|repeat|frontmatter|band|state`. Deliberately excludes message text and chapter number (Novel-OS `Finding.key` rationale, MIT): reworded messages must not resurrect a dismissal, and the same contradiction surfaces at whichever chapter it is next observed.
- **Dismissal discipline**: the muse (or any agent) runs `vellum dismiss <key> --reason "<author words, verbatim>"` — never without the author's explicit word. Dismissed choices are never re-raised.
- **Expiry / re-arm**: when `bible validate` detects the underlying fact changed (entity status change, `died-in` edit, promise `payoff-in` edit, knowledge entry revision), the exemption flips to `stale` and the finding re-arms once with note "previously dismissed; underlying fact changed on \<date\>". Muse re-asks; the author re-decides.
