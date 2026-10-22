# Contributing

Vellum is a working tool for novelists, and it is deliberately conservative
about what it depends on. Contributions are welcome when they respect the
constraints below. If you are unsure whether a change fits, open an issue first.

## The constraints that keep it shippable

1. **The engine stays Python 3.8 and standard-library only.** No runtime
   dependencies, no new imports outside the standard library, no f-strings with
   syntax newer than 3.8, no `match` statements. The engine is copied into
   authors' novel projects; it must run there with nothing installed.
2. **The three hard gates stay three.** Do not add a blocking gate. Findings
   that are not gate-worthy are advisory and silent when clean.
3. **Gate verdicts come from disk, never from chat.** A change that lets an
   agent's claim satisfy a gate is a design regression, even if the tests pass.
4. **Stance isolation is structural.** Critics and readers stay read-only by
   frontmatter; the writer stays restricted to `manuscript/` and `work/drafts/`.
   Do not widen a tool list to make a workflow convenient.
5. **The plugin must remain installable on stock Claude Code.** No private
   services, no custom host, no required Node toolchain, no WSL requirement.
6. **Windows is a first-class platform.** Hooks must stay POSIX-sh compatible
   and bash-3.2-safe, with LF line endings, `LC_ALL=C` where byte stability
   matters, and no associative arrays or `mapfile`.

## Before you open a pull request

Run all three checks locally:

```bash
python -m pytest tests/ -q          # 155 tests, engine + hooks + series
python scripts/ci/lint_vellum.py    # frontmatter, attribution, vocabulary, size
python scripts/build_site.py --check
```

The site check needs the site-only dependencies once:

```bash
python -m pip install -r requirements-site.txt
```

If you changed anything that feeds the site — plugin version, agent, command, or
skill frontmatter — regenerate and commit `docs/`:

```bash
python scripts/build_site.py
```

Do not hand-edit generated files in `docs/`. Edit `site/templates/`,
`site/static/`, or `scripts/build_site.py`, then rebuild.

## Frontmatter rules

- An agent's `name` must equal its filename; a skill's `name` must equal its
  directory name.
- `description` is required and should say *when* to load the agent or skill,
  not just what it is.
- Agent `model` must be one of the aliases the lint accepts (`opus`, `sonnet`,
  `haiku`, `inherit`) — not a pinned full model ID.
- Every skill or agent that ports a mechanism must carry the attribution header
  recorded in `ATTRIBUTION.md`.
- The 100 KB size cap applies to every component file. If a document needs more,
  split it into a `references/` resource and load it on demand.

## Tests

- Engine and hook behaviour belongs in `tests/test_engine.py` and
  `tests/test_hooks.py`; series behaviour in `tests/test_series_followup.py`.
- Fixtures live under `tests/fixtures/`. Assert exact finding keys, not
  substrings, when a key is part of the contract.
- Hooks are tested by feeding them the JSON payload Claude Code would send — not
  by calling internal functions directly.
- A bug fix needs a regression test that fails without the fix.

## The site

- `SITE_URL` in `scripts/build_site.py` is the only place the public host is
  defined. Do not hard-code the host in templates.
- The build is deterministic: no timestamps, no random data, no environment
  sniffing. `--check` fails if `docs/` is stale.
- Site-only dependencies belong in `requirements-site.txt`. They must never be
  imported by the plugin's engine or hooks.
- Screenshots are captured from the built site and stored in
  `site/static/screenshots/`; the build copies them into `docs/assets/`.

## Commits and licensing

- Keep commits focused; explain *why* in the message.
- By contributing, you agree your work is licensed under Apache-2.0, the
  project's license.
- Do not remove or alter upstream copyright notices. Attribution is a condition
  of several source licenses, not a courtesy.
