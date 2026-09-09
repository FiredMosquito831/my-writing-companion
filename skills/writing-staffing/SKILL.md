---
name: writing-staffing
description: >
  Dispatch reference for composing writing teams. Teaches which skills to
  load for each subagent, which resources to reference, and when to fan out
  versus run parallel lanes. Load when staffing a workflow.
---

# Writing Staffing

Each subagent has its own skill set. This skill teaches what *extra* skills
to load and reference when dispatching work.

**Fan-out** gives the same question and files to different model families for
independent judgment. Reserve it for high-stakes calls where model diversity
can reveal different blind spots. **Parallel lanes** use different prompts or
focus areas; use them when the work divides cleanly.

## Dispatch Reference

### `@writer`

Extra skills: `/character-sim` for voice fidelity, `/shared-dao` for
project vocabulary, `/style-guardrails` and `/voice` for prose.

Reference: name the production mode from `/creative-writing-modes` →
`resources/prose-modes.md` (fresh draft, revision, bridge, alternate take,
line polish). Point to `/creative-writing-craft` →
`resources/prose-writing.md` or `resources/scene-construction.md` when
relevant. Include style files, character state, and continuity anchors.
The spawn prompt always carries the fixed context recipe (spec §9): mode +
intent, state card, scene brief, previous-chapter tail (~500–800 words),
character cards, voice, vocab, craft pointers, word budget, continuity
anchors. Fill chapter frontmatter completely (`characters`, `mentions`,
`promises-advanced`, `pov`) — the maintenance pass derives what it can and
flags the rest.

Write only under `manuscript/` and `work/drafts/` (plus `work/` files the
spawn prompt names); never `kb/` or `state/`, and never the gate inputs
(`work/outline/` approval flags, `work/critique-reports/`,
`work/cold-reads/` — hooks block subagent writes there). One writer per
scene — voice consistency degrades when multiple writers handle adjacent
content.

### `@critic`

Extra skills: `/creative-writing-craft` for prose/voice focus, `/shared-dao`
for vocabulary checks, `/gates` for the shared rubric and finding schema,
`/style-guardrails` for the standing slop tables (loaded by writer AND
critics before drafting/critiquing prose).

Assign a focus area: structure, character, voice, prose, or continuity.
Include style files for voice critique. Run different focus areas as parallel
lanes. Scale to stakes: 1–2 for low-stakes, 3 for standard chapters, 4–5 for
pivotal scenes with duplicated coverage on the critical dimension.

For a pivotal scene or disputed judgment, fan out the same critical dimension
once across two strong model families, then synthesize the disagreement.

**Persona panel** (milestone chapters, or when muse wants execution critique
from a named critical lens): fan out `@critic` with `focus: persona:<name>`
for the four personas in `/story-review` →
`resources/prose-critique/personas/{wood,king,leguin,gay}.md`. Personas
critique execution, not premise (base rule).

### `@editor`

Name the edit level: editorial review, developmental, line edit, copyedit,
proofreading. Point to `/story-review` → `resources/editorial-review.md` for
holistic pass, or the specific edit-level resource.

Use when the draft needs a priority order across concerns. For depth on one
dimension, use `@critic`.

### `@continuity-checker`

Extra skills: `/story-ledgers`, `/kb-integrity`.

Run the deterministic engine first (`ledger check`, `bible validate`); spend
your own reading on what it cannot judge: knowledge boundaries, plausibility,
terminology drift. Never re-report findings whose keys are in
`kb/exemptions.json`.

### `@blind-reader` (pivotal chapters only, at acceptance)

Extra skills: `/gates`.

Prompt = chapter prose + previous-chapter tail + quality-bar axes, NOTHING
else — no outline, no `kb/`, no style files, no critiques. Read-only (no
Write/Edit/Bash/Glob/Grep). Judges as a reader who knows nothing of the plan.
Muse persists the verdict to `work/critique-reports/blind-chapter-NN.md`.

### `@beta-reader` (pre-export)

