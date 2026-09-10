---
title: "<chapter title>"
number: 0
status: outlined
approved-outline: work/outline/chapter-NN.md
pov: character-<pov-slug>
characters: []
mentions: []
promises-advanced: []
custody: []
tense: null
pov-person: null
word-target: 3200
word-count: null
---

<!--
Schema per design-spec.md section 7.2 (extended from story-skills chapter-template + oh-story
word contract). Field semantics:
- status: outlined | draft | revised | accepted | final
- pov: must appear in characters: (ledger check: POV-not-in-cast)
- characters: present in-scene; mentions: referenced/remembered/dead (no continuity error)
- promises-advanced: promise ids touched this chapter
- custody: prop ids this chapter holds or moves (ledger check validates each against the
  prop's recorded status — unknown ids, or props whose status is destroyed/lost/resolved,
  are findings)
- tense / pov-person (optional): narrative tense ("present", "imperfect",
  "perfect-compus", "past", ...) and narration person ("first", "third") for the
  morphology scan (`vellum style stats --morphology`, report-only). When null they are
  inherited from kb/story.md frontmatter. Deliberate tense moves (flashback, epistolary
  inserts) are carved out per-line with the tense:skip valve — see
  style-guardrails/resources/structural-caps.md.
- number is the ordering key; ordering is by frontmatter number, never by filename.
Example (spec section 7.2): title "The Salt Road", number 7, pov character-mira-tarn,
characters [character-mira-tarn, character-old-tom], mentions [character-vess],
promises-advanced [promise-ring-of-oath], custody [prop-ring-of-oath], word-target 3200,
word-count 3148.
project-setup copies this template into manuscript/chapters/ per new chapter.
-->
