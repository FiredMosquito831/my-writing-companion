---
name: story-ledgers
description: |
  Load when planning chapters, capturing what a chapter changed, or answering what is still open or who knows what. The story-ledgers skill owns the deterministic continuity layer: the ledger file schemas (promises, questions, knowledge, props, characters, clock), the fixed-section state card, and the chapter-transaction close-out. It is the reference the engine's ledger/bible/wordcount checks validate against — and the source the state card is derived from.
---

# Story Ledgers

The story-ledgers skill owns the deterministic continuity layer — the machine-checkable ledger files that `vellum ledger check`, `bible validate`, and `wordcount` validate against, the fixed-section state card that is the one-screen resume artifact, and the chapter-transaction close-out that keeps them current. It is the source of truth the state card is derived from, and the reference every knowledge/critic agent loads when capturing what a chapter changed.

## What this skill is

- The **ledger file schemas** — promises, questions, knowledge (3-level certainty), props, characters, clock — as machine-checkable YAML frontmatter with prose guidance. `vellum ledger check` validates these against the manuscript.
- The **state card** spec — the fixed seven-section, ≤12KB, engine-regenerated resume artifact (`state/state-card.md`).
- The **chapter transaction** — the mechanical + LLM close-out that runs on acceptance.
- A **self-contained** reference: it restates the exemption format, the dismissal discipline, and the "never hand-edit derived files" rule so knowledge agents can act without loading `kb-integrity/`. Cross-references to `gates/`, `voice/`, and `kb-integrity/` are pointers only.

## Load the resource needed

- `resources/ledger-files.md` — the ledger schemas: `kb/promises/`, `kb/questions/`, `kb/knowledge/` (3-level certainty, queryable via `vellum knowledge`), `kb/props/` (custody), `kb/characters/`, `kb/clock.md`, and `kb/exemptions.json` (key format, dismissal discipline, expiry/re-arm).
- `resources/state-card.md` — the fixed seven-section state card spec (Story position · Open promises & questions · Active cast · Knowledge boundaries · Props & clock · Next beats with word quotas · Flags), the ≤12KB hard cap, the engine-writes / never-hand-edits rule, and how it is used for resume and writer spawns.
- `resources/write-time-capture.md` — the chapter transaction: the mechanical half (acceptance close-out via `check-prose-after-write.sh`, writer-stop pre-pass via `chapter-maintenance.sh` — wordcount, ledger check, state rebuild), the LLM half (`@kb-lead` — fact/ledger capture + frontmatter backfill), the close-out sequence, and the "never hand-edit derived files" rule.

**Series attachment (optional).** When a book is linked to a library, entity frontmatter MAY carry an opt-in `series-id:` line (e.g. `series-id: char:lena-popescu`). Absent = entity invisible to the series layer. No change to ledger file schemas; the series layer reads the join key only. Canon truth lives in `series/bible.json`, never mirrored as `canon:` in book kb files. See `/series`.

## Who loads this skill

- **Muse** — when planning chapters, answering "what's still open / who knows what," or routing capture work.
- **`@kb-lead`** — the knowledge-capture worker; writes only under `kb/`, runs the engine checks after updates, never touches `manuscript/` or `state/` by hand.
- **`@continuity-checker`** — runs the deterministic engine first (`ledger check`, `bible validate`), spends its own reading on what the engine cannot judge (knowledge boundaries, plausibility, terminology drift), and never re-raises dismissed findings.
- **Writer** — to understand what frontmatter the chapter must carry (`characters`, `mentions`, `promises-advanced`, `pov`) so the maintenance pass does not go blind.
- **Critics** — to read the ledgers as ground truth when scoring continuity/structure.

## How it fits the chapter loop

1. **Outline** → outliner writes `work/outline/chapter-NN.md` with per-beat word quotas and `verbatim:` lines.
2. **Draft** → writer fills chapter frontmatter (`characters`, `mentions`, `promises-advanced`, `pov`).
3. **Accept** → the acceptance edit triggers the mechanical close-out (acceptance edit → PostToolUse hook); the writer-stop hook runs the same pass as an advisory pre-pass; muse routes `@kb-lead` for the LLM half; `state rebuild` regenerates the card.
4. **Next chapter** → SessionStart prints the updated card; the outline gate checks `pending_capture`.

## The exemption protocol (restated)

Findings are dismissed, not deleted: `vellum dismiss <key> --reason "<author words, verbatim>"`, keyed `<category>:<entity_id>` (category ∈ `continuity|canon|voice|craft|structure|pace|repeat|frontmatter|band|state`). Never run dismiss without the author's explicit word. Exemptions expire (`stale`) when the underlying fact changes, re-arm once, and the author re-decides. See `ledger-files.md` for the full format.