Extra skills: `/gates`, `/creative-writing-craft`.

Reads `kb/story.md` (premise + promise) + genre file from
`/creative-writing-craft/resources/genre/` + the full manuscript in order
first; outlines/style/critiques only after the first read. Emits
`work/critique-reports/readiness-report.md` with verdict `PASS|REVISE`.

### `@cold-reader` (cold-read batches)

Extra skills: `/cold-read`, `/gates`.

Charter + reader ledger + last ~40 issue lines + the batch's chapters only;
never outline or editorial notes during a batch. Returns append-ready
`CR-###` issue lines, ledger-section updates, and the batch report.

### `@kb-lead` (fact extraction + ledger capture at chapter acceptance)

Extra skills: `/story-memory`, `/story-ledgers`.

Writes only under `kb/`; runs `state rebuild` + `bible validate` +
`ledger check` after updates. Replaces the muse's apply-it-yourself
fallback — knowledge capture routes here. Completes chapter frontmatter
fields the writer left blank when determinable from ledger/prose evidence;
flags anything uncertain as a finding instead of guessing. Never touches
`manuscript/`, `work/drafts/`, or `state/` by hand.

### `@disruptor` (author opts in, flat chapters)

Extra skills: `/creative-writing-craft`, `/story-planning`.

Proposal-only escalation lane; never writes. Given a chapter/outline the
author has judged flat, proposes up to 3 escalation options (raise a cost,
invert an expectation, introduce a complication with teeth, collapse a
safety), each with where-it-lands, what-it-costs, what-it-forecloses. Author
picks or dismisses; dismissed proposals are not re-raised.

### `@brainstormer`

Extra skills: `/character-sim` for character arcs, `/creative-research` for
real-world grounding.

Run parallel lanes on different *angles*, not the same angle. Three perspectives
beats five instances of one.

### `@outliner`

Outlining starts after direction is chosen — use `@brainstormer` first.
Output: outline frontmatter (`approved: false`, `pivotal: false`,
`word-target`, `verbatim:` list) with per-beat word quotas summing ≈
`word-target`. Use `/md-validation` for mermaid syntax guidance.

### `@style-creator`

Extra skills: `/style-guardrails`, `/voice`.

Include sample chapters or existing style files. Point to
`/creative-writing-craft` → `resources/style-analysis.md`. Fills
`kb/styles/voice.md` Part 2 from author samples, runs drift checks
(`style stats --baseline`) every `drift_interval` chapters, and harvests
author edits into voice exemplars.

### `@reader-sim`

Extra skills: `/character-sim` when the reader persona is a specific
character type.

Specify the reader persona and knowledge boundary (what has this reader
already read). Include the draft.

Run after the write/critique loop converges, before presenting to the
author. A scene can be technically clean and leave a reader cold.

### `@character-sim`

Include character state and voice/style files. Specify the scenario or
relationship to explore. Use one parallel lane per character or perspective
for independent exploration; use one shared simulation when testing their
interaction.

### `@web-researcher`

Specify the question, story context, and what the story currently assumes
so the researcher can flag contradictions.

## Context packs

When assembling a writer prompt, rank candidate context by relevance (cast,
referenced facts, vocab) and cap total — `vellum pack chapter-NN` does the
deterministic half (`{paths, inline}` JSON on stdout: state card, scene brief
path, previous-chapter tail, cast cards, relevant vocab, continuity anchors
ranked by referenced entities). Muse composes the rest per the §9 recipe.

## Stall detection

Mechanism from Novel-OS's sagging-middle detector (MIT, credited): if the
protagonist is reactive for 3 consecutive chapters with zero movement in the
state-card `Story position` / cast lines, muse proposes a structural
intervention. A flat chapter is a signal, not a verdict — the disruptor lane
is the author-opted escalation.

## Effort Scaling

Scale critic coverage to stakes. Knowledge maintenance waits until direction
or chapters settle. Reader-sim runs after the write/critique loop converges.
