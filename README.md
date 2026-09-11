<div align="center">

# 📖 Vellum

**A working novelist's daily tool for Claude Code.**

One command for the chapter loop. Three hard gates.<br/>
Everything else advisory — and silent when clean.

[![Tests](https://github.com/FiredMosquito831/my-writing-companion/actions/workflows/tests.yml/badge.svg)](https://github.com/FiredMosquito831/my-writing-companion/actions/workflows/tests.yml)
[![Lint](https://github.com/FiredMosquito831/my-writing-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/FiredMosquito831/my-writing-companion/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
[![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-8A5CF6.svg)](https://claude.com/claude-code)

[Install](#-install) · [Quickstart](#-quickstart-your-first-session) · [Gate model](#-the-gate-model) · [Library & series (v0.2.0)](#-library--series-layer-v020) · [Architecture](#️-architecture) · [FAQ](#-faq)

</div>

---

Vellum is authored by [FiredMosquito831](https://github.com/FiredMosquito831) — a fork of [`haowjy/creative-writing-skills`](https://github.com/haowjy/creative-writing-skills) (Apache-2.0), rebuilt into a complete novel-writing harness that combines the best verified mechanisms of twenty systems in this space (see [Credits](#-credits--how-vellum-improves-on-them)). Every ported mechanism is credited in [ATTRIBUTION.md](ATTRIBUTION.md), the build spec lives in [DESIGN.md](DESIGN.md), and the full validation record — including what we know is still rough — is in [VALIDATION.md](VALIDATION.md).

## 🤔 Why Vellum?

Long-form fiction is where LLM workflows fall apart. Drafts drift toward the statistical average. Critique leaks into drafting and everything starts flattering itself. Continuity dies at context compaction, somewhere around chapter nine. And "please be consistent" is a wish, not a mechanism.

Vellum replaces wishes with machinery:

- **Gates read from disk, not from chat.** An agent can *say* the outline was approved. Gate 1 checks the outline file's frontmatter. Claims don't unblock prose; artifacts do.
- **Critique never shares a context with drafting.** Sixteen agents with strict stance isolation: the writer can't read the critiques, the critics can't write prose, and the coordinator owns the gates from artifacts only.
- **The boring checks run in Python, not tokens.** A stdlib-only engine handles dead characters reappearing, promises out of order, props teleporting, knowledge arriving before its chapter. An LLM never spends your quota on what a hash check already knows.
- **State survives the session.** A fixed one-screen state card, rebuilt mechanically, printed at every session start. Put the manuscript down for a month; pick the thread back up in one read.
- **You are the editor-in-chief.** Call a finding intentional and it's recorded as an exemption *in your own words*, never re-raised. If the underlying fact changes, the question re-arms exactly once.

## ✨ Highlights

| | | |
|---|---|---|
| 🔁 | **One-command chapter loop** | `/vellum:write-chapter` runs outline → approval → draft → critique → acceptance → knowledge capture. Interrupt anywhere; the state card puts you back in one screen. |
| 🚦 | **Three hard gates, exactly** | Approved outline before prose. A blind-reader verdict on pivotal chapters. A beta-reader PASS before export. Nothing else blocks you. |
| 🤫 | **Advisory by default** | Prose tells, continuity lints, voice drift — they surface only when they have something to say, and stay silent when clean. |
| 🎙️ | **Your voice, measured** | Style profiles built from *your* prose samples, with drift detection against a measured baseline. Per-character dialogue fingerprints catch character voices drifting into one. Style bans never override your measured voice. |
| 🕵️ | **Readers who can't flatter you** | The blind reader sees your chapter and nothing else — no outline, no plan, no context to be fooled by. The beta reader scores before export; a hard PASS or the export waits. |
| 📚 | **Series-aware (v0.2.0)** | An optional library/series layer for multi-book canon: a series bible with per-book value maps, a retcon lifecycle that records your words verbatim, published books frozen by default. Findings stay advisory — the gates stayed three. |
| 🪟 | **Windows-first, dependency-light** | No Node, no pip, no WSL, no build step. Python ≥ 3.8 stdlib only. Tested on `ubuntu-latest` *and* `windows-latest` CI. |

## 📦 Install

Requirements: Claude Code, Git (hooks run under its bundled bash), and a Python ≥ 3.8 interpreter on PATH (`python3`, `python`, or the Windows `py -3` launcher). Node is not required. Pandoc is optional (DOCX/PDF export only; the markdown bundle and EPUB build without it).

**From GitHub:**

```
/plugin marketplace add FiredMosquito831/my-writing-companion
/plugin install vellum@my-writing-companion
```

Prefer the terminal? `claude plugin marketplace add FiredMosquito831/my-writing-companion`, then `claude plugin install vellum@my-writing-companion`.

**From a local clone:**

```
claude plugin marketplace add C:/path/to/my-writing-companion
claude plugin install vellum@my-writing-companion
```

Verify with `/plugin` (vellum should be enabled). After your next session start, the `/vellum:` commands are live.

## 🚀 Quickstart: your first session

1. **Set up the project.** In your novel folder (empty or an existing manuscript), run `/vellum:init` or tell Claude: *"Set up my novel project."* The `project-setup` skill interviews you (genre, POV, progress, writing samples), seeds the layout (`manuscript/`, `kb/`, `state/`, `work/`, `export/`), copies the engine and templates in, closes with a voice-capture interview (3–5 samples of your own prose become `kb/styles/voice.md` and the measured baseline), and finishes by running the initial `state rebuild` for you.
2. **Check the dashboard.** `/vellum:status` prints the state card, gate statuses, and the resume pointer. From now on, every session starts with the card on screen.
3. **Write a chapter.** `/vellum:write-chapter next` (or any number). The muse spawns `@outliner` for beats with word quotas and verbatim anchor lines, shows you the outline, and waits. Your approval — `approved: true` in the outline's frontmatter — is what disarms gate 1. Say "pivotal" if the chapter is load-bearing; only you set that flag.
4. **Draft, critique, accept.** The muse spawns `@writer` with a fixed context pack: state card, scene brief, previous-chapter tail, cast cards, voice profile, word budget. The post-write net scans silently. Critics report; the muse synthesizes; you accept. Pivotal chapters also need the blind reader's verdict before acceptance.
5. **Capture and close.** Acceptance triggers the mechanical close-out — word counts, ledger check, state rebuild — and routes `@kb-lead` to extract what happened into the ledgers. Before a chapter goes `final`, the muse offers one demolition pass. You may decline; demolition is a tool, not a tax.
6. **Later.** `/vellum:cold-read` for batch fresh-eyes reads with a rolling reader ledger, `/vellum:retune` to recalibrate voice from a raw sample, `/vellum:export` for the readiness check and the EPUB build.

## 🚦 The gate model

Exactly three hard gates; everything else is advisory. Each gate reads its artifact **from disk** — never a claim from chat. Predicates fail open on genuine uncertainty (a missing Python runtime can never mis-block you). The one deliberate exception: gate-input protection fails closed when it cannot verify session context.

| # | Gate | Enforced by | Blocks | Satisfied by |
|---|---|---|---|---|
| 1 | **Approved outline before prose** | PreToolUse hooks on Write/Edit *and* Bash (redirection, heredoc, `sed -i`, copy-laundering all checked) | Any write into `manuscript/chapters/` | `work/outline/chapter-NN.md` with frontmatter `approved: true`, plus `state check` (no half-committed prior chapter, no pending capture). Subagents cannot self-approve outlines or forge critique artifacts. |
| 2 | **Blind-reader verdict on pivotal chapters** | `state check` at acceptance + `vellum readiness` cross-check | Marking a `pivotal: true` chapter `accepted` | `work/critique-reports/blind-chapter-NN.md` from a real `@blind-reader` run (it sees only the chapter and the previous tail — it has Read and nothing else), verdict ≠ `LOST`, with the reader's self-recorded run stamp (or a cited transcript) as provenance. In single-agent mode, the author either drops the pivotal flag or explicitly enables the warned fallback (`blind_gate_fallback: true` in `kb/project-config.json`) — the engine rejects the fallback stamp without it. |
| 3 | **Beta-reader PASS before export** | `vellum readiness` (required by `/vellum:export`) | Export | `work/critique-reports/readiness-report.md` with `verdict: PASS` — every axis ≥ 7, mean ≥ 7.5, no put-down point in chapters 1–3 — from a real `@beta-reader` run. |

Never-blocking advisory layers: the post-write prose net (AI-tell tiers, hard signals, voice-debt ledger), cold-read BLOCKER-class issues (they block export only until resolved or dismissed with your sign-off), the disruptor lane, the persona panel. Two further gates ship **off** by default — `voice_debt_gate` and `stop_gate` in `kb/project-config.json` — flip them on only if you want a fourth and fifth.

Your dismissals are first-class: `vellum dismiss <key> --reason "<your words>"` (or `/vellum:dismiss`) records the exemption, and no agent re-raises it. If the underlying fact changes, the exemption goes stale and re-arms exactly once.

## 🏗️ Architecture

Four layers, deliberately separated:

1. **The deterministic engine** — `scripts/vellum` + `scripts/vellum_lib/`. Python ≥ 3.8, stdlib-only: no pip, no Node, no build. It absorbs every check no LLM should pay for — state rebuild/check, ledger continuity (dead characters, promise ordering, knowledge boundaries, prop custody, clock monotonicity), word bands, bible validation, measured style stats, context packing, exemptions, and the export build (markdown bundle + stdlib EPUB). `project-setup` copies it into your novel repo so it runs from the project root.
2. **Hooks** — harness-enforced. The outline gate (Write/Edit and Bash paths) blocks unapproved prose. The post-write prose net scans drafts and stays silent when clean. Session lifecycle: state card on start, snapshot before compact, pending-capture reminder on stop, mechanical close-out when the writer subagent finishes.
3. **Agents** (16) — the **muse** coordinates: it owns the gates (from disk artifacts only) and routes every specialist — outliner, writer, critics, blind/beta/cold readers, kb-lead, disruptor, style-creator. Critics and readers are read-only by frontmatter. The writer writes only under `manuscript/` and `work/drafts/`. Critique, drafting, and memory-update never share a context.
4. **Skills** (34) — the methodology container: craft references, ledger schemas, gate rubrics, the cold-read protocol, demolition, voice work, the series-layer operator's manual, and the series-bible data-dialect reference. Resources load on demand.

### What it installs

- **`agents/`** — 16 agents: muse, outliner, writer, critic, editor, blind-reader, beta-reader, cold-reader, kb-lead, disruptor, style-creator, continuity-checker, character-sim, reader-sim, brainstormer, web-researcher.
- **`skills/`** — 34 skills, including `story-ledgers`, `gates`, `style-guardrails`, `voice`, `cold-read`, `demolition`, `export`, `kb-integrity`, `project-setup`, and the two new v0.2.0 skills: the `series` operator's manual and the `series-bible` data-dialect reference for the library layer.
- **`commands/`** — `/vellum:init`, `/vellum:write-chapter`, `/vellum:status`, `/vellum:cold-read`, `/vellum:retune`, `/vellum:export`, `/vellum:dismiss`, and `/vellum:series` for the library layer.
- **`hooks/`** — 7 hook scripts across 6 lifecycle events (details in [`hooks/README.md`](hooks/README.md)).
- **`templates/`** — the schemas your project is seeded with: chapter frontmatter, ledgers, state card, scene cards, cold-read kit, project config, measured baseline, and the retcon plan template for series work.

## 📚 Library & series layer (v0.2.0)

**What it is.** An optional layer for authors writing a series, so canon is carried forward explicitly instead of re-invented book by book. The library lives **outside** every book project — `project-setup` never creates one, and `library init` refuses to run inside a book — so a v0.1.1 single-book project keeps working byte-identically whether the layer is installed or not, and whether any book is linked.

**What it stores.** The series root holds `library.json` (manifest), `series/bible.json` (the single source of truth for canon, with per-field `by-book` value maps — no log-walking, no `canon:` mirror in any book file), `series/retcons.jsonl` (append-only audit log that records your words verbatim), `series/exemptions.json` (series-scope dismissals, never written into a book), and human-owned `series/errata.md`. A linked book gets only an inert pointer sidecar, `.vellum/series-link.json`, plus an optional opt-in `series-id:` line on entity frontmatter.

**How you work it.** Run `/vellum:series` and the muse routes you through the `series` skill. The engine subcommands (all `--root <library-root>`, no walk-up discovery) are:

| Subcommand | Purpose |
|---|---|
| `library init <root>` (`--root <root>` also accepted) | Create the library tree outside any book project. |
| `library link <book-root>` / `unlink` | Attach or detach a book; link is idempotent and crash-recoverable. |
| `library validate` | Read-only integrity check (schemas, half-linked states, refs, `series-id:` joins, errata refs); `--fix` repairs sidecars. |
| `library bootstrap <book-root> [--plan\|--apply]` | Deterministic canon capture: exact / alias / `[?]` match tiers. `[?]` rows write nothing until you resolve them; `--apply` requires an approved plan. |
| `library retcon-check <book-root>` | Run the detection catalog (dead-character reanimation, open-thread carry, knowledge anachronism, canon divergence, …) — read-only, findings are advisory. |
| `library retcon-plan <book-root>` | Draft a retcon plan report from `templates/retcon-plan.md`. |
| `library retcon --apply <plan-file>` | Apply an approved plan row-by-row; refuses without `approved: true` and your verbatim words on every row. |
| `library state <book-root>` | Print the series state card (also injected into `vellum state` when a book is linked). |
| `library timeline` | Emit the stable `E###` master timeline (never renumbered). |
| `library handoff <book-root>` | Generate the next book's handoff: frozen canon, iron facts, do-not-re-explain register, open retcons, errata posture. |
| `library dismiss <finding-id> --reason "…"` | Record a series-scope dismissal in your own words. |

**Doctrine.** The three hard gates stay three — series findings are advisory and the layer adds no fourth gate. Book status is `draft | published | archived`: published canon is frozen (the default merge is *retcon record required* — the draft loses, never later-wins), and `archived` books are fully quiet. A linked book's `kb/story.md`, `CLAUDE.md`, and hooks are never edited by the layer, and no book-side schema bump is required.

<details>
<summary><strong>🗂️ State files explained</strong> (what's yours, what's the engine's)</summary>

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

- **`state/_tracking-state.json`** — the transactional tracking state: per-chapter statuses, `pending_capture` (an accepted chapter whose knowledge capture hasn't closed), schema version. `state check` refuses a new chapter start while a transaction is half-committed.
- **`state/state-card.md`** — the fixed 7-section one-screen resume card (story position, open promises/questions, active cast, knowledge boundaries, props & clock, next beats with quotas, flags), hard-capped at 12 KB. Session start prints it; the writer's context pack inlines it.
- **`state/_derived-hashes.json`** — sha256 of the last engine-written content of the two files above. Hand-edit a derived file and the hash check raises `state:hand-edited`, with the fix: run `python scripts/vellum state rebuild`.
- **`state/.vellum.lock`** — exclusive write lock (stale locks over 60 s are warned and cleared).

Division of authority: your prose is ground truth; `kb/` is durable canon; `state/` is derived and engine-owned; `work/` is scratch. When state and prose disagree, vellum surfaces the conflict — it never silently rewrites prose to match stale tracking.

</details>

<details>
<summary><strong>🪟 Windows notes</strong></summary>

- **Hooks run under Git Bash** (bundled with Git for Windows) — no WSL needed.
- **Interpreter resolution** tries `python3`, then `python`, then the `py -3` launcher, each probed for ≥ 3.8. The outline gate's core predicate is pure bash, so gate 1 works even with no Python at all (engine preconditions then skip with a one-line advisory — fail-open by doctrine).
- **Path handling** is tested on `windows-latest` CI: drive letters, paths with spaces, CRLF files, and UTF-8 BOMs are all normalized. Repo files are pinned to LF via `.gitattributes`; `LC_ALL=C` wherever byte-stable matching matters.
- **Large payloads** are piped to the interpreter via stdin, never passed as arguments (the E2BIG trap), with a regression test above 128 KiB.
- Run the test suite from any bash: `python -m pytest tests/ -q`.

</details>

## ❓ FAQ

**Do I need Python?**
Strongly recommended. Without it, gate 1 still works (its predicate is pure bash) and the engine-dependent preconditions fail open with an advisory. With it, everything works.

**Will it rewrite my prose?**
No. Critics and readers are read-only by frontmatter. The writer agent writes only under `manuscript/` and `work/drafts/`. Every acceptance, every export, every dismissal is yours to give.

**What happens when a gate blocks me?**
You get the exact artifact it wanted and the command that satisfies it — approve the outline, run the blind reader, finish the pending capture. Gates explain themselves; they never leave you guessing, and they never lock your manuscript (it's your git repo).

**Can I bring an existing manuscript?**
Yes. `project-setup` works on existing folders, and the state engine builds its tracking from what's on disk.

**How is this different from just prompting Claude Code?**
Prompting asks the model to be consistent. Vellum enforces it: hooks that can't be talked past, a Python engine that checks what code can check, agents whose permissions make contamination impossible, and state that survives context compaction.

## 📈 Status: v0.2.0

New in v0.2.0, per [`library-spec.md`](../library-spec.md): the optional **library/series layer** — the `scripts/library.py` entry point backed by three series modules (`scripts/vellum_lib/series_cli.py`, `scripts/vellum_lib/series_bible.py`, `scripts/vellum_lib/series_checks.py`), the `vellum:series` skill with its agent-facing detection-catalog reference, the retcon-plan template, the `/vellum:series` command, and a fail-open series line in the session-start hook for linked books. The release suite has **155 passing tests** (120 engine/hook tests plus 35 series follow-up tests). Compatibility is enforced, not promised: a byte-identity golden suite runs the full v0.1.1 command surface on a linked project and asserts identical output, and an inert-to-old-engine test deletes the new modules and re-runs the surface. See [Library & series layer](#-library--series-layer-v020) above and [DESIGN.md §18](DESIGN.md).

### v0.1.1 record

Implemented per [DESIGN.md](DESIGN.md): 16 agents, 32 skills, 7 commands (including `/vellum:init`), 7 hooks, the complete stdlib engine, templates, **98 passing tests** on a seeded fixture project, and CI on two operating systems. An end-to-end paper-run exercised every gate, hook, and engine path on Windows.

New in v0.1.1, beyond the fixes to the eight paper-run findings: the craft layer grew — an **obligatory scenes & conventions checklist** per genre (Story Grid, ideas-only) that the outliner and beta reader actually check; a **try-fail failure ladder** resource for arc planning and saggy middles; a **revision plan** artifact (`work/revision-plan.md`, with `vellum revision status`) that triages every finding from every review source into one tracked plan; a **beta-synthesis protocol** for when parallel readers disagree; **per-character dialogue profiles** with a blind speaker-attribution test (`style stats --dialogue`); and a **tense/person morphology scan** for Romanian prose in the advisory post-write net (`style stats --morphology` — report-only, carve-out-able). Everything new is advisory; the three gates stayed three. Details and audit record in [VALIDATION.md §5–6](VALIDATION.md).

The eight paper-run findings from v0.1.0 are resolved — see [VALIDATION.md §4](VALIDATION.md) for the fix record. Notable in v0.1.1: gate-artifact provenance now uses the reader's self-recorded run stamp (with an optional transcript-path binding), single-agent pivotal chapters have a documented author-enabled fallback (`blind_gate_fallback` in `kb/project-config.json`), `project-setup` runs the initial `state rebuild`, and `/vellum:init` gives setup a first-class entry point.

## 🙏 Credits — and how Vellum improves on them

Vellum stands on a lot of shoulders. It was built by deep-reading twenty storywriting systems and combining their best verified mechanisms into one coherent, tested architecture — keeping what worked, fixing what didn't. The full design story lives in [ATTRIBUTION.md](ATTRIBUTION.md); the short version:

| Source | We took | Vellum improves by |
|---|---|---|
| [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills) (base, Apache-2.0) | Muse architecture, stance isolation, edit chain, craft corpus | Adding what it lacked: blocking gates, a deterministic engine, tests + CI; removing its private-tool coupling so it runs on stock Claude Code |
| [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) (MIT) | Bible schema, promise/question ledgers, continuity check catalog | Auto-invoking the checks via hooks (theirs was a standalone CLI), plus prop custody, clock checks, and timeline-scoped knowledge queries |
| [zenstory-ai/oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode) (MIT) | Guard hooks, transactional state card | Portable English implementation, fail-open gates that can't mis-block you, gate-input forgery protection, Windows + test coverage |
| [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) + [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) (MIT) | Detector categories, replacement tables | Fiction carve-outs and a hard law: style bans cap at the author's measured baseline — the net never flattens voice |
| [simonediroma/claude-ghost-writer](https://github.com/simonediroma/claude-ghost-writer) (MIT) | Demolition protocol, voice retune | Chapter-scoped, logged, declinable demolition; retune inside a full measured-voice lifecycle with drift checks and a falsification test |
| [epicsagas/Velith](https://github.com/epicsagas/Velith) (Apache-2.0) | Beta-reader gate, quality bar | Readiness thresholds enforced by the engine, with a sha256 export manifest recording which gates passed |
| [geobond13/fiction-forge](https://github.com/geobond13/fiction-forge) (MIT) | Cold-read protocol, markdown ledgers | Subagent-batched cold reads, and a rolling issue log unified with the first-class exemption system |
| [howells/fiction](https://github.com/howells/fiction) (MIT) | Persona critics (Wood, King, Le Guin, Gay) | Wiring them into the automated pipeline (theirs were manual summons), bound to a shared rubric so verdicts cite criteria |
| [rhavekost/author-toolkit](https://github.com/rhavekost/author-toolkit) (MIT) | Weiland/Bell beat map, finding schema | Beats as auditable structure maps wired into planning/audit modes, not just reference reading |
| [mrigankad/Novel-OS](https://github.com/mrigankad/Novel-OS) (MIT) | Dismissed-findings keying, stall detector | Stdlib Python re-implementation; exemptions re-arm once when the underlying fact changes (entity-hash staleness) |
| [felipelobomotta-blip/book-genesis-v4](https://github.com/felipelobomotta-blip/book-genesis-v4) (ideas) | The blind-reader gate | A strictly read-only agent inside the plugin with engine cross-checks — not an external CLI |
| Craft theory: Shawn Coyne, Sanderson/Butcher/Writing Excuses, Gaiman/Craig/MorningStar, BubbleCow/Windrow, Michel/Yang/Brei (ideas only) | Obligatory scenes, try-fail ladders, beta doctrine, revision-letter practice, dialogue stylometry | Original checkable resources implementing the mechanisms — all prose our own, all ideas credited |

License-wise: the base fork's Apache-2.0 copyright is retained; MIT sources keep their notices; unlicensed sources contributed ideas only — no text or code was copied. See [LICENSE](LICENSE), [NOTICE](NOTICE), and [ATTRIBUTION.md](ATTRIBUTION.md).

## 📄 License

Apache-2.0 (inherited from the base fork; see [LICENSE](LICENSE)). Ported MIT sources keep their notices; unlicensed sources contributed ideas only — no text or code was copied.
