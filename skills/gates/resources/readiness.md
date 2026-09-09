# Readiness

The preconditions `vellum readiness` evaluates before export. The export gate (`/vellum:export`) runs this checklist; it prints PASS or a prioritized missing list. Every item here must be satisfied for the gate to pass. The gate reads artifacts from disk — never the muse's word.

## The checklist

### 1. Every chapter `status: final`; frontmatter complete
- Every chapter under `manuscript/chapters/` has frontmatter `status: final`.
- Frontmatter is complete: `number`, `pov`, `characters`, `mentions`, `promises-advanced`, `word-count` all present (chapters with < 200 words are exempt from the cast/promise fields). `vellum ledger check` emits `frontmatter:incomplete` otherwise — it fails loud, never silently passes.
- `vellum bible validate` is clean, or every remaining finding is covered by an active exemption in `kb/exemptions.json`.

### 2. Ledgers clean
- `vellum ledger check` returns zero unresolved findings outside `kb/exemptions.json`.
- The cold-read `issues.md` has no open BLOCKER. MAJOR/MODERATE findings need a triage note in the machine form: a pipe-delimited line within three lines of the issue carrying `| fixed |`, `| deferred-with-author-signoff |`, or `| accepted-limitation |` verbatim (e.g. `CR-005 | triage | fixed | what was done`) — see `cold-read/resources/issue-format.md`. Plain-language notes without the pipe token do not count.
- `vellum wordcount` is within band for every chapter (default ±15% from `word-target`, per `kb/project-config.json`).

### 3. Readiness report exists and PASSES
`work/critique-reports/readiness-report.md` exists with frontmatter:

```yaml
---
verdict: PASS          # PASS | REVISE
score: 7.8             # mean of axes
axes: {voice: 8, structure: 7, depth: 8, specificity: 8, reader: 8}
put_down_points: []    # chapter numbers; any in ch. 1-3 disqualifies
read_at: 2026-09-09
readers: 4
transcript: <path>     # path of the beta-reader subagent transcript the muse
                       # transcribed; `vellum readiness` verifies it exists
                       # and carries the verdict (provenance binding)
---
```

PASS rule (from `quality-bar.md`): every axis ≥ 7, mean ≥ 7.5, no put-down in chapters 1–3. The gate reads artifacts from disk — never the muse's word — so the report also cites the beta-reader run behind it via `transcript:`.

### 4. Word-budget report attached
Total manuscript word count vs. plan, and per-chapter band compliance. Produced by `vellum wordcount`.

### 5. Pivotal chapters have blind artifacts
Every chapter the author flagged `pivotal: true` at outline acceptance has a `work/critique-reports/blind-chapter-NN.md` with verdict ≠ `LOST`. `vellum readiness` cross-checks: a `pivotal: true` chapter without its artifact is a missing item. (This closes the "partial blind gate" — the gate is binary per pivotal chapter.)

## How muse uses this

Muse does not re-litigate the checklist. Muse runs `vellum readiness`, reads its output, and presents the prioritized missing list to the author. When the list is empty, muse runs `vellum export build`. The gate is the engine's verdict, not muse's judgment.

## Opt-in gates (default off)

`kb/project-config.json` can enable two additional gates without changing this checklist:
- `voice_debt_gate: true` — the post-write net's tier-1 debt becomes blocking (not advisory).
- `stop_gate: true` — `session-stop.sh` blocks on truncation/refusal markers in the current chapter.

Both default **off** — the three hard gates stay exactly three unless the author opts in.
