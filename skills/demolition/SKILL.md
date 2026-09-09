---
name: demolition
description: |
  Load when the author invokes demolition on a chapter draft, or when muse offers it before marking a chapter final. The demolition skill is hostile critical analysis applied to fiction: it finds every vulnerability in a chapter — one at a time, never softened, no solutions during demolition — and logs each resolved/deferred/accepted issue in the chapter's Demolition Log. It is the strongest pre-final check; the author may decline it, and declining is recorded.
---

<!-- Adapted from claude-ghost-writer/skills/demolish/SKILL.md — MIT. Changes: re-scoped from essay/manifesto demolition to fiction; 7 vulnerability categories tuned to narrative; chapter Demolition Log placed in the chapter file per vellum conventions; book-level log moved to work/demolition-history.md. -->

# Demolition

Adapted from `claude-ghost-writer/skills/demolish/SKILL.md` — MIT. Changes: re-scoped from essay/manifesto demolition to **fiction** — the 7 vulnerability categories are tuned to narrative (plot causality; established fact/terms; thematic consequence; internal contradictions; premise boundary cases; unearned motivations/setup; genre-contract violations + comps); the chapter Demolition Log is placed in the chapter file per vellum conventions; the book-level `work/demolition-history.md` replaces `demolition-history.md` at project root. Core protocol kept verbatim in spirit: one criticism at a time, never soften, no solutions during demolition, the escalating escape-hatch sequence, weak/strong response tests, `--light` mode.

Demolition is hostile critical analysis. It is not feedback, not a critique, not a line edit. It systematically finds every structural weakness, logical flaw, undefined concept, internal contradiction, and problematic implication in a chapter — **one at a time** — and forces the author to resolve, narrow, or consciously accept each one. It runs on chapter **drafts** (after drafting, before `final`), and muse offers it once per chapter before marking it `final`. The author may decline; declining is recorded in one line in the chapter's Demolition Log.

## When to run

- **Author-invoked** on any chapter draft.
- **Muse-offered** before marking a chapter `final` (muse offers; author may decline).
- Not on every chapter by default — demolition almost never runs unless the author or muse invokes it. It is a stress-test, not a gate.

## Fiction-tuned vulnerability categories

The original 7 categories (logical structure, definitions, implications, internal contradictions, scope/edge cases, missing foundations, external vulnerabilities) are reframed for narrative:

1. **Plot causality** — Does the central dramatic question hold? Non sequiturs? Causation that is asserted, not earned? Does the chapter prove what it promises to prove, or something adjacent?
2. **Established fact / terms** — Are the story's own facts, terms, and rules used consistently? Same term differently in different parts? Metaphors used as arguments? Worldbuilding introduced and then contradicted?
3. **Thematic consequence** — Does the chapter's logic, followed honestly, lead to conclusions the story would reject? Uncomfortable implications the narrative does not acknowledge?
4. **Internal contradictions** — Does any part of the chapter contradict another? Does the resolution contradict a premise? Claims that cannot both be true?
5. **Premise boundary cases** — Does the story break at its edges? Boundary cases the setup cannot accommodate? Scope overstated?
6. **Unearned motivations / setup** — Character choices without visible motivation? Emotional beats that have not been earned? Revelations without setup? Payoffs without cost?
7. **Genre-contract violations + comps** — Does the chapter break the promises the genre made to the reader? Where does it sit next to the comps — better, worse, or reading as a weaker version of an existing book?

## Rules (non-negotiable)

- **One criticism at a time. Always.**
- **Do not soften the criticism.**
- **Do not offer solutions during demolition.** Solutions come in integration (after the chapter is structurally sound).
- **Do not move to the next criticism until the current one is resolved or consciously deferred.**
- **Attack specific claims, terms, implications — never "the chapter in general."**
- **Goal: a stronger chapter, not a defeated author.**

## Persona lenses (optional pre-pass)

For milestone chapters the muse MAY run the story-review persona panel as a demolition pre-pass: spawn `@critic` with `focus: persona:<name>` (wood, king, leguin, gay — `story-review/resources/prose-critique/personas/`), one reader lens per lane, and map each persona's objections onto the 7 vulnerability categories above before Phase 1. The personas surface reader-lens objections (target-reader, hostile-reader, domain-expert, editor angles) that a single demolitionist reading misses; they inform the map — the one-criticism-at-a-time protocol below is unchanged. Critics cannot write; their findings are muse-persisted like any critique.

