---
description: Record an author dismissal of a finding as an exemption (requires the reason in the author own words).
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents). $ARGUMENTS = finding key + the author's reason.

Refuse to run unless BOTH are true:
1. The author, in this conversation, said the finding is intentional — the machine never dismisses on its own judgment, and a stale or inherited dismissal does not count.
2. The reason is the author's own words. Use them verbatim — never paraphrase, polish, or summarize. If the author gave no reason, ask for one in their own words; if they decline to give one, the finding stands.

Then run `python3 scripts/vellum dismiss <key> --reason "<author words, verbatim>"` (resolve the interpreter in order: `python3`, `python`, `py -3`; ≥ 3.8; the engine lives at the project root's `scripts/vellum`, installed by `project-setup`, falling back to `${CLAUDE_PLUGIN_ROOT}/scripts/vellum` when absent). The key format is `<category>:<entity_id>`, category ∈ `continuity|canon|voice|craft|structure|pace|repeat|frontmatter|band|state` — deliberately excluding message text and chapter number, so a reworded message cannot resurrect the dismissal. Pass the finding's key exactly as the engine printed it; the engine validates the category.

Never re-raise a dismissed finding. Exemptions re-arm once if the underlying fact changes (`bible validate` flips them to `stale`); only then may you ask again — once.
