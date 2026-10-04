# Server-rendered UI with vendored HTMX, no JavaScript build

Pages are rendered by FastAPI and Jinja, including the generated device artwork, the charts and the heatmap; filtering, grouping and sorting are Python functions. HTMX swaps parts of the page and listens to server-sent events for live updates, and roughly 100 lines of plain JavaScript handle the rest. HTMX and its SSE extension are vendored into `web/static/vendor/` with their versions in the file names, so the UI works on a LAN without a CDN. A single-page app was rejected because it would add a second toolchain to maintain for a dashboard that fits server rendering well.

## Consequences

- Device artwork is plain data (circles, strokes, fills) drawn by a Jinja macro, never HTML built in Python, so everything stays autoescaped.
- Upgrading HTMX means replacing the vendored files and the `<script>` paths in `base.html`.
