# Vellum hooks (Workstream C)

This directory is the deterministic, script-side half of the plugin. Every check that
does not need an LLM lives here; the agents (`agents/`) and skills (`skills/`) handle
judgment. The hooks run under **Git Bash on Windows** (POSIX `sh`-compatible, `LC_ALL=C`,
no associative arrays, no `mapfile`, bash-3.2-safe, LF line endings).

## Layout

```
hooks/
  hooks.json                 # Claude Code hook-event manifest (the only file Claude reads)
  scripts/
    lib/common.sh            # shared library: project_root, vellum_py, gate predicate, helpers
    prose_core.py            # stdlib Python: extract-target / scan / emit-grep
    guard-outline-before-prose.sh   # BLOCKING gate 1 (Write/Edit/MultiEdit)
    guard-bash-prose-writes.sh      # BLOCKING gate 1, alternate path (Bash)
    check-prose-after-write.sh      # advisory post-write prose net
    session-start.sh                 # advisory resume card
    pre-compact.sh                   # snapshot state before compact
    session-stop.sh                  # pending-capture reminder + opt-in stop gate
    chapter-maintenance.sh           # SubagentStop writer: mechanical close-out
```

## hooks.json

The manifest maps Claude Code hook events to scripts. Valid events used:
`PreToolUse`, `PostToolUse`, `SessionStart`, `PreCompact`, `Stop`, `SubagentStop`.

| Event | Matcher | Script | Blocking? |
|---|---|---|---|
| PreToolUse | `Write\|Edit\|MultiEdit` | `guard-outline-before-prose.sh` | **yes** (exit 2) |
| PreToolUse | `Bash` | `guard-bash-prose-writes.sh` | **yes** (exit 2) |
| PostToolUse | `Write\|Edit\|MultiEdit` | `check-prose-after-write.sh` | no (advisory) |
| SessionStart | `startup\|resume\|clear\|compact` | `session-start.sh` | no |
| PreCompact | (none) | `pre-compact.sh` | no |
| Stop | (none) | `session-stop.sh` | only if `stop_gate: true` |
| SubagentStop | `writer` | `chapter-maintenance.sh` | no |

Each script is invoked as `bash "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/<name>.sh"`.
`${CLAUDE_PLUGIN_ROOT}` is the plugin root; the scripts resolve the *author's* project
root themselves via `project_root()` (CLAUDE_PROJECT_DIR -> git root -> cwd).

## The three hard gates (spec 10.1)

1. **Outline before prose** — `guard-outline-before-prose.sh` + `guard-bash-prose-writes.sh`.
   A prose write to `manuscript/chapters/chapter-NN.md` is blocked (exit 2) unless
   `work/outline/chapter-NN.md` exists with frontmatter `approved: true` **and**
   `vellum state check` passes. The outline predicate is pure bash; the engine's
   `state check` is an *additional* precondition that is skipped (one advisory line)
   when no Python interpreter resolves. The gate never dies with a missing runtime —
   fail-open on uncertainty is doctrine (better to miss than mis-block).
2. **Blind reader** — enforced by `@blind-reader` (agent), not a hook.
3. **Beta reader** — enforced by `@beta-reader` + `vellum readiness` (agent/engine).

Everything else (post-write net, demolition, disruptor, persona panel, cold read) is
advisory and silent when clean.

## Script details

### guard-outline-before-prose.sh (BLOCKING)
Reads the hook JSON from stdin, extracts `tool_input.file_path` (via `prose_core.py
extract-target`, with a pure-bash `grep`/`sed` fallback), normalizes the path (drive
letters, backslashes), and runs the shared `prose_gate_block_reason` predicate in
`lib/common.sh`. Non-prose targets and unresolvable paths exit 0 (fail open). On block,
stderr is exactly one sentence naming the missing precondition and the command to fix it.

### guard-bash-prose-writes.sh (BLOCKING, alternate path)
Scans `tool_input.command` for redirection (`>`, `>>`), heredoc, `tee`, `cp`, `mv`
writing into `manuscript/chapters/`, extracts candidate targets, and runs the same
predicate. An **outline-copy detector** blocks a new chapter that is >90% line-identical
to an existing chapter (byte-size pre-filter, then `comm` on sorted lines). Uncertain
cases exit 0.

