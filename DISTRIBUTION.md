# DISTRIBUTION — practical release checklist for Vellum

Practical, sourced from the distribution research behind v0.2.0 (registry survey, official review policy, repo-metadata audit of high-star plugin repos). Checked boxes are done as of v0.2.0; unchecked ones are the next actions. Two ground rules from the research: **bump `plugin.json` AND the marketplace entry version on every release** (Claude Code caches plugins; a stale version silently blocks updates), and **assume official reviewers read the entire shipped payload, including dotdirs and scripts** — disclose everything the plugin touches.

## 1. Repo foundation (required before any submission)

- [x] `.claude-plugin/plugin.json`: kebab-case name (`vellum`), strict semver, author, homepage → repo URL.
- [x] `marketplace.json`: same version number as `plugin.json`, per-plugin entry with description.
- [x] Version bumped on **every** release (v0.2.0 done); tag + GitHub Release per release (done for v0.1.1, v0.2.0).
- [x] Skills under `skills/<name>/SKILL.md` with explicit `name`/`description` frontmatter (all 34; the CI lint checks this).
- [x] README: badges, one-line value prop, copy-paste install block, FAQ, gate model, credits with licenses.
- [x] LICENSE (Apache-2.0) + NOTICE + ATTRIBUTION.md for ported MIT/ideas-only sources.
- [x] CI: pytest matrix on `ubuntu-latest` + `windows-latest`, plus a validate/lint workflow.
- [ ] CHANGELOG.md as a top-level file (currently the changelog lives in [VALIDATION.md §5](VALIDATION.md) — consider extracting).
- [ ] Demo GIF/screenshot above the fold (high-star repos correlate with this; Vellum's state card and gate-block output are the two shots to capture).
- [ ] Description-cap check: every skill `description` well under the 1,536-char listing cap (over it, trigger phrases get silently truncated).

## 2. Registry listings

| Registry | Action | Status |
|---|---|---|
| **Official Claude plugin directory** | Submit via the form at [claude.com/docs/plugins/submit](https://claude.com/docs/plugins/submit) (Claude.ai Team/Enterprise) or `platform.claude.com/plugins/submit` (Console). **Never PR to `anthropics/claude-plugins-community`** — it is a read-only mirror; PRs auto-close. | [ ] Repo is public; run `claude plugin validate` first. Review is automated + periodic rescreening of every update; must comply with the [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy) and AUP. Reviewers read everything — hooks included — so the security self-audit below matters. |
| **ClaudePluginHub** | Paste the public GitHub URL at [claudepluginhub.com/tools/submit-plugin](https://www.claudepluginhub.com/tools/submit-plugin); then claim ownership for analytics + verified badge; embed the install-count badge in README. Auto-discovery also scans GitHub Code Search, but claiming is faster. | [ ] |
| **Build with Claude** (davepoon/buildwithclaude) | PR into the repo's `plugins/` structure; auto-published on merge. It is also an installable marketplace itself. | [ ] |
| **claudeskills.info** | No form — auto-indexed from GitHub when valid SKILL.md files exist. Verify indexing after a few days; per-skill pages carry install counts. | [ ] (auto) |
| **awesome-claude-code** (hesreallyhim, 51k★) | Issue-based submission using their **exact issue template** (display name, category, links, license, one resource per issue). Highly selective, aggressive anti-spam — template violations close instantly. | [ ] |
| **awesome-claude-code-plugins** (ccplugins / hekmon8) | PR with plugin README. Criteria: functional, documented, open-source, maintained, safe. Cheap to do; multi-registry presence compounds. | [ ] |

## 3. Repo metadata for discovery

- [x] **Description**: keyword-front-loaded one-liner (GitHub code search and Copilot's semantic index both read it). Set via API for v0.2.0: "Vellum - a working novelist daily tool for Claude Code: three hard gates, a deterministic continuity engine, and a series-aware library layer."
- [x] **Topics**: 8 precise lowercase topics set via API: `claude-code`, `claude-plugin`, `novel-writing`, `fiction-writing`, `creative-writing`, `story-bible`, `writing-tools`, `ai-writing`. Room to grow toward 15+ (candidates: `claude-code-plugins`, `agent-skills`, `anthropic`, `agentic-coding`, `developer-tools`, `writing-software`, `continuity`).
- [ ] **Social preview**: 1280×640 PNG, one-time manual upload in Settings → Social preview (no API). Candidate: the three-gates diagram or the state card.
- [x] **Releases + tags**: `v0.2.0` tag on the ship commit with release notes summarizing v0.1.1 + v0.2.0 (updates auto-mirror to the official directory after listing — no re-submission needed).
- [ ] Discussions enabled on the repo.
- [ ] `llms.txt` / structured FAQ (the README FAQ exists; an `llms.txt` at repo root is the cheap GEO add for AI-discoverability).

## 4. Security self-audit (official-directory gate)

- [x] Whole-tree grep (including dotdirs) for data collection / exfiltration: the engine and hooks are stdlib-only, no network calls, no telemetry; scripts live in `scripts/vellum_lib/` and `hooks/scripts/` with no writes outside the author's project tree.
- [x] Hooks do only their stated job (gate prose writes, lifecycle state card); gate-input protection documented in [README](README.md) — install description discloses what the plugin does.
- [x] No coercive instructions in skill text ("always run me first" patterns fail official review); every skill description states its actual trigger.
- [ ] Re-run this audit before each official-directory submission and after any hook change.

## 5. Launch channels (after listing)

- Show HN with technical depth (the three-gates-from-disk + stance-isolation architecture is the story; lead with mechanisms, not adjectives).
- Reddit: 2–4 weeks of membership-first participation in r/WritingWithAI and adjacent subs before any product post; answer genuinely relevant threads as the core motion — value-not-promotion, or the post reads as spam.
- Multi-host distribution is a proven growth pattern (one skill, many installers): the engine already runs standalone from a project copy; a `uvx`/`npx`-style standalone installer for the Python engine is an optional future add.

## 6. Per-release cadence (ongoing)

1. Bump `plugin.json` + `marketplace.json` version; commit; tag; GitHub Release.
2. Update README status section; add the changelog entry at the top of VALIDATION.md §5.
3. Push → CI green → the official directory mirrors automatically after listing.
4. Remind users in release notes to run `/plugin marketplace update` (Claude Code update-detection bugs are documented — e.g. anthropics/claude-code#54276).
