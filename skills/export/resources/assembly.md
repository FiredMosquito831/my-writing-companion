# Export Assembly

The deterministic assembly phase of `/vellum:export` — what `vellum export build` does after `vellum readiness` passes. The skill is the operator's manual; the engine implementation lives in `scripts/vellum_lib/export.py` (Workstream B). This file documents the order of parts, the chapter-joining conventions, and the scene-break rules so the operator can verify the build.

## Preconditions (the gate)

Assembly never runs unless `vellum readiness` prints PASS (`gates/resources/readiness.md`). The preconditions are: every chapter `status: final` with complete frontmatter; ledgers clean (zero unresolved findings outside exemptions; cold-read `issues.md` has no open BLOCKER); the readiness report PASSES (every axis ≥ 7, mean ≥ 7.5, no put-down in chapters 1–3); the word-budget report is attached; every pivotal chapter has its blind artifact. If any precondition fails, `readiness` prints a prioritized fix list and assembly does not run.

## Order of parts

The assembled manuscript is built in this order, always:

1. **Title page** — title, author, book-uuid (from `kb/story.md`), build date.
2. **Copyright placeholder** — a stub the author fills; never invented by the build.
3. **Front matter** — dedication, epigraph, etc., if present in `manuscript/front-matter/`.
4. **Joined chapters** — in frontmatter `number` order (never filename order), scene-break conventions applied.
5. **Back matter** — afterword, acknowledgments, etc., if present.
6. **Manifest** — `manifest.md`: chapter list, word counts, sha256 checksums, gate provenance.

## Chapter joining

- Chapters are ordered by frontmatter `number`, never by filename. (Filenames are `chapter-NN.md` with 2-digit minimum padding; books past 99 use consistent 3-digit padding — but ordering is always by `number`.)
- Each chapter's body is taken from its `manuscript/chapters/chapter-NN.md`, **stripping the YAML frontmatter** (frontmatter is metadata, not prose).
- Chapters are joined with a consistent scene-break / chapter separator.

## Scene-break conventions

- A chapter start is a new page (or a `# Chapter N — Title` heading in the markdown bundle).
- Internal scene breaks within a chapter are preserved exactly as written in the source — the build does not add, remove, or normalize them. If the source uses `---`, the build keeps `---`. If the source uses a blank line, the build keeps a blank line.
- The build never rewrites prose. Export is a build artifact; the manuscript is untouched.

## The output

`vellum export build --out export/manuscript-<date>` writes:
- The joined markdown manuscript.
- `manifest.md` (see `manifest.md`).
- `--epub`: a stdlib-zipfile EPUB with a stable `urn:uuid:<book-uuid>` identifier from `kb/story.md` so highlights survive rebuilds. No pandoc required.
- DOCX/PDF via pandoc when present on the system; otherwise the markdown bundle + instructions. Pandoc is optional, never on the critical path.

## Gate provenance (never silent)

The manifest records, for every chapter: whether its outline was approved, whether it is pivotal, the blind-read verdict (for pivotal chapters), and the word count + sha256. Stale exemptions the author re-armed are listed under Logged Overrides with their keys. The beta-reader PASS certificate and cold-read triage are gate preconditions — the build only runs after `vellum readiness` passes — so the manifest proves what was accepted, and the readiness report carries the scores. See `manifest.md` for the exact fields.
