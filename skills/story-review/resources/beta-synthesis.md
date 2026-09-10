# Beta Synthesis: Conflicting Reader Reports

Mechanism credited to public craft citations — Neil Gaiman's reader-feedback maxim (via public citation), Spann Craig's beta-management practice, and MorningStar Editing's feedback-triage guidance; ideas only — no source text copied. Changes: re-cast as the vellum merge protocol for parallel reader reports; the classification, frequency rule, and symptom-to-cause translation are written fresh for the vellum loop and wired into the shared finding schema and revision plan.

Load this when merging **parallel reader reports that conflict** — the beta four-reader protocol, the persona panel, a reader-sim lane, or any mix. `reader-sim-signal.md` covers sim-vs-critique convergence; this file covers reader-vs-reader conflict. The rule it enforces: **never average conflicting verdicts silently.** Averaged axes hide the disagreement the author most needs to see.

## Step 1 — Strip identities, cluster by passage

Re-sort the notes by **passage, not by reader**. Reader identity is metadata, not evidence: "Reader C hated chapter 12" is unusable, "chapter 12's time skip confused two of four readers" is signal. A passage-centered cluster shows immediately whether the reports disagree about the same text or are talking past each other about different ones.

## Step 2 — Classify every note before weighing it

Each note gets one class, applied before any weighing happens:

| Class | Meaning | What it weighs as |
|---|---|---|
| `preference` | Taste: a different reader, or the same reader on another day, could want the opposite | Logged; see the frequency rule |
| `craft` | A technique-level fault the prose model can confirm (POV break, unearned turn, filter words) | Weighed by evidence; route to critics for confirmation |
| `friction` | A report of stumbling: confusion, a re-read, a dropped thread, a put-down moment | Always investigated — friction is *what happened to the reader*, and readers do not fake it |

The same complaint can be any of the three. "The dialogue is too quippy" is a preference when it names a style, craft when it names homogenized voices, friction when the reader reports losing track of who is speaking. Classify from the note's evidence, not its tone.

## Step 3 — The frequency rule for preferences

- A **singleton preference** — one reader, one passage, class `preference` — is logged as **declined-by-default** (into the revision plan, with the reader count in the note) unless the author explicitly overrides. One reader's taste is data about one reader.
- **3-of-n confirms a pattern**: when the same preference-class note appears from three or more readers (or a clear majority), it stops being taste and becomes evidence about the book's actual audience — reclassify with the author.
- `craft` and `friction` notes are **not** subject to the frequency rule. One reader's genuine friction outweighs three readers' indifference; craft findings stand or fall on the prose model, not the vote count.

Record the counts (`1 of 4`, `3 of 4`) in the merged finding — the author decides with the distribution visible.

## Step 4 — The Gaiman discipline

Readers are almost always **right about what's wrong** and almost always **wrong about the fix**. Remember the maxim when their suggested fixes conflict: the contradiction lives in the fixes, not in the underlying reports. Two readers demanding opposite changes to a passage are usually both pointing at the same defect from opposite sides.

So, for every accepted note:

1. **Translate symptom → candidate cause.** "The sentry scene drags" is a symptom; candidate causes are a missing goal, a repeated emotional beat, or late entry into the scene. The note itself never names the cause — readers diagnose what happened to them, not why.
2. **Critics confirm the cause before any edit.** Hand the candidate causes to a critique pass as findings to confirm or kill (signal-class `friction` findings, shared schema). No edit proceeds on a reader's self-diagnosis.
3. **Confusion never auto-means "add explanation."** The default reflex — reader is confused, therefore add a paragraph of explanation — is the single most damaging misreading of feedback. Confusion is diagnostic of an information-design problem somewhere near the passage; the fix is as often to cut a spoiler, sharpen a want, or let the reader hold the question longer. Confirmed confusion routes to a critic, never straight to added prose.

## Output

- Accepted notes → candidate causes for critics to confirm → confirmed findings become rows in `work/revision-plan.md` (`resources/revision-plan.md`).
- Declined-by-default singleton preferences → declined rows in the plan with the count and the class in the note, so the decision is auditable and the muse never re-raises it.
- The author sees the **conflict, not the mean**: which clusters disagreed, at which passages, in which classes, with counts.
