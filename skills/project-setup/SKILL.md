---
name: project-setup
description: >
  One-time project setup for creative writing. Interviews you about your project, collects writing samples, proposes kb structure, and creates CLAUDE.md with project conventions.
---

# Project Setup

Guide the author through setting up their creative writing project. The goal
is a working `CLAUDE.md` and the full vellum project layout (spec §3.7) that
all agents read for project-specific conventions, plus initial style files if
writing samples are available.

## Learn About the Project

Ask about:

- What kind of project: novel, short story collection, serial?
- How far along: starting fresh, or existing chapters and worldbuilding?
- Single POV or multiple? Linear or non-linear timeline? How much worldbuilding?
- Where do they keep their writing? What's the existing layout?
- Genre (for the genre profiles `style stats` and `wordcount` cite).

## Writing Samples and Style

Ask about writing samples: these are the foundation for style analysis:

- Do they have sample chapters or scenes already written?
- Do they have writing from other projects that captures the voice they want?
- Are there published works they want to draw style inspiration from?
- Voice goals: close third, omniscient, first person? Formal, colloquial?

Collect whatever they have. Save samples to `kb/samples/` so they're available
for future style analysis. If they have enough material, offer to analyze
their style using the `/creative-writing-craft` methodology: read the samples,
identify the voice dimensions, and produce initial style files in `kb/styles/`.

If they're starting fresh with no samples, capture their voice goals in
CLAUDE.md so style files can be created from early drafts.

### Voice-capture interview

If samples are provided, run the voice-capture interview: collect 3–5 author
samples → `kb/samples/` → hand to `@style-creator`, who fills
`kb/styles/voice.md` Part 2 (identity scaffold: Tone, Sentence Rhythm,
Vocabulary Register, POV & Tense, Dialogue Conventions, Exemplar Passages,
Anti-Exemplars) per `/voice` → `resources/voice-template.md`. Also build the
measured per-1k voice profile per `/voice` → `resources/voice-profile.md`.

While interviewing, load these craft references as needed to ground the
conversation (optional, zero pipeline cost):
- `/creative-writing-craft` → `resources/scene-and-sequel.md` (scene =
  goal/conflict/disaster; sequel = reaction/dilemma/decision) — named failure
  patterns (flat scenes = missing disaster or skipped sequel).
- `/creative-writing-craft` → `resources/psychic-distance.md` — Gardner's five
  distances; POV-lurch diagnosis.

## Propose and Iterate

Based on what you learn, draft a `CLAUDE.md` section and show it to the
author. Cover:

- **Project overview**: what the project is, one paragraph
- **Author's space**: where the author keeps their writing and how it's
  organized
- **KB structure**: what subdirectories exist under `kb/` and what they're
  for (see Create-the-Files below for the full §3.7 layout).
- **Voice and style**: what style files exist, what samples they're derived
  from, voice goals not yet captured
- **Conventions**: anything project-specific: naming patterns, chapter
  numbering, POV tagging, spoiler handling
- **Shared vocabulary**: early canonical terms, aliases, invented words,
  genre terms with project-specific meanings, and terms the author wants
  agents to avoid or distinguish

Present the draft and let the author adjust. Iterate until they're satisfied.

## Tell the author the three gates

In one paragraph, explain the three hard gates the plugin enforces: (1) no
prose is written to a chapter until its outline is approved; (2) a chapter
the author flags pivotal is not accepted until the blind reader returns a
verdict other than LOST; (3) the manuscript is not exported until the beta
reader returns a PASS. Everything else is advisory and silent when clean.

## Create the Files

Once approved, create the full §3.7 layout:

1. Write or update `CLAUDE.md` with the agreed content.
2. Create the `kb/` structure:
   - `kb/story.md` with `schema-version: 2` (adapted from
     `story-skills/docs/schema-v2.md` — see the template for required
     frontmatter: `title`, `schema-version`, `genre`, `status`, `themes`,
     `pov`, `tense`; add `book-uuid` for the stable EPUB identifier, and
     `author`, `year` for the title page).
   - `kb/characters/`, `kb/world/`, `kb/timeline/`
   - `kb/styles/{voice.md, baseline.md}`, `kb/samples/`, `kb/vocab.md`
   - `kb/promises/`, `kb/questions/`, `kb/knowledge/`, `kb/props/`,
     `kb/clock.md`
   - `kb/issues/`, `kb/exemptions.json` (from `templates/exemptions.json`),
     `kb/project-config.json` (from `templates/project-config.json`)
3. Create `manuscript/chapters/` (chapters are added per `/vellum:write-chapter`,
   from `templates/chapter.md`).
4. Create `state/` (machine-authoritative; the engine writes
   `_tracking-state.json`, `_derived-hashes.json`, `state-card.md`,
   `.vellum.lock` — never hand-edited).
5. Create `work/` with `outline/`, `drafts/`, `critique-reports/`,
   `brainstorm/`, `demolition-history.md`, `voice-debt.json`,
   `cold-reads/<YYYY-MM>/`, `snapshots/`.
6. Create `export/`.
7. Copy `templates/` into the project so chapter/scene-card/promise/question/
   knowledge/prop/character/state-card/baseline/exemptions/project-config/
   cold-read templates are available locally.
8. Create `kb/styles/voice.md` from the voice template (`/voice` →
   `resources/voice-template.md`) and `kb/styles/baseline.md` from
   `templates/baseline.md` (the §8.3 numeric table `style stats --baseline`
   diffs against — filled by `@style-creator` from the sample corpus). The
   template ships with empty rate cells and `measured: false`: the engine
   ignores the baseline until `@style-creator` fills the measured rates and
   sets `measured: true`. Checklist: verify `kb/styles/baseline.md` no
   longer carries `measured: false` once the voice-capture interview is
   done — a baseline still in template shape means the measured-profile law
   has nothing measured to adapt to.
9. Copy the deterministic engine into the project: the plugin's
   `scripts/` directory (`vellum` entry + `vellum_lib/`) →
   `<project>/scripts/`. Every agent, command, and skill invokes
   `python3 scripts/vellum …` relative to the project root; without this
   copy those calls fail. When the plugin copy must serve instead, invoke
   `${CLAUDE_PLUGIN_ROOT}/scripts/vellum` and extend any Bash allowlist
   accordingly.
10. Record chapter word-target conventions (default 3200, band ±15%, from
    `kb/project-config.json`).
11. Run `git init` and write `.gitattributes`:

    ```
    *.md text eol=lf
    *.sh text eol=lf
    *.py text eol=lf
    ```

12. Write `kb/project-config.json` from `templates/project-config.json`
    (`drift_interval: 5`, `voice_debt_gate: false`, `stop_gate: false`,
    `default_word_target: 3200`, `word_band: 0.15` — the two extra gates
    default off so the three hard gates stay exactly three).
13. Save any writing samples to `kb/samples/`.
14. If samples were provided and the author wants style analysis, produce
    initial style files in `kb/styles/` and hand the samples to
    `@style-creator`.

## Existing Projects

If `CLAUDE.md` already has creative writing conventions, read it first and
suggest updates rather than overwriting. If the §3.7 layout is partially
present, fill the gaps rather than recreating from scratch.
