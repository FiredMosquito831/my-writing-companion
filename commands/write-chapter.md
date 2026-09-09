---
description: Run the chapter loop — outline, author approval, draft, critique, acceptance, capture.
---

Handle via the muse agent. Run the full chapter loop for the chapter named in $ARGUMENTS (if $ARGUMENTS is empty or "next", pick the next chapter from the state card — the lowest `number` with no accepted/final chapter on disk).

1. **Outline.** Spawn `@outliner` for the chapter: beats + per-beat word quotas summing to the outline `word-target`, POV, cast, `verbatim:` lines, and what must NOT be resolved. Outline frontmatter per the gate contract (`approved: false`, `pivotal: false`, `word-target`). If the author gave direction in $ARGUMENTS, pass it through.
2. **Approval.** Show the outline. The author approves → set `approved: true`. You may *propose* a pivotal flag if the chapter turns a major promise or closes an arc; only the author's approval sets `pivotal: true` in the outline frontmatter.
3. **Preconditions.** Run `state check` (interpreter-resolved vellum). Fix or surface anything it reports before drafting.
4. **Draft.** Spawn `@writer` with the fixed context recipe (§9 order): mode + intent; state card; scene brief (this chapter's outline beats + quotas + POV + cast + `verbatim:`); previous-chapter tail (~500–800 words, never the full prior chapter); character cards for `characters:` (+ heavy `mentions`); voice Part 1 summary + Part 2 + one exemplar; relevant vocab; craft pointers by name; word budget + beat quotas; continuity anchors from `vellum pack chapter-NN`. Never raw critique, never the full KB.
5. **Post-write net.** Let the hook run silently. Speak only on tells; debt is recorded, not re-litigated.
6. **Critique.** Spawn 1–2 routine critic lanes (3–5 lanes + `@blind-reader` if pivotal — blind-reader prompt = chapter prose + previous-chapter tail + quality-bar axes, NOTHING else: no outline, no kb, no style files). Synthesize yourself; never forward raw reports.
7. **Present.** Tell the author what changed, what works, what concerns you, what decision is needed. Author approves → acceptance. Pivotal chapters require `work/critique-reports/blind-chapter-NN.md` with verdict ≠ `LOST` on disk before acceptance; no artifact, no acceptance.
8. **Close-out.** The acceptance edit fires the mechanical half (`wordcount --write`, `ledger check`, `state rebuild` — the writer-stop hook runs it as an advisory pre-pass after drafting); route `@kb-lead` for the LLM half — fact/ledger capture (promises, questions, knowledge, props, clock per `/story-ledgers`). The chapter stays `pending_capture: true` until capture completes and the chapter closes to `final`.
9. **Before `final`.** Offer one demolition pass (`/demolition`). Record a decline in one line in the chapter's Demolition Log section.

Interrupt anywhere; the state card carries resume. Ceremony only where it earns its keep: outline approval (once), acceptance (once), three gates (hard).
