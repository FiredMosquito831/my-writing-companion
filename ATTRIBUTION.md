# ATTRIBUTION

**Author:** Vellum is authored and maintained by [FiredMosquito831](https://github.com/FiredMosquito831) (2026). It is a fork of [`haowjy/creative-writing-skills`](https://github.com/haowjy/creative-writing-skills) (the `cw/` distribution); the base author's Apache-2.0 copyright and notice are retained in [LICENSE](LICENSE) and [NOTICE](NOTICE) — authorship of the plugin and copyright of the base are different things, and both are recorded here.

Base commit: `fd7a3ad9cd7697a0645ff6ff4bd5e809cf7673a3` (v0.5.9, 2026-08-08).

## How Vellum improves on its sources

Vellum was built by deep-reading twenty systems in this space and combining the best verified mechanisms of each into one coherent, tested architecture. What follows is what we took from each and what we did better. (The table below is the file-level legal record; this is the design-level story.)

**haowjy/creative-writing-skills (base, Apache-2.0).** *Took:* the muse coordinator, stance-isolated subagents, the five-level edit chain, the story-KB concept, and the craft corpus. *Improved:* fixed its two structural gaps — it had no deterministic enforcement and no hooks (its continuity work was advisory), and it coupled to the author's private Meridian memory tool. Vellum adds a blocking gate layer, a stdlib Python engine, and runs fully on stock Claude Code, with tests and CI — none of which the base had.

**danjdewhurst/story-skills (MIT).** *Took:* the schema-versioned bible, promise/question ledger schemas, and the deterministic continuity check catalog. *Improved:* the base shipped its checker as a standalone CLI you had to remember to run; vellum's hooks invoke the engine automatically on every relevant event, and added checks the base lacked (prop custody, clock monotonicity, timeline-scoped `knowledge --as-of` queries with dramatic-irony views).

**zenstory-ai/oh-story-claudecode (MIT).** *Took:* blocking guard hooks and the transactional state-card design. *Improved:* de-coupled from the Chinese web-novel ecosystem (hanzi-specific matching, serialization economics), made the gates fail-open on a missing runtime so they can never mis-block an author, added gate-input protection (subagents cannot forge approvals), and carried it to Windows/Git Bash with regression tests — the source had none.

**conorbronsdon/avoid-ai-writing + hardikpandya/stop-slop (MIT).** *Took:* detector categories and replacement tables. *Improved:* both tune for blog/nonfiction voice; vellum filters them through fiction carve-outs and, crucially, subordinates the bans to the author's *measured* voice baseline — style rules cap at baseline×1.25 rather than flattening voice to a generic "clean" register.

**NousResearch/autonovel (no license — ideas only).** *Took:* the tier taxonomy, structural-cap concept, and tuning-fork voice scaffold. *Improved:* re-derived all word lists independently, and wired the idea into a mechanical post-write hook with numeric thresholds instead of leaving it as prose guidance in a document.

**simonediroma/claude-ghost-writer (MIT).** *Took:* the demolition critique protocol and voice retune. *Improved:* demolition became chapter-scoped, logged, and explicitly declinable (declining is recorded, not punished); retune became part of a full measured-voice lifecycle with drift checks and a blind-tag falsification test the source never had.

**epicsagas/Velith (Apache-2.0).** *Took:* the four-reader beta protocol, quality bar, and export-readiness gate. *Improved:* the readiness thresholds are enforced by the engine (`vellum readiness`), not by prompt compliance; the export manifest records gate provenance (sha256, which gates passed, logged overrides), making the gate auditable after the fact.

**geobond13/fiction-forge (MIT).** *Took:* the cold-read protocol and the markdown ledger set. *Improved:* adapted the single-agent protocol to subagent orchestration with batching and a rolling reader ledger, and unified its issue log with the shared finding/exemption schema so cold-read findings can be dismissed with the same first-class exemption mechanism as everything else.

**howells/fiction (MIT).** *Took:* the persona critics (Wood, King, Le Guin, Gay). *Improved:* the source's critics were orphaned from its pipeline (manual summons only); vellum routes them inside the automated review flow, each bound to the shared quality rubric so their verdicts cite criteria instead of inventing them.

**rhavekost/author-toolkit (MIT).** *Took:* the Weiland/Bell beat map and the finding schema. *Improved:* beats became auditable structure maps wired into planning and audit modes rather than reference reading, and the finding schema was extended with exemption keying and signal classes.

**mrigankad/Novel-OS (MIT).** *Took:* dismissed-findings keying, the check catalog, and the reactive-protagonist stall detector. *Improved:* re-implemented in stdlib Python, made exemptions re-arm exactly once when the underlying fact changes (entity-hash staleness), and merged the catalog with story-skills' into one engine.

**felipelobomotta-blip/book-genesis-v4 (ideas only).** *Took:* the blind-reader gate concept. *Improved:* implemented as a strictly read-only agent (Read tool, nothing else) inside the plugin, cross-checked by the engine, with self-recorded run-stamp provenance — instead of a separate Python CLI standing outside Claude Code.

**Claude-Book, Claude-Code-Novel-Writer, GOAT, Re3, LongWriter (ideas only).** *Took:* the immutable-bible/versioned-state split, the hooks-suite pattern, scene cards, word budgets, and the recursive-reprompting context recipe. *Improved:* these were scattered across architectures that cannot run together; vellum merged them into one pipeline where the state card *is* the reprompting skeleton and scene cards carry the budgets.

**Craft theory sources (ideas only — Shawn Coyne's obligatory moments, Sanderson/Butcher/Writing Excuses try-fail ladders, Gaiman/Craig/MorningStar beta doctrine, BubbleCow/Windrow revision-letter practice, Michel/Yang/Brei stylometry).** All prose re-written as original checkable resources; the mechanisms credit the theory, the text is ours. Each is named in the table below with the file that implements it.

The per-file legal record follows.

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
