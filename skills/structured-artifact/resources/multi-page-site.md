# Multi-Page Site

A folder of static HTML pages when one page can't carry the structure: the
index is a map, each child page owns one cluster of beats.

## Folder layout

```
artifact/
  index.html      # the map: answer + links to child pages
  shared.css      # theme variables, layout, typography
  shared.js       # theme toggle, nav highlighting
  <topic>.html    # one child page per beat cluster
```

Flat folder, relative links (`href="topic.html"`). No server required — it must
work from `file://`.

## The index is a map

`index.html` carries the answer in its first viewport, then links out. Each
link states what the reader will learn there, not just a title:

```html
<nav class="page-map">
  <a href="runtime.html">
    <strong>Runtime loop</strong>
    <span>How a turn moves from request to checkpoint</span>
  </a>
  <a href="storage.html">
    <strong>Storage</strong>
    <span>What owns bytes, what owns meaning</span>
  </a>
</nav>
```

If the index needs its own scroll to list the pages, there are too many pages —
merge clusters.

## Child pages

Each child page stands alone: its own lede, then depth. Top of every page gets
the same minimal nav so the reader can always get back:

```html
<header>
  <a href="index.html">← Index</a>
  <span class="crumb">Runtime loop</span>
  <button onclick="toggleTheme()">☀/🌙</button>
</header>
```

Cross-link between child pages inline where beats connect ("checkpoints are
written by the <a href="runtime.html#loop">runtime loop</a>") rather than
forcing a round-trip through the index.

## Shared assets

- `shared.css` holds the theme variables and layout from
  `layout-and-theme.md`; pages must not redefine colors locally.
- `shared.js` holds the theme toggle and persistence so the choice follows the
  reader across pages.
- Repeat the CDN `<script>` tags per page — there is no bundler; each page is
  self-sufficient.
