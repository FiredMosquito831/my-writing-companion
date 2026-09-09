# Vellum deterministic engine package (design-spec.md section 5).
# Original code (base design credited in ATTRIBUTION.md).
# Python >= 3.8, stdlib only, zero pip dependencies.
"""vellum_lib — the deterministic engine package.

Modules (spec 5.1/5.2):
- util        paths, atomic writes, lockfile, hash verification, yaml-lite
              frontmatter parser, word rule, exemptions, findings
- state       state rebuild / state check
- ledgers     ledger check (deterministic continuity catalog)
- bible       bible validate / reindex / links
- wordcount   wordcount [--write] + band check
- knowledge   knowledge <character> --as-of N [--audience]
- style_stats style stats [--baseline] (single metrics module)
- pack        pack chapter-NN (deterministic writer context pack)
- exemptions  dismiss / debt list|clear
- export      readiness / export build [--epub]
- cli         argparse dispatch
"""

__version__ = "0.1.0"
