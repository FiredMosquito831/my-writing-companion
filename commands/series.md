---
description: Operate the library/series layer — link books, capture series canon, run retcon checks, plan and apply retcons.
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents). Then load the **`series`** skill (`skills/series/SKILL.md`): it is the operator's manual for the library layer and owns the retcon lifecycle (plan → approve → apply), the detection catalog (`skills/series/references/checks.md`), the do-not-re-explain register, and handoff generation. Route judgment-flagged rows to `@kb-lead` / your own critique — the engine never resolves them.

$ARGUMENTS (optional) = the `library` subcommand to run plus its arguments. With no arguments, print the series state summary (`library state <book-root>`) and the subcommand table below.

**Engine entry point:** `scripts/library.py`, run via the resolved interpreter (`python3` → `python` → `py -3`; ≥ 3.8; the plugin copy lives at `${CLAUDE_PLUGIN_ROOT}/scripts/library.py` when the project has no local copy). Every subcommand takes `--root <library-root>`; without it the command refuses — there is no filesystem walk-up discovery of the library. Exit codes: `0` clean · `1` findings or a plan awaiting author action (advisory, never a gate) · `2` usage/schema/environment error.

| Subcommand | What it does |
|---|---|
| `library init <library-root>` (`--root <library-root>` also accepted) | Create the library tree (manifest, `series/`, `reports/`, `handoff/`). Refuses inside a book project. |
| `library link <book-root>` | Attach a book: writes `.vellum/series-link.json` then the manifest entry (idempotent-completing). Link only — no canon capture. |
| `library unlink <book-root>` | Detach a book; canon is retained and flagged as orphan refs. |
| `library validate` | Read-only integrity check: half-linked states, paths, schemas, `established-in` refs, `series-id:` joins, errata refs. `--fix` regenerates stale sidecars. |
| `library bootstrap <book-root> [--plan\|--apply]` | Deterministic canon capture from the book kb: exact / alias / `[?]` match tiers. `[?]` rows write nothing until the author resolves them; `--apply` runs only on an approved plan. |
| `library retcon-check <book-root>` | Run the detection catalog (deceased-as-of-start, open-thread carry, knowledge anachronism, canon divergence, …) — read-only. |
| `library retcon-plan <book-root>` | Produce `reports/retcon-plan-<ts>.md` from `templates/retcon-plan.md` for author review. |
| `library retcon --apply <plan-file>` | Apply an approved plan row-by-row (refuses without `approved: true` and a non-empty verbatim `author_words` on every row). Each row's `new_by_book` is merged onto the existing by-book map; changing any published or archived ordinal additionally requires `override_published: true`. |
| `library state <book-root>` | Print the series state card (also injected into `vellum state` for linked books). |
| `library timeline` | Emit the `E###` master timeline (stable, never renumbered; read-only). Events are minted only by approved `retcon --apply` rows of `kind: established-before`, with an explicit coordinate; bootstrap does not parse kb timeline markdown. |
| `library handoff <book-root>` | Generate `handoff/handoff-<ordinal>.md` for the next book: frozen canon, iron facts, do-not-re-explain register, open retcons, errata posture. |
| `library dismiss <finding-id> --reason "…"` | Record a series-scope dismissal — the reason must be the author's own words, verbatim. For an intentional recurring apparition, a per-chapter deceased finding can be dismissed once with the wildcard `series:deceased-as-of-start:<series-id>:*`. Same discipline as `/vellum:dismiss`; series dismissals live only in the library and never touch the book's `kb/exemptions.json`. |

Doctrine (binding): series findings are **advisory — the layer adds no fourth gate**. All series-canonical state lives in the library (`series/bible.json`); a book project never gains a canon mirror, and `kb/story.md`, `CLAUDE.md`, and book hooks are never edited by the layer. Book status doctrine: `draft` accepts retcon proposals; `published` canon is frozen (default: retcon record required — the draft loses, never later-wins); `archived` is fully quiet. A v0.1.1 project without a link works byte-identically whether or not the library layer is installed.