### check-prose-after-write.sh (advisory + acceptance close-out)
Runs only on `manuscript/chapters/chapter-*.md`. Scans hard signals in bash:
truncation (file <200 bytes, or last line not ending in terminal punctuation —
ASCII class plus multibyte UTF-8 tails so an em-dash or ellipsis ending is
never mis-flagged), model refusal / AI self-reference phrases, placeholder
remnants (`[TODO`, `[INVENTED]`, etc.), engineering/outline words leaked into
prose, and `[VERIFY]` remnants. Then runs the style tier net via
`prose_core.py scan` (tier-1 kill-on-sight, tier-2 cluster heuristic,
em-dash density with the list-item typography carve-out and the measured
baseline cap, near-verbatim duplicate lines), falling back to an embedded
tier-1 `grep` pattern when Python is absent. Output is a `PostToolUse`
`additionalContext` JSON block, one line per finding; exit 0 always; silent
when clean. Writes/updates `work/voice-debt.json` with open tier-1 hits. A
`<!-- voice:skip -->` comment anywhere in the chapter suppresses tier-1 debt
accrual for that chapter (author escape hatch).

When the edit leaves the chapter at `status: accepted`/`final`, this hook also
runs the **mechanical chapter close-out** (`wordcount --write`, `ledger check`,
`state rebuild`) — the transaction fires at acceptance, per
`write-time-capture.md`. Silent on success.

### session-start.sh (advisory)
If `state/state-card.md` exists, prints the 7-section card, the last 5 issue lines from
the most recent cold-read ledger, the pending `[VERIFY]` count, and a resume pointer
(current chapter + outline status). Otherwise one line suggesting `/vellum:status`.
Silent on non-vellum projects.

### pre-compact.sh
Copies `state/state-card.md`, the heads of the `kb/` registry `_index.md` files, the
current chapter path, and the last 40 issue lines into
`work/snapshots/compact-<timestamp>/`. No git operations. Silent on success.

### session-stop.sh
If `state/_tracking-state.json` has `pending_capture: true`, prints one reminder line
naming the close-out (capture via `@kb-lead`, demolition offer, `status: final`,
`python scripts/vellum state rebuild`). If `kb/project-config.json` has
`stop_gate: true`, also runs the hard-signal scan (truncation + refusal only) on the
current chapter and blocks (exit 2) on hits. Default config (`stop_gate: false`)
never blocks.

### chapter-maintenance.sh (SubagentStop, matcher `writer`)
Advisory maintenance pre-pass after the writer finishes: `vellum wordcount --write
&& ledger check && state rebuild` against the chapter the writer actually touched
(identified from the SubagentStop transcript, falling back to the highest-numbered
chapter). Success is **silent** (stdout goes to the transcript). Ledger findings print
as an advisory report. Missing interpreter **or an unavailable engine** falls back to
a bash word-count + an honest advisory line. The transaction itself fires at
acceptance (`check-prose-after-write.sh`), per `write-time-capture.md`.

## Shared library: lib/common.sh

- `project_root()` — CLAUDE_PROJECT_DIR -> git root -> cwd.
- `normalize_target()` — backslash-to-slash + drive-letter absolute path handling.
- `vellum_py()` — interpreter resolution (python3, python, `py -3`; >= 3.8 probe).
- `fm_field()`, `strip_frontmatter()`, `current_chapter()`, `json_escape()`.
- `prose_gate_block_reason()` — the shared gate-1 predicate used by both guards.

## prose_core.py (stdlib Python >= 3.8)

Subcommands:
- `extract-target` — JSON on stdin -> target path on stdout.
- `scan <file> [--format json|text] [--debt <project-root>]` — findings (JSON lines or
  text). Tier tables live at the top of the file (fiction-tuned, re-derived from the
  avoid-ai-writing tier tables, MIT, with the autonovel tier taxonomy credited
  ideas-only). `--debt` updates `work/voice-debt.json` (honors `<!-- voice:skip -->`).
- `emit-grep` — prints a single `grep -E` pattern for the tier-1 table (bash fallback).

## Portability & design rules

- **Never export the tool payload** (E2BIG): Write/Edit/MultiEdit payloads carry whole
  chapters. The payload stays in a shell variable and is piped to the interpreter via
  stdin only where needed.
- **`LC_ALL=C`** everywhere matching happens (byte-stable against non-UTF-8 locales).
- **Fail-open on uncertainty** in blocking gates: parse failure or target ambiguity
  exits 0; the engine's `state check` is skipped (with an advisory) when no Python
  resolves.
- **Silent when clean**: advisory hooks produce no output when there is nothing to say.
- **Windows**: drive-letter paths (`C:/`, `C:\`, lowercase) are normalized; scripts are
  always invoked via `bash` + the resolved Python interpreter (never the exec bit).
