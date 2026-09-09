---
name: zoom-out
description: Use when orienting in an unfamiliar area — fans out exploration across structure, knowledge, and history, then synthesizes one orientation map.
---

# Zoom Out

Load `/qi-layer` if it isn't already loaded.

Orient in an unfamiliar area by exploring multiple angles — each covering a
different lens — then synthesizing the findings into one orientation map. A
single angle sees one slice; zoom-out covers structure *and* knowledge *and*
history at once, so the picture isn't skewed by one lens.

Use when starting in an unfamiliar subsystem, picking up someone else's work,
or when the user says "orient me" / "what's the lay of the land here."

## Fan Out

Explore each angle independently, scoped to one question each:

- **Structure** — callers, dependencies, module boundaries, entry points, where behavior actually lives.
- **Documented knowledge** — what's been written about this area in the KB, guides, and reference docs — architecture, patterns, synthesized research.
- **Decision history** — why it's shaped this way — prior choices, rejected alternatives, constraints discovered. Skip when there's no relevant history.
- **Domain concepts** — the vocabulary in use (KB vocab pages, project guides, context docs).

Scope each exploration to its angle with concrete path or topic targets. Don't
let one pass cover two angles — the value is independent coverage.

## Synthesize

Read the findings and produce one orientation map, not four stitched-together
dumps:

- **What this is** — the area's purpose and boundaries, in two or three sentences.
- **Structure** — the modules and interfaces that matter and how they connect (a mermaid diagram if the shape is spatial).
- **Why it's like this** — the decisions and constraints that explain the current shape.
- **Vocabulary** — the terms needed to speak about it precisely.
- **Open threads** — gaps, debt, or unresolved questions surfaced.

When findings contradict each other, resolve it rather than listing both — code
is ground truth; a doc that disagrees is stale (note it). Keep the map tight:
the goal is a reader who can now navigate the area, not an exhaustive transcript.
