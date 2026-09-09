# Diff / Comparison

Side-by-side or unified diff view with syntax highlighting. Use for before/after
comparisons, version diffs, or change review. For a short comparison without
syntax highlighting, two `<pre>` elements side by side with highlighted lines
beat loading a library.

## Library

**Diff2Html** for rendering + **jsdiff** for computing diffs from strings. Use
the `-slim` bundle (~97 KB gzipped, common languages: JS, TS, Python, CSS,
JSON…) — the full bundle is ~335 KB for every highlight.js language and rarely
earns it. jsdiff is ~10 KB gzipped.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/diff2html@3/bundles/css/diff2html.min.css">
<script src="https://cdn.jsdelivr.net/npm/diff@9/dist/diff.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/diff2html@3/bundles/js/diff2html-ui-slim.min.js"></script>
```

If you already have a unified diff string, omit jsdiff.

## Minimal Example

```html
<div>
  <button onclick="renderDiff('side-by-side')">Side by Side</button>
  <button onclick="renderDiff('line-by-line')">Unified</button>
</div>
<div id="diff"></div>
<script>
const oldText = "function greet(name) {\n  return 'Hello ' + name;\n}\n";
const newText = "function greet(name) {\n  return `Hello ${name}!`;\n}\n";
const patch = Diff.createTwoFilesPatch("old.js", "new.js", oldText, newText);

function renderDiff(mode) {
  const el = document.getElementById("diff");
  el.innerHTML = "";
  const ui = new Diff2HtmlUI(el, patch, {
    drawFileList: false,
    outputFormat: mode,
    matching: "lines",
    highlight: true,
  });
  ui.draw();
  ui.highlightCode();
}

renderDiff("side-by-side");
</script>
```
