# The State Card

Mechanism from `oh-story-claudecode/skills/story-long-write/SKILL.md` context-file design (MIT) — the fixed-section, ≤12KB, engine-regenerated state card. Changes: structure rewritten for English and the vellum layout; the seven sections are fixed by spec §7.2; hash-verified (engine writes `state/_derived-hashes.json`; mismatch → finding `state:hand-edited`).

The state card (`state/state-card.md`) is the **one-screen interrupt/resume** artifact. It is the only state file a human reads; everything under `state/` else is machine-authoritative and **never hand-edited** (the engine enforces this with sha256 hashes — `vellum state rebuild` regenerates, `vellum state check` verifies). The card is rebuilt after every chapter transaction (`chapter-maintenance.sh` → `vellum state rebuild`).

## Hard constraints

- **≤ 12 KB.** The engine refuses to write and reports if content overflows. If your content threatens the cap, cut prose before cutting sections — all seven sections are mandatory.
- **Seven fixed sections**, in this order. Never add, remove, or reorder.
- **Engine-written, never hand-edited.** Derived from `kb/` + `manuscript/` frontmatter + ledgers. If prose and state disagree, surface — never silently fix (GR-09: manuscript prose > outline > state > derived metrics).

## The seven sections

### 1. Story position
Where the reader is *now*: the current chapter, its status (`outlined|draft|revised|accepted|final`), the POV character, the immediate situation, and the story-day/clock reading from `kb/clock.md`. 2–4 lines. This is the first thing a resumed session reads.

### 2. Open promises & questions (top N by age)
The oldest unresolved promises and questions, drawn from `kb/promises/` and `kb/questions/`. Top N by age (default 5), each one line: id, status, planted/raised in, target-by if any. Dormant promises (no movement > 3 chapters) flagged. This is the "what is the reader waiting on" view.

### 3. Active cast state (one line each)
One line per active character: id, name, status (`alive|deceased|unknown`), last-seen chapter, and a one-phrase situation. Dead characters omitted unless relevant to an open promise. POV-eligible cast marked.

### 4. Knowledge boundaries
Who knows what that matters *now*: drawn from `kb/knowledge/`. Only knowledge that could be misused — secrets, things learned off-page, things the reader knows but a character doesn't. A character acting on unheld knowledge is a BLOCKER; this section is the cheat-sheet that prevents it.

### 5. Props & clock
The active-prop inventory (id, holder, location, status) from `kb/props/`, and the current row of every active clock thread from `kb/clock.md`. Collisions (two props, one slot) flagged.

### 6. Next beats with word quotas
The next chapter's outline beats (from `work/outline/chapter-NN.md`): beat summary + POV + word quota, summing ≈ the chapter's `word-target`. This is the writer's immediate brief.

### 7. Flags
The engine-emitted warnings, one line each (`state.py _build_card` — nothing else appears here):
- Active exemptions (count + oldest), stale exemptions re-armed.
- Open voice-debt count from `work/voice-debt.json` (the post-write net's open tier-1 items).
- Any `pending_capture: true` warning (the previous chapter's transaction is not yet closed).

The cold-read state — the do-not-re-explain register, open BLOCKERs/MAJORs — lives in the active cold-read ledger (`work/cold-reads/<YYYY-MM>/reader_ledger.md` + `issues.md`), not on the card; the resume recipe loads the last ~40 issue lines alongside the card.

## How it is used

- **SessionStart** (`hooks/session-start.sh`): prints the card + last 5 `work/` issue lines + pending `[VERIFY]` count + resume pointer. One screen; resume is instant.
- **Writer spawn** (§9 recipe slot 2): the card is inlined (~1.2k tokens) so the writer has full continuity context without reading the whole KB.
- **Muse**: reads the card to confirm direction before spawning the next agent. Never hand-edits it.

## What it is not

The card is a *view*, not the source of truth. The sources are `kb/`, `manuscript/` frontmatter, and the ledgers; the card is derived from them by `vellum state rebuild`. If the card and the sources disagree, the sources win and the card is rebuilt — the discrepancy is surfaced to the author, never silently resolved.
