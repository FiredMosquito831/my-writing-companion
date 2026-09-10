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
2. **Blind reader** — `@blind-reader` (Read-only, sees nothing of the plan), BLOCKING at acceptance for author-flagged `pivotal: true` chapters: acceptance requires `work/critique-reports/blind-chapter-NN.md` with verdict ≠ `LOST`. **Single-agent (no-subagent) fallback:** a single context cannot honestly run the blind gate. Muse says so plainly and the author chooses: (a) drop the `pivotal: true` flag, or (b) enable the fallback — the author sets `blind_gate_fallback: true` in `kb/project-config.json` (the author's decision point; the muse never sets it), then the main loop performs a naive-eyes pass in a fresh stance-turn, records the artifact with `run_stamp: blind-reader (single-agent fallback) <verdict> <date>`, and presents the author an explicit warning that the verdict is weaker than a true blind read before acceptance on a verdict ≠ `LOST`. The engine enforces the ordering: `state check` and `vellum readiness` reject a fallback-qualified stamp unless the flag is set. Never skip the gate silently.
3. **Beta reader** — `@beta-reader`, BLOCKING for export: `vellum readiness` requires `work/critique-reports/readiness-report.md` `verdict: PASS`. The gate reads the artifact from disk, never the muse's word.

Everything else (post-write prose net, demolition, disruptor, persona panel, cold read) is advisory and silent when clean. Two more gates (`voice_debt_gate`, `stop_gate`) are opt-in via `kb/project-config.json` and default off — the three-gate philosophy holds unless the author opts in.

## Gate-artifact provenance (v0.1.1)

Gate artifacts are muse-transcribed, so each must carry a provenance record that a real reader run produced the verdict it holds. Two accepted forms, strongest first:

- **`run_stamp:`** — the reader agent **self-records** a run stamp in its returned report frontmatter at run time: `run_stamp: <agent> <verdict> <YYYY-MM-DD[THH:MM:SSZ]>`. The muse transcribes it verbatim like the verdict itself — inventing it is the same fabrication as inventing the verdict. This is the default record: unlike a SubagentStop payload, it reliably reaches the conversation that persists the artifact.
- **`transcript:`** — the subagent transcript path; the engine verifies the file exists and carries the verdict. The muse records it when the path is known, including via the documented search (list the newest `*.jsonl` session transcripts under `~/.claude/projects/<project-slug>/` by mtime, `grep -l` for the verdict line).

`vellum readiness` and `state check` verify whichever form is present; an artifact with neither (or with a stamp that disagrees with its own verdict) fails the gate. A `(single-agent fallback)` qualifier on a stamp is accepted only when the author has enabled the no-subagent fallback in `kb/project-config.json` (`blind_gate_fallback: true`, default off); without the flag the artifact fails the gate — the fallback is the author's choice, recorded at the author's decision point, never the muse's. The three-gates-from-disk doctrine is unchanged: the gate is the file, not the muse's judgment.

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
