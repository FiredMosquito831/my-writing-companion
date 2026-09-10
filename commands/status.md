---
description: Print the state card, gate statuses, and open findings summary.
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents). Report project status in one screen, no ceremony.

1. **State card.** Print `state/state-card.md` verbatim if it exists; if missing, run `state rebuild` first (never hand-write it). If no interpreter resolves, say so and rebuild nothing.
2. **Gate statuses** — read from artifacts on disk only, never from memory:
   - Outline gate: is there a chapter in `work/outline/` awaiting approval (`approved: false`)?
   - Blind gate: list every chapter with `pivotal: true` in its outline and whether `work/critique-reports/blind-chapter-NN.md` exists with verdict ≠ `LOST`.
   - Export gate: does `work/critique-reports/readiness-report.md` exist with `verdict: PASS`?
3. **Open findings.** Run `ledger check` and `bible validate` (skip with a one-line note if no interpreter resolves); summarize unresolved findings outside `kb/exemptions.json`, plus `debt list` when `voice_debt_gate` is on.
4. **Resume pointer.** Current chapter, its outline status, pending `[VERIFY]` count, next suggested action (`/vellum:write-chapter next`, a pending capture, or export readiness).

Ground truth precedence: user > manuscript prose > outline > state > derived metrics. If state and prose disagree, surface the conflict to the author — never silently fix either side.
