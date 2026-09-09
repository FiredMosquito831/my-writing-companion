---
id: knowledge-<kebab-slug>
type: knowledge
title: "<short label>"
statement: "<canon fact prose>"
holders: []
audience-learned-in: null
superseded-by: null
---

<!--
Schema per design-spec.md section 7.3 (3-level certainty; fiction-forge cold-read knowledge map
+ Novel-OS-style per-holder query; queryable via `vellum knowledge <character-id> --as-of N`).
holders is a list of maps:
  - character: character-<slug>
    learned-in: chapter-NN
    certainty: knows | half-glimpse | audience-only
audience-learned-in: chapter-NN when the READER learns it (dramatic-irony queries).
File name: <id>.md under kb/knowledge/.
-->
