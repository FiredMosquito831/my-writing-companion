# Vellum — The Complete Tutorial

*Everything the plugin does, every command you can run, what fires automatically, what you must invoke yourself, and how all the pieces connect. For v0.2.0.*

---

## Table of contents

1. [What Vellum is](#1-what-vellum-is)
2. [The mental model](#2-the-mental-model)
3. [Install](#3-install)
4. [Your first project](#4-your-first-project)
5. [The chapter loop (the main workflow)](#5-the-chapter-loop-the-main-workflow)
6. [Slash commands — the full registry](#6-slash-commands--the-full-registry)
7. [The engine — full CLI registry](#7-the-engine--full-cli-registry)
8. [The series layer (multi-book)](#8-the-series-layer-multi-book)
9. [The agents](#9-the-agents)
10. [The skills](#10-the-skills)
11. [The hooks — what runs automatically](#11-the-hooks--what-runs-automatically)
12. [Automatic vs. manual: the honest table](#12-automatic-vs-manual-the-honest-table)
13. [State files — who owns what](#13-state-files--who-owns-what)
14. [Architecture — how it all connects](#14-architecture--how-it-all-connects)
15. [Flow diagrams](#15-flow-diagrams)
16. [The gate model in depth](#16-the-gate-model-in-depth)
17. [Rescue manual — common situations](#17-rescue-manual--common-situations)
18. [FAQ](#18-faq)

---

## 1. What Vellum is

Vellum is a Claude Code plugin for writing novels. Its promise: **one command for the chapter loop, three hard gates, everything else advisory and silent when clean.**

It exists because long-form fiction is where LLM workflows fall apart: drafts drift toward the statistical average, critique leaks into drafting, continuity dies at context compaction, and "please be consistent" is a wish, not a mechanism. Vellum replaces wishes with machinery — hooks that physically block unapproved prose, a Python engine that checks what code can check, agents whose permissions make contamination impossible, and state that survives sessions and months away from the manuscript.

## 2. The mental model

Four layers, deliberately separated:

```
┌────────────────────────────────────────────────────────────┐
│  YOU (the author)                                          │
│  approve outlines · accept chapters · dismiss findings     │
│  set the pivotal flag · decide canon                       │
└────────────┬───────────────────────────────────────────────┘
             │ slash commands / conversation
┌────────────▼───────────────────────────────────────────────┐
│  THE MUSE (coordinator)                                    │
│  owns the gates from disk artifacts ONLY                   │
│  routes specialists — never drafts, never judges its own   │
└──────┬─────────────┬──────────────┬───────────────────────┘
       │             │              │
┌──────▼─────┐ ┌─────▼──────┐ ┌─────▼─────────┐
│  AGENTS    │ │ SKILLS     │ │ ENGINE        │
│  16 spawns │ │ 34 methods │ │ (Python CLI)  │
│  isolated  │ │ loaded on  │ │ deterministic │
│  stances   │ │ demand     │ │ stdlib-only   │
└────────────┘ └────────────┘ └──────┬────────┘
                                     │
┌────────────────────────────────────▼───────────────────────┐
│  HOOKS (harness-enforced, fire automatically)              │
│  outline gate · prose net · session lifecycle              │
└────────────────────────────────────────────────────────────┘
```

The one-sentence version: **you talk to the muse, the muse routes isolated workers, the workers use the engine and the skills, and the hooks enforce the rules no one can talk their way around.**

## 3. Install

Requirements: Claude Code, Git (hooks run under its bundled bash), Python ≥ 3.8 on PATH (`python3`, `python`, or Windows `py -3`). No Node, no pip, no WSL. Pandoc optional (DOCX/PDF export only).

From GitHub:

```
/plugin marketplace add FiredMosquito831/my-writing-companion
/plugin install vellum@my-writing-companion
```

Then restart the session (or run `/reload-plugins`). Verify: `/vellum:status` should respond.

## 4. Your first project

In your novel folder (empty or an existing manuscript), run:

```
/vellum:init
```

or just tell Claude: *"Set up my novel project."*

`project-setup` interviews you (genre, POV, progress, writing samples), seeds the layout, copies the engine in, captures your voice from 3–5 samples of your own prose, and finishes with an initial `state rebuild`. After this, every session in that folder starts with your state card on screen.

**Multi-book authors:** during setup you can attach the book to a series (see [section 8](#8-the-series-layer-multi-book)), or link it later.

## 5. The chapter loop (the main workflow)

This is 90% of daily use. One command:

```
/vellum:write-chapter next
```

What happens, in order:

| Step | Who | What | You do |
|---|---|---|---|
| 1 | muse | spawns `@outliner` → beats with word quotas + verbatim anchor lines written to `work/outline/chapter-NN.md` | **read the outline, approve it** (`approved: true` in frontmatter — this disarms gate 1) |
| 2 | you | say "pivotal" if the chapter is load-bearing | optional; only you can set this flag |
| 3 | muse | spawns `@writer` with a fixed context pack (state card, scene brief, previous-chapter tail, cast cards, voice profile, word budget) | wait |
| 4 | hooks | post-write prose net scans the draft automatically | nothing — silent when clean |
| 5 | muse | spawns read-only critics; pivotal chapters also get the `@blind-reader` (sees only the prose, no plan) | read the synthesis |
| 6 | you | **accept the chapter** | your acceptance is the transaction trigger |
| 7 | engine | mechanical close-out fires automatically: wordcount band check, ledger check, state rebuild | nothing |
| 8 | muse | routes `@kb-lead` to extract what happened into the ledgers | answer its questions |
| 9 | muse | before `final`: offers one **demolition pass** | accept or decline (declining is recorded, never punished) |

You can interrupt at any step. The state card is your save point — `/vellum:status` and you're back.

## 6. Slash commands — the full registry

All commands are namespaced `/vellum:`. Each one addresses the muse in the **main loop** (the loop adopts the muse role — commands never spawn a "muse subagent").

| Command | What it does | When you use it |
|---|---|---|
| `/vellum:init` | Run project-setup: interview, seed the project, capture voice, initial state rebuild | once per book |
| `/vellum:write-chapter [N]` | The full chapter loop (see section 5) | every chapter |
| `/vellum:status` | Print the state card, gate statuses, open findings | any time; also fires automatically at session start |
| `/vellum:cold-read` | Set up and run batch fresh-eyes reads with a rolling reader ledger | every ~10 chapters, or before export |
| `/vellum:retune` | Recalibrate the voice profile from a raw prose sample | when the prose stops sounding like you |
| `/vellum:export` | Readiness check (gate 3), then markdown bundle + EPUB | when the manuscript is done |
| `/vellum:dismiss` | Record an exemption for a finding — requires the reason in your own words | when the engine or a critic flags something you intended |
| `/vellum:series` | Operate the library/series layer (see section 8) | multi-book authors |

## 7. The engine — full CLI registry

The engine is a stdlib-only Python CLI. You rarely invoke it by hand — agents and hooks call it — but knowing the surface helps. Run as `python scripts/vellum <command>` (from your project, where setup copied it).

**Book engine (`scripts/vellum`):**

| Command | Purpose |
|---|---|
| `state rebuild` / `state check` | regenerate / verify the transactional tracking state and state card |
| `ledger check` | run the deterministic continuity catalog (dead characters, promise ordering, knowledge boundaries, prop custody, clock monotonicity) |
| `bible validate` / `bible reindex` / `bible links` | kb schema validation, registry rebuilds, cross-reference integrity |
| `wordcount` | words per chapter + band check vs the outline's quota |
| `knowledge <id> --as-of N [--audience]` | who knows what as of chapter N; dramatic-irony views |
| `style stats [--baseline] [--dialogue] [--morphology]` | measured voice profile, drift vs baseline, per-character dialogue fingerprints, tense/person morphology scan (Romanian-aware) |
| `pack` | assemble the writer's context pack |
| `dismiss <key> --reason "…"` | record an exemption (hash-keyed; re-arms once if the fact changes) |
| `debt list` / `debt clear` | voice-debt accounting |
| `revision status` | triaged revision-plan tracker |
| `readiness` | gate-3 preconditions check |
| `export build` | markdown bundle + stdlib EPUB with gate-provenance manifest |

**Exit codes everywhere:** `0` clean · `1` findings (advisory) · `2` usage/schema/environment error.

## 8. The series layer (multi-book)

For authors with more than one book. The layer lives at its own entry point — `scripts/library.py` — and a linked book gains series canon; an unlinked book behaves *byte-identically* to a single-book setup.

**Concepts:**

- **Library** — a folder above your books holding the series bible and reports. One per series.
- **Series bible** (`series/bible.json` + markdown) — the single source of truth for shared canon: characters, world rules, facts, **per-book value maps** (where each character/relationship stands in each book).
- **Retcon lifecycle** — plan → you approve → apply. Your words recorded verbatim. **Published books are frozen by default:** on contradiction, the draft loses, never "later-wins" — unless you explicitly override with `override_published: true`.
- **Dismissals** — series-scope exemptions live in the library only; same discipline as book dismissals (your verbatim words, entity-hash re-arm when facts change).

**The 12 subcommands** (`python scripts/library.py <command> --root <library-root> …` — `--root` is mandatory, there is no walk-up discovery):

| Command | What it does |
|---|---|
| `library init` | create the empty library tree (manifest, `series/`, `reports/`, `handoff/`) |
| `library link <book-root>` | attach a book (writes the series-link sidecar + manifest entry) |
| `library unlink <book-root>` | detach; canon retained, orphan refs flagged |
| `library bootstrap <book-root> [--plan\|--apply]` | capture canon from the book's kb: exact / alias / `[?]` match tiers; `[?]` rows write nothing until you resolve them |
| `library retcon-check <book-root>` | run the detection catalog (deceased-as-of-start, open-thread carry, knowledge anachronism, canon divergence…) — read-only |
| `library retcon-plan <book-root>` | produce a retcon plan document for your review |
| `library retcon --apply <plan-file>` | apply an **approved** plan row-by-row (refuses without `approved: true` and verbatim `author_words` on every row) |
| `library state <book-root>` | print the series state card (also injected into the book's state card when linked) |
| `library timeline` | emit the `E###` master timeline (stable IDs, never renumbered) |
| `library handoff <book-root>` | generate the handoff doc for the next book |
| `library validate [--fix]` | read-only integrity check; `--fix` regenerates stale sidecars |
| `library dismiss <id> --reason "…"` | record a series-scope dismissal |

**Doctrine:** series findings are advisory — **the layer adds no fourth gate.** A `draft` book accepts retcon proposals; a `published` book's canon is frozen; an `archived` book is fully quiet.

In practice you drive all of this through `/vellum:series` rather than raw commands.

**A worked example — starting Volume II of CARTE2:**

```
python scripts/library.py init --root ../my-series-library
python scripts/library.py link . --root ../my-series-library
python scripts/library.py bootstrap . --plan --root ../my-series-library   # review the [?] rows
python scripts/library.py bootstrap . --apply --root ../my-series-library  # after approving
```

…then, months later, when Volume II has a draft:

```
python scripts/library.py retcon-check . --root ../my-series-library       # advisory findings
python scripts/library.py retcon-plan . --root ../my-series-library        # plan for your review
python scripts/library.py retcon --apply reports/retcon-plan-XXXX.md --root ../my-series-library
```

(or just run `/vellum:series` and ask for each step by name.)

## 9. The agents

16 subagents, strict stance isolation — critique, drafting, and memory-update never share a context. The muse routes them; you can also summon any directly (e.g. `@vellum:critic`).

| Agent | Role | Permissions posture |
|---|---|---|
| `muse` | coordinator, primary entry point, owns the gates from disk artifacts only | broad but never drafts |
| `outliner` | beats with word quotas + verbatim anchor lines | writes outlines only |
| `writer` | production prose from the context pack | writes only `manuscript/` + `work/drafts/`; **cannot read critiques** |
| `critic` | deep adversarial critique, one focus area at a time | read-only |
| `editor` | holistic editorial pass (structure, voice, line, copy, proof priorities) | read-only |
| `blind-reader` | gate 2: naive-eyes verdict on pivotal chapters; knows nothing of the plan | Read tool, nothing else |
| `beta-reader` | gate 3: four-reader readiness read before export | read-only |
| `cold-reader` | one cold-read batch; assessment only | read-only |
| `continuity-checker` | cross-references content vs established canon | read-only + engine access |
| `reader-sim` | experiential reader response from a caller-specified persona | read-only |
| `character-sim` | in-character conversation for voice discovery / pressure tests | constrained |
| `style-creator` | builds/updates the voice profile and measured baseline from your samples | writes only `kb/styles/` |
| `kb-lead` | knowledge capture into the ledgers after acceptance | writes only `kb/` + runs engine checks |
| `disruptor` | controlled-wildness proposals for flat chapters | read-only, proposal-only |
| `brainstormer` | creative option generation for scoped questions | constrained |
| `web-researcher` | factual grounding for fiction (history, culture, domain expertise) | web + notes |

**Model tiering:** architect-class agents (muse, writer, critic, editor, blind/beta readers) run on the strongest model tier; checker-class work runs lighter. You never manage this.

## 10. The skills

34 skills are the methodology container. You almost never invoke them by name — agents load what their contracts declare, and in conversation they trigger by relevance. The load-bearing ones:

| Skill | Owns |
|---|---|
| `project-setup` | the init interview, project seeding, voice capture |
| `story-planning` | creative direction, story architecture, scene cards, try-fail ladders, structure beats |
| `story-ledgers` | ledger schemas, state card, chapter-transaction close-out |
| `style-guardrails` | the fiction anti-slop reference (tiered tables, structural caps, carve-outs) |
| `voice` | the voice lifecycle: capture, measured profile, drift checks, blind-tag test, retune |
| `gates` | the shared quality rubric, export-readiness checklist, genre profiles, finding schema |
| `story-review` | the edit chain: editorial review → developmental → line → copyedit → proofread; persona critics; beta synthesis; revision plans |
| `cold-read` | the fresh-eyes batch protocol |
| `demolition` | hostile critical analysis, one vulnerability at a time, never softened |
| `kb-integrity` | operating manual for the engine's checks + the exemption protocol |
| `series` / `series-bible` | the library layer's operator manual and schemas |
| `export` | readiness evaluation + bundle/EPUB assembly |
| `writing-principles` | reader reward channels and the LLM failure modes that damage them |
| `creative-writing-craft` / `creative-writing-modes` / `llm-writing` | prose craft, drafting modes, deliberate word choice |
| `creative-research` | sourced research reports for story grounding |
| `shared-dao` | canonical story vocabulary |
| the rest (`information-hierarchy`, `intent-modeling`, `md-validation`, …) | shared quality infrastructure used by agents internally |

## 11. The hooks — what runs automatically

Seven scripts across six lifecycle events. You never invoke these; Claude Code fires them, and they cannot be forgotten or talked past.

| Event | Script | Does |
|---|---|---|
| `PreToolUse` (Write/Edit) | `guard-outline-before-prose.sh` | **gate 1**: blocks prose writes into `manuscript/chapters/` without an approved outline + clean state |
| `PreToolUse` (Bash) | `guard-bash-prose-writes.sh` | same gate for the bash path (redirections, heredocs, `sed -i`, copy-laundering all checked) |
| `PostToolUse` (Write/Edit) | `check-prose-after-write.sh` | the post-write prose net: AI-tell tiers, hard signals, voice debt — silent when clean |
| `SessionStart` | `session-start.sh` | prints the state card (+ the series line if linked; fail-open) |
| `PreCompact` | `pre-compact.sh` | snapshots state before context compaction |
| `Stop` | `session-stop.sh` | pending-capture reminders |
| `SubagentStop` (writer) | `chapter-maintenance.sh` | mechanical chapter close-out after the writer finishes |

Two further gates exist but ship **off**: `voice_debt_gate` and `stop_gate` in `kb/project-config.json`. Flip them on only if you want a fourth and fifth hard gate.

## 12. Automatic vs. manual: the honest table

The question "does it fire by itself?" has four different answers depending on the layer:

| Layer | Fires automatically? | Details |
|---|---|---|
| **Hooks (7)** | **Yes — always.** | Harness-enforced on every session/tool event. Cannot be forgotten, skipped, or talked past. Fail-open on genuine uncertainty (a missing Python runtime never mis-blocks you); the one deliberate exception is gate-input protection, which fails closed when it cannot verify session context. |
| **Engine (both CLIs)** | **No — but you never need to.** | Invoked automatically *by* the hooks and by agents through their Bash allowlists. Direct invocation is for power use and rescue scenarios (section 17). |
| **Agents (16)** | **No.** | Spawned by the muse as part of a workflow, or summoned by you explicitly (`@vellum:critic`). They are workers, not reflexes. |
| **Skills (34)** | **Mostly.** | Agents load what their frontmatter declares, with progressive disclosure of resources. In main-loop conversation they trigger by relevance to your request — probabilistic, driven by description quality. For *guaranteed* behavior on important flows, use the commands. |
| **Commands (8)** | **No — this is your steering wheel.** | You run these. Everything starts with one. |

So the practical answer: **hooks are automatic, everything else waits for you or the muse.** Your daily interface is exactly two commands (`/vellum:write-chapter`, `/vellum:status`) plus conversation.

## 13. State files — who owns what

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

Division of authority: your prose is ground truth; `kb/` is durable canon; `state/` is derived and engine-owned (hash-verified — hand-editing is detected and reported with the fix); `work/` is scratch. When state and prose disagree, vellum surfaces the conflict; it never silently rewrites prose to match stale tracking.

## 14. Architecture — how it all connects

The request path, end to end:

1. **You** type `/vellum:write-chapter next`. The command body loads the muse's instructions into the main loop.
2. **The muse** reads the state card (via the engine), confirms no transaction is half-committed (`state check`), then spawns `@outliner`.
3. **The outliner** reads `kb/` and the ledgers (directly — it has Read), writes the outline with quotas and anchor lines. Muse shows it to you.
4. **You approve.** The outline file now carries `approved: true`. This is a disk artifact, not a claim.
5. **The muse** asks the engine to `pack` the writer's context (state card, scene brief, prev-chapter tail, cast cards, voice, budget) and spawns `@writer`.
6. **The writer** writes the chapter. Gate 1's PreToolUse hooks evaluate every write: approved outline present? state clean? Then the write passes; without it, the write is blocked with a message naming the missing artifact.
7. **The PostToolUse hook** runs the prose net on the draft. Findings (if any) are advisory and recorded.
8. **The muse** spawns critics (and `@blind-reader` if pivotal). Their verdicts are written to `work/critique-reports/`. Gate 2 checks the blind artifact exists with a passing verdict *from disk* at acceptance time.
9. **You accept.** The close-out runs: `wordcount` (band check), `ledger check`, `state rebuild`. `@kb-lead` extracts facts into the ledgers. The transaction closes — `pending_capture` clears.
10. **Gate 3** waits far away at export: `vellum readiness` requires a beta-reader report with every axis ≥ 7 before `export build` produces the bundle + EPUB.

The design invariants that make this safe:

- **Gates read from disk, never from chat.** An agent can say anything; the gate checks the file.
- **Stance isolation by frontmatter.** The writer cannot read critiques; critics cannot write prose; the muse never drafts.
- **Fail-open by doctrine.** Genuine uncertainty never locks your manuscript (it's your git repo).
- **Advisory by default.** Only three things in the system block; everything else surfaces and stays quiet when clean.
- **Series is canon, not control.** The library layer informs; it never gates.

## 15. Flow diagrams

**The chapter loop:**

```
/vellum:write-chapter next
        │
        ▼
   ┌─────────┐   spawn    ┌──────────┐  outline  ┌───────────┐
   │  MUSE   │───────────▶│ @outliner│──────────▶│ outline.md│
   └────┬────┘            └──────────┘           └─────┬─────┘
        │                                        YOU APPROVE
        │                                     (approved: true)
        │                                              │
        ▼ pack (engine)                                │
   ┌─────────┐   spawn    ┌──────────┐  chapter  ┌─────▼─────┐
   │  MUSE   │───────────▶│ @writer  │──────────▶│ chapter-NN│
   └────┬────┘            └──────────┘      │    └───────────┘
        │                                   │
        │                    ┌──────────────▼──────────────┐
        │                    │ GATE 1 (PreToolUse hooks)   │
        │                    │ approved outline + state ok? │──no──▶ BLOCKED
        │                    └──────────────┬──────────────┘      (names the fix)
        │                                  yes
        │                                   │
        │                    ┌──────────────▼──────────────┐
        │                    │ POST-WRITE NET (auto)       │──▶ advisory findings
        │                    └──────────────┬──────────────┘
        ▼ spawn critics (+ @blind-reader if pivotal)
   ┌─────────────────────────────────────────────┐
   │ YOU READ THE SYNTHESIS AND ACCEPT           │
   │ (pivotal: gate 2 requires blind ≠ LOST)     │
   └──────────────────────┬──────────────────────┘
                          ▼
            mechanical close-out (auto): wordcount → ledger → state rebuild
                          ▼
              @kb-lead captures into the ledgers
                          ▼
            (before final) demolition offered — you may decline
```

**Gate 3 — the export path:**

```
/vellum:export
      │
      ▼
vellum readiness ──── missing/failed ───▶ blocked, names what's needed
      │
   PASS (beta-reader report on disk, every axis ≥ 7,
         mean ≥ 7.5, no put-down point in ch 1–3)
      │
      ▼
export build ──▶ markdown bundle + EPUB
                 manifest: sha256 + which gates passed + logged overrides
```

**The series layer:**

```
        ┌─────────────────── LIBRARY ───────────────────┐
        │  series/bible.json   (single source of truth) │
        │  reports/            handoff/                 │
        └──────┬───────────────────────────┬────────────┘
               │ link                      │ link
        ┌──────▼──────┐             ┌──────▼──────┐
        │   BOOK 1    │             │   BOOK 2    │
        │  (CARTE2)   │             │  (drafts)   │
        └─────────────┘             └─────────────┘
   book 1 kb ──bootstrap──▶ series bible ──context──▶ book 2 drafting
   book 2 draft ──retcon-check──▶ advisory findings ──plan→approve→apply──▶ bible
   book 1 status: published → canon FROZEN (draft loses by default)
```

## 16. The gate model in depth

Exactly three hard gates; everything else is advisory. Each gate reads its artifact **from disk** — never a claim from chat.

| # | Gate | Enforced by | Blocks | Satisfied by |
|---|---|---|---|---|
| 1 | Approved outline before prose | PreToolUse hooks (Write/Edit + Bash) | any write into `manuscript/chapters/` | `work/outline/chapter-NN.md` with `approved: true`, plus clean `state check` |
| 2 | Blind verdict on pivotal chapters | `state check` at acceptance + readiness cross-check | marking a `pivotal: true` chapter `accepted` | `work/critique-reports/blind-chapter-NN.md`, verdict ≠ `LOST`, from a real `@blind-reader` run |
| 3 | Beta PASS before export | `vellum readiness` | export | `readiness-report.md` with `verdict: PASS` — every axis ≥ 7, mean ≥ 7.5 |

Gate-input protection: subagents cannot self-approve outlines or forge critique artifacts — the gate checks session context and fails **closed** when it cannot verify it (the one deliberate exception to fail-open).

Your dismissals are first-class: record an exemption in your own words and no agent re-raises it. If the underlying fact changes, the exemption goes stale and re-arms exactly once.

## 17. Rescue manual — common situations

| Situation | What to do |
|---|---|
| "state:hand-edited" finding | `python scripts/vellum state rebuild` (the message names this) |
| Gate 1 blocked my write | Look at the block message: it names the missing artifact. Usually: approve the outline, or finish a pending capture |
| First chapter start is refused (chapter-transaction block) | Run `python scripts/vellum state rebuild` once (v0.2.0's `/vellum:init` does this for you) |
| A finding is wrong / intentional | `/vellum:dismiss` with the reason **in your own words** — it will not be re-raised unless the fact changes |
| Prose stopped sounding like me | `/vellum:retune` with a fresh raw sample |
| Chapter feels flat | Ask the muse for the `@disruptor` lane, or run a demolition pass |
| Readers disagree about a chapter | `/vellum:cold-read` batch, then the beta-synthesis protocol merges conflicting notes |
| I want everything about right now | `/vellum:status` — the state card, gates, and open findings in one screen |
| Engine missing/broken in an old project | Re-run `/vellum:init` (it copies the current engine and rebuilds state) |
| A series check nags about an intentional choice | `library dismiss <finding-id> --reason "…"` — series exemptions live in the library |

## 18. FAQ

**Do I need Python?** Strongly recommended. Without it, gate 1 still works (pure bash) and engine preconditions fail open with an advisory. With it, everything works.

**Will it rewrite my prose?** No. Critics and readers are read-only by frontmatter; the writer writes only under `manuscript/` and `work/drafts/`; acceptance, export, and dismissal are yours.

**Do skills fire automatically?** Mostly — they load by relevance in conversation, and agents load what their contracts declare. Commands are your guarantee for the flows that matter.

**Can I bring an existing manuscript?** Yes — `/vellum:init` works on existing folders, and the engine builds tracking from what's on disk. (CARTE2 — 53 chapters, ~167k words — was onboarded this way.)

**How is this different from just prompting Claude Code?** Prompting asks the model to be consistent. Vellum enforces it: hooks that can't be talked past, a Python engine that checks what code can check, agents whose permissions make contamination impossible, and state that survives context compaction.

**What if I only write one book?** Then ignore section 8 entirely. The series layer is opt-in and invisible when unlinked.

---

*Vellum is authored by [FiredMosquito831](https://github.com/FiredMosquito831), forked from [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills) with mechanisms credited from a dozen systems — full story in [ATTRIBUTION.md](ATTRIBUTION.md). License: Apache-2.0.*
