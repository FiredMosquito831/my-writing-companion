# Write-Time Capture — the Chapter Transaction

<!-- Adapted from oh-story-claudecode (skills/story-setup, transactional state design) — MIT. Changes: rewritten in English for the vellum layout; the transaction trigger, pending_capture semantics, and the hook split (writer-stop pre-pass + acceptance close-out) are vellum-specific. -->

The chapter transaction is the mechanical + LLM close-out that runs when a chapter moves to `accepted`. It has two halves that must both complete before the next chapter can be drafted: a **mechanical half** (the `chapter-maintenance.sh` hook — deterministic, silent on success) and an **LLM half** (muse routes `@kb-lead` for fact and ledger capture). This file is the operator's manual for the transaction. The golden rule: **never hand-edit derived files** — the engine regenerates them and hash-verifies.

## When it runs

The transaction fires at **chapter acceptance** — the PostToolUse hook (`check-prose-after-write.sh`) runs the mechanical close-out the moment an edit leaves a chapter at `status: accepted` (or `final`). The SubagentStop hook (`chapter-maintenance.sh`, matcher `writer`) runs the same mechanical pass as an **advisory pre-pass** right after drafting, against the chapter the writer actually touched (identified from the SubagentStop transcript) — that pass keeps word counts and the state card fresh while the chapter is still a draft; the transaction itself completes at acceptance. Muse separately routes `@kb-lead` for the LLM half.

`pending_capture: true` is set by acceptance: a chapter sitting at `status: accepted` has an unclosed transaction (capture, demolition decision, close to `final` still owed), and `state rebuild` derives the flag from that. The transaction must complete before the next chapter's outline-before-prose gate will pass — `vellum state check` refuses a new-chapter start while `pending_capture: true`, and `session-stop.sh` prints one reminder naming the close-out while it is set.

## The mechanical half (`check-prose-after-write.sh` at acceptance; `chapter-maintenance.sh` as the writer-stop pre-pass)

Runs silently on success (stdout goes to transcript, so silent-on-success is mandatory):

1. `vellum wordcount --write` — compute words per chapter, update `word-count` frontmatter, band-check vs `word-target`.
2. `vellum ledger check` — deterministic continuity over the just-accepted chapter (findings print; they do not abort the rebuild).
3. `vellum state rebuild` — regenerate `state/_tracking-state.json` and `state/state-card.md` from the updated `kb/` + frontmatter + ledgers; recompute `voice_debt`; write `_derived-hashes.json`; derive `pending_capture`.

A missing interpreter or an unavailable engine degrades to a bash wordcount + one honest advisory line naming the cause (the gate never dies with a missing runtime; fail-open is doctrine). The SubagentStop pre-pass targets the chapter the writer actually touched (transcript-derived), so a revision of chapter 3 updates chapter 3, not the highest-numbered file.

## The LLM half (`@kb-lead`)

Muse routes `@kb-lead` to capture what the mechanical half cannot judge:

- **Fact extraction**: new canon facts the chapter established (character state, timeline, reveals, terminology) → written to `kb/` under kb-lead's exclusive write access.
- **Ledger capture**: new promises planted/reinforced/paid, questions raised/answered, knowledge gained (with `learned-in` + certainty), prop custody changes, clock advances → written to the ledger files. Custody movement is mirrored in the chapter's `custody:` frontmatter (prop ids the chapter holds or moves) — `ledger check` validates it against each prop's recorded status.
- **Frontmatter backfill**: complete any chapter frontmatter fields the writer left blank when determinable from ledger/prose evidence; flag anything uncertain as a finding instead of guessing.
- **Promotion decisions**: provisional → canon facts are reported to muse for author confirmation before writing settled canon.

kb-lead runs `vellum state rebuild` + `vellum bible validate` + `vellum ledger check` after its updates and fails loudly on schema violations. kb-lead **never** touches `manuscript/`, `work/drafts/`, or `state/` by hand (engine-regenerated only).

## The close-out sequence (author's view)

1. Chapter accepted → the mechanical close-out fires (acceptance edit → PostToolUse hook); muse routes `@kb-lead` for the LLM half.
2. `pending_capture` reads `true` while the chapter sits at `status: accepted`.
3. Capture + demolition decision complete → the chapter moves to `final` → the next rebuild flips `pending_capture` to `false`.
4. Next session's SessionStart hook prints the updated card → resume is one screen.
5. Next `/vellum:write-chapter` passes the outline gate.

## Never hand-edit derived files

`state/_tracking-state.json`, `state/state-card.md`, and the ledger `_index.md` registries are engine-written. The engine hash-verifies them (`state/_derived-hashes.json`); a mismatch → finding `state:hand-edited` ("state files are engine-written; run `vellum state rebuild`"). `vellum bible reindex` repairs the registries. If you need to change what a derived file says, change its *sources* (`kb/`, frontmatter, ledgers) and rebuild — never edit the derived file directly.
