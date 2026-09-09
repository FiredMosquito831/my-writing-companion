# Quality Bar

Adapted from `Velith/agents/beta-reader.md` — Apache-2.0. Changes: extracted the five-axis rubric and PASS rule into a shared reference all critics load (never restate the axes); added per-gate verdict contracts (blind ENGAGED|STALLED|LOST, beta PASS|REVISE, critic blocking severities); integrated with the finding schema and the readiness gate.

The shared rubric every critic scores against. **All agents reference this file; never restate the axes in an agent body or a finding.** When a finding cites an axis, it names the axis and the score — the anchors live here.

## The five axes (1–10, with anchors)

| Axis | 1–3 | 4–6 | 7–8 | 9–10 |
|---|---|---|---|---|
| **Voice** | Generic, interchangeable, or off-register; reads as AI-default. | Competent but flat; voice present but not distinctive. | Distinctive and consistent; sounds like a person, with the project's register. | Unmistakable; the sentence-level identity is the book's signature. |
| **Structure** | Broken causality, missing scenes, or pacing that loses the reader. | Functional but mechanical; beats land but do not compel. | Solid architecture; scenes connect by "therefore/but"; the shape serves the story. | Inevitable; every scene earns its place and the turns surprise. |
| **Depth** | Surface; tells without showing; themes stated directly. | Some interiority or consequence, but shallow. | Characters have visible inner lives; themes emerge from action. | Layered; rereading rewards; the work knows more than it says. |
| **Specificity** | Vague, swappable, abstract; could be about anything. | Some concrete detail, but uneven. | Consistently grounded in the senses, names, numbers, the particular. | Precise and estranging; the detail makes the familiar strange. |
| **Reader** | The reader is lost, bored, or distrustful. | The reader continues but is not compelled. | The reader is engaged and trusts the prose; would keep going. | The reader is gripped; put-down points none; would recommend. |

Scoring is judgment, not a checklist. A 7 is "good, would not block"; an 8 is "strong"; 9–10 is "exceptional, rare." Most published-good chapters land 6–8. The mean is the beta-reader score; the per-axis floor is the PASS gate.

## Per-gate verdict contracts

Each gate maps the rubric (and other signals) to a fixed verdict. The contracts are binding — a gate does not invent its own criteria.

### Gate 1 — Outline before prose (blocking)
Not scored on the rubric. Pure predicate: `work/outline/chapter-NN.md` exists, frontmatter `approved: true`, and `vellum state check` passes (fail-open if no interpreter). See `hooks/scripts/guard-outline-before-prose.sh`.

### Gate 2 — Blind reader (blocking at acceptance, pivotal chapters only)
Verdict: `ENGAGED | STALLED | LOST`.
- **ENGAGED** — the reader, knowing nothing of the plan, was compelled; no put-down point; confusion list empty or minor. Acceptance allowed.
- **STALLED** — the reader continued but was not compelled; confusion or AI-feel flags present. Revise and re-read before acceptance.
- **LOST** — the reader would have stopped; put-down point, broken causation, or the chapter does not work standalone. **Blocks acceptance.**

The blind reader also scores the five axes (its scores feed the readiness report). It never suggests fixes — verdict only.

### Gate 3 — Beta reader (blocking for export)
Verdict: `PASS | REVISE`.
- **PASS rule**: every axis ≥ 7, mean ≥ 7.5, no put-down point in chapters 1–3, and the genre professional (Reader D) would not be embarrassed to have acquired it.
- **REVISE**: otherwise. The report provides a prioritized fix list — the five changes that would most raise the verdict, each with location, evidence, intervention kind, and axis moved.

The beta reader reads the artifact on disk (`work/critique-reports/readiness-report.md`), not the muse's word. The gate is the file.

### Critic findings (advisory)
Findings use the shared severity scale (`finding-schema.md`): `note | suggestion | warning | blocker`. Which severity blocks acceptance vs. export is fixed here:
- **Blocker** — blocks acceptance (pivotal) and export. On-page contradiction, timeline impossibility, knowledge from nowhere, wrong established fact, truncation/refusal markers.
- **Warning** — does not block alone; 3+ warnings on one axis pull that axis below the PASS floor.
- **Suggestion / Note** — advisory; silent when clean.

## How critics use it

1. Load this file before reading (it is the `gates` skill in every critic's skill list).
2. Score each axis after the read, one sentence of justification each, drawing on all the reader's evidence.
3. Map the scores + the gate's verdict contract to a verdict.
4. Emit findings in the shared schema (`finding-schema.md`), naming the axis and score — never restating the anchors.

## Genre adjustment

Numeric genre truth (chapter-length norms, dialogue-ratio bands, scene-length norms per genre) lives in `genre-profiles.md`. Critics cite it when scoring structure/pace; they do not restate it. A thriller's pace bar is not a literary-fiction's pace bar — the genre profile sets the band.
