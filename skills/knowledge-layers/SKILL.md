---
name: knowledge-layers
description: 'Use when deciding where knowledge goes or reading/writing durable docs: AGENTS.md, .context/, KB, docs/, and work directories.'
---

# Knowledge Layers

Load `/qi-layer` when writing or editing AGENTS.md or .context/ files: it
owns the craft (four principles, contents guidelines, what doesn't belong).
Load `/information-hierarchy` if not already loaded for disclosure tiers.
Load `/llm-writing` if not already loaded.

## The Five Layers

| Layer | What it holds | When to use it |
|---|---|---|
| `AGENTS.md` | Intent and mental model for a directory | First thing agents read on entry; what to understand *before* working here |
| `.context/` | Contracts, architecture, rationale (`CONTEXT.md`); deferred work (`TODO`, `FUTURE`) | Reference depth and tracked deferrals, co-located with the code they describe |
| KB | Cross-cutting decisions, domain concepts, patterns | Spans directories; outlives sessions; no single directory owns it |
| `docs/` | User-facing documentation | Different audience, different update cadence |
| Work directory | Temporary design decisions and scratch | Not colocated with durable content; scoped to an active work item |

## Placement Rules

If it's intent/mental-model for a directory → `AGENTS.md`.
If it's directory-scoped depth an agent looks up → `.context/`.
If it's deferred work scoped to this directory → `.context/TODO` (must-do)
or `.context/FUTURE` (nice-to-have). Flat markdown lists — each entry names
the affected path and concrete follow-up. Cross-cutting items or items needing
external visibility get filed in the project's issue tracker instead.
If it's big picture — cross-cutting decisions, domain concepts,
higher-level system architecture → KB.
If it's for end users → `docs/`.
If it's a temporary work artifact → work directory.

When in doubt, colocate. Knowledge that depends on one subsystem belongs
in that subsystem's AGENTS.md or .context/ even when it reads like a
concept; the KB stays code-agnostic, holding what survives implementation
change. Knowledge that lives far from what it describes rots faster:
changes to the code don't trigger awareness that a distant doc needs
updating.

## Current Truth Over History

Every durable layer — AGENTS.md, `.context/`, KB, `docs/` — holds the best
current understanding; work directories may keep intermediate reasoning
while their work item is active. When durable content is
superseded, delete it or (for KB pages) move it to `archive/`
(`.kgignore`'d, excluded from the knowledge graph). Live content never
references archived content. Pages read as current truth, never narrate
their own evolution.

**Deletion needs no replacement.** A page whose subject is gone, or that
describes behavior the system no longer has, gets deleted on sight — even
with nothing new to write in its place. Stale knowledge is worse than a
gap: agents load it and reason from it. Deletion is the content-truth
owner's call; structural roles flag instead.

**Git history is the archive.** Commit untracked files before deleting them
so the removal lands in history, and say what was removed and why in the
commit message. Deletion is cheap because nothing tracked is ever truly
lost.

**Truth is anchored per layer.** AGENTS.md and `.context/` describe the
checkout that contains them: update them in the same branch as the code
change and let the merge carry both — with parallel PRs in flight, each
branch documents itself. The KB is code-agnostic: it records the current
settled intent — what the system *should be* — and a settled decision is KB
truth the moment it's made, merged or not. Unsettled intent isn't KB
material; it stays in the work directory. `docs/` describes shipped
behavior.

Decision records are the exception: preserve superseded decisions in place
when they explain why the system changed. Mark the old decision as
superseded and link to the replacement.

## KB Conventions

### Structure

The KB is a directory tree like any other: it carries its own AGENTS.md
and `.context/` pair, written per `/qi-layer` — intent in AGENTS.md,
governance depth (writing conventions, structure, validation) in
`.context/`. Read the KB's own `AGENTS.md` before writing. Treat this
skill as the cross-project default; the local KB guide wins for that KB.
See `resources/bootstrap.md` for a suggested starting layout.

### Wiki Page Conventions

Follow `/information-hierarchy`. One concept per document; name files by
what they describe (`token-validation.md`), not when (`auth-redesign-notes.md`).
Cross-reference instead of re-explaining. Load `/shared-dao` for vocabulary
methodology. Use mermaid for anything spatial; capture what code can't
easily tell you.

## Operations

**Ingest**: new information enters the KB. Read the source, extract key
knowledge, write or update wiki pages, and update indexes/cross-links touched
by the change.

**Maintain**: keep the wiki current per Current Truth Over History above.

**Lint**: health-check the wiki. Look for contradictions, stale claims,
orphan pages, missing cross-references. Use `/md-validation` for link
checking and diagram validation.

Flag content needing human attention with `> [!FLAG] **Needs human review**`.
