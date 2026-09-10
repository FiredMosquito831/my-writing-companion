---
name: story-review
description: |
  Review work after prose exists: editorial review, craft critique, continuity/voice review, copyediting, proofreading, and synthesis of reader-sim signal. Load when diagnosing a draft rather than rewriting it.
---

# Story Review

Analytical review of existing prose. This skill is for diagnosis, not
rewriting. Keep `/reader-sim` separate when the task needs a felt first-time
reader experience rather than analytical critique.

Choose the review level before reading. Start big before small unless the
caller explicitly asks for a late-stage pass. The edit levels move from
structural to surface, and each assumes the levels above it are stable:

- **Editorial review** — holistic third-party book-editor pass. What kind of
  revision does this draft need, and in what order?
- **Developmental edit** — structure, promise, causality, pacing, character
  arc. Is the draft the right shape?
- **Line edit** — voice, rhythm, clarity, texture. Does the prose move well?
- **Copyedit** — grammar, usage, punctuation, consistency. Is it correct?
- **Proofreading** — final surface pass. What slipped through?

Each level has a dedicated resource with method and checklist:

- `resources/editorial-review.md`
- `resources/developmental-edit.md`
- `resources/line-edit.md`
- `resources/copyedit.md`
- `resources/proofreading.md`

For adversarial craft critique (as opposed to editorial review), load:

- `resources/prose-critique.md` — methodology and focus-area routing.
- `resources/prose-critique/` — deep resources per focus area (structure,
  character, voice, prose, continuity).

## Persona panel

For milestone chapters or disputed judgments, muse fans out `@critic` with
`focus: persona:<name>`. Each persona critiques the chapter's **execution, not its
premise** (base rule) — how the prose works, not whether the story should exist.
Personas load `gates/` for the shared quality bar and score the five axes.

- `resources/prose-critique/personas/wood.md` — James Wood: sentences, consciousness, free indirect style, the life of detail. (Literary fiction.)
- `resources/prose-critique/personas/king.md` — Stephen King: story above all, character, honesty, the hatred of adverbs. (Genre / commercial.)
- `resources/prose-critique/personas/leguin.md` — Ursula K. Le Guin: world-building as meaning, prose as music, the moral weight of imagination, the dragons. (Fantasy / SF.)
- `resources/prose-critique/personas/gay.md` — Roxane Gay: representation, voice and authenticity, the body, power, emotional truth. (Contemporary / literary.)

The four personas are opus-tier read-only critics. Muse synthesizes their reports
(the digest pattern from `fiction/agents/review-coordinator.md`, MIT, may be used
to fan out per-chapter critics and cache reports for 15+ chapter books). A persona
panel is advisory; it does not block a gate.

When review incorporates reader-sim data:

- `resources/reader-sim-signal.md` — how to interpret and synthesize
  reader-sim output alongside analytical critique.

## From findings to a revision plan

Vellum produces findings in four places (critiques, cold-read issues,
demolition logs, the beta report) and the reader-sim lane adds a fifth.
After **any** review program — critique fan-out, cold read, demolition,
beta read — merge all sources into the revision plan instead of presenting
raw lists: dedupe across sources, triage into buckets, and let the author
decide row by row.

- `resources/revision-plan.md` — the `work/revision-plan.md` artifact:
  append-only rows, triage buckets, the `open | in-progress | resolved |
  declined` statuses (declined rows carry the author's reason, verbatim —
  the muse never re-opens one), the intake protocol, and the per-round
  definition of done. `vellum revision status` cross-checks it (report-only).

## When reader reports conflict

When parallel reader reports disagree (beta four-reader protocol, persona
panel, reader-sim lane), run the synthesis protocol before weighing
anything — and never average conflicting verdicts silently:

- `resources/beta-synthesis.md` — strip reader identities, cluster notes by
  passage, classify each `preference | craft | friction`, apply the
  frequency rule (singleton preference = declined-by-default; 3-of-n
  confirms a pattern), and translate every accepted note from symptom to
  candidate cause for critics to confirm before any edit.
