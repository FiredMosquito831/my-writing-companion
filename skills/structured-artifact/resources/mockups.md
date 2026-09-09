# Mockups

Show what you're proposing instead of describing it. A wireframe HTML page
answers "what will this look like?" faster than paragraphs.

## Wireframe style

Grayscale boxes, real proportions, placeholder content. The point is layout and
flow, not visual design — resist styling it.

```html
<style>
  .wf { border: 2px dashed var(--line); border-radius: 6px;
        padding: 0.75rem; margin: 0.5rem 0; color: var(--muted); }
  .wf-row { display: flex; gap: 0.5rem; }
  .wf-row > .wf { flex: 1; }
  .wf-label { font-size: 0.75rem; text-transform: uppercase;
              letter-spacing: 0.05em; }
</style>

<div class="wf"><span class="wf-label">Toolbar</span> — search, filters, new-item button</div>
<div class="wf-row">
  <div class="wf" style="max-width:240px"><span class="wf-label">Nav</span> — workbench list</div>
  <div class="wf"><span class="wf-label">Content</span> — thread view, newest at bottom</div>
</div>
```

Stack the wireframe rows vertically on mobile (the `.wf-row` flex wraps or
switches to column under `md:`).

## Annotations

Number the regions and explain each in a list next to (or below) the
wireframe — don't scatter prose inside the boxes:

```html
<div class="wf"><span class="wf-label">③ Detail panel</span></div>
<ol class="annotations">
  <li>Toolbar stays fixed; everything else scrolls.</li>
  <li>Nav collapses to a bottom tab bar on mobile.</li>
  <li>Opens on row tap; bottom sheet on mobile, sidebar on desktop.</li>
</ol>
```

## States and variants

Show the states that drive the design decision — empty, loading, error, and the
mobile variant — as separate labeled wireframes on the same page. A mockup that
only shows the happy path on desktop hides the hard questions.
