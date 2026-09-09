# VALIDATION

The design lineage, validation record, and test results for Vellum v0.1.0 (2026-09-09).

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

## 4. Known limitations (logged by the paper-run, still open)

Ranked as the paper-run reported them; all are LLM-side glue or UX issues, not engine/gate defects.

1. **Transcript-provenance requirement may be unsatisfiable by the muse (HIGH).** Both report gates bind to a `transcript:` field sourced "from the spawn's SubagentStop payload," but SubagentStop payloads reach hooks, not the parent conversation, and the muse has no documented fallback for finding the transcript path. Needs a surfaced path, a documented search convention, or a documented fallback.
2. **Pivotal chapters in single-agent (no-subagent) mode are unbuildable (MEDIUM).** Gate 2 requires a naive-eyes run that cannot exist in one context; the single-agent fallback never says what to do (decline the pivotal flag / soft-fail).
3. **First `/vellum:write-chapter` trips the chapter-transaction block (LOW-MEDIUM, recoverable).** `project-setup` never says to run an initial `state rebuild`; the block names the fix but is doubled/garbled wording on a new user's first contact.
4. **Setup entry point is skill-only (LOW).** No `/vellum:init` command; discovery relies on the `project-setup` skill description matching the request.
5. **`style stats --baseline <file>` argument order is order-sensitive (LOW).** The documented order works; the reversed order errors, recoverable via `--help`.
6. **Minor engine quirks (LOW).** Duplicate ids possible in `work/voice-debt.json` after rescans; `prose_core.py extract-target` exits 1 (not silent fail-open) on malformed JSON (guarded by callers); the outliner doesn't name `work/outline/` explicitly.
7. **Model IDs in agent frontmatter are not verifiable at lint time (LOW).** If unresolvable at install, agents would fall back or error.
8. **"Handle via the muse agent" is ambiguous (LOW-MEDIUM).** Commands never say whether to spawn the muse subagent (impossible from a subagent) or adopt the muse role in the main loop; the intended reading is the latter, supported by the `creative-writing-muse` single-agent fallback.
