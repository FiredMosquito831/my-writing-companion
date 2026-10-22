# Changelog

Notable changes to Vellum. The plugin's version of record is
`.claude-plugin/plugin.json`.

## Unreleased — documentation site

- Add a generated static site at <https://vellum.danubelabs.net>, built from the
  repository's own manifest and frontmatter by `scripts/build_site.py`
  (Jinja2, deterministic output, stale-output check in CI).
- Add full SEO metadata, an Open Graph image, `sitemap.xml`, `robots.txt`, a
  `CNAME`, and a custom 404.
- Rewrite the README's opening with a site link and real screenshots.
- Add `SECURITY.md`, `CONTRIBUTING.md`, and this changelog.
- No plugin behaviour changed. The engine remains Python 3.8 stdlib-only.

## v0.2.0 — 2026-09-10

The optional library / series layer.

- New `scripts/library.py` entry point and three series modules
  (`series_cli.py`, `series_bible.py`, `series_checks.py`): library init, link
  and unlink, validate, bootstrap, retcon check/plan/apply, state, timeline,
  handoff, and dismiss.
- New `series` skill (operator's manual and detection catalog) and
  `series-bible` skill (data dialect), plus the `/vellum:series` command and the
  retcon-plan template.
- Series bible with per-field `by-book` value maps; append-only retcon log that
  records the author's words verbatim; series-scope exemptions; published canon
  frozen by default.
- A fail-open series line in the session-start hook for linked books.
- The layer adds no fourth gate and no book-side schema bump. Compatibility is
  enforced by a byte-identity golden suite and an inert-to-old-engine test.
- Suite grows to **155 passing tests** (120 engine/hook, 35 series follow-up),
  on `ubuntu-latest` and `windows-latest`.

## v0.1.1 — 2026-09-10

Fixes for all eight v0.1.0 paper-run findings, plus craft additions.

- Gate-artifact provenance via the reader's self-recorded run stamp, with an
  optional transcript-path binding.
- Documented, author-enabled fallback for pivotal chapters in single-agent mode
  (`blind_gate_fallback` in `kb/project-config.json`); the engine rejects a
  fallback stamp without it.
- `/vellum:init` as a first-class setup entry point; `project-setup` runs the
  initial `state rebuild`.
- Obligatory scenes and conventions checklist per genre; try-fail failure
  ladder; revision plan (`work/revision-plan.md`, `vellum revision status`);
  beta-synthesis protocol; per-character dialogue profiles with a blind
  speaker-attribution test; Romanian tense/person morphology scan.
- 98 passing tests. Everything new is advisory; the three gates stayed three.

## v0.1.0 — 2026-09-09

Initial release.

- 16 agents, 32 skills, 7 commands, 7 hooks, the complete stdlib engine,
  templates, and CI on two operating systems.
- Three hard gates: approved outline before prose, blind-reader verdict on
  pivotal chapters, beta-reader PASS before export.
- Three adversarial validation rounds: 92 findings logged, all fixed. An
  end-to-end paper-run exercised every gate, hook, and engine path on Windows.
