---
name: export
description: |
  Load for /vellum:export. The export skill is the operator's manual for building the final manuscript: it runs the readiness gate, interprets a failure as a prioritized fix list, runs the deterministic build on PASS, and explains the manifest and the pandoc fallback. The engine implementation lives in scripts/vellum_lib/export.py (Workstream B); this skill is what the operator (muse) follows.
---

# Export

The export skill is the operator's manual for `/vellum:export` — the command that builds the final manuscript artifact. It is **not** the build engine (that is `scripts/vellum_lib/export.py`, Workstream B); it is the sequence the operator follows, the gate it runs first, and the way it interprets success and failure. The manuscript on disk is untouched — export is a build artifact, assembled from the gated sources.

## The export sequence

1. **Run `vellum readiness`.** This evaluates the preconditions (`gates/resources/readiness.md`): every chapter `final` with complete frontmatter, ledgers clean, the readiness report PASSES, the word-budget report attached, pivotal chapters have blind artifacts.
2. **If PASS** → run `vellum export build --out export/manuscript-<date> [--epub]`. Interpret the manifest (`resources/manifest.md`).
3. **If not PASS** → readiness prints a prioritized missing list. Present it to the author; do not run the build.

Muse does not re-litigate the gate. Muse runs `vellum readiness`, reads its output, and either runs the build or presents the fix list. The gate is the engine's verdict.

## Interpreting a failure

A failed readiness check prints a prioritized fix list. The format mirrors the beta-reader REVISE output: the changes that would most raise the verdict, each with location, evidence, intervention kind, and the axis/gate it moves. The author works the list, re-runs `/vellum:export`, and the gate re-evaluates. Common failures:

- **Incomplete frontmatter** on a chapter → `vellum ledger check` emits `frontmatter:incomplete`; the author (or `@kb-lead`) fills the fields.
- **Open ledger findings** → resolve or dismiss-with-author-signoff (`vellum dismiss`).
- **Readiness report REVISE** → the beta reader's prioritized fix list; revise and re-run the beta read.
- **Pivotal chapter missing blind artifact** → run the blind read for that chapter.
- **Cold-read BLOCKER** → resolve or triage.

## On PASS — the build

`vellum export build --out export/manuscript-<date>` assembles (`resources/assembly.md`):

- Title page, copyright placeholder, front/back matter, joined chapters (in frontmatter `number` order), and the manifest.
- `--epub` adds a stdlib-zipfile EPUB with a stable `urn:uuid:<book-uuid>` identifier from `kb/story.md` so highlights survive rebuilds. **No pandoc required** — the EPUB writer is stdlib zipfile.
- DOCX/PDF via pandoc when present; otherwise the markdown bundle + instructions. Pandoc is optional, never on the critical path.

## The manifest

The build writes `manifest.md` (`resources/manifest.md`): chapter list, word counts, sha256 checksums, and **gate provenance** for every chapter (outline-approval date, blind verdict, beta scores, logged overrides). Export never silently drops a gate — the provenance is attached. The manifest is the build's certificate; it is not the manuscript.

## Load the resource needed

- `resources/assembly.md` — the deterministic assembly phase: order of parts, chapter-joining conventions, scene-break rules, the output files, and gate provenance.
- `resources/manifest.md` — the manifest fields: build metadata, chapter list, per-chapter gate provenance, book-level gates, overrides, and checksums.

## What export is not

Export does not edit the manuscript, does not re-litigate the gates, and does not replace the readiness report or the blind/beta artifacts — it references them. The manuscript is the source of truth; the export is a build artifact assembled from it. If the manuscript changes after export, the author re-runs the build (the manifest's checksums detect the drift).
