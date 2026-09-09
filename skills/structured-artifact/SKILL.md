---
name: structured-artifact
description: |
  Load when building a static HTML artifact — single page or multi-page site —
  to make structured information explorable through layout and navigation.
disable-model-invocation: true
---

# Structured Artifact

A structured artifact is plain HTML that opens from `file://` and works on a
phone. Load `/information-hierarchy` first — it decides what each page shows
and in what order; this skill builds it.

## One page or several

Start from one `index.html`. Its first viewport carries the answer, and depth
discloses in place — `<details>`, popovers, a collapsible detail panel. Grow
into a folder (`index.html` + child pages + `shared.css`) when readers need
whole pages per branch: the index becomes a map with links, and each child
page stands alone with its own lede. `resources/multi-page-site.md` has the
folder mechanics.

## Build so it keeps working

Everything ships static — plain `<script>` tags, zero build step — so the
artifact opens anywhere, years later, with nothing installed. CDN tags are
the default; vendor the scripts into the folder when the artifact must work
offline (`resources/layout-and-theme.md`). Resource snippets show the shape
of each library's use, pinned only to a major version — before building,
web-search the library's current version and syntax when anything looks
dated, rather than trusting the snippet as frozen truth. Design for a
narrow viewport and let wider layouts be enhancements; touch targets stay
≥ 44px and diagrams pan and pinch. Drive colors from CSS custom properties on
`:root`, default light, with a ☀/🌙 toggle that adds `.dark` to `<html>` —
readers get a readable page in daylight and a choice at night.

`resources/layout-and-theme.md` has the concrete layout, theme, and mobile
patterns shared across everything below.

## Verify the end state

Open the artifact in a browser before calling it done — a snippet that
looked right in the editor still fails at runtime (a CDN URL 404s, a library
changed its API, a diagram overflows). Check what a reader meets: the first
viewport carries the answer, every page renders at ~375px width, the theme
toggle flips both text and embedded content, links between pages resolve,
and Mermaid diagrams render correctly.

## Enrichments

Mix and match resources and patterns as needed, starting with the simplest
pattern and adding complexity only when information hierarchy calls for it.

Load a resource when a beat calls for its pattern:

| Pattern | When a beat needs | Resource |
|---|---|---|
| Multi-page site | Index + child pages, nav, cross-links | `resources/multi-page-site.md` |
| Mockup | Wireframe or annotated plan the reader must see | `resources/mockups.md` |
| Diagram | Dependencies, flow, system maps | `resources/diagrams.md` |
| Data table | Records with sortable/filterable columns | `resources/data-table.md` |
| Data chart | Quantities, trends, distributions | `resources/data-chart.md` |
| Timeline | Chronological events with detail | `resources/timeline.md` |
| Tree / TOC | Hierarchy navigation, document outline | `resources/tree-and-toc.md` |
| Card grid | Items with summary + expandable detail | `resources/card-grid.md` |
| Diff / comparison | Before/after, version diff | `resources/diff-view.md` |

For custom node rendering, drag, or live filtering on graphs beyond what
Mermaid offers, see `resources/experimental-react-flow.md`.
