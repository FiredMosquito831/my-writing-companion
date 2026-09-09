---
name: md-validation
description: Use when validating markdown links or Mermaid diagrams.
---

# md-validation

## Mermaid Diagrams

Validate Mermaid diagrams render correctly before shipping. Open the HTML
artifact in a browser and check every diagram visually — syntax errors show
as broken renders, not error messages.

Common failure modes:
- Unquoted labels with punctuation break the parse
- Bare lowercase `end` collides with subgraph terminator
- Node IDs starting with `o` or `x` after edge markers get misparsed
- Custom fills without matching text color make labels unreadable

See `resources/mermaid-authoring.md` for the full authoring rules (quoting,
line breaks, reserved words, themes).

## Markdown Links

Check that relative links between pages resolve. When building a multi-page
artifact or KB, broken cross-references silently rot — verify each link
target exists before committing.
