# VELLUM — Definitive Build Spec

**Date:** 2026-09-09. **Base:** fork of `haowjy/creative-writing-skills` `cw/` distribution.
**Philosophy (binding):** a working novelist's daily tool, not a pipeline to admire. One command for the chapter loop; exactly three hard gates (approved outline before prose; blind-reader verdict on pivotal chapters; beta-reader PASS before export); everything else advisory and silent when clean. Stance isolation is sacred; scripts absorb every check no LLM should burn tokens on; a fixed state card makes interrupt/resume one screen. The author approves, dismisses, and retunes — the machine never re-litigates a dismissed choice.

All `repos/<repo>/<path>` paths below are relative to `C:/Users/iulia/Desktop/ultra-writing-plugin/repos/`. Base paths are relative to `repos/creative-writing-skills/cw/`.

---

## 0. How to use this spec (builder ownership map)

Eight parallel workstreams. Each owns whole directories; no file has two owners. Interfaces between workstreams are the schemas in §3 and the CLI contract in §5 — builders code against those, not against each other.

| WS | Owns | Depends on |
|---|---|---|
| **A** | `.claude-plugin/`, ATTRIBUTION.md, NOTICE, LICENSE, `.gitattributes`, `.github/`, all **edits to existing** `agents/*.md` and `skills/*` | §3 conventions only |
| **B** | `scripts/` (the deterministic engine) | §3, §5 |
| **C** | `hooks/` | §3, §5, §6 |
| **D** | `skills/{story-ledgers, kb-integrity, gates}` | §3, §5 |
| **E** | `skills/{style-guardrails, voice}`, `agents/style-creator.md` edit coordination with A (A owns the file; E supplies content, see §8) | §3, §5 |
| **F** | `agents/{blind-reader, beta-reader, cold-reader}.md`, `skills/cold-read`, `skills/story-review` persona resources | §3, §5 |
| **G** | `agents/kb-lead.md`, `agents/disruptor.md`, `skills/{demolition, export}`, `commands/`, `templates/` | §3, §5, §7 |
| **H** | `tests/`, CI fixture project, Windows hook-test job (adds a workflow file under `.github/workflows/` — coordinates with A, which owns the edited base `ci.yml`) | §5, §6 |

Coordination rules: E writes the *content* of `agents/style-creator.md` as a completed file and hands it to A for final integration; A applies the same rule for any file listed in two workstreams (there is exactly one: `style-creator.md`). H's workflow file name (`tests.yml`) cannot collide with A's edited `ci.yml`.

Base facts (verified): the `cw/` distribution ships **11 agents** and **24 skills** (not 28 as earlier drafts said — count them in §2 tree). It ships **zero hooks** and **zero commands**. Known base faults fixed here: broken `story-planning` resource list (`cw/skills/story-planning/SKILL.md` lines 13–15 all point at `resources/story-planning.md`), Meridian leaks at `cw/agents/continuity-checker.md:31` (`meridian kg graph`) and `cw/agents/outliner.md:40` (`meridian mermaid check`), `kb-lead` referenced in `cw/agents/muse.md:71` but never shipped.

---

## 1. Runtime decision (judge-driven change — read first)

The judged design ran the deterministic engine on Node (`vellum.js`). Both losing reviews flagged this ("node dependency weakens the gate story"; "continuity enforcement dies entirely without node"; "kb-lead's required `node vellum.js` calls are outside its declared allowlist"). **Change: the engine is Python ≥ 3.8, stdlib only, zero pip dependencies** (`scripts/vellum` + `scripts/vellum_lib/`). Rationale: the `py -3` launcher ships with every python.org Windows install; stdlib-only means no build, no venv.

- **Interpreter resolution (single source of truth, in `hooks/scripts/lib/common.sh`):**

  ```sh
  vellum_py() {
    for c in python3 python "py -3"; do
      if command -v ${c% *} >/dev/null 2>&1 && [ "$c" = "py -3" -o "$c" != "py -3" ]; then
        if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
          printf '%s\n' "$c"; return 0
        fi
      fi
    done
    return 1
  }
  ```

  Hooks call `VELLUM_PY=$(vellum_py)` and invoke `"$VELLUM_PY" "$SCRIPTS/vellum" <sub>`. No `exec` bit reliance (Windows); always invoke via the interpreter.
