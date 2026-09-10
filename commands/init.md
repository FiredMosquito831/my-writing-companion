---
description: Set up a creative-writing project for this plugin — run the project-setup skill (interview, kb layout, CLAUDE.md, initial state rebuild).
---

Adopt the muse role: load the muse instructions (`creative-writing-muse`) and run this in the main loop — do not spawn a "muse" subagent (a subagent cannot spawn subagents).

Run the **`project-setup`** skill end to end. It interviews the author about the project, collects writing samples into `kb/samples/`, creates the full vellum project layout (`kb/`, `manuscript/chapters/`, `state/`, `work/`, `export/`, local `templates/`, the copied engine under `scripts/`), writes `CLAUDE.md` with the project conventions, tells the author the three hard gates, and finishes by running the **initial `state rebuild`** so the first `/vellum:write-chapter` starts clean.

$ARGUMENTS (optional): anything the author already knows — genre, working title, where existing chapters live. Pass it into the interview instead of re-asking.

On existing projects, `project-setup` reads the current `CLAUDE.md` first and fills gaps rather than overwriting.
