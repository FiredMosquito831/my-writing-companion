# Data Table

Filterable, sortable, searchable table. Use when the information is records with
columns. For ≤20 rows, a plain `<table>` with click-to-sort headers is less code
than any library — reach for Tabulator when the reader needs live filtering or
the rows outgrow a screen.

## Library

**Tabulator** — ~101 KB gzipped JS, ~4 KB CSS. Mature, zero dependencies,
virtual DOM rendering for large datasets.

```html
<link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6/dist/js/tabulator.min.js"></script>
```

## Minimal Example

```html
<input id="search" placeholder="Search..." oninput="applyFilter()">
<div id="table"></div>
<script>
const table = new Tabulator("#table", {
  data: [
    { name: "Parser", type: "code", score: 8 },
    { name: "Release docs", type: "docs", score: 5 },
  ],
  layout: "fitColumns",
  columns: [
    { title: "Name", field: "name", sorter: "string" },
    { title: "Type", field: "type", sorter: "string" },
    { title: "Score", field: "score", sorter: "number" },
  ],
});

function applyFilter() {
  const q = document.getElementById("search").value.toLowerCase();
  table.setFilter(row =>
    Object.values(row).join(" ").toLowerCase().includes(q)
  );
}

table.on("rowClick", (e, row) => {
  showDetail(row.getData().name);  // wire to detail panel
});
</script>
```

Handles 100–500 rows without pagination. For larger datasets, enable Tabulator's
virtual DOM rendering.