- **Gate survival without Python:** the outline gate's core predicate (approved-outline frontmatter) is **pure bash**; the engine's `state check` is an *additional* precondition that is skipped (with a one-line advisory) when `vellum_py` fails. The gate never dies with a missing runtime; fail-open on uncertainty is doctrine (better to miss than mis-block).
- **Metric-code drift fix (judge-flagged on the loser):** `cw/skills/story-review/resources/prose-critique/analyze.py` is retained but receives a header comment `# SUPERSEDED by 'vellum style stats' — kept for backward compatibility only; do not extend.` All new metrics live in one module (`vellum_lib/style_stats.py`).
- **Agent allowlists** gain the exact Bash patterns for the engine (see each agent's frontmatter in §4): `Bash(python3 scripts/vellum*)`, `Bash(python scripts/vellum*)`, `Bash(py -3 scripts/vellum*)`.

Other judge-driven changes are marked **[JUDGE-FIX]** throughout and summarized in §13.

---

## 2. Full file tree (target: `C:/Users/iulia/Desktop/ultra-writing-plugin/vellum/`)

Fork = copy `repos/creative-writing-skills/cw/**` into `vellum/`, then apply all changes below. Repo-root files copied from the base repo root: `LICENSE` (Apache-2.0), `.github/workflows/ci.yml` (edited, A), `.gitattributes` (new, A). Do **not** copy: `.git/`, `agents/` (repo-root Mars-source agents), `skills/` (repo root), `mars.toml` if present, `.claude/`, `.codex/`, `.githooks/`, `bootstrap/`, `scripts/sync_cw_skills.py`, `scripts/create_skill_zips.py`, `CHANGELOG.md`, `AGENTS.md`, root `CLAUDE.md`.

```
vellum/
├── .claude-plugin/
│   ├── plugin.json                      # A — edited from cw/.claude-plugin/plugin.json
│   └── marketplace.json                 # A — adapted from repo root .claude-plugin/marketplace.json
├── ATTRIBUTION.md                       # A
├── NOTICE                               # A
├── LICENSE                              # A — verbatim from base repo root
├── .gitattributes                       # A — new
├── .github/workflows/ci.yml             # A — edited from base
├── .github/workflows/tests.yml          # H — new
├── hooks/                               # C — all new
│   ├── hooks.json
│   └── scripts/
│       ├── lib/common.sh
│       ├── guard-outline-before-prose.sh
│       ├── guard-bash-prose-writes.sh
│       ├── check-prose-after-write.sh
│       ├── session-start.sh
│       ├── pre-compact.sh
│       ├── session-stop.sh
│       ├── chapter-maintenance.sh
│       └── prose_core.py                # Python; pure-bash fallback lives inside the .sh files
├── scripts/                             # B — all new
│   ├── vellum                           # entry script (shebang python3; invoked via resolved interpreter)
│   └── vellum_lib/
│       ├── __init__.py
│       ├── util.py          # paths, atomic write, lockfile, yaml-lite frontmatter parser
│       ├── state.py         # state rebuild / state check / state card
│       ├── ledgers.py       # ledger check
│       ├── bible.py         # bible validate / reindex / links
│       ├── wordcount.py
│       ├── knowledge.py     # knowledge <character> --as-of N
│       ├── style_stats.py   # style stats
│       ├── pack.py          # pack chapter-NN
│       ├── exemptions.py    # dismiss / exemption staleness
│       ├── export.py        # export build (md bundle + stdlib EPUB + manifest)
│       └── cli.py           # argparse dispatch, exit codes
├── agents/                              # 16 total: 11 base + 5 new
│   ├── brainstormer.md  character-sim.md  critic.md  editor.md  reader-sim.md  web-researcher.md   # A: kept verbatim
│   ├── muse.md                # A edited
│   ├── writer.md              # A edited
│   ├── outliner.md            # A edited
│   ├── continuity-checker.md  # A edited
│   ├── style-creator.md       # A applies file authored by E
│   ├── blind-reader.md        # F new
│   ├── beta-reader.md         # F new
│   ├── cold-reader.md         # F new
│   ├── kb-lead.md             # G new
│   └── disruptor.md           # G new [JUDGE-FIX]
├── skills/                              # 32 total: 24 base + 8 new
│   ├── (24 base dirs kept; A edits 6 of them:
│   │    story-planning, writing-staffing, story-review, project-setup, story-memory, creative-writing-muse)
│   ├── story-ledgers/                   # D new  + resources/{ledger-files.md, state-card.md, write-time-capture.md}
│   ├── style-guardrails/                # E new  + resources/{tiers.md, structural-caps.md, smell-tests.md, fiction-carveouts.md}
│   ├── voice/                           # E new  + resources/{voice-template.md, drift-check.md, retune.md, voice-profile.md, blind-tag-test.md}
│   ├── cold-read/                       # F new  + resources/{charter.md, reader-ledger.md, issue-format.md, batching.md}
│   ├── gates/                           # D new  + resources/{quality-bar.md, readiness.md, finding-schema.md, genre-profiles.md}
│   ├── demolition/                      # G new
│   ├── export/                          # G new  + resources/{assembly.md, manifest.md}
│   └── kb-integrity/                    # D new
├── commands/                            # G — all new
│   ├── write-chapter.md  status.md  cold-read.md  retune.md  export.md  dismiss.md
├── templates/                           # G — all new (copied into author projects by project-setup)
│   ├── chapter.md  scene-card.md  promise.md  question.md
│   ├── knowledge-entry.md  prop.md  character.md  state-card.md
│   ├── project-config.json  exemptions.json
│   └── cold-read/{charter.md, reader-ledger.md, issues.md, batch-report.md}
└── tests/                               # H — all new (repo-level; not part of plugin runtime)
    ├── conftest.py  test_hooks.py  test_engine.py
    └── fixtures/sample-project/         # seeded project with one instance of every error class
```

Base skill inventory (the 24 kept dirs, for A's checklist): character-sim, creative-research, creative-writing-craft, creative-writing-modes, creative-writing-muse, grill-with-docs, information-hierarchy, intent-modeling, kb-management, knowledge-layers, llm-writing, md-validation, project-setup, qi-layer, reader-sim, reflect, shared-dao, story-memory, story-planning, story-review, structured-artifact, writing-principles, writing-staffing, zoom-out.

---

## 3. Global conventions (binding on every workstream)

### 3.1 Naming

- Entity ids: `<type>-<kebab-slug>` (e.g. `promise-ring-of-oath`, `character-mira-tarn`). File name for a kb entity = `<id>.md`. Kebab-case, ASCII, ≤ 48 chars.
- Chapters: `manuscript/chapters/chapter-NN.md`, NN zero-padded 2 digits minimum (books past 99 use consistent 3-digit padding: `chapter-100.md`); ordering is by frontmatter `number`, never by filename.
- Issue ids: cold-read `CR-###` (zero-padded 3, per-ledger counter); findings from all critics use the shared finding schema (§3.6).
- Exemption keys: `<category>:<entity_id>` where category ∈ `continuity|canon|voice|craft|structure|pace|repeat`. Deliberately excludes message text and chapter number (Novel-OS rationale: reworded messages must not resurrect a dismissal).
- Script/shell: POSIX sh-compatible bash, `LC_ALL=C` wherever matching; no associative arrays, no `mapfile`, bash-3.2-safe; LF endings everywhere.

### 3.2 Agent file format (frontmatter style follows the base exactly)

```markdown
---
name: <agent-name>                    # kebab, matches filename
description: <one sentence, when-to-use>
model: claude-opus-4-6 | claude-sonnet-5
skills:
- <skill-name>                        # agent declares its skill set (base constraint 2)
tools:
- Read
- Bash(rg *)
disallowed-tools:
- Edit
- Write
- AskUser
---

<body>
```

Rules: read-only critics/critiquers must list `Edit`, `Write` (and where applicable `AskUser`) under `disallowed-tools` and must not list them under `tools`. Model tiering: heavy judgment (muse, writer, critic, editor, style-creator, blind-reader, beta-reader, disruptor) = `claude-opus-4-6`; structure/depth-checks (outliner, continuity-checker, cold-reader, kb-lead, character-sim, reader-sim) = `claude-sonnet-5` (follow each base file's existing tier; new files per this rule).

### 3.3 Skill file format

`skills/<name>/SKILL.md` with frontmatter exactly like the base's (see `cw/skills/story-planning/SKILL.md`):

```markdown
---
name: <skill-name>
description: |
  <when to load; one paragraph>
---
```

Skills are self-contained (no cross-skill dependencies; a pointer line is allowed, the pointed-to content must be restated or loadable by name). Resources live in `resources/` and are loaded by name. Every ported resource carries an attribution header (§3.7).

### 3.4 Command file format

```markdown
---
description: <one line shown in /help>
---
<prompt body. Address the muse agent: "Spawn/handle via the muse agent...". Use $ARGUMENTS for args.>
```

### 3.5 Attribution header format (CI-checked)

- `.md`: first line after frontmatter:
  `<!-- Adapted from OWNER/REPO (path/in/repo) — LICENSE. Changes: one-line summary. -->`
- `.py` / `.sh`: line(s) 2+ directly under the shebang:
  `# Adapted from OWNER/REPO (path) — MIT`  +  `# Changes: one-line summary`
- Ideas-only sources (unlicensed): `Mechanism credited to OWNER/REPO; no source text or code copied.`
- Unported (original) files: no header. Every file whose content derives from another repo MUST carry the header; CI greps for missing ones against the ATTRIBUTION.md table.

### 3.6 Shared finding schema (`gates/resources/finding-schema.md`)

Adapted from `author-toolkit/references/finding-schema.json` (MIT). All critics MAY emit this JSON; muse uses it when merging parallel reports.

```json
{
  "audit": "continuity|prose|structure|voice|reader",
  "technique": "short-kebab-tag",
  "severity": "note|suggestion|warning|blocker",
  "location": {"file": "manuscript/chapters/chapter-07.md", "line": 42, "quote": "…"},
  "issue": "one sentence",
  "confidence": "deterministic|judgment"
}
```

### 3.7 Project layout (created by `project-setup` in the *author's* project; documented in its CLAUDE.md, swappable per base constraint 4)

```
manuscript/chapters/chapter-NN.md
kb/
  story.md                 # schema-version: 2
  characters/*.md  world/*.md  timeline/
  styles/{voice.md, baseline.md}  samples/  vocab.md
  promises/*.md  questions/*.md  knowledge/*.md  props/*.md  clock.md
  issues/*.md              # base writing-issues ledger (unchanged)
  exemptions.json  project-config.json
state/                     # machine-authoritative; NEVER hand-edited (enforced, §5)
  _tracking-state.json  _derived-hashes.json  state-card.md  .vellum.lock
work/
  outline/  drafts/  critique-reports/  brainstorm/
  demolition-history.md  voice-debt.json
  cold-reads/<YYYY-MM>/{charter.md, reader_ledger.md, issues.md, batches/}
  snapshots/
export/
```

### 3.8 Config (`kb/project-config.json`, created from `templates/project-config.json`)

```json
{
  "drift_interval": 5,
  "voice_debt_gate": false,
  "stop_gate": false,
  "default_word_target": 3200,
  "word_band": 0.15
}
```

`voice_debt_gate` and `stop_gate` default **off** — the three hard gates stay exactly three unless the author opts into more. [JUDGE-FIX: adopts Scriptorium's toxic-debt and Stop gates as opt-in so the default experience keeps the three-gate philosophy.]

---

## 4. Workstream A — packaging, base agent edits, base skill edits

### 4.1 `.claude-plugin/plugin.json`

Edit from `cw/.claude-plugin/plugin.json`: `name: "vellum"`, `version: "0.1.0"`, rewritten description ("A working novelist's daily tool for Claude Code: one command for the chapter loop, three hard gates, everything else advisory and silent when clean."), keep `author` (Jimmy Yao, per Apache-2.0 fork courtesy) and add `"homepage"` unchanged. [JUDGE-FIX: real product name so `/vellum:` prefixes resolve.]

### 4.2 `.claude-plugin/marketplace.json`

Adapt from `repos/creative-writing-skills/.claude-plugin/marketplace.json`: `name: "vellum"`, metadata version `0.1.0`, plugins[0].name `vellum`, description rewritten, `source: "./vellum"` if the marketplace sits at repo root, else `"."`. Keep owner block.

### 4.3 ATTRIBUTION.md + NOTICE

Reproduce the attribution table below verbatim as the core of `ATTRIBUTION.md` (add intro: fork provenance, date, base commit). `NOTICE` bundles: Apache-2.0 notice for the base + Velith; MIT notices for all MIT sources; the autonovel ideas-only statement.

| Source (exact path) | License | Ported | How |
|---|---|---|---|
| base `cw/*` (haowjy/creative-writing-skills) | Apache-2.0 | Entire skeleton (agents, skills, muse architecture) | Fork, retain copyright/notice |
| `story-skills/docs/schema-v2.md`; `skills/plot-structure/references/{promise,question}-template.md`; `skills/chapter-writing/references/chapter-template.md`; continuity CLI contract in `skills/revision-continuity/SKILL.md` | MIT | Bible schema, promise/question ledger schemas, word rule, deterministic check catalog | Adapted (layout renamed), MIT notice |
| `oh-story-claudecode/skills/story-setup/references/templates/hooks/*`; `story-long-write` state-card/_tracking-state design | MIT | Hook logic, portability lessons, transactional state + state card | Rewritten in English; mechanisms + lessons credited; script headers cite |
| `avoid-ai-writing/detector/patterns.js`, `references/patterns.md`, `dist/avoid-ai-writing.md` | MIT | Detector categories + replacement tables | Python port in `prose_core.py`/`vellum_lib` with notice; tables adapted |
| `stop-slop/references/{phrases,structures}.md`, `SKILL.md` | MIT | Supplemental phrase/structure lists | Nonfiction-tuned — only through the fiction-carveouts filter |
| `autonovel/voice.md`, `ANTI-PATTERNS.md`, `ANTI-SLOP.md` | **No license — all rights reserved** | Tier taxonomy, structural-cap concept, tuning-fork scaffold, smell tests | **Ideas only; all prose and tables re-written independently; no verbatim text.** Attribution: "Tier taxonomy and voice-scaffold structure inspired by NousResearch/autonovel." Word lists re-derived |
| `claude-ghost-writer/skills/{demolish,retune}/SKILL.md` | MIT | Demolition, retune protocols | Fiction-tuned adaptation, MIT notice |
| `Velith/agents/beta-reader.md` + quality-bar | Apache-2.0 | Beta-reader four-reader protocol, verdict schema, readiness gate, shared rubric | Adapted, Apache notice |
| `fiction-forge/docs/cold-read.md`, `templates/{read_charter,reader_ledger,issues,batch_report}.md` | MIT | Cold-read protocol end-to-end | Heavily adapted to subagent orchestration; protocol credited |
| `fiction/agents/{james-wood,stephen-king,ursula-le-guin,roxane-gay}.md`, `agents/review-coordinator.md` | MIT | Persona critics, digest/fan-out coordinator | Trimmed/rewritten, MIT notice |
| `author-toolkit/skills/story-structure/references/{landmark-beats,signposts,structure-map}.md`, `references/finding-schema.json` | MIT | Weiland/Bell beats, finding schema | Adapted, MIT notice |
| `Novel-OS/core/continuity_engine.py` (Finding.key exemption design, dormant-thread/sagging-middle checks) | MIT | Dismissed-findings keying, check catalog, stall detector | Re-implemented in Python, MIT notice |
| book-genesis-v4 blind-judge/disruptor/audit-gate | various | Blind-read gate, disruptor lane (design-level) | Ideas only where unlicensed; credited in ATTRIBUTION |
| Claude-Book, Claude-Code-Novel-Writer, GOAT scene cards, Re3/LongWriter, Fablecraft/Scriptorium review mechanisms | various | Architectural ideas (immutable-bible split, hooks suite, word budgets, context recipe, measured voice profile, stdlib runtime policy) | Design-level inspiration, credited; no code/text copied from unlicensed repos |

### 4.4 `.gitattributes` (plugin repo root, new)

```
* text=auto
*.sh text eol=lf
*.py text eol=lf
*.md text eol=lf
```

### 4.5 Edited base agents (A)

For each: copy the `cw/agents/<file>.md`, then apply the edit list. Keep base frontmatter shape (§3.2).

**muse.md** (keep `model: claude-opus-4-6`, skills list; keep tools, ADD `- Bash(python3 scripts/vellum*)`, `- Bash(python scripts/vellum*)`, `- Bash(py -3 scripts/vellum*)`):
1. Replace the `kb-lead` hedge at line ~71 ("where a kb-lead subagent exists") with: knowledge capture routes to `@kb-lead` (shipped).
2. New section "**Own the Gates**": muse enforces the three blocking gates and *never* marks them satisfied on its own judgment — only from artifacts on disk (`state/_tracking-state.json` for outline acceptance, `work/critique-reports/blind-chapter-NN.md` verdict ≠ `LOST` for pivotal acceptance, `work/critique-reports/readiness-report.md` `verdict: PASS` for export). Muse may *propose* a chapter be flagged pivotal; only the author's approval at outline-acceptance sets `pivotal: true` in the outline frontmatter. [JUDGE-FIX: pivotal flagging is author-approved, not muse-judged.]
3. New section "**Dismissal routing**": when the author says a finding is intentional, muse runs `"$PY" scripts/vellum dismiss <key> --reason "<author words, verbatim>"` and never re-raises it. Muse never runs `dismiss` without the author's explicit word.
4. New section "**Ground truth**" (GR-09): precedence user > manuscript prose > outline > state > derived metrics. When state and prose disagree: surface, never silently fix.
5. New section "**Offer demolition before final**": before marking a chapter `final`, muse offers one demolition pass (`/vellum` demolition skill); author may decline; declining is recorded in one line in the chapter's Demolition Log section. [JUDGE-FIX: demolition almost never runs if author-invoked only.]

**writer.md** (opus; keep existing disallowed git tools): add contract line: "Write only under `manuscript/` and `work/`; never `kb/` or `state/`." Add skills entries `style-guardrails`, `voice`. Add note: the spawn prompt always carries the fixed context recipe (§9 of this spec); fill chapter frontmatter completely (`characters`, `mentions`, `promises-advanced`) — the maintenance pass derives what it can and flags the rest. [JUDGE-FIX: addresses "state rebuild quietly goes blind if writer skips frontmatter."]

**outliner.md** (sonnet): replace the line at file line 40 (`run \`meridian mermaid check\``) with: "Use `/md-validation` for mermaid syntax guidance." Add output requirements: outline frontmatter per §7.1 (`approved: false`, `pivotal: false`, `word-target`, `verbatim:` list); per-beat word quotas summing ≈ `word-target`.

**continuity-checker.md** (sonnet): delete the sentence containing `meridian kg graph` (file line ~31); replace with: "Run the deterministic engine first (`python scripts/vellum ledger check` and `bible validate`); spend your own reading on what it cannot judge: knowledge boundaries, plausibility, terminology drift. Never re-report findings whose keys are in `kb/exemptions.json`." Add tools entries for the three vellum Bash patterns.

**style-creator.md** (opus; content authored by E, file applied by A): keep base frontmatter + add skills `style-guardrails`, `voice`. Body adds three duties: (1) fill `kb/styles/voice.md` Part 2 from author samples in `kb/samples/` using `creative-writing-craft/resources/style-analysis.md` methodology; (2) run drift checks (`vellum style stats --baseline` mechanical + LLM comparison against exemplar/anti-exemplar fork) every `drift_interval` chapters or on "this doesn't sound like me"; (3) **author-edit harvesting**: when the author edits an accepted chapter, diff author text vs the prior agent draft (from `work/drafts/`) and promote characteristic choices into voice exemplars — the strongest available voice signal, free. (4) build the measured per-1k voice profile (§8).

### 4.6 Edited base skills (A)

**story-planning**: fix the broken resource list (lines 13–15 must point at the real files: `resources/creative-direction.md`, `resources/brainstorming.md`, `resources/story-architecture.md` — check actual names on disk and point each bullet at the file it describes). Add two resources:
- `resources/structure-beats.md` — Adapted from `author-toolkit/skills/story-structure/references/landmark-beats.md`, `signposts.md`, `structure-map.md` (MIT): K.M. Weiland 10-beat map + James Scott Bell 14 signposts with percentage positions; each beat annotated with the word-quota convention.
- `resources/scene-cards.md` — written fresh (GOAT-Storytelling-Agent scene card concept, credited ideas-only): 9 fields — Characters, Place, Time, Event, Conflict, Story value, Value charge, Mood, Outcome — plus a template block. Add SKILL.md bullets loading both.

**writing-staffing**: add dispatch entries (each states what the spawned agent may/may not read): `@blind-reader` (pivotal chapters only; prompt = chapter prose + previous-chapter tail + quality-bar axes, NOTHING else — no outline, no kb); `@beta-reader` (pre-export; may read kb/story.md + genre file + full manuscript first; outlines/style/critiques only after first read); `@cold-reader` (batch assignment; charter + ledger + last 40 issues + batch's chapters); `@kb-lead` (fact extraction + ledger capture at chapter acceptance, replacing the muse's apply-it-yourself fallback); `@disruptor` (proposal-only; author opts in for flat chapters; never writes). Add **context packs** section: when assembling a writer prompt, rank candidate context by relevance (cast, referenced facts, vocab) and cap total; `vellum pack chapter-NN` does the deterministic part. Add **stall detection** (mechanism from Novel-OS sagging-middle detector, credited): protagonist reactive for 3 consecutive chapters + zero movement in state-card `Story position`/cast lines → muse proposes a structural intervention.

**story-review**: add `resources/prose-critique/personas/{wood,king,leguin,gay}.md` — Adapted from `fiction/agents/{james-wood,stephen-king,ursula-le-guin,roxane-gay}.md` (MIT), each trimmed to critical lens + method + tone (≤ 60 lines each). SKILL.md gains a "Persona panel" section: muse fans out `@critic` with `focus: persona:<name>` for milestone chapters; personas critique execution, not premise (base rule). Add header comment to `resources/prose-critique/analyze.py`: `# SUPERSEDED by 'vellum style stats' — kept for backward compatibility only; do not extend.`

**project-setup**: extend the Create-the-Files step: create the full §3.7 layout; copy `templates/` into the project; write `kb/story.md` with `schema-version: 2` (adapted from `story-skills/docs/schema-v2.md`); create `kb/styles/voice.md` from the voice template; run `git init` + write `.gitattributes` (`*.md text eol=lf`, `*.sh text eol=lf`); record chapter word-target conventions; run the **voice-capture interview** (collect 3–5 author samples → `kb/samples/` → hand to `@style-creator`); tell the author the three gates in one paragraph; write `kb/project-config.json`. Also add two optional craft resources (see §8.4) to the interview's "what to load" list.

**story-memory**: add one line to the resource list: "For promises/questions/knowledge/props/clock capture, also load `/story-ledgers` (it restates what it needs)." Pointer only — skills stay self-contained.

**creative-writing-muse**: stance list gains Ledgers (`/story-ledgers`), Gates (`/gates`), Demolition (`/demolition`), Voice (`/voice`); add note that in single-agent mode the stance switch replaces subagent isolation — demolition and drafting must never share a stance-turn.

### 4.7 `.github/workflows/ci.yml` (A edits)

Start from `repos/creative-writing-skills/.github/workflows/ci.yml`. Changes: (1) delete the meridian install + `meridian mars check` steps; (2) keep `claude plugins validate cw` → change to `claude plugins validate vellum`; keep frontmatter check (globs now `agents/*.md skills/*/SKILL.md`); (3) replace `sync_cw_skills.py --lint` with a `scripts/ci/lint_vellum.py` (H-owned; A references it) that checks: no Meridian vocab (`meridian|opus46|fable|sol|hook\.toml`) anywhere under `vellum/`; every file in `skills/ hooks/ scripts/ templates/` that appears in the ATTRIBUTION table carries the §3.5 header; `hooks.json` JSON parses; no file under `vellum/` exceeds 100 KB. (4) add job calling H's tests (see §11).

---

## 5. Workstream B — the deterministic engine (`scripts/`)

Python ≥ 3.8, stdlib only (`sys, os, re, json, hashlib, argparse, datetime, zipfile, shutil, tempfile, unicodedata`). Entry `scripts/vellum`:

```python
#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vellum_lib.cli import main
if __name__ == "__main__":
    sys.exit(main())
```

Header: `# Vellum deterministic engine. Original code (base design credited in ATTRIBUTION.md).` Always invoked as `"$VELLUM_PY" <root>/scripts/vellum <subcommand>`; never relies on the exec bit.

### 5.1 Global engine rules (in `vellum_lib/util.py`)

- **Atomic writes:** every write of a derived file goes to `<file>.tmp-<pid>` then `os.replace()`.
- **Lockfile:** any command that writes state takes an exclusive lock via `state/.vellum.lock` (`os.open(O_CREAT|O_EXCL)`; stale > 60 s → warn + proceed). On lock contention: exit 2 with message.
- **Hash-verified derived files** [JUDGE-FIX, from Scriptorium]: `state/_derived-hashes.json` maps each derived file (`state/_tracking-state.json`, `state/state-card.md`) → sha256 of the last engine-written content. `state check` recomputes; mismatch → finding `state:hand-edited` ("state files are engine-written; run `vellum state rebuild`"). `bible reindex` repairs.
- **Frontmatter parser:** minimal YAML subset parser (key: value, lists via `- `, single-level nested maps for `holders:`/`custody:`; quoted strings; no anchors). Fail loudly (exit 2) on unparseable frontmatter with file+line.
- **Word rule** (verbatim from `story-skills/docs/schema-v2.md`, MIT): a word is a run of letters/digits in any script; apostrophes and hyphens join.
- **Exemptions:** every check loads `kb/exemptions.json` and drops findings whose `key` matches an entry with `status: active`. `status: stale` entries re-arm once.
- **Exit codes:** 0 clean · 1 findings · 2 schema/usage error.

### 5.2 Subcommands (CLI contract — C, D, G, H code against this)

| Command | Behavior |
|---|---|
| `state rebuild` | Regenerate `state/_tracking-state.json` from `kb/` + `manuscript/` frontmatter + ledgers, then `state/state-card.md` (7 fixed sections, ≤ 12 KB hard cap — refuse + report if content overflows). Fields and example in §7.2. Also computes `voice_debt` from `work/voice-debt.json`. Writes `_derived-hashes.json`. |
| `state check` | Transactional invariants (outline-gate precondition): state exists; schema_version current; no half-committed chapter (previous chapter `status ∈ {accepted, final}` for a new-chapter start); `pending_capture: false`; derived-file hashes match. Exit 0/2 with one-line reason. |
| `wordcount [--write] [chapters…]` | Compute words per chapter; `--write` updates `word-count` frontmatter; band check vs `word-target` (default ±15% from project config); outside band = finding with pointer to `creative-writing-craft/resources/prose-writing.md` compression guidance. |
| `ledger check` | Deterministic continuity (catalog adapted from `story-skills` revision-continuity contract + `Novel-OS/core/continuity_engine.py`, MIT): dead-character reappearances (character `status: deceased` + `died-in` vs chapter `characters:` lists; `mentions:` exempt); promise ordering (`planted-in` ≤ `reinforced` < `payoff-in`; unfired setups past `target-by`; dormant promises > 3 chapters); question states; POV-not-in-cast (chapter `pov:` must appear in `characters:`); **frontmatter completeness** — missing `characters`/`mentions`/`promises-advanced`/`pov` on any chapter with ≥ 200 words → finding `frontmatter:incomplete` (fails loud, never silently passes) [JUDGE-FIX]; prop custody vs `custody:` owner/location; knowledge `learned-in`/`holders` vs chapters where the character uses the fact (see `knowledge`); clock-table monotonicity within a thread; outline-verbatim lines present in accepted chapters. |
| `knowledge <character-id> --as-of N` | Queryable knowledge backend [JUDGE-FIX, from Scriptorium]: prints the facts the character holds as of chapter N with certainty levels; `--audience` flag gives audience-knowledge view for dramatic-irony checks. Feeds `ledger check`: using a fact in a chapter before its `learned-in` is a hard error. |
| `bible validate` / `reindex` / `links` | Frontmatter schema validation for every kb entity (§3.7 schemas); kebab-case ids; rebuild `_index.md` registries deterministically; cross-reference integrity (broken id references = findings). Port of the story-skills CLI contract, adapted to our layout. |
| `style stats <file\|glob> [--baseline]` | Sentence-length distribution + variance (burstiness), opener variety, dialogue ratio, em-dash density, type-token ratio, paragraph-shape entropy. `--baseline` compares to `kb/styles/baseline.md` (keyed numeric profile, §8.2) and appends a drift report section. Also computes the **measured per-1k voice profile** (§8.2). |
| `pack chapter-NN` | Assemble the deterministic half of the writer context pack: state card, scene brief path, previous-chapter tail (last ~500–800 words), cast cards for `characters:`, relevant vocab sections, ledger anchors ranked by referenced entities. Emits a path list + inlined small files (JSON to stdout: `{paths: […], inline: {…}}`). |
| `dismiss <key> --reason "…"` | Append `{key, reason, dismissed_at, chapter, status: "active"}` to `kb/exemptions.json`. Refuses if key exists active. |
| `debt list` / `debt clear <id\|all>` | Voice-debt accounting [JUDGE-FIX, from Scriptorium]: reads `work/voice-debt.json` (written by the post-write hook). `state check` consults it when `voice_debt_gate: true`. |
| `readiness` | Evaluates §10 preconditions; prints PASS or a prioritized missing list. |
| `export build --out <dir> [--epub]` | Deterministic assembly (§10.2): joined chapters, title page, manifest with sha256 checksums + gate provenance; `--epub` builds a stdlib-zipfile EPUB with a stable identifier (`book-uuid` from `kb/story.md`) so highlights survive rebuilds [JUDGE-FIX: removes pandoc from the critical path; pandoc remains optional for DOCX/PDF]. |

---

## 6. Workstream C — hooks

All scripts bash (run under Git Bash on Windows), invoked as `bash "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/<name>.sh"`. Shared rules (lessons carried from `oh-story-claudecode/skills/story-setup/references/templates/hooks/` — read `guard-outline-before-prose.sh`, `check-prose-after-write.sh`, `lib/common.sh` there before writing; credit in headers): `export LC_ALL=C` for byte-stable matching; **never export the tool payload** (E2BIG — pipe to interpreter via stdin); fail-open on uncertainty in blocking gates; node/python-optional with pure-bash fallback; silent when clean; drive-letter normalization (`\\`→`/`, `[A-Za-z]:[/\]` case branch); `project_root()` / `resolve_project_path()` / `vellum_py()` from `lib/common.sh` (ported and translated from `oh-story-claudecode/.../lib/common.sh` — drop the Chinese active-book logic, keep CLAUDE_PROJECT_DIR→git-root→cwd resolution and the LC_ALL=C lessons as comments).

### 6.1 `hooks/hooks.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/guard-outline-before-prose.sh\""}]},
      {"matcher": "Bash", "hooks": [{"type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/guard-bash-prose-writes.sh\""}]}
    ],
    "PostToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-prose-after-write.sh\""}]}
    ],
    "SessionStart": [
      {"matcher": "startup|resume|clear|compact", "hooks": [{"type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-start.sh\""}]}
    ],
    "PreCompact": [{"hooks": [{"type": "command",
      "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/pre-compact.sh\""}]}],
    "Stop": [{"hooks": [{"type": "command",
      "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-stop.sh\""}]}],
    "SubagentStop": [
      {"matcher": "writer", "hooks": [{"type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/chapter-maintenance.sh\""}]}
    ]
  }
}
```

[ JUDGE-FIX: SessionStart matcher includes `clear` — `startup|resume|compact` alone missed it. PreCompact needs no matcher. ]

### 6.2 Scripts

Each script: `#!/bin/bash` + attribution header (port credit to oh-story) + `set -u` (no `-e`; every failure mode handled explicitly).

