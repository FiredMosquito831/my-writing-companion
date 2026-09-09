# Finding schema

Adapted from `author-toolkit/references/finding-schema.json` — MIT. Changes: re-cast as a prose resource; audit and severity vocab fixed to the vellum gate contracts.

All critics MAY emit this JSON; the muse uses it when merging parallel reports (spec section 3.6).

```json
{
  "audit": "continuity|prose|structure|voice|reader",
  "technique": "short-kebab-tag",
  "severity": "note|suggestion|warning|blocker",
  "location": {"file": "manuscript/chapters/chapter-07.md", "line": 42, "quote": "…"},
  "issue": "one sentence",
  "confidence": "deterministic|judgment"
}
```

Field notes:

- `audit`: which lane produced the finding — continuity, prose, structure, voice, or reader.
- `technique`: short kebab tag naming the specific device or fault (e.g. `filter-words`, `head-hopping`).
- `severity`: `note` (observation) < `suggestion` < `warning` < `blocker`. Only `blocker` blocks acceptance or export; which severities block per lane is fixed in `quality-bar.md`.
- `location`: file, line, and a short verbatim quote anchoring the finding.
- `issue`: one sentence. No softening, no solutions in the finding itself.
- `confidence`: `deterministic` (engine-produced, reproducible) or `judgment` (LLM opinion).

Exemption keying: a dismissed finding is keyed `<category>:<entity_id>` (category ∈ `continuity|canon|voice|craft|structure|pace|repeat|frontmatter|band|state`) — deliberately excluding message text and chapter number, so reworded messages cannot resurrect a dismissal (Novel-OS `Finding.key` rationale, MIT, credited — see `story-ledgers/resources/ledger-files.md` for the `kb/exemptions.json` format). Pass the key exactly as the engine printed it; the engine validates the category.
