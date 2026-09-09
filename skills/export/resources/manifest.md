# Export Manifest

The manifest (`export/manuscript-<date>/manifest.md`) is the build's certificate: what was assembled, its checksums, and the gate provenance for every chapter. It is the artifact that makes export auditable — the author can see exactly what was shipped, in what order, and which gates each chapter passed. The engine writes it (`scripts/vellum_lib/export.py`); this file documents its fields exactly as the build emits them.

## Fields

### Build metadata
The manifest's header line records the build date and the chapter count: `Built <ISO date> from <N> final chapter(s). Source of truth: manuscript/ (untouched).`

### Chapter table
One row per chapter, in assembly order (frontmatter `number` order):

| Column | Source |
|---|---|
| `chapter` | source file `manuscript/chapters/chapter-NN.md` |
| `words` | word count of the chapter body (engine word rule) |
| `sha256` | sha256 of the chapter file's current bytes (first 16 hex chars) |
| `approved outline` | whether `work/outline/chapter-NN.md` has `approved: true` (gate 1) |
| `pivotal` | whether the outline is flagged `pivotal: true` |
| `blind verdict` | the frontmatter `verdict` of `work/critique-reports/blind-chapter-NN.md`; `none` when the chapter is not pivotal or has no artifact |

### Logged overrides
Stale exemptions (dismissals the engine re-armed because the underlying fact changed) are listed under **Logged overrides** with the exemption key and stale note — never silent. Active exemptions are not listed; they simply suppress their findings, and the readiness gate reports anything the exemption does not cover.

### EPUB identifier
When `kb/story.md` carries a `book-uuid`, the manifest records the stable identifier `urn:uuid:<book-uuid>` (highlights survive rebuilds).

### Conversion note
The manifest closes with the DOCX/PDF note: via pandoc when present; otherwise convert the markdown bundle with your editor of choice.

## What the manifest does not carry
- **Beta-reader verdict and axes** — the PASS certificate is the readiness report itself (`work/critique-reports/readiness-report.md`); the manifest references it by being built only after `vellum readiness` passes. It is not duplicated per chapter.
- **Cold-read triage status** — evaluated by `vellum readiness` before the build runs; open BLOCKERs block the build instead of being stamped into the manifest.
- **Per-chapter frontmatter-completeness / wordcount-in-band flags** — `bible validate` and `ledger check` findings block readiness; the manifest lists chapters that passed.

## Checksums

Each chapter row carries a sha256 (of the chapter source file). A mismatch between a chapter's current checksum and the manifest's is a signal the manuscript was edited after export — the author re-runs the build.

## What the manifest is not

The manifest is a certificate, not the manuscript. The manuscript is the joined markdown (and optionally the EPUB); the manifest proves what it contains and how it was gated. It does not replace the readiness report or the blind-read artifacts — it references them.
