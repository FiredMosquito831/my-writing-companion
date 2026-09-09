---
name: kb-integrity
description: |
  Load when a vellum check failed, or when muse routes integrity work. The kb-integrity skill teaches how to run the deterministic engine (bible validate, ledger check, wordcount, state check, knowledge --as-of), interpret their findings, apply the exemption protocol, and repair derived files. It is the operator's manual for the mechanical half of the continuity layer — the cold read and the critics find what these linters cannot.
---

# KB Integrity

The kb-integrity skill is the operator's manual for the deterministic engine — the mechanical half of the continuity layer. It teaches **which command to run, how to read what it says, what to do when it flags something, and how to repair things when they break**. The engine is a regression fence, not a discovery tool: it catches the errors no API call should be spent on (dead-character reappearances, promise ordering, knowledge `learned-in` violations, schema violations, hand-edited state). The cold read and the critics find what the linters cannot — but the linters are what you run first, because they are deterministic, cheap, and reproducible.

## The engine commands

Run from the project root. All are stdlib Python, invoked as
`python3 scripts/vellum <sub>` — resolve the interpreter in order `python3`,
`python`, `py -3` (≥ 3.8). The engine is installed at the project root's
`scripts/vellum` by `project-setup`; the hooks invoke the plugin's copy via
the same contract (`VELLUM_PY` is resolved internally by
`vellum_py()` in `hooks/scripts/lib/common.sh` — agents never need that
variable). Exit codes: **0 clean · 1 findings · 2 schema/usage error**.

| Command | What it does | When to run |
|---|---|---|
| `vellum bible validate` | Frontmatter schema validation for every kb entity; kebab-case ids; cross-reference integrity (broken id references = findings). | After any kb/ edit; as a precondition for export. |
| `vellum bible reindex` | Rebuild the `_index.md` registries deterministically. | After validate reports broken references or missing registry entries. |
| `vellum bible links` | Cross-reference integrity only. | When an entity was renamed or removed. |
| `vellum ledger check` | Deterministic continuity: dead-character reappearances, promise ordering, question states, POV-not-in-cast, frontmatter completeness, prop custody, knowledge `learned-in` violations, clock monotonicity, outline-verbatim presence. | After every chapter acceptance; before export. |
| `vellum wordcount [--write]` | Words per chapter; `--write` updates `word-count` frontmatter; band check vs `word-target`. | After drafting; before export. |
| `vellum knowledge <character-id> --as-of N [--audience]` | Queryable knowledge backend: facts the character holds as of chapter N with certainty levels; `--audience` gives the reader-knowledge view for dramatic-irony checks. | When a character uses a fact; when checking dramatic irony. |
| `vellum state check` | Transactional invariants: state exists; schema current; no half-committed chapter; `pending_capture: false`; derived-file hashes match. | As the outline-gate precondition; before export. |
| `vellum state rebuild` | Regenerate `state/_tracking-state.json` + `state/state-card.md` from sources; recompute hashes. | After kb/ or frontmatter edits; to repair a `state:hand-edited` finding. |
| `vellum style stats <file> [--baseline]` | Sentence-length distribution, burstiness, opener variety, dialogue ratio, em-dash density, TTR, paragraph-shape entropy; `--baseline` diffs against `kb/styles/baseline.md`. | On demand; every `drift_interval` chapters. |

## Interpreting findings

Findings are emitted in the shared schema (`gates/resources/finding-schema.md`): `audit` (continuity|prose|structure|voice|reader), `technique` (short kebab tag), `severity` (note|suggestion|warning|blocker), `location` (file, line, quote), `issue` (one sentence), `confidence` (deterministic|judgment). Deterministic findings are reproducible; judgment findings are LLM opinion.

- **Exit 0** — clean. No action.
- **Exit 1** — findings present. Read them; resolve or dismiss.
- **Exit 2** — schema/usage error. The command itself could not run (unparseable frontmatter with file+line, missing required file). Fix the input, re-run.

## The exemption protocol

When a finding is **intentional** (the author confirms it is a deliberate choice, not an error):

1. **Never silently accept it.** Run `vellum dismiss <key> --reason "<the author's words, verbatim>"`. The key is `<category>:<entity_id>` (category ∈ `continuity|canon|voice|craft|structure|pace|repeat|frontmatter|band|state`) — deliberately excluding message text and chapter number so reworded messages cannot resurrect a dismissal.
2. **Never run dismiss without the author's explicit word.** The machine does not re-litigate a dismissed choice.
3. **Expiry / re-arm:** when `bible validate` detects the underlying fact changed (entity status, `died-in`, promise `payoff-in`, knowledge revision), the exemption flips to `stale` and the finding re-arms once with a note. Muse re-asks; the author re-decides.

When a finding is **an error**: fix the source (the kb entity, the frontmatter, the prose), then re-run the check. Do not dismiss errors.

## Repairing derived files

`state/_tracking-state.json`, `state/state-card.md`, and the ledger `_index.md` registries are **engine-written, never hand-edited**. The engine hash-verifies them (`state/_derived-hashes.json`); a mismatch → finding `state:hand-edited`. To repair:

- `vellum state rebuild` — regenerates the tracking state and state card from `kb/` + frontmatter + ledgers; rewrites the hashes.
- `vellum bible reindex` — rebuilds the `_index.md` registries.

If you need to change what a derived file says, change its **sources** and rebuild — never edit the derived file directly.

## Scanners are regression fences, not discovery

The deterministic engine catches the errors no API call should be spent on. It does **not** catch whether a chapter is flat, whether a voice has drifted in quality, whether a scene earns its payoff, or whether a reader would keep going. Those are what the **cold read** (`cold-read/` skill) and the **critics** (`story-review/`, `gates/`) are for. Run the engine first (cheap, deterministic); run the readers after (expensive, judgment). The engine is the fence; the readers are the discovery.