## Light mode

If the author invokes with `--light`, activate Light Mode: identify only the **3 most critical issues** (the central dramatic question's biggest weakness, the most obvious logical gap or missing evidence, the most predictable objection a reader would raise), skip formal prioritization, then run the one-at-time dialogue normally. Appropriate for late-revision chapters, time pressure, or a quick stress-test.

## Phase 0 — Understand the chapter

Read in order: (1) the full chapter text; (2) the `## Demolition Log` at the bottom of the chapter file; (3) `work/demolition-history.md` — active sections only (Summary, Recurring Patterns, Open Deferred Issues, Accepted Limitations). From the history: check Recurring Patterns (has this vulnerability type appeared in other chapters? flag as a pattern, not a local issue) and Open Deferred Issues (are any relevant to this chapter?).

If a Demolition Log exists: list resolved/integrated issues (do not re-raise), deferred issues (raise first), accepted-limitation issues (skip unless new context makes them critical). Present a brief summary to the author.

If no Log exists, this is the first cycle. Ask: what type of scene is this? Who is the intended reader? What is the one thing you most want this chapter to be remembered for?

## Phase 1 — Map the vulnerabilities

Internally identify all potential weaknesses across the 7 fiction categories. Do not present this map to the author.

## Phase 2 — Prioritize

Select the most serious vulnerabilities; rank by impact (which, if unaddressed, most damages the chapter with the intended reader). Start with the most serious. Never present more than one at a time.

## Phase 3 — Demolish one at a time

State the problem precisely (not "this section is unclear" but "you claim X in paragraph 3, but this is unfalsifiable because..."). Explain why it matters (what does this flaw cost the chapter? who would use it against the story?). **Do not offer the solution.** Ask: "How do you respond to this?"

## Phase 4 — Evaluate the response

When the author responds, evaluate honestly before accepting.

If the author does not know how to respond, apply this escalating sequence — one step at a time:

1. **Rephrase** — restate simpler. Does the problem make sense this way?
2. **Narrow** — forget the whole chapter. Just this: do you think [the specific claim] is true? Why?
3. **Find the intuition** — ignore how to argue it. What do you *feel* is the right answer?
4. **Offer escape hatches** (author chooses and fills in): (a) **Modify** the claim so this criticism no longer applies — how? (b) **Narrow** the scope so this case falls outside it — where's the boundary? (c) **Accept** this as a known limitation and move on.

Never fill in the content of any option. If still stuck after all four steps, defer: park it in the Demolition Log as deferred — sometimes the answer appears after writing more of the book.

A **strong response** modifies the claim, narrows the scope, provides a counter-argument that genuinely neutralizes the criticism, or acknowledges the limitation and declares it outside scope. A **weak response** restates the original claim, changes the subject, appeals to intention ("what I meant was..."), or concedes without integrating. If weak: the original problem remains — try again, or pick an escape hatch.

## Phase 5 — Continue until exhausted

Move through each vulnerability in order of severity. Stop when all major vulnerabilities are addressed, the author asks to stop, or the author declares a known limitation. End with a summary, then update **both logs**:

**1. Chapter Demolition Log** (bottom of the chapter file):

```markdown
## Demolition Log

### Cycle [N] — [date]

| Issue | Category | Status | Resolution |
|---|---|---|---|
| [description] | [category from the 7] | resolved | [one line: how it was resolved] |
| [description] | [category] | deferred | [one line: why deferred] |
| [description] | [category] | accepted-limitation | [one line: declared out of scope because] |
```

**2. `work/demolition-history.md`** (book-level):
- Add this cycle's issues under the chapter's section.
- Update the Summary counters.
- If any issue matches a pattern already seen in another chapter → add/update Recurring Patterns.
- If deferred → add to Open Deferred Issues.
- If accepted-limitation → add to Accepted Limitations.

Then say: both logs updated. The author integrates the resolved responses into the text (muse routes the writer; demolition never writes).
