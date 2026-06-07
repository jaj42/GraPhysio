# GraPhysio web frontend

Phase 3 of the [web migration](../WEB_MIGRATION_PLAN.md): a **read-only** React +
uPlot viewer that proves the server-side-downsample → uPlot viewport loop is smooth
on real 125 Hz multi-hour data.

## How it works

The full curves never reach the browser. On every zoom / pan / resize the chart
reads uPlot's visible x-range and pixel width, debounces, and asks the backend for an
M4-decimated window of that exact range (`GET /curves/{name}/window`) for each curve.
The response is Apache Arrow IPC, parsed straight into the typed arrays uPlot renders
— so the payload stays a few thousand points per curve whether it's 1M or 100M
samples. Decimation is always M4 (pixel-accurate); it is deliberately not a user
option.

Flow: **New Plot menu → pick a source → (browse for a path if needed) → answer the
reader's parameter schema → all of the resulting curves are shown overlaid** in one
pan/zoomable plot. Sources are a file, or a live source (DWC / Iceberg) or a parquet
directory — `GET /sources` lists whatever the backend has installed; file & directory
sources open the browser, the rest go straight to the parameter form.

- `src/api.ts` — backend client; Arrow parsing and the epoch-ns ↔ epoch-seconds
  conversion (the backend's int64-ns timestamps exceed JS's safe-integer range).
- `src/FileBrowser.tsx` — server-side file/folder picker driven by `GET /browse` (the
  native file dialog can't hand the page a server path, and the data already lives
  on the self-hosted box, so we navigate the server's filesystem instead of
  uploading). Has a directory-select mode for parquet-directory sources.
- `src/ParamForm.tsx` — generic renderer for a reader's `ParamSpec` schema (the web
  analog of the desktop's `askUserValue`); drives the staged `POST /files` →
  `POST /files/{id}` load. Phase 4 reuses it for filter/transform forms.
- `src/Chart.tsx` — the uPlot instance and the debounced viewport-fetch loop. All
  curves overlay on one shared x-axis; since each is decimated independently, the
  windows are merged onto a union-x axis with `spanGaps` so each line still draws
  through its own real samples.
- `src/wheelZoom.ts` — wheel-zoom + drag-pan + double-click-reset plugin (uPlot
  ships none of these for a continuously re-fetched viewport).
- `src/App.tsx` — orchestrates browse → param form → overlaid view; shows fetch
  stats (`points · ms`).

## Run

Start the backend (from the repo root). `GRAPHYSIO_DATA_ROOT` sets the directory the
file browser is confined to (default: your home directory):

```bash
GRAPHYSIO_DATA_ROOT=/path/to/data uv run --extra server \
    uvicorn graphysio.server.app:app --reload
# or: uv run poe web-back   (uses the default data root)
```

Then the frontend:

```bash
cd web
npm install
npm run dev          # http://localhost:5173
# or, from the repo root: uv run poe web-front
```

The frontend calls the backend at `http://localhost:8000` by default (CORS is open
for localhost). Override with `VITE_API_BASE`, e.g. `VITE_API_BASE=/api npm run dev`
to use the same-origin Vite proxy instead.

In the app: click **New Plot**, choose a source (e.g. File), browse to a file and
click it, answer the load form (e.g. encoding, which columns, which time index), then
scroll to zoom, drag to pan, shift-drag to box-zoom, double-click to reset.
