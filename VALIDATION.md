# VALIDATION

The design lineage, validation record, and test results for Vellum. Design and validation record for v0.1.0 (2026-09-09); the paper-run findings were fixed and released as v0.1.1 (2026-09-10, see §4–§6); the optional library/series layer shipped as v0.2.0 (2026-09-10, see §5 changelog and [`library-spec.md`](../library-spec.md)).

## 1. Design lineage: base + grafts

**Base:** a fork of [`haowjy/creative-writing-skills`](https://github.com/haowjy/creative-writing-skills) (Apache-2.0), the `cw/` plugin distribution — v0.5.9, base commit `fd7a3ad9cd7697a0645ff6ff4bd5e809cf7673a3`. It was selected from 20 candidate story-writing repos as the only one pairing a CI-validated marketplace plugin with deep multi-agent stance separation and the deepest craft layer; its faults (no hooks, no deterministic engine, no ledgers, no gates, no export) are additive gaps, not structural rot. The full selection analysis and verified fault list are in the project's `base-analysis.md`.

**Grafts:** 16 graft requirements (GR-01…GR-16) were planned from the other 19 repos, then unified into the binding build spec ([DESIGN.md](DESIGN.md)) by a chief-architect pass over competing design proposals. The graft sources:

| Graft | Source | What came across |
|---|---|---|
| Deterministic continuity engine + schema-versioned bible + fact-keyed exemptions | story-skills, Novel-OS (both MIT) | Bible schema, promise/question ledgers, word rule, `Finding.key` exemption design, dormant-thread/stall checks |
| Blocking guard hooks + lifecycle suite | oh-story-claudecode (MIT), Claude-Code-Novel-Writer, The-Crucible, write_ai_agent | Outline-before-prose + Bash guard, post-write net, E2BIG/drive-letter/fail-open lessons, SessionStart/PreCompact/Stop/SubagentStop hooks |
| Anti-slop style guardrails + detector | autonovel (ideas-only), avoid-ai-writing, stop-slop (MIT) | Tier taxonomy (re-derived data), detector categories, fiction-carveouts filter |
| Blind judge + disruptor + audit gate | book-genesis-v4 (design-level), Scriptorium (ideas) | Blind-read gate, disruptor lane, hash-verified state, opt-in debt/stop gates |
| Beta-reader readiness gate + quality bar | Velith (Apache-2.0) | Four-reader protocol, verdict schema, PASS rule |
| Ground-truth precedence | Claude-Code-Novel-Writer | user > prose > outline > state > derived metrics |
| Persona critics + fan-out | howells/fiction (MIT) | Persona panel, review-coordinator digest pattern |
| Demolition + retune | claude-ghost-writer (MIT) | 7-category demolition protocol, voice retune loop |
| Cold-read protocol | fiction-forge (MIT) | Charter, rolling reader ledger, issue format, prop custody, clock rows |
| Voice drift + word contract + knowledge-as-of | The-Crucible, oh-story, fiction-forge, Claude-Book | Retune loop, word quotas/bands, timeline-scoped knowledge, measured voice profile |
| Structure beats + finding schema + context packs | author-toolkit, Novel-OS (MIT) | Weiland/Bell beats, shared finding schema, stall detection |

Full per-file provenance with licenses and changes: [ATTRIBUTION.md](ATTRIBUTION.md). The spec also carries a 17-item judge-fix ledger (DESIGN.md §16) recording weaknesses found in design review and their fixes — e.g. Node→stdlib-Python engine, blind-reader reduced to `Read`-only, hash-verified atomic state, author-approved `pivotal:` flag, stdlib EPUB export.

## 2. Validation rounds

After the eight build workstreams completed, the plugin went through three adversarial validate→fix rounds with independent multi-lens validators (craft and slop, platform hooks and manifests, Windows portability, license/security hygiene), then a mechanical lint and an end-to-end paper-run. **92 findings were logged and all 92 were fixed and verified:**

| Round | Findings | Severity breakdown | Character of the round | Fix verification |
|---|---|---|---|---|
| 1 | 37 | 6 critical, 13 major, 18 minor | The critical tier built the missing deterministic engine (12 `vellum_lib` modules), the agent-side engine path (`project-setup` step 9 copies `scripts/` into the author project), and the whole test/CI workstream (64 tests, fixture project seeded with one instance of every deterministic error class). Majors/minors hardened hooks (compound-command bypass, gate-input protection, `fm_field` inline-comment trap) and packaging (attribution headers, NOTICE/LICENSE completion). | All fixed; suite green |
| 2 | 30 | 7 major, 23 minor | Gate integrity: blind-artifact YAML contract, transcript provenance for gate reports (closes the muse-authored-report path), pivotal-acceptance precondition in `state check`, `state check [target]` scoping (fixes over-blocking of in-progress edits), outline flag-scoped gate-input protection, Bash write-indicator scan (`sed -i`, `perl -i`, interpreter-embedded writes), tier-1 table sync check in CI. | All fixed; 78/78 tests |
| 3 | 25 | 1 major, 24 minor | Conformance and polish: state-card overflow freeze instead of crash, a latent stale-exemption path-prefix bug found and fixed, gate-input fail-closed on unverifiable session context, mechanism-agnostic outline-copy detector, front/back-matter export, deep frontmatter CI lint (name/model/skill-dir checks), tool-name normalization across all 16 agents. | All fixed; 79/79 tests |

Each round was a batch of independent validators with distinct lenses (craft/slop, platform hooks and manifests, Windows portability + license/security hygiene), each reporting only real, actionable findings that fed the next fix round. After round 3, the remaining validation passes were the mechanical lint and the end-to-end paper-run (§3); neither found any new engine or gate defect — the paper-run's findings (§4) are all LLM-side glue or UX issues.

## 3. Test results

**pytest suite** — `tests/test_engine.py` + `tests/test_hooks.py` against a fixture project seeded with one instance of every deterministic error class (dead-character reappearance, promise ordering, POV-not-in-cast, custody drift, knowledge violation, clock non-monotonicity, hand-edited state, exemption active/stale, word band, …). Each engine test asserts exact finding keys.

- Final state on the development machine (Windows 10, Git Bash, Python 3.14): **79 passed, 0 failed** (2026-09-09).
- CI: `.github/workflows/tests.yml` runs the same suite on `ubuntu-latest` and `windows-latest` (two-OS matrix, mandatory per the judge-fix ledger).

**Plugin lint** — `scripts/ci/lint_vellum.py` (Meridian-vocab leak grep, attribution-header completeness vs ATTRIBUTION.md, hooks.json parse, 100 KB size cap, deep frontmatter checks, tier-1 table sync): **clean, exit 0**.

**Machine lint (independent agent)** — a 53-check mechanical lint pass: all 5 JSON files parse; plugin.json complete; all 16 agent frontmatters parse with unique names and valid tools; all 32 SKILL.md files carry name + description; all hook-script references resolve (7 scripts across 6 event groups). 37/53 PASS; the 16 "FAIL" rows were solely the linter's model-alias criterion (`sonnet`/`opus` aliases) against the plugin's deliberate full model IDs (`claude-opus-4-6`, `claude-sonnet-5`) — syntactically valid identifiers that the plugin's own CI lint accepts by design; no content defect.

**Paper-run smoke test (end-to-end)** — a sandbox project was seeded exactly as `project-setup` documents, then the full new-novel flow was executed with the real hook scripts (fed the JSON payloads Claude Code sends) and the real engine: outline → gate-block-without-outline → gate-pass-with-approved-outline → drafting → acceptance → capture → export (bundle + EPUB + manifest). Verified working, executed not just read:

- Gate 1 blocks exactly as documented on both the Write and Bash paths (missing outline, unapproved outline, heredoc/redirect laundering; Windows drive-letter paths normalize); after approval + `state rebuild` it passes; subagent-context writes to `work/critique-reports/` and self-approval in `work/outline/` are blocked; ambiguous context fails closed.
- Gate 2: `state check` refuses acceptance of a pivotal chapter without a verdict-carrying blind artifact (and rejects `LOST`); `readiness` cross-checks pivotal coverage and transcript provenance.
- Acceptance transaction fires the mechanical close-out; `pending_capture` blocks the next chapter start until `final`.
- Gate 3 + export: correct prioritized fix lists at each stage, then PASS; bundle + EPUB + manifest with per-chapter gate provenance and stable `urn:uuid`.
- Post-write net, voice debt, `style stats --baseline` drift (measured-profile law honored), ledger check, dismiss/re-arm, `knowledge --as-of --audience`, `pack`, `bible validate`, session-start/pre-compact lifecycle: all exercised and working.

## 4. Paper-run findings — all resolved in v0.1.1

Ranked as the paper-run reported them; all were LLM-side glue or UX issues, not engine/gate defects. Each is now resolved; the fix is recorded under the finding. The three-gates-from-disk doctrine is unchanged — gate verdicts are still read from artifacts on disk, never from the muse's word.

1. **RESOLVED (was HIGH): transcript-provenance requirement may be unsatisfiable by the muse.** Redesigned to a workable two-form provenance binding (gates skill §"Gate-artifact provenance", `agents/muse.md`, `agents/beta-reader.md`, `agents/blind-reader.md`, `vellum_lib/export.py`). The reader agent now **self-records a run stamp** in its returned report frontmatter at run time (`run_stamp: <agent> <verdict> <ISO date>`), which the muse transcribes verbatim like the verdict itself — inventing it is the same fabrication as inventing the verdict, and unlike a SubagentStop payload it reliably reaches the conversation that persists the artifact. The stronger `transcript:` binding is kept and verified as before; the muse records the transcript path when it knows it, with a **documented search fallback** (newest `*.jsonl` session transcripts under `~/.claude/projects/<project-slug>/`, `grep -l` for the verdict line). `vellum readiness` and `state check` accept either form and reject a stamp that names the wrong agent, disagrees with the report's verdict, or is malformed. Covered by `test_readiness_accepts_self_recorded_run_stamp` and `test_state_check_blind_artifact_accepts_run_stamp`; the previous transcript-path tests pass unchanged.
2. **RESOLVED (was MEDIUM): pivotal chapters in single-agent (no-subagent) mode are unbuildable.** The fallback decision is now documented where the gate is enforced: muse (`agents/muse.md`, "Single-agent (no-subagent) mode and the blind gate"), gates skill (`skills/gates/SKILL.md` gate 2), command (`commands/write-chapter.md` step 6), and DESIGN §10.1. The author explicitly chooses: **(a) drop the `pivotal: true` flag**, or **(b) soft-fail** — the main loop performs a naive-eyes pass in a fresh stance-turn, records the artifact with `run_stamp: blind-reader (single-agent fallback) <verdict> <date>`, and presents an explicit warning that the verdict is weaker than a true blind read before acceptance on a verdict ≠ `LOST`. Skipping the gate silently is forbidden in all three documents; the engine check (artifact with verdict ≠ `LOST` on disk) is unchanged.
3. **RESOLVED (was LOW-MEDIUM): first `/vellum:write-chapter` trips the chapter-transaction block.** `skills/project-setup/SKILL.md` gained a final step 15: **run the initial `state rebuild`** (interpreter resolved `python3` → `python` → `py -3`, ≥ 3.8; verify the state files exist; a plain warning when no interpreter resolves). The garbled block wording is fixed at both sources: `hooks/scripts/lib/common.sh` ("…complete the chapter close-out with your Python interpreter (…), or run /vellum:write-chapter, and retry.") and `hooks/scripts/session-stop.sh` ("…or run /vellum:write-chapter, which walks the close-out with you.").
4. **RESOLVED (was LOW): setup entry point is skill-only.** Added `commands/init.md`: `/vellum:init` routes to the `project-setup` skill, with a description keyed to setup intent ("Set up a creative-writing project… run the project-setup skill"), and passes `$ARGUMENTS` (genre, title, existing material) into the interview.
5. **RESOLVED (was LOW): `style stats --baseline` argument order is order-sensitive.** `scripts/vellum_lib/cli.py` now accepts `--baseline` on both the `style` group and the `stats` action (distinct dests, merged in the handler), so both the documented `style stats <file> --baseline` and the hoisted `style --baseline stats <file>` parse. Covered by `test_style_stats_baseline_accepts_both_argument_orders`.
6. **RESOLVED (was LOW): minor engine quirks.** (a) `prose_core.py write_voice_debt` now **dedupes `work/voice-debt.json` by id on every write** (first occurrence kept), so rescans can no longer accumulate duplicate ids. (b) `prose_core.py extract-target` **fails open**: malformed/non-object JSON or a missing path field exits 0 with a one-line advisory on stderr instead of exit 1, per the fail-open doctrine (callers already fell back to bash extraction). (c) `agents/outliner.md` names the output path explicitly: `work/outline/chapter-NN.md` (zero-padded), the exact path the gate and pack read.
7. **RESOLVED (was LOW): model IDs in agent frontmatter are stale aliases.** All 16 agents now use the current model aliases — `opus` (heavy judgment tier) and `sonnet` (structure/depth tier) — instead of pinned full IDs (`claude-opus-4-6`, `claude-sonnet-5`) that could fail to resolve at install; the aliases also satisfy external validators' model-alias criterion by design. `scripts/ci/lint_vellum.py` `ALLOWED_MODELS` updated to `{"opus", "sonnet", "haiku", "inherit"}`; DESIGN §3.2 records the tiering rule with the shipped alias note.
8. **RESOLVED (was LOW-MEDIUM): "Handle via the muse agent" is ambiguous.** Every command body now states explicitly: **the main loop ADOPTS the muse role** (loads the muse instructions, `creative-writing-muse`) — never "spawn the muse," because a subagent cannot spawn subagents and commands run in the main loop. Applied to all seven commands (`init`, `status`, `write-chapter`, `cold-read`, `retune`, `export`, `dismiss`); no agent or command anywhere instructs a subagent to spawn subagents. DESIGN §3.4's command-format convention was updated to match.

Also fixed in the same pass (fresh audit discrepancies): DESIGN §6.2's `chapter-maintenance.sh` row was stale against the shipped implementation — reworded to the actual semantics (the mechanical close-out fires at acceptance from `check-prose-after-write.sh`; `chapter-maintenance.sh` is an advisory writer-stop pre-pass; `state rebuild` derives `pending_capture` from chapter status, no hook clears it); DESIGN §13 step 4 aligned; and DESIGN §4.2 now records the shipped marketplace name (`my-writing-companion`, so installs resolve as `vellum@my-writing-companion`) instead of the spec-literal `vellum` — the plugin name, which drives `/vellum:` prefixes, was already correct.

## 5. Changelog

### v0.2.0 (2026-09-10) — the library / series layer

Implemented per [`library-spec.md`](../library-spec.md) (final spec, post-judge absorption: Design B's skeleton + A's transaction discipline + C's freeze doctrine; all 47 judge-flagged weaknesses addressed in the spec's §16 ledger). The layer is **optional**: a v0.1.1 single-book project keeps working byte-identically whether or not the library is installed and whether or not a book is linked — compatibility is enforced by tests (below), not promised.

**Engine (scripts/)**

- New `scripts/library.py` — engine entry point for all `library` subcommands (`init`, `link`, `unlink`, `validate`, `bootstrap`, `retcon-check`, `retcon-plan`, `retcon --apply`, `state`, `timeline`, `handoff`, `dismiss`), dispatched by `vellum_lib/series_cli.py`. Every subcommand takes `--root <library-root>` (no walk-up discovery); fixed exit codes 0 clean / 1 findings-or-plan / 2 usage-schema error; findings are informational — the layer adds **no fourth gate**.
- New `scripts/vellum_lib/series_bible.py` — bible load/validate, per-field `by-book` resolution (§11 effective-at-ordinal, no log walk), timeline index. A separate series dialect; the v0.1.1 `vellum_lib/bible.py` REQUIRED/ENUMS registry is untouched.
- New `scripts/vellum_lib/series_checks.py` — the §10 detection catalog (deceased-as-of-start, open-thread carry, world-fact knowledge anachronism, canon divergence with iron-fact elevation, unqualified-ref, orphan-book-ref, id-mismatch, half-linked, retcon-log-orphan, established-ref-missing), deterministic checks counted separately from judgment-flagged rows.
- Machine state is all JSON (`library.json`, `series/bible.json`, `series/exemptions.json`, append-only `series/retcons.jsonl`); writes serialize through `library-root/.lock` (30 s contention timeout → exit 2); `library init` refuses inside a book project; `link` is sidecar-first and idempotent-completing (half-state recoverable by `library validate`).

**Skill, command, template**

- New skill `vellum:series` (`skills/series/SKILL.md` + `references/checks.md`): the library-layer workflow and operator's manual — retcon lifecycle (plan → author approval with verbatim words → per-row apply), the detection catalog in agent-facing copy, the do-not-re-explain register, handoff generation. No gate logic.
- New skill `vellum:series-bible` (`skills/series-bible/SKILL.md`): the bible schema and data-dialect reference for kb-lead (field encodings, coordinate conventions, effective-at-N).
- New command `/vellum:series` (`commands/series.md`): routes to the skill and documents the twelve `library` subcommands with their contracts.
- New template `templates/retcon-plan.md`: the plan report format whose `approved: true` frontmatter plus non-empty verbatim `author_words` per row are what `library retcon --apply` requires.
- Cross-references: `kb-integrity` notes the series companions for linked books; `story-ledgers` documents the opt-in `series-id:` entity-frontmatter join key. Book-local command contracts unchanged.

**Hooks**

- `hooks/scripts/session-start.sh` (fail-open): for a linked book, appends a one-line series state summary via an engine one-liner (`library.py state --card-line`), stderr discarded; on any error (missing root, engine-copy lag, crash) the line is silently omitted and session start is never blocked. Unlinked books: byte-identical v0.1.1 behavior.

**Compatibility contract (tests)**

- Byte-identity golden suite (library-spec §17 T1–T3): the full v0.1.1 command surface (`vellum state` card with its generated timestamp normalized and the injected series section isolated per T3, `ledger check`, `bible validate`, `wordcount`, `knowledge --as-of`, cold-read hooks) asserts identical stdout + file hashes on the fixtures before link, after link, after bootstrap `--apply` (only `series-id:` lines added), and after a retcon `--apply`; an inert-to-old-engine test (T2) deletes the new modules and re-runs the v0.1.1 verbs unchanged. Plus T4–T12: link/unlink lifecycle, bootstrap match tiers (prose names never match), retcon transactions (per-row all-or-nothing, `series:retcon-log-orphan` recovery), the detection catalog (positive + negative fixtures), freeze doctrine (`published` = retcon-record-required default, `archived` = fully quiet), exemption entity-hash staleness, version tolerance (unknown sidecar schema → exit 2; engine-copy lag advisory), `.lock` concurrency, and the per-command exit-code table.

**Docs, packaging**

- README: new Library & series layer section, v0.2.0 highlights row and status; DESIGN.md: new §18 (library/series semantics) plus file-tree, engine-contract, and command-list updates; this changelog.
- Version 0.2.0 in `.claude-plugin/plugin.json` and `marketplace.json` (metadata + plugin entry).
- `scripts/ci/lint_vellum.py` clean after the release.

**Validation record.** The v0.2.0 build went through the same adversarial pattern as the v0.1.0 build: independent validators, then a fix round, then independent scenario verification. **86 validation findings were logged and all 86 were fixed** across three multi-lens validator rounds over the new engine modules, skill/command/template layer, and hooks (round-by-round fix verification: suite grew 117 → 132 → 146 → 147 passing through the fix cycles; each fix round re-ran the full suite plus lint). Test-phase results, all executed (not read):

1. **Full lifecycle scenario (two-book sandbox).** `library init` refused inside a book (exit 2), link of a `published` and a `draft` book, bootstrap `--plan`/`--apply` on both books (ambiguity rows written nothing until resolved; unapproved `--apply` refused), deliberate retcons fired `series:deceased-as-of-start` and `series:canon-divergence` with `series_scope: true` and exit 1 — no blocker, no fourth gate. Freeze doctrine verified live: a plan touching book 1's frozen value was refused; an approved retcon flushed only the targeted exemption, which re-fired once when the underlying fact changed; a hash-stale dismissal re-fired after a direct kb edit. Final `validate`, `state`, `timeline`, `handoff` all clean. Sandbox: `ultra-writing-plugin/sandbox-v02` (library `aethelgard-library`, books `book1`/`book2`).
2. **Migration test (v0.1.1 book → new library).** A fresh v0.1.1-shaped project was linked to a new series library: no data loss (`kb/story.md` sha256 byte-identical pre/post; joined entities differ only by the added `series-id:` line, proven by hash comparison), `state rebuild`/`state check` green post-migration, the full v0.1.1 command surface byte-identical pre/post link, and the lifecycle probes (half-link recovery, unlink/re-link, retcon-check advisory-only, fail-open hook) all passed. Sandbox: `ultra-writing-plugin/sandbox-migration`.
3. **v0.1.1 regression run (no-regression verdict).** The v0.2.0 working tree versus v0.1.1 (git `d62fc14`) on an identically seeded series-free single-book project: full engine surface and all hooks identical in stdout/stderr/exit codes (only the rebuild timestamp normalized), finding-key sets byte-identical (zero `series:*` keys), engine-written files identical, zero series files created. Sole delta: the intentional `vellum engine 0.2.0` version string.
4. **Windows path torture test.** Spaces, drive letters (incl. cross-drive links), 16-level nesting at 262-char paths, CRLF, detached-revival, and error paths all passed. Found and fixed, each with a regression test in `tests/test_series_followup.py` and re-verified end-to-end: **F1** a BOM'd kb entity silently half-joined (frontmatter invisible, no `series-id` written, `validate` clean) — BOM tolerated on read, injection now fails loud with a preflight that refuses the whole `--apply`; **F2** piped stdout was cp1252 on Windows — engine streams now force UTF-8 at import; **F3** BOM in engine-owned JSON bricked every library command — reads now use `utf-8-sig`; an unreadable sidecar is reported as its own finding, not misdiagnosed as stale; **F4** the yaml-lite flow-map parser split inside quoted values and never unquoted keys, blocking `--apply` on comma-bearing resolution notes — parser is now quote-aware; plus **S1** spec §15 migration examples omitting the mandatory `--root` — spec amended. Torture workspaces were cleaned up after verification.

**Final state at release:** **155 passed** (120 engine/hook + 35 series follow-up), `scripts/ci/lint_vellum.py` clean, `vellum --version` reports `vellum engine 0.2.0`.

### v0.1.1 (2026-09-10)

**Gate integrity**
- Redesigned gate-artifact provenance: the reader agent self-records a `run_stamp:` in its report frontmatter at run time (muse transcribes verbatim); the verified `transcript:` binding is kept as the strongest form, with a documented transcript-search fallback for the muse. The engine accepts either and validates stamp shape, agent, and verdict agreement (`vellum_lib/export.py`).
- Documented the single-agent (no-subagent) fallback for the blind gate in the muse, gates skill, write-chapter command, and DESIGN §10.1: the author chooses to drop the pivotal flag or accept a warned soft-fail.

**Engine (scripts/vellum_lib)**
- `style stats --baseline` now parses in both argument orders (`style --baseline stats <file>` accepted).
- Engine version bumped to 0.1.1.

**Hooks**
- `prose_core.py`: `extract-target` fails open (exit 0 + advisory) on malformed or fieldless JSON; `write_voice_debt` dedupes `work/voice-debt.json` by id.
- Chapter-transaction block messages de-garbled in `lib/common.sh` and `session-stop.sh`.

**Packaging, agents, commands**
- Agent frontmatter model IDs moved to current aliases (`opus` / `sonnet`); lint `ALLOWED_MODELS` updated.
- New `/vellum:init` command routing to `project-setup`; `project-setup` gained a final **initial `state rebuild`** step with interpreter resolution.
- All commands now state that the main loop adopts the muse role (never spawn a muse subagent).
- Version 0.1.1 in `.claude-plugin/plugin.json` and `marketplace.json` (metadata + plugin entry); README status updated.

**Docs**
- DESIGN.md: §3.2 model-tier aliases; §3.4 command-format convention; §4.2 shipped marketplace name record; §6.2/§13 chapter-transaction semantics corrected (acceptance close-out in `check-prose-after-write.sh`; `chapter-maintenance.sh` advisory pre-pass; `pending_capture` derived, never cleared); §10.1/§10.2/§11 provenance and fallback semantics; §12.5 `init.md`.

**Tests:** 79 → 98 passing (new: both `--baseline` orders; run-stamp provenance for the readiness report and the blind artifact, including the single-agent fallback stamp; ADD-5 dialogue-stats and ADD-6 morphology engine tests; `revision status` tests). `scripts/ci/lint_vellum.py` clean.

## 6. Craft additions pass (2026-09-10) — audit results and shipped additions

**How the pass ran.** After the v0.1.1 fix round, a research round (four fresh reports: story-structure theory, professional revision doctrine, serial-engagement research, LLM creative-writing failure modes) produced candidate additions, selected against the design constraints — the three hard gates stay exactly three; everything new is advisory or report-only mechanical; stdlib-only engine; no new mandatory artifacts. Six additions were accepted (ADD-1…ADD-6, each dedupe-checked against the existing skill layer) and built in this pass; the rejected candidates and reasons are recorded in the project's `additions-spec.md`.

**Audit results.** A closing audit of the extension round — spec-vs-shipped conformance, cross-link integrity, and engine edge cases across the modified files — logged **14 findings; all 14 were fixed** before release. The fixes spanned doc/spec drift, missing cross-references between skills and agents, engine edge cases in the new metrics (attribution heuristics, ambiguity handling), and attribution-header coverage for the new idea-sourced files. Re-verified: full suite green, lint clean.

**Additions shipped (all advisory or report-only; no gate added):**

1. **ADD-1 — Obligatory scenes & conventions checklist per genre** (mechanism credited to Shawn Coyne, *The Story Grid* — ideas only, rewritten as checkable questions): `skills/gates/resources/genre-profiles.md` gains a per-genre section (fantasy/thriller/mystery/romance/horror/litfic) of obligatory moments that must be on the page plus conventions; `@outliner` checks arc outlines deliver them, `@beta-reader` verifies they are dramatized before PASS.
2. **ADD-2 — Try-fail cycles with escalating costs** (Sanderson BYU lectures / Butcher convention notes / Writing Excuses 10.29 & 21.14 — ideas only): new `skills/story-planning/resources/try-fail.md`, the arc-level failure ladder (2–3 attempts before the goal succeeds, each costing more than the last; barrier vs attempt; anti-checklist warning). Wired into `story-planning/SKILL.md`, `structural-problems.md` (saggy-middle prescription), `@outliner` (arc outlines must show the ladder), and a critic diagnostic.
3. **ADD-3 — Revision-plan artifact** (editorial-letter reception doctrine — BubbleCow/Windrow, ideas only): new `skills/story-review/resources/revision-plan.md` defining `work/revision-plan.md` — the append-only, triaged, status-tracked synthesis of all findings from every source (critiques, cold-read CR-###, demolition, beta, sims), with per-round definition of done and declined rows carrying the author's verbatim reason. New engine subcommand `vellum revision status` cross-checks resolved rows against source artifacts (report-only). Muse merge duty wired into `agents/muse.md` and `story-review/SKILL.md`.
4. **ADD-4 — Beta-feedback synthesis protocol for conflicting readers** (Gaiman maxim / Spann Craig / MorningStar Editing — ideas only): new `skills/story-review/resources/beta-synthesis.md` — strip reader identities, cluster by passage, classify each note `preference | craft | friction` before weighing, the frequency rule (singleton preference declined-by-default; 3-of-n confirms a pattern), symptom-to-candidate-cause translation. Shared finding schema gained the optional backward-compatible `signal-class` field; muse merge-step wired in.
5. **ADD-5 — Per-character dialogue fingerprint + speaker-attribution test** (grounded in quotation-attribution/speaker-identity stylometry: Michel et al. 2024, Yang et al. 2024, Brei et al. ACL 2026): new `skills/voice/resources/character-dialogue-profiles.md` (character-page `dialogue profile` section + the ~70% blind speaker-attribution test); `style stats --dialogue` (per-speaker stats, pairwise-convergence flags, report-only); skeleton in `templates/character.md`; duties wired into `@character-sim` and the critique voice lens.
6. **ADD-6 — Tense/person morphology scan** in the mechanical net (report-only): `style stats --morphology` — rule-based Romanian morphology pass (narrative-tense distribution, narration-person distribution, drift vs frontmatter `tense:`/`pov-person:`, mid-chapter shifts; ambiguity-tolerant, stdlib regex only). Chapter frontmatter gained optional `tense:`/`pov-person:` fields (inherited from `kb/story.md` when null); the scan runs as part of the advisory post-write pass (no exit-code change, silent when clean), with the `voice:skip` carve-out and a per-line `<!-- tense:skip -->` valve for deliberate tense play (`structural-caps.md`).

**Tests:** suite grew to **98 passing** on the seeded fixture project (dialogue-stats, morphology, and `revision status` engine tests included); `scripts/ci/lint_vellum.py` clean after the pass (including its extended file set).
