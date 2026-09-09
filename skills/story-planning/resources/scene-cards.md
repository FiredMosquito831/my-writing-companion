# Scene Cards

Mechanism credited to GOAT-Storytelling-Agent (scene card concept); no source text or code copied. Changes: re-cast as a vellum planning/briefing tool; the 9 fields are written fresh for the vellum outline workflow; integrated with the chapter template and the §9 drafting context recipe.

A scene card briefs an individual scene before it is drafted. It is the unit the outliner produces when breaking a beat into scenes, and the unit the writer reads (via `vellum pack`) when drafting. One card per scene; the card travels with the outline into the writer's context pack.

## The 9 fields

| Field | Question it answers |
|---|---|
| **Characters** | Who is present in-scene (not just POV)? |
| **Place** | Where does it happen? |
| **Time** | When — story-day, time of day, relation to the last scene? |
| **Event** | What happens, concretely? |
| **Conflict** | What opposes the POV character's goal *in this scene*? |
| **Story value** | What value (life/death, trust/fear, freedom/cage) is at stake? |
| **Value charge** | Does the value shift positive or negative by the scene's end? |
| **Mood** | What should the reader feel? |
| **Outcome** | What is the disaster / turn — "no" or "yes, but"? |

## Template block

```markdown
## Scene: <kebab-slug> (Chapter <NN>, beat <B>)

- **Characters:** <character-a>, <character-b>
- **Place:** <location>
- **Time:** <story-day / time>
- **Event:** <one sentence: what happens>
- **Conflict:** <what opposes the goal>
- **Story value:** <value> — charge: <+/–>
- **Mood:** <reader effect>
- **Outcome:** <disaster / turn>
- **POV:** <character-pov>
- **Word quota:** <words> (fraction of chapter word-target)
- **Promises advanced:** <promise-ids>
- **Verbatim:** <lines that must appear unchanged>
```

## How it is used

- **Outliner** produces one card per scene when breaking a beat; cards are stored alongside `work/outline/chapter-NN.md`.
- **`vellum pack chapter-NN`** assembles the deterministic half of the writer's context pack from `work/outline/chapter-NN.md`; the scene cards for the chapter (stored alongside the outline) are inlined by the **muse** when composing the pack — they are muse-composed context in recipe slot 3, not engine output.
- **Writer** drafts to the card — the card is the brief, the chapter template (`templates/chapter.md`) is the container.
- **Critics** check the drafted scene against the card's intent (did the scene do what the card promised? did the value charge shift as planned?).

## Relation to scene-and-sequel

The card's Conflict / Outcome fields map to the scene (goal/conflict/disaster) half of `creative-writing-craft/resources/scene-and-sequel.md`. A card whose Outcome is a frictionless win is a flag — the scene needs a real turn.
