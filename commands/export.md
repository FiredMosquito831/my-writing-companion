---
description: Evaluate readiness, then build the export bundle.
---

Handle via the muse agent. $ARGUMENTS = optional output directory (default `export/manuscript-<date>`).

Run the §10.2 sequence in order; stop at the first failed precondition and print the prioritized fix list:

1. `readiness` (vellum). Requires ALL of: every chapter `status: final` with complete frontmatter; `ledger check` clean outside `kb/exemptions.json` (cold-read `issues.md` has no open BLOCKER; MAJOR/MODERATE need a triage note — fixed / deferred-with-author-signoff / accepted-limitation); `work/critique-reports/readiness-report.md` on disk with `verdict: PASS` (every axis ≥ 7, mean ≥ 7.5, no put-down in chapters 1–3); word-budget report attached. The gate reads the artifact from disk, never your word — no report, no export.
2. On PASS: `export build --out <dir>` (`--epub` for the stdlib EPUB with the stable `urn:uuid` identifier).
3. Interpret `manifest.md` for the author: chapter list, word counts, checksums, gate provenance (outline approval dates, blind verdicts, beta scores, logged overrides — never silent).
4. DOCX/PDF via pandoc when present; otherwise hand over the markdown bundle + conversion instructions.

The manuscript is untouched — export is a build artifact. If readiness fails, the failure output is a prioritized fix list (five changes with location, evidence, intervention kind, axis moved); route fixes back through the chapter loop, never straight to prose edits.
