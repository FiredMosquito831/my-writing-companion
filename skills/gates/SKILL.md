---
name: gates
description: |
  Load when muse accepts a pivotal chapter, before export, or for any scoring task. The gates skill owns the shared quality rubric, the export-readiness checklist, the shared finding schema, and the numeric genre profiles. Every critic and gate-owning agent loads this so verdicts are consistent and criteria are referenced, never invented per-agent.
---

# Gates

The gates skill is the single source of verdict criteria for the plugin. It owns four things: the **shared quality rubric** all critics score against, the **readiness checklist** that gates export, the **shared finding schema** all critics emit, and the **numeric genre profiles** that give "too long / too talky / too slow" a meaning. Every critic and every gate-owning agent loads this skill so that verdicts are consistent and criteria are *referenced*, never re-litigated per-agent.

## The three hard gates (binding)

These are the only blocking gates by default. Their contracts live here and in the hooks/engine; agents do not re-litigate them.

1. **Outline before prose** — `hooks/scripts/guard-outline-before-prose.sh` + `guard-bash-prose-writes.sh`, BLOCKING (exit 2): prose writes to `manuscript/chapters/` require an author-approved outline (`approved: true`) and a clean `vellum state check` (fail-open if no interpreter resolves).
2. **Blind reader** — `@blind-reader` (Read-only, sees nothing of the plan), BLOCKING at acceptance for author-flagged `pivotal: true` chapters: acceptance requires `work/critique-reports/blind-chapter-NN.md` with verdict ≠ `LOST`.
3. **Beta reader** — `@beta-reader`, BLOCKING for export: `vellum readiness` requires `work/critique-reports/readiness-report.md` `verdict: PASS`. The gate reads the artifact from disk, never the muse's word.

Everything else (post-write prose net, demolition, disruptor, persona panel, cold read) is advisory and silent when clean. Two more gates (`voice_debt_gate`, `stop_gate`) are opt-in via `kb/project-config.json` and default off — the three-gate philosophy holds unless the author opts in.

## Load the resource needed

- `resources/quality-bar.md` — the shared five-axis rubric (voice, structure, depth, specificity, reader), 1–10 with anchors; the per-gate verdict contracts (blind ENGAGED|STALLED|LOST, beta PASS rule, critic blocking severities). **All agents reference this file; never restate the axes.**
- `resources/readiness.md` — the export preconditions as a checklist `vellum readiness` evaluates: every chapter `final` with complete frontmatter, ledgers clean, readiness report PASSES, word-budget report attached, pivotal chapters have blind artifacts.
- `resources/finding-schema.md` — the shared JSON schema all critics MAY emit (`audit`, `technique`, `severity`, `location`, `issue`, `confidence`); muse uses it when merging parallel reports.
- `resources/genre-profiles.md` — numeric genre truth (chapter-length norms, dialogue-ratio bands, scene-length norms per genre) that critics and the muse cite when scoring and when setting `word-target`. The engine stays mechanical (`wordcount` checks `word-target` ± band); agents reference the genre bands, never restate the numbers.

## How critics use this skill

1. Load `gates` (it is in every critic's skill list) — this gives the rubric, the finding schema, and the genre bands.
2. Read the manuscript (or chapter) with the persona/focus assigned by muse.
3. Score the five axes per `quality-bar.md`, one sentence of justification each.
4. Emit findings in the shared schema (`finding-schema.md`), naming the axis and score — never restating the anchors.
5. Apply the relevant gate's verdict contract (blind, beta, or critic-severity) — the contract is fixed here, not invented per-report.

## How muse uses this skill

Muse does not re-litigate the gates. Muse:
- Runs the deterministic preconditions (`vellum state check`, `ledger check`, `bible validate`, `wordcount`) and reads their output.
- Reads the artifacts on disk (blind verdict, readiness report) — the gate is the file, not muse's judgment.
- Presents the author with what the gate requires to pass, and the prioritized fix list when it does not.
- Runs `vellum readiness` before export and `vellum export build` when it passes.