| Script | Event | Behavior |
|---|---|---|
| `guard-outline-before-prose.sh` | PreToolUse Write/Edit/MultiEdit | Read stdin JSON; extract `tool_input.file_path` (pipe to `prose_core.py extract-target`; **pure-bash fallback**: `grep`/`sed` for `"file_path"\s*:\s*"..."`). Normalize path. If target NOT under `manuscript/chapters/` → exit 0. Else check: (1) `work/outline/chapter-NN.md` exists and frontmatter `approved: true` (bash grep; two-digit NN from the target filename); (2) if `vellum_py` resolves: `"$VELLUM_PY" scripts/vellum state check` exit 0 (else print one advisory line to stderr and continue — the bash predicate still gates); (3) rewriting an existing `draft` chapter re-checks only (2). Parse failure or target ambiguity → exit 0 (fail-open). On block: exit 2, stderr = exactly one sentence naming the missing precondition + the exact command to satisfy it. **BLOCKING — gate 1.** |
| `guard-bash-prose-writes.sh` | PreToolUse Bash | Same stdin; scan `tool_input.command` for redirection/heredoc/tee/cp/mv writing into `manuscript/chapters/` (pattern list from oh-story's Bash-guard concept). If found, run the same predicate as the Write guard for the detected target. **Outline-copy detector**: target is a new chapter file while a prior chapter of near-identical byte size exists → run `diff` similarity; > 90 % shared lines → block. Uncertain → exit 0. **BLOCKING — gate 1, alternate path.** |
| `check-prose-after-write.sh` | PostToolUse Write/Edit/MultiEdit | Only for `manuscript/chapters/*.md`. Hard signals: truncation markers, model-refusal phrases, placeholder text (`[TODO`, `[INVENTED]` flagged if left in an `accepted` chapter), engineering words in prose, `[VERIFY]` remnants ("extract to kb questions before acceptance"). Then engine path: `prose_core.py scan <file>` (tier-1 banned words, tier-2 cluster heuristic, em-dash density, near-verbatim duplicated line check — patterns ported from `avoid-ai-writing/detector/patterns.js` fiction subset + autonovel tier tables *as re-derived data*). Bash fallback: `grep -n` tier-1 table embedded in `prose_core.py --emit-grep`. Output: PostToolUse additionalContext JSON, one line per finding. **Advisory, exit 0 always; silent when clean.** Writes/updates `work/voice-debt.json` (open tier-1 hits with ids) for the debt accounting. `<!-- voice:skip -->` anywhere in the chapter suppresses tier-1 debt accrual for that chapter (author escape hatch). |
| `session-start.sh` | SessionStart | If `state/state-card.md` exists: print card + last 5 `work/` issue lines + pending `[VERIFY]` count + resume pointer (current chapter, its outline status). Else: one line suggesting `/vellum:status`. Advisory. |
| `pre-compact.sh` | PreCompact | Copy `state/state-card.md`, ledger `_index` heads, current chapter path, last 40 lines of the active issue log → `work/snapshots/compact-<timestamp>/`. No git operations. Silent on success. |
| `session-stop.sh` | Stop | If `state/_tracking-state.json` has `pending_capture: true` → one reminder line naming the close-out command; else silent. If `kb/project-config.json` `stop_gate: true`: also run the post-write hard-signal scan on the current chapter and emit a block on truncation/refusal markers only (documented opt-in fourth gate). Default config = never blocks. |
| `chapter-maintenance.sh` | SubagentStop matcher `writer` | Runs the mechanical close-out itself: `"$VELLUM_PY" scripts/vellum wordcount --write && ledger check && state rebuild`. Success → **silent** (sets `pending_capture: false`; muse still does LLM-side fact extraction via `@kb-lead` — this hook is the mechanical half of the transaction). Failure → print failing check + fix direction as the SubagentStop message (stdout goes to transcript; hence silent-on-success is mandatory). Missing interpreter → bash wordcount + advisory line. |

### 6.3 `prose_core.py`

Python (stdlib). Subcommands: `extract-target` (JSON on stdin → target path on stdout), `scan <file>` (findings JSON lines on stdout), `emit-grep` (tier-1 table as egrep pattern). Data tables (tier-1/tier-2/filler) live at the top as Python lists — re-derived word lists (autonovel is ideas-only; supplemented by fiction-relevant entries from `avoid-ai-writing/references/patterns.md`, MIT, which IS ported and credited). Attribution header cites both.

---

## 7. Workstream D — state, ledger, and gate skills + schemas

### 7.1 Outline frontmatter (written by `@outliner`, approved by author; gate-1 input)

```yaml
---
chapter: 7
title: "The Salt Road"
approved: false          # author acceptance, recorded by muse; gate 1 requires true
pivotal: false           # author-approved flag; gate 2 (blind reader) requires it for acceptance
word-target: 3200
verbatim:
  - "You buried him where the road forks."
  - "Second time someone has lied to me about a grave."
---
## Beats
1. <beat> — quota 900 — POV Mira — ...
```

### 7.2 Chapter frontmatter (`templates/chapter.md`; extended from `story-skills/skills/chapter-writing/references/chapter-template.md` + oh-story word contract)

```yaml
---
title: "The Salt Road"
number: 7
status: outlined|draft|revised|accepted|final
approved-outline: work/outline/chapter-07.md
pov: character-mira-tarn
characters: [character-mira-tarn, character-old-tom]   # present in-scene
mentions: [character-vess]                              # referenced/remembered/dead — no continuity error
promises-advanced: [promise-ring-of-oath]
word-target: 3200
word-count: 3148
---
```

### 7.3 Ledger schemas (D; full examples go in `story-ledgers/resources/ledger-files.md`; `templates/*.md` carry the same frontmatter)

**`kb/promises/<id>.md`** (schema adapted from `story-skills/skills/plot-structure/references/promise-template.md`, MIT; extended with `reinforced:` + `planned` status):

```yaml
---
id: promise-ring-of-oath
type: promise
title: "The ring must be returned to the House"
status: planned|planted|reinforced|paid-off|abandoned
planted-in: chapter-03
reinforced: [chapter-09]
payoff-in: null          # chapter-NN once paid
target-by: chapter-20    # soft deadline; ledger check flags unfired setups past target
abandoned-reason: null
---
<prose: the promise as the reader experiences it>
```

**`kb/questions/<id>.md`** (adapted from `question-template.md`, MIT):

```yaml
---
id: question-who-burned-the-annex
type: question
title: "Who burned the annex?"
status: open|answered|dormant
raised-in: chapter-02
answered-in: null
answer: null
---
```

**`kb/knowledge/<id>.md`** (3-level certainty; mechanism from fiction-forge cold-read knowledge map + Novel-OS-style per-holder query — queryable via `vellum knowledge`):

```yaml
---
id: knowledge-tom-faked-his-death
type: knowledge
title: "Tom faked his death"
statement: "Old Tom is alive; the funeral was staged."   # canon fact prose
holders:
  - character: character-mira-tarn
    learned-in: chapter-09
    certainty: knows          # knows | half-glimpse | audience-only
audience-learned-in: chapter-09   # when the READER learns it (dramatic-irony queries)
superseded-by: null
---
```

**`kb/props/<id>.md`** (custody from fiction-forge prop custody):

```yaml
---
id: prop-ring-of-oath
type: prop
title: "Ring of Oath"
introduced-in: chapter-01
custody:
  owner: character-mira-tarn   # or null
  location: "Mira's coat pocket"
  status: in-play              # in-play | destroyed | lost | resolved
history:
  - {chapter: 3, change: "Given to Mira by Tom"}
---
```

**`kb/characters/<id>.md`**:

```yaml
---
id: character-old-tom
type: character
name: "Old Tom"
status: alive            # alive | deceased | unknown
died-in: null            # chapter-NN when status: deceased
aliases: ["Thomas Reave"]
pov-eligible: true
---
```

**`kb/clock.md`** — one table, rows = threads (position/clock rows from `fiction-forge/templates/reader_ledger.md`, MIT):

```markdown
| thread | started | position as of | clock reading | last chapter |
|---|---|---|---|---|
| siege-countdown | ch 4 | day 9 of 30 | 21 days remain | 7 |
```

**`kb/exemptions.json`**:

```json
{
  "schema_version": 1,
  "exemptions": [
    {"key": "continuity:character-old-tom-seen-after-death",
     "reason": "Ghost sightings are intentional (author words here)",
     "dismissed_at": "2026-09-09", "chapter": "chapter-09",
     "status": "active", "stale_note": null}
  ]
}
```

`status: active|stale`. **Expiry / re-arm:** when `bible validate` detects the underlying fact changed (entity status change, `died-in` edit, promise `payoff-in` edit, knowledge entry revision), the exemption flips to `stale` and the finding re-arms once with note "previously dismissed; underlying fact changed on <date>". Muse re-asks; author re-decides. (Novel-OS `Finding.key` rationale + fractal dirty-propagation idea, MIT, credited.)

### 7.4 `skills/story-ledgers/` (D, new)

SKILL.md frontmatter per §3.3; trigger description: "Load when planning chapters, capturing what a chapter changed, or answering what's still open / who knows what."
- `resources/ledger-files.md` — the §7.3 schemas with prose guidance. Header: Adapted from `story-skills/skills/plot-structure/references/{promise,question}-template.md` — MIT.
- `resources/state-card.md` — the fixed 7-section state-card spec (mechanism from `oh-story-claudecode/skills/story-long-write/SKILL.md` context-file design, MIT; structure rewritten for English): **Story position · Open promises & questions (top N by age) · Active cast state (one line each) · Knowledge boundaries · Props & clock · Next beats with word quotas · Flags (exemptions digest, do-not-re-explain register)**. ≤ 12 KB hard cap.
- `resources/write-time-capture.md` — the chapter transaction: after a chapter is accepted → capture facts (`@kb-lead`) → update ledgers → `state rebuild`. Never hand-edit derived files (hash check enforces).

### 7.5 `skills/kb-integrity/` (D, new)

Trigger: "a vellum check failed, or muse routes integrity work." Teaches: run `vellum bible validate / ledger check / wordcount / state check / knowledge --as-of`; interpret findings; the exemption protocol (`dismiss` only with the author's explicit word; key format; what expiry means); `bible reindex` repairs; "scanners are regression fences, not discovery" (fiction-forge framing) — the cold read finds what linters can't.

### 7.6 `skills/gates/` (D, new)

Trigger: "muse before accepting a pivotal chapter, before export, any scoring task."
- `resources/quality-bar.md` — shared 5-axis rubric (voice, structure, depth, specificity, reader), 1–10 with anchors (adapted from `Velith/agents/beta-reader.md` quality-bar, Apache-2.0). All agents reference this file; never restate the axes. Adds per-gate verdict contracts [JUDGE-FIX]: each gate's PASS / REVISE / ESCALATE criteria written as a table (blind: `ENGAGED|STALLED|LOST`; beta: PASS rule below; critic: what severity blocks acceptance vs notes).
- `resources/readiness.md` — the §10 preconditions as a checklist muse can evaluate.
- `resources/finding-schema.md` — §3.6 schema with examples.
- `resources/genre-profiles.md` [JUDGE-FIX, from Fablecraft] — numeric genre truth agents reference, never restate: chapter-length norms, dialogue-ratio bands, scene-length norms per genre (fantasy/thriller/mystery/romance/horror/litfic — aligning with `creative-writing-craft/resources/genre/*`). `style stats` and `wordcount` findings cite it.

---

## 8. Workstream E — voice and style

### 8.1 `skills/style-guardrails/` (E, new)

Trigger: "loaded by writer AND critics before drafting/critiquing prose; also drives the post-write net."
- `resources/tiers.md` — Tier-1 kill-on-sight table, Tier-2 suspicious-in-clusters-of-three, Tier-3 filler phrases. Structure ported from `autonovel/voice.md` **ideas-only** (no license — all prose and tables re-written independently; word lists re-derived, supplemented by fiction-safe entries ported from `avoid-ai-writing/dist/avoid-ai-writing.md` + `references/patterns.md`, MIT, and `stop-slop/references/phrases.md` + `structures.md`, MIT, used only through the carve-out filter). Header: `Mechanism credited to NousResearch/autonovel; no source text copied. Supplemental lists Adapted from avoid-ai-writing (MIT) and stop-slop (MIT).`
- `resources/structural-caps.md` — numeric thresholds with fiction tuning: em-dashes per page, hedges per page, sentence-length variance floor, consecutive-paragraph-opener repetition, negative-setup/positive-flip sentence shape. Detector mechanics taxonomy from `autonovel/ANTI-PATTERNS.md` (ideas-only) machine-implemented from `avoid-ai-writing/detector/patterns.js` categories (MIT — Python port lives in `prose_core.py`).
- `resources/smell-tests.md` — four tests (read-aloud, surprise, specificity, "AI wrote this?"), rewritten (autonovel ideas-only).
- `resources/fiction-carveouts.md` — stop-slop lists are nonfiction-tuned; explicit exemption rubric (deliberate voice register, unreliable-narrator diction, period dialogue) so the mechanical net never flattens voice.
- **The measured-profile law** [JUDGE-FIX, from Fablecraft]: bans never override the measured author profile — if the author uses em-dashes at 4/1k, 4/1k is correct for this book; caps adapt to `kb/styles/baseline.md` rather than judging the author's voice a violation.

### 8.2 `skills/voice/` (E, new)

Trigger: "project-setup voice capture; every `drift_interval` chapters; author says 'this doesn't sound like me'."
- `resources/voice-template.md` — two-part `kb/styles/voice.md`: Part 1 guardrails (tier summary restated inline for self-containment + the measured-profile law); Part 2 identity scaffold: Tone, Sentence Rhythm, Vocabulary Register, POV & Tense, Dialogue Conventions, Exemplar Passages (3–5 paragraphs = the tuning fork), Anti-Exemplars (3–5 paragraphs of what this voice is NOT). Scaffold from `autonovel/voice.md` Part 2, rewritten (ideas-only).
- `resources/voice-profile.md` [JUDGE-FIX, from Fablecraft] — the **measured per-1k voice profile**: `vellum style stats` emits per-1k rates (em-dashes, hedges, tier-1/tier-2 hits, dialogue ratio, TTR, burstiness) into `kb/styles/baseline.md` as a numeric table; **bidirectional diff**: drift reports list both over-shoot (subtraction needed) and under-shoot vs the author's own rates (restoration needed — "you cannot edit toward a voice you haven't measured"); author-measured rates override tier bans (cross-links §8.1 law).
- `resources/blind-tag-test.md` [JUDGE-FIX, from Fablecraft] — falsifiable check that voice capture worked: shuffle author-corpus passages with manuscript passages, tags stripped; a fresh `@critic` (no project context) sorts them; < 75 % correct attribution = voice capture failed, redo exemplars.
- `resources/drift-check.md` — mechanical pass (`style stats --baseline`) + LLM pass (style-creator vs exemplar/anti-exemplar fork). Every `drift_interval` chapters or on demand.
- `resources/retune.md` — Adapted from `claude-ghost-writer/skills/retune/SKILL.md` (MIT): author gives raw unguided voice sample; analyze the gap (sentence length, word choice, rhythm, pronoun distance, energy); one alignment pass; no structural changes; update exemplars with the author's own words; **never evaluate the author's raw input for quality**.

### 8.3 `kb/styles/baseline.md` (template in `templates/`; written by style-creator)

```markdown
---
schema-version: 1
sample-chapters: [1,2,3]
---
| metric | author rate (per 1k words) |
|---|---|
| em-dash | 2.1 |
| hedge | 0.8 |
| tier1-hit | 0.0 |
| dialogue-ratio | 0.38 |
| ttr | 0.51 |
| burstiness (sentence-len sd/mean) | 0.62 |
```

### 8.4 Craft additions to `creative-writing-craft` [JUDGE-FIX, from Fablecraft]

A adds (content spec by E) two resources, written fresh (classic craft canon — Swain's scene-and-sequel, Gardner's psychic distance — cited ideas-only, teach-never-write rule):
- `resources/scene-and-sequel.md` — scene (goal/conflict/disaster) + sequel (reaction/dilemma/decision) rubric; named failure patterns (flat scenes = missing disaster or skipped sequel); used by muse to annotate briefs and critics to diagnose flat scenes.
- `resources/psychic-distance.md` — Gardner's five distances; POV-lurch diagnosis; when widening/narrowing distance earns its cost.
SKILL.md resource list gains both. Zero pipeline cost — opt-in craft references.

---

## 9. The drafting context recipe (writer spawn prompt — fixed order, ~3–4k tokens; implemented by muse + `vellum pack`)

1. **Mode + intent** (2–3 lines): production mode (`creative-writing-modes` section), reader effect, emotional target, what stays ambiguous.
2. **State card** — `state/state-card.md` inlined (~1.2k tokens).
3. **Scene brief / beat sheet** — this chapter's outline section: beats + quotas, POV, cast, `verbatim:` lines, what NOT to resolve.
4. **Previous-chapter tail** — last ~500–800 words, never more, never full prior chapters (Re3 principle: re-inject state + plan + summary, not raw prior text).
5. **Character cards** — only `characters:` entries (+ heavy `mentions`).
6. **Voice** — `kb/styles/voice.md` Part 1 summary + Part 2 + one exemplar.
7. **Vocab** — relevant sections.
8. **Craft pointers** (names only): `prose-writing.md`, `scene-construction.md`, scene-and-sequel if flagged flat, mode section of `prose-modes.md`.
9. **Word budget** — target + beat quotas + band.
10. **Continuity anchors** — top ledger lines this chapter touches (from `vellum pack`).

Never included: full KB, full manuscript, critique reports (revision mode carries only the specific findings being addressed), raw JSON, other chapters' prose. `vellum pack` resolves 4/5/7/10 deterministically; muse composes 1–3/6/8/9.

---

## 10. Gates, readiness, export

### 10.1 Gate table (binding)

| Gate | Actor | Blocking? | Blocks what |
|---|---|---|---|
| Outline-before-prose | `guard-outline-before-prose.sh` + `guard-bash-prose-writes.sh` | **BLOCKING** (exit 2) | Prose writes to `manuscript/chapters/` without author-approved outline or with uncommitted prior-chapter transaction |
| Post-write prose net | `check-prose-after-write.sh` | Advisory (blocking only under opt-in `voice_debt_gate`/`stop_gate`) | — |
| Critique isolation | Architecture | Structural | Critics can't write; writer never sees raw critique; muse synthesizes |
| Blind reader | `@blind-reader` | **BLOCKING at acceptance** for author-flagged pivotal chapters | Acceptance requires `work/critique-reports/blind-chapter-NN.md` with verdict ≠ `LOST`; `state check` refuses the acceptance + `vellum readiness` cross-checks every `pivotal: true` chapter has its artifact [JUDGE-FIX: closes the "partial blind gate" flag] |
| Demolition | Muse dialogue, offered before `final` | Advisory | Nothing automatic; deferred/accepted issues surface in `readiness` |
| Disruptor | `@disruptor` [JUDGE-FIX] | Advisory, opt-in | Nothing — proposal-only escalation lane for flat chapters |
| Persona panel | `@critic` × 4 personas | Advisory | Milestone chapters, disputed judgments |
| Cold read | `@cold-reader` batches | Advisory; BLOCKER-class findings block export until resolved or dismissed-with-author-signoff | Export |
| Beta reader | `@beta-reader` | **BLOCKING for export** | `vellum readiness` requires `work/critique-reports/readiness-report.md` `verdict: PASS`. The gate reads the artifact from disk, not muse's word |

### 10.2 Export / readiness (`/vellum:export` → `vellum readiness` → `vellum export build`)

Requires ALL of:
1. Every chapter `status: final`; frontmatter complete (`bible validate` clean or exempted).
2. `ledger check` clean — zero unresolved findings outside `kb/exemptions.json`; cold-read `issues.md` has no open BLOCKER (MAJOR/MODERATE need a triage note: fixed / deferred-with-author-signoff / accepted-limitation).
3. `work/critique-reports/readiness-report.md` exists:

   ```yaml
   ---
   verdict: PASS          # PASS | REVISE
   score: 7.8             # mean of axes
   axes: {voice: 8, structure: 7, depth: 8, specificity: 8, reader: 8}
   put_down_points: []    # chapter numbers; any in ch. 1–3 disqualifies
   read_at: 2026-09-09
   readers: 4
   ---
   ```

   PASS rule (from Velith, adapted): every axis ≥ 7, mean ≥ 7.5, no put-down in chapters 1–3.
4. Word-budget report attached (total vs plan; per-chapter bands).
5. `vellum export build --out export/manuscript-<date>` assembles: title page, copyright placeholder, front/back matter, joined chapters in order, `manifest.md` (chapter list, word counts, sha256 checksums, **gate provenance**: outline approval dates, blind verdicts, beta scores, logged overrides — never silent). `--epub`: stdlib-zipfile EPUB, stable `urn:uuid:<book-uuid>` identifier from `kb/story.md` so highlights survive rebuilds. DOCX/PDF via pandoc when present; otherwise markdown bundle + instructions. The manuscript is untouched — export is a build artifact.

Failure prints a prioritized fix list (beta REVISE format: five changes, each with location, evidence, intervention kind, axis moved).

---

## 11. Workstream F — reader agents and cold read

### 11.1 `agents/blind-reader.md` (F, new; opus)

```yaml
---
name: blind-reader
description: Naive-eyes verdict on a pivotal chapter; knows nothing of the plan.
model: claude-opus-4-6
skills:
- gates
tools:
- Read
disallowed-tools:
- Edit
- Write
- AskUser
- Bash
- Glob
- Grep
---
```

**[JUDGE-FIX: tools are `Read` only — the judged design's `Bash(cat *, rg *)` undermined the isolation promise.]** Body contract: sees ONLY the chapter file (via Read, path given by muse) + previous-chapter tail pasted in the prompt. Must not open outline, kb/, `work/critique-reports`, or style files — it has no tools to do so. Judges as a reader who knows nothing of the plan: where they're confused, where causation breaks, where they'd stop, whether the chapter works standalone. Report: verdict `ENGAGED | STALLED | LOST`, put-down point, confusion list, AI-feel flags; scores the five `gates/resources/quality-bar.md` axes. Never suggests fixes. If muse cannot honestly spawn it without leaking plan context, the chapter isn't ready for a blind read. Output persisted by muse to `work/critique-reports/blind-chapter-NN.md` (muse writes; blind-reader has no Write).

### 11.2 `agents/beta-reader.md` (F, new; opus)

```yaml
---
name: beta-reader
description: Four-reader full-manuscript readiness read before export.
model: claude-opus-4-6
skills:
- gates
- creative-writing-craft
tools:
- Read
- Glob
- Grep
disallowed-tools:
- Edit
- Write
- AskUser
- Bash
---
```

Body: port of `Velith/agents/beta-reader.md` four-reader protocol (A/B target personas, C AI-skeptic, D genre professional) — read that file first and adapt (paths re-scoped to our layout). Reads `kb/story.md` (premise + promise) + genre file from `creative-writing-craft/resources/genre/`, then the full manuscript in order. Must NOT read outlines, style files, or critiques before the first read. Emits: per-chapter engagement table, put-down points, confusion log, AI-feel log (named tells + quotes), promise assessment, five-axis scores per `gates/resources/quality-bar.md`, verdict `PASS|REVISE` with the §10.2 frontmatter. Report returned to muse; muse persists to `work/critique-reports/readiness-report.md`.

### 11.3 `agents/cold-reader.md` (F, new; sonnet)

```yaml
---
name: cold-reader
description: Executes one cold-read batch; assessment only, never edits.
model: claude-sonnet-5
skills:
- cold-read
- gates
tools:
- Read
- Grep
- Glob
- Bash(rg *)
disallowed-tools:
- Edit
- Write
- AskUser
---
```

Body: executes one batch of the `cold-read` skill protocol: reads charter + reader ledger + last ~40 issue lines, continues from `NEXT:`, reads only the batch's chapters. Returns (a) append-ready issue lines in the fixed CR format, (b) ledger section updates (clock rows, promise register deltas, knowledge map deltas, prop custody deltas, do-not-re-explain additions, new `NEXT:` text), (c) batch report (what WORKS, grades, seam assessment, "would a paying reader keep going?"). Rule zero: assessment-only. No peeking: never opens outline or editorial notes during a batch.

### 11.4 `skills/cold-read/` (F, new)

Trigger: "`/vellum:cold-read`, after every major editorial program, before export."
- `resources/charter.md` — Adapted from `fiction-forge/docs/cold-read.md` + `templates/read_charter.md` (MIT): reader persona ("devoted genre reader who just finished the previous book, with a line-editor's ear; experience first, diagnosis second"), rule zero (assessment only), AUTO-FIX vs PROPOSE tiers (reversibility + judgment).
- `resources/reader-ledger.md` — Adapted from `fiction-forge/templates/reader_ledger.md` (MIT): NEXT marker with WATCH list, position/clock table, promise register, knowledge map, prop custody, do-not-re-explain register, PROTECT list. "A stale ledger is an amnesiac reader." PROTECT never excuses mechanical errors (seasons, ages, inventories).
- `resources/issue-format.md` — Adapted from `fiction-forge/docs/cold-read.md`: fixed line `CR-### | ch:line | SEV | CAT | "quote" | reader-moment | fix direction | LINE/SCENE/STRUCT/META`; SEV `BLOCKER|MAJOR|MODERATE|MINOR`; CAT `CONT|CANON|VOICE|CRAFT|STRUCT|PACE|REPEAT|META`.
- `resources/batching.md` — 8–11 chapter batches cut at natural milestones; one batch per sitting; resume recipe (charter + ledger + last 40 issues → continue from NEXT); every issue names its reader-moment; grade what works.

Orchestration lives in the skill, not the agent: muse spawns `@cold-reader` per batch, persists ledger/issues updates itself. For 15+ chapters muse MAY use the digest pattern from `fiction/agents/review-coordinator.md` (MIT) — spawn per-batch readers, aggregate from summaries, cache per-batch reports on disk.

---

## 12. Workstream G — kb-lead, disruptor, demolition, export skill, commands, templates

### 12.1 `agents/kb-lead.md` (G, new; sonnet)

```yaml
---
name: kb-lead
description: Knowledge-capture worker; writes only under kb/ and runs engine checks after updates.
model: claude-sonnet-5
skills:
- story-memory
- story-ledgers
tools:
- Read
- Write
- Edit
- Bash(cat *)
- Bash(rg *)
- Bash(find *)
- Bash(python3 scripts/vellum*)
- Bash(python scripts/vellum*)
- Bash(py -3 scripts/vellum*)
disallowed-tools:
- AskUser
---
```

**[JUDGE-FIX: the vellum Bash patterns are inside the allowlist — the judged design required node calls the allowlist forbade.]** Body contract: writes ONLY under `kb/`; runs `state rebuild` + `bible validate` + `ledger check` after updates; NEVER touches `manuscript/`, `work/drafts/`, or `state/` by hand (engine-regenerated only). Uses `/story-memory` resources (`fact-extraction.md`, `story-reference-writing.md`) plus `/story-ledgers` for promise/knowledge/prop/clock capture. Fails loudly on schema violations; reports promotion decisions (provisional → canon) back to muse for author confirmation before writing settled canon. Also completes chapter frontmatter fields the writer left blank when determinable from ledger/prose evidence, flagging anything uncertain as a finding instead of guessing [JUDGE-FIX].

### 12.2 `agents/disruptor.md` (G, new; opus) [JUDGE-FIX, from Scriptorium]

```yaml
---
name: disruptor
description: Controlled-wildness proposals for flat chapters; proposal-only.
model: claude-opus-4-6
skills:
- creative-writing-craft
- story-planning
tools:
- Read
- Grep
- Glob
disallowed-tools:
- Edit
- Write
- Bash
- AskUser
---
```

Body (design-level port of book-genesis-v4's disruptor, credited ideas-only): given a chapter/outline the author has judged flat, proposes escalation options (raise a cost, invert an expectation, introduce a complication with teeth, collapse a safety) — 3 proposals max, each with where-it-lands, what-it-costs, what-it-forecloses. Never writes. Author picks or dismisses; dismissed proposals are not re-raised (same discipline as exemptions).

### 12.3 `skills/demolition/` (G, new)

Trigger: "author invokes on a chapter draft; muse offers it before `final`." Port of `claude-ghost-writer/skills/demolish/SKILL.md` (MIT) — read that file and adapt. Fiction-tuned 7 vulnerability categories: plot causality; established fact/terms; thematic consequence; internal contradictions; premise boundary cases; unearned motivations/setup; genre-contract violations + comps. Keep verbatim-in-spirit: one criticism at a time; never soften; no solutions during demolition; escalating escape-hatch sequence (Rephrase→Narrow→Find the intuition→Modify/Narrow/Accept); weak-response tests; `--light` mode. Chapter Demolition Log lives in the chapter file (frontmatter-adjacent section) + book-level `work/demolition-history.md` (Recurring Patterns / Open Deferred Issues / Accepted Limitations).

### 12.4 `skills/export/` (G, new)

Trigger: "`/vellum:export`." SKILL.md: run `vellum readiness`; if PASS run `vellum export build`; interpret manifest; pandoc fallback behavior. `resources/assembly.md` (order of parts, chapter joining, scene-break conventions) and `resources/manifest.md` (manifest fields + checksums + gate provenance). Engine implementation is B's (`vellum_lib/export.py`); this skill is the operator's manual.

### 12.5 Commands (G; format per §3.4)

- `write-chapter.md` — body walks muse through the §13 loop verbatim; `$ARGUMENTS` = optional chapter number or "next".
- `status.md` — print state card + gate statuses + open findings summary.
- `cold-read.md` — `$ARGUMENTS` = optional chapter range; set up `work/cold-reads/<YYYY-MM>/` from `templates/cold-read/` if missing; spawn batches.
- `retune.md` — voice retune protocol (`voice/resources/retune.md`).
- `export.md` — §10.2 sequence.
- `dismiss.md` — `$ARGUMENTS` = key + reason; refuses to run unless the author's message contains the reason in their own words; calls `vellum dismiss`.

### 12.6 `templates/` (G)

Files carry the schemas of §7 (chapter, promise, question, knowledge-entry, prop, character), `state-card.md` (7-section skeleton with placeholders), `exemptions.json` (§7.3 example with empty array), `project-config.json` (§3.8), and `cold-read/{charter.md, reader-ledger.md, issues.md, batch-report.md}` adapted from the fiction-forge templates (MIT, credited). `scene-card.md` = the 9-field card from `story-planning/resources/scene-cards.md`. `templates/scene-card.md` is referenced by project-setup.

---

## 13. The chapter loop (what the author actually does)

1. `/vellum:write-chapter` → muse confirms direction in one exchange, spawns `@outliner` (beats + quotas + `verbatim:`), shows outline, author approves → `approved: true`; author (or muse proposal the author approves) sets `pivotal:`.
2. Muse runs `state check`, spawns `@writer` with the §9 pack. Post-write net runs silently (speaks only on tells; debt recorded).
3. Muse spawns routine critics (1–2 lanes normal, 3–5 + blind reader for pivotal), synthesizes, presents: what changed, what works, what concerns, what decision is needed. Author approves → acceptance (pivotal: blind artifact required).
4. `chapter-maintenance.sh` runs the mechanical close-out silently; muse routes `@kb-lead` for fact/ledger capture; state card rebuilds.
5. Muse offers demolition before `final` (author may decline). Interrupt anywhere; next session the SessionStart hook prints the state card. `/vellum:status` any time.

Ceremony only where it earns its keep: outline approval (once), acceptance (once), three gates (hard).

---

## 14. Workstream H — tests and CI

- `tests/test_engine.py` (pytest): engine unit tests against `tests/fixtures/sample-project/` — a fixture project seeded with **one instance of every deterministic error class** [JUDGE-FIX, from Fablecraft]: dead-character reappearance, promise planted after payoff, unfired setup past target, dormant promise, POV-not-in-cast, prop custody drift, knowledge `learned-in` violation, clock non-monotonicity, schema violation, frontmatter-incomplete, hand-edited state (hash mismatch), exemption active vs stale, word-band violation. Each test asserts the **exact expected finding keys** — the fixture project turns the engine test from smoke into specification.
- `tests/test_hooks.py`: hook-contract tests run through Git Bash on both `ubuntu-latest` and `windows-latest` [JUDGE-FIX: Windows runner mandatory]: block/allow matrix for the outline gate; E2BIG regression (pipe a >128 KiB payload through stdin); CRLF files; UTF-8 BOM; paths with spaces; drive-letter cases (`C:/`, `C:\`, lowercase); node/python-absent degradation (engine commands fail-open, bash predicates still gate); outline-copy detector >90 % similarity.
- `.github/workflows/tests.yml` (H): matrix job running pytest on both OSes under bash; feeds into CI status.
- Validation gate: `claude plugins validate vellum` green; lint_vellum.py (§4.7) green.

## 15. Build order (dependency-respecting)

1. **A:** fork + packaging + de-meridian + story-planning fix (can start immediately).
2. **B:** engine package + `templates` schemas frozen (B and G coordinate via §7 schemas only — G writes template files, B validates against them in tests).
3. **C:** hooks + `lib/common.sh` + `prose_core.py` (outline gate first, post-write net, lifecycle).
4. **D:** `story-ledgers`, `kb-integrity`, `gates`.
5. **E:** `style-guardrails`, `voice`, style-creator content, craft additions.
6. **A:** staffing dispatch + muse gate contract + remaining skill edits.
7. **F:** reader agents + `cold-read` + personas.
8. **G:** `demolition`, `export`, commands, kb-lead, disruptor.
9. **H:** tests, fixture project, CI wiring; **A:** ATTRIBUTION/NOTICE final pass.

---

## 16. Judge-flagged weaknesses — fix ledger

| # | Flag (from panel reviews) | Fix in this spec |
|---|---|---|
| 1 | Node dependency weakens the gate story; engine dead without node; kb-lead's CLI calls outside its allowlist | §1: Python-stdlib engine, interpreter resolution chain, bash-fallback gate predicate; §12.1 allowlist fixed |
| 2 | Blind-reader's `Bash(cat/rg)` undermines isolation | §11.1: `Read` only |
| 3 | Writer must dutifully fill frontmatter or state rebuild goes blind | §5.2 `ledger check` `frontmatter:incomplete` finding; §12.1 kb-lead backfill duty; §4.5 writer contract |
| 4 | Thinnest craft layer (no measured voice profile, no scene-and-sequel/psychic-distance) | §8.2 voice-profile.md, §8.4 craft resources |
| 5 | No disruptor | §12.2 |
| 6 | No genre numeric profiles; verdict contracts as vibes | §7.6 genre-profiles.md + verdict contracts in quality-bar.md |
| 7 | "Never hand-edit" never checked; no atomicity | §5.1 hash verification, atomic writes, lockfile |
| 8 | Toxic-debt gate; Scriptorium's Stop gate | §6.2 debt accounting + `<!-- voice:skip -->`; both **opt-in** via `kb/project-config.json` so the three-gate philosophy holds by default (§3.8) |
| 9 | Pandoc dependency at export | §5.2 stdlib EPUB writer; pandoc optional |
| 10 | Knowledge certainty not queryable | §5.2 `knowledge --as-of N`; registered-knowledge anachronism = hard ledger error |
| 11 | CI thinner than portability claims; smoke-level engine tests | §14 fixture project asserting exact findings; windows-latest hook suite |
| 12 | Pivotal flagging muse-judged; blind gate partial | §4.5 author-approved `pivotal:`; §10.1 readiness cross-check |
| 13 | Demolition never runs at the moment it helps | §4.5/§13 muse offers it before `final` |
| 14 | Single-file CLI monolith | §2 `vellum_lib/` package modules |
| 15 | Metric codepath drift | §1 analyze.py superseded header; single `style_stats.py` |
| 16 | SessionStart matcher misses `clear` | §6.1 |
| 17 | Bans can flatten a Tier-1-voiced author | §8.1 measured-profile law + `voice:skip` valve |

## 17. Deliberately NOT built (ceremony control — binding)

No dashboard/localhost server, no SQLite/graph databases, no MCP server dependency, no per-episode voice tables re-enforced automatically, no 16-axis polish, no autonomous pipelines, no per-chapter opus blind reads (pivotal only), no default-on fourth gate. Every mechanism earns its place by (a) blocking something that must not happen, (b) replacing an LLM call with a script, or (c) persisting reader/critic state across sessions. That is the whole plugin.
