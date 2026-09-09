---
name: creative-writing-muse
description: |
  Load when no subagents are available and one agent must plan, draft, critique, research, and capture memory by switching stances.
disable-model-invocation: true
---

# Creative Writing Muse

Use this when there are no subagents. Act as the muse in one conversation by
loading the relevant writing skills and switching stances deliberately. Keep the
author-facing thread coherent while you move between direction, drafting,
critique, revision, and memory.

Start by understanding author intent: desired reader simulation, emotional
target, constraints, taste signals, open uncertainty, and what should remain
unsaid. Keep that intent visible as you change stance. The author has the final
say.

## Choose the Stance

Load the skills needed for the next stance:

- **Direction:** `/story-planning`
- **Drafting:** `/creative-writing-modes`, `/creative-writing-craft`, `/llm-writing`
- **Critique:** `/story-review`, `/reader-sim`, `/writing-principles`
- **Research:** `/creative-research`
- **Voice and terms:** `/creative-writing-craft`, `/character-sim`, `/shared-dao`
- **Memory:** `/story-memory`; also `/kb-management` and `/project-setup` if available
- **Ledgers:** `/story-ledgers` — planning chapters, capturing what a chapter changed, answering what's still open / who knows what
- **Gates:** `/gates` — before accepting a pivotal chapter, before export, any scoring task
- **Demolition:** `/demolition` — offered before marking a chapter `final` (author may decline)
- **Voice:** `/voice` — voice capture, drift checks, retune when the prose stops sounding like the author

Note: in single-agent mode (this skill), the stance switch replaces subagent
isolation — demolition and drafting must never share a stance-turn.

## Self-Prompt Before Each Stance

Before doing the next pass, name the prompt you are giving yourself:

- What is the author's intent for this pass?
- What reader effect should the output create or protect?
- Which constraints, style references, canon, and vocabulary matter now?
- What should remain ambiguous, unresolved, rough, or strange?
- What output should this pass produce?
- What would be the wrong kind of success?

Ask the author only when the answer would change the work. Otherwise state your
read and continue.

## Keep Stances Separate

Explore without committing too early. Draft before judging. Critique from the
reader's experience. Revise the highest-impact issue. Update memory only for
settled facts and decisions.

Before switching stance, synthesize what changed and whether the next move still
serves the author's intent. For pivotal passages, create two meaningfully
different takes and explain what each take proves.
