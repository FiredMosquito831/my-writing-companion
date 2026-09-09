# Vellum

A working novelist's daily tool for Claude Code: one command for the chapter loop, three hard gates, everything else advisory and silent when clean.

Fork of [`haowjy/creative-writing-skills`](https://github.com/haowjy/creative-writing-skills) (Apache-2.0). See [ATTRIBUTION.md](ATTRIBUTION.md) for the provenance of every ported mechanism, [VALIDATION.md](VALIDATION.md) for the validation and test record, and [NOTICE](NOTICE) for license notices. The binding build spec is [DESIGN.md](DESIGN.md).

## What it is

Vellum sits between you and your manuscript the way a good first reader and a continuity-minded editor would: always there, never in the way.

- **One command for the chapter loop** — `/vellum:write-chapter`: outline → you approve → draft → critique → acceptance → knowledge capture. Interrupt anywhere; the state card puts you back in one screen.
- **Exactly three hard gates** — approved outline before prose, a blind-reader verdict on pivotal chapters, a beta-reader PASS before export (see [The gate model](#the-gate-model)).
- **Everything else advisory and silent when clean** — prose tells, continuity lints, voice drift: they surface only when they have something to say.
- **The author decides** — findings you call intentional are recorded as exemptions in your own words and never re-raised (unless the underlying fact changes, which re-arms the question once).

## Architecture overview

Four layers, deliberately separated:

1. **The deterministic engine** — `scripts/vellum` + `scripts/vellum_lib/` is a Python ≥ 3.8, **stdlib-only** CLI (no pip, no Node, no build). It absorbs every check no LLM should burn tokens on: state rebuild/check, ledger checks (dead characters, promise ordering, knowledge boundaries, prop custody, clock monotonicity), word counts and bands, bible validation, measured style stats, context packing, exemptions, and the export build (markdown bundle + stdlib EPUB). Agents invoke it through their Bash allowlists; it is also copied into your project by setup so it runs from the project root.
2. **Hooks** (`hooks/`) — harness-enforced. The outline gate (Write/Edit and Bash paths) blocks unapproved prose; the post-write prose net scans drafts for AI tells and hard signals and stays silent when clean; the session lifecycle (state card on session start, snapshot before compact, pending-capture reminder on stop, mechanical chapter close-out after the writer subagent finishes).
3. **Agents** (`agents/`, 16) — the **muse** is the coordinator and primary entry point: it owns the gates (from artifacts on disk only), routes every specialist (outliner, writer, critics, blind/beta/cold readers, kb-lead, disruptor, style-creator), and never re-litigates your dismissed choices. Critics and readers are read-only by frontmatter; the writer can write only under `manuscript/` and `work/drafts/` (plus a few named work files); stance isolation means critique, drafting, and memory-update never share a context.
4. **Skills** (`skills/`, 32) — the methodology container: craft references, ledger schemas, gate rubrics, the cold-read protocol, demolition, voice and style work. Agents declare their skill sets; resources load on demand.

## Install

Requirements: Claude Code, Git (hooks run under its bundled bash), and a Python ≥ 3.8 interpreter on PATH (`python3`, `python`, or the Windows `py -3` launcher). Node is not required. Pandoc is optional (DOCX/PDF export only; the markdown bundle and EPUB build without it).

This repo is a self-registering marketplace: `.claude-plugin/marketplace.json` declares one plugin, `vellum`, with `source: "."`.

**From GitHub:**

```
/plugin marketplace add FiredMosquito831/my-writing-companion
/plugin install vellum@my-writing-companion
```

(or from a terminal: `claude plugin marketplace add FiredMosquito831/my-writing-companion` then `claude plugin install vellum@my-writing-companion`.)

**From a local clone** (if you've checked the repo out):

```
claude plugin marketplace add C:/path/to/my-writing-companion
claude plugin install vellum@my-writing-companion
```

(or add the folder through the in-session `/plugin` UI: Add marketplace → paste the path → Install vellum.)

Verify with `/plugin` (vellum should be enabled) — after your next session start, the `/vellum:` commands are available.

## Quickstart: your first session

1. **Set the project up.** In your novel folder (empty or existing), tell Claude: *"Set up my novel project."* This routes to the `project-setup` skill, which interviews you (genre, POV, progress, writing samples), seeds the full project layout (`manuscript/`, `kb/`, `state/`, `work/`, `export/`), copies the engine (`scripts/`) and `templates/` into the project, and ends with a voice-capture interview — 3–5 samples of your own prose go to `kb/samples/` and `@style-creator` builds `kb/styles/voice.md` and the measured baseline. Then initialize the engine state once: `python scripts/vellum state rebuild` (use `python3` or `py -3` on Windows as available).
2. **Check the dashboard.** `/vellum:status` prints the state card, gate statuses, and the resume pointer. On every future session start, the SessionStart hook prints the card automatically.
3. **Write a chapter.** `/vellum:write-chapter next` (or a chapter number): the muse spawns `@outliner` (beats with word quotas + verbatim lines), shows you the outline, and you approve it — that approval (`approved: true` in the outline frontmatter) is what disarms gate 1. Say "pivotal" if the chapter is load-bearing; only you set that flag.
4. **Draft, critique, accept.** The muse spawns `@writer` with a fixed context pack (state card, scene brief, previous-chapter tail, cast cards, voice, word budget). The post-write net runs silently. Critics report; the muse synthesizes and asks for your acceptance. A pivotal chapter additionally needs the blind reader's verdict (`ENGAGED`/`STALLED`, never `LOST`) before acceptance.
5. **Capture and close.** Acceptance triggers the mechanical close-out (word counts, ledger check, state rebuild) and routes `@kb-lead` to extract facts into the ledgers. Before a chapter is marked `final`, the muse offers one demolition pass — you may decline.
6. **Later** — `/vellum:cold-read` (batch fresh-eyes reads with a rolling reader ledger), `/vellum:retune` (voice recalibration from a raw sample), `/vellum:export` (readiness check, then a markdown bundle + EPUB with a manifest recording gate provenance).

## The gate model

Exactly three hard gates; everything else is advisory. Each blocking gate reads its **artifact from disk** — never a claim from chat. Gate predicates fail open on genuine uncertainty (a missing Python runtime can never mis-block you); the one deliberate exception is gate-input protection, which fails closed when it cannot verify session context.

| # | Gate | Enforced by | Blocks | Satisfied by |
|---|---|---|---|---|
| 1 | Approved outline before prose | PreToolUse hooks on Write/Edit **and** Bash (redirection, heredoc, `sed -i`, copy-laundering all checked) | Any write into `manuscript/chapters/` | `work/outline/chapter-NN.md` with frontmatter `approved: true`, plus `state check` (no half-committed prior chapter, no pending capture). Gate-input protection: subagents cannot self-approve outlines or forge critique artifacts. |
| 2 | Blind-reader verdict on pivotal chapters | `state check` at acceptance + `vellum readiness` cross-check | Marking a `pivotal: true` chapter `accepted` | `work/critique-reports/blind-chapter-NN.md` written from a real `@blind-reader` run (the agent sees only the chapter + previous tail — it has Read and nothing else), verdict ≠ `LOST`, with transcript provenance. |
| 3 | Beta-reader PASS before export | `vellum readiness` (required by `/vellum:export`) | Export | `work/critique-reports/readiness-report.md` with frontmatter `verdict: PASS` — every axis ≥ 7, mean ≥ 7.5, no put-down point in chapters 1–3 — from a real `@beta-reader` run, with transcript provenance. |

Advisory layers that never block by default: the post-write prose net (AI-tell tiers, hard signals, voice-debt ledger), cold-read BLOCKER-class issues (block export only until resolved or dismissed with your sign-off), the disruptor lane, the persona panel. Two further gates exist but ship **off**: `voice_debt_gate` and `stop_gate` in `kb/project-config.json` — flip them on only if you want a fourth and fifth hard gate.

Your dismissals are first-class: `vellum dismiss <key> --reason "<your words>"` (or `/vellum:dismiss`) records the exemption; no agent re-raises it. If the underlying fact later changes, the exemption goes `stale` and re-arms exactly once.

## State files explained

`project-setup` seeds your novel repo with:

```
manuscript/chapters/chapter-NN.md   # the prose — ground truth
kb/                                 # the story bible (yours to edit)
  story.md  characters/  world/  timeline/
  styles/{voice.md, baseline.md}  samples/  vocab.md
  promises/  questions/  knowledge/  props/  clock.md
  issues/  exemptions.json  project-config.json
state/                              # machine-authoritative — NEVER hand-edit
  _tracking-state.json  _derived-hashes.json  state-card.md  .vellum.lock
work/                               # scratch: outline/, drafts/, critique-reports/,
  cold-reads/<YYYY-MM>/  snapshots/  voice-debt.json  demolition-history.md
export/                             # build artifacts only
```

The `state/` files are the engine's:

- **`state/_tracking-state.json`** — the transactional tracking state: per-chapter statuses, `pending_capture` (an accepted chapter whose knowledge capture hasn't closed), schema version. `state check` refuses a new chapter start while a transaction is half-committed.
- **`state/state-card.md`** — the fixed 7-section one-screen resume card (story position, open promises/questions, active cast, knowledge boundaries, props & clock, next beats with quotas, flags), hard-capped at 12 KB. Session start prints it; the writer's context pack inlines it.
- **`state/_derived-hashes.json`** — sha256 of the last engine-written content of the two files above. If you hand-edit a derived file, the hash check raises `state:hand-edited` and tells you the fix: run `python scripts/vellum state rebuild`.
- **`state/.vellum.lock`** — exclusive write lock (stale locks over 60 s are warned and cleared).

Division of authority: your prose and your edits are ground truth; `kb/` is durable canon; `state/` is derived and engine-owned; `work/` is scratch. When state and prose disagree, vellum surfaces the conflict — it never silently rewrites prose to match stale tracking.

## Windows notes

- **Hooks run under Git Bash** (`bash "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/..."`), which ships with Git for Windows; no WSL needed.
- **Interpreter resolution** tries `python3`, then `python`, then the `py -3` launcher (installed with python.org Python) — each probed for ≥ 3.8. The engine is always invoked via the resolved interpreter, never an exec bit. The outline gate's core predicate is pure bash, so gate 1 still works with no Python at all (engine preconditions are then skipped with a one-line advisory — fail-open by doctrine).
- **Path handling** is tested on `windows-latest` CI: drive letters (`C:/`, `C:\`, lowercase), paths with spaces, CRLF files, and UTF-8 BOMs are all normalized; all repo files are pinned to LF via `.gitattributes`; `LC_ALL=C` is set wherever byte-stable matching matters.
- **Large payloads** are never passed as arguments (the E2BIG trap) — hook input is piped to the interpreter via stdin; there is a regression test for >128 KiB payloads.
- The pytest suite runs in CI on both `ubuntu-latest` and `windows-latest`; on Windows, run it from any bash (e.g. Git Bash): `python -m pytest tests/ -q`.

## What it installs

- **agents/** — 16 agents (muse, outliner, writer, critic, editor, blind-reader, beta-reader, cold-reader, kb-lead, disruptor, style-creator, continuity-checker, character-sim, reader-sim, brainstormer, web-researcher).
- **skills/** — 32 skills, including `story-ledgers`, `gates`, `style-guardrails`, `voice`, `cold-read`, `demolition`, `export`, `kb-integrity`, `project-setup`.
- **commands/** — `/vellum:write-chapter`, `/vellum:status`, `/vellum:cold-read`, `/vellum:retune`, `/vellum:export`, `/vellum:dismiss`. Each command body addresses the muse; the three hard gates are read from disk artifacts only, never satisfied by judgment.
- **hooks/** — 7 hook scripts across 6 lifecycle events (see `hooks/README.md`).
- **templates/** — the schemas your project is seeded with (chapter frontmatter, promise/question/knowledge/prop/character ledgers, state card, scene cards, cold-read kit, project config, measured baseline).

## Status: v0.1.0

Implemented per DESIGN.md: 16 agents, 32 skills, 6 commands, 7 hooks, the Python engine (all subcommands, stdlib-only), templates, 79 passing tests on a seeded fixture project, and CI (`.github/workflows/{ci,tests}.yml` + `scripts/ci/lint_vellum.py`). An end-to-end paper-run exercised every gate, hook, and engine path on Windows — see [VALIDATION.md](VALIDATION.md) for the record and the known limitations it logged.

One setup note: the engine runs from the author project — `project-setup` copies the plugin's `scripts/` into the project so `python scripts/vellum …` resolves; the hooks always use the plugin's copy via the resolved interpreter.

## License

Apache-2.0 (inherited from the base fork; see [LICENSE](LICENSE)). Ported MIT sources keep their notices; unlicensed sources contributed ideas only — no text or code copied.
