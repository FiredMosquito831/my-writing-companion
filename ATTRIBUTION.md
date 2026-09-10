# ATTRIBUTION

Vellum is a fork of [`haowjy/creative-writing-skills`](https://github.com/haowjy/creative-writing-skills) (the `cw/` distribution), made 2026-09-09. Base commit: `fd7a3ad9cd7697a0645ff6ff4bd5e809cf7673a3` (v0.5.9, 2026-08-08).

<!-- This table is the CI lint source of truth: lint_vellum.py (spec section 4.7) greps for missing attribution headers against it. Every file whose content derives from another repo MUST carry the §3.5 header; unported original files carry none. Rows verified against the actual ported files. -->

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
| `fiction/agents/{james-wood,stephen-king,ursula-le-guin,roxane-gay}.md`, `agents/review-coordinator.md` | MIT (per source README "License: MIT"; the repo publishes no LICENSE file — evidence note, not a waiver) | Persona critics, digest/fan-out coordinator | Trimmed/rewritten, MIT notice. Decision recorded: the persona files' verbatim author voice quotes are retained as short attributed critical quotations (fair-quotation use); the repo's MIT claim does not cover the underlying quotations — see NOTICE for the caveat and the paraphrase guidance. |
| `author-toolkit/skills/story-structure/references/{landmark-beats,signposts,structure-map}.md`, `references/finding-schema.json` | MIT | Weiland/Bell beats, finding schema | Adapted, MIT notice |
| `Novel-OS/core/continuity_engine.py` (Finding.key exemption design, dormant-thread/sagging-middle checks) | MIT | Dismissed-findings keying, check catalog, stall detector | Re-implemented in Python, MIT notice |
| book-genesis-v4 blind-judge/disruptor/audit-gate | various | Blind-read gate, disruptor lane (design-level) | Ideas only where unlicensed; credited in ATTRIBUTION |
| Claude-Book, Claude-Code-Novel-Writer, GOAT scene cards, Re3/LongWriter, Fablecraft/Scriptorium review mechanisms | various | Architectural ideas (immutable-bible split, hooks suite, word budgets, context recipe, measured voice profile, stdlib runtime policy) | Design-level inspiration, credited; no code/text copied from unlicensed repos |
| Shawn Coyne, *The Story Grid* (obligatory scenes & conventions concept) | Book — all rights reserved | Obligatory moments + conventions checklists in `skills/gates/resources/genre-profiles.md` | Ideas only; rewritten as original checkable questions; no source text copied |
| Brandon Sanderson (BYU creative-writing lectures); Jim Butcher (convention-notes essays); Writing Excuses eps. 10.29 / 21.14 | various | Try-fail / failure-ladder mechanism in `skills/story-planning/resources/try-fail.md` | Ideas only; all prose original; no source text copied |
| Neil Gaiman (reader-feedback maxim, via public citation); Spann Craig (beta-management practice); MorningStar Editing (feedback-triage guidance) | various | Beta-report merge protocol in `skills/story-review/resources/beta-synthesis.md` | Ideas only; all prose original; no source text copied |
| BubbleCow (Gary Smailes); Windrow (editorial-letter reception doctrine) | various | Cross-source revision-plan mechanism in `skills/story-review/resources/revision-plan.md` | Ideas only; all prose original; no source text copied |
| Michel et al. 2024; Yang et al. 2024; Brei et al. ACL 2026 (quotation-attribution / speaker-identity stylometry research) | various | Per-character dialogue blind-attribution test in `skills/voice/resources/character-dialogue-profiles.md` | Ideas only; all prose original; no source text copied |

## Header conventions

Attribution header format (CI-checked, spec section 3.5):

- `.md`: first line after frontmatter: `<!-- Adapted from OWNER/REPO (path/in/repo) — LICENSE. Changes: one-line summary. -->`
- `.py` / `.sh`: line(s) 2+ directly under the shebang: `# Adapted from OWNER/REPO (path) — MIT` + `# Changes: one-line summary`
- Ideas-only sources (unlicensed): `Mechanism credited to OWNER/REPO; no source text or code copied.`
- Unported (original) files: no header. Every file whose content derives from another repo MUST carry the header; CI greps for missing ones against the table above.
