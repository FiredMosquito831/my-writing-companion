# Layout and Theme

Shared patterns for all structured artifacts. Load this alongside the
pattern-specific resource.

## Mobile-First Layout

Design for a narrow viewport, then enhance. A single scrolling column is the
base layout; sidebars and multi-column arrangements are `md:`-and-up additions.

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

- Content flows top to bottom on mobile: toolbar, content, detail.
- Detail views are bottom sheets on narrow screens, sidebars on wide screens —
  one Tailwind breakpoint (`md:`) covers both.
- Tap targets ≥ 44px. Diagrams get touch pan/pinch-zoom.
- Test by narrowing the window to ~375px before calling it done.

## CDN Base Stack

```html
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4/dist/index.global.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/github.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js"></script>
```

Tailwind's browser build (v4) is a single IIFE — configure via
`<style type="text/tailwindcss">` with `@theme { ... }` blocks; the old
`tailwind.config = {}` object is gone. highlight.js is only needed if the
artifact shows syntax-highlighted code in detail panels: call
`hljs.highlightAll()` (or `hljs.highlight(code, { language })` for dynamic
content), and swap `github.min.css` / `github-dark.min.css` on theme toggle.

### Vendoring for offline use

When the artifact must open without a network, download each library into the
folder and reference it relatively:

```bash
mkdir -p vendor
curl -fsSL https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4/dist/index.global.js -o vendor/tailwind.js
curl -fsSL https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js -o vendor/mermaid.min.js
curl -fsSL https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js -o vendor/highlight.min.js
```

```html
<script src="vendor/tailwind.js"></script>
<script src="vendor/mermaid.min.js"></script>
<script src="vendor/highlight.min.js"></script>
```

Use each library's single-file browser build (UMD/IIFE, like
`dist/*.min.js` on jsDelivr) — ESM URLs such as `esm.sh` fetch further
imports at runtime and fail offline. The whole base stack above vendors
cleanly; each file is self-contained with no runtime fetches.

## Wide-Screen Enhancement

On `md:` and up, the artifact may fill the browser window with a flex column:

```html
<body style="display:flex;flex-direction:column;height:100vh;overflow:hidden;margin:0">
  <header><!-- toolbar: title, theme toggle, nav buttons --></header>
  <main style="display:flex;flex:1;min-height:0;gap:1rem;padding:1rem">
    <!-- optional left sidebar (nav, ~300px) -->
    <section style="flex:1;min-width:0;overflow:hidden">
      <!-- primary content area -->
    </section>
    <!-- optional right sidebar (detail, ~360px) -->
  </main>
</body>
```

`min-height: 0` on `<main>` prevents flex children from overflowing. The
content section takes all remaining space.

### Collapsible sidebars

Sidebars are flex children with a width transition. Collapsing sets width to 0;
a fixed-width inner wrapper prevents content reflow during animation.

```html
<div id="detail-panel" class="sidebar collapsed">
  <div class="sidebar-inner" style="width:360px">
    <!-- detail content here -->
  </div>
</div>
```

```css
.sidebar {
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.2s ease;
}
.sidebar.collapsed { width: 0; }
.sidebar:not(.collapsed) { width: 360px; }
.sidebar-inner { height: 100%; overflow-y: auto; }
```

```js
function toggleDetail() {
  document.getElementById('detail-panel').classList.toggle('collapsed');
}
```

Both sidebars start collapsed. Open the detail sidebar when the viewer taps or
clicks an element.

## Theme

Drive all colors from CSS custom properties. Default to light; toggle with a
class on `<html>`.

```css
:root {
  --bg: #ffffff; --surface: #f5f5f5; --text: #1a1a1a;
  --muted: #6b7280; --line: #e5e7eb; --accent: #2563eb;
}
.dark {
  --bg: #1a1a1a; --surface: #262626; --text: #e5e5e5;
  --muted: #9ca3af; --line: #404040; --accent: #60a5fa;
}
body { background: var(--bg); color: var(--text); }
```

```js
function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme',
    document.documentElement.classList.contains('dark') ? 'dark' : 'light');
}
if (localStorage.getItem('theme') === 'dark') {
  document.documentElement.classList.add('dark');
}
```

When using Mermaid, re-initialize with the matching theme after toggle — see
`diagrams.md`.

For multi-page sites, put the variables and toggle in `shared.css` /
`shared.js` so every page stays consistent — see `multi-page-site.md`.

## Serve Over Tailscale (optional)

View the artifact on another device by serving over your tailnet. Only offer if
Tailscale is present: `command -v tailscale`.

```bash
PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()')
python3 -m http.server "$PORT" &
tailscale serve --bg "$PORT"
```

Proxies HTTPS on your tailnet to `localhost:$PORT`. Tear down with
`tailscale serve --bg "$PORT" off`.
