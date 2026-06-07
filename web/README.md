# GraPhysio web frontend

Phase 3 of the [web migration](../WEB_MIGRATION_PLAN.md): a **read-only** React +
uPlot viewer that proves the server-side-downsample → uPlot viewport loop is smooth
on real 125 Hz multi-hour data.

## How it works

The full curve never reaches the browser. On every zoom / pan / resize the chart
reads uPlot's visible x-range and pixel width, debounces, and asks the backend for a
min/max-decimated window of that exact range (`GET /curves/{name}/window`). The
response is Apache Arrow IPC, parsed straight into the typed arrays uPlot renders —
so the payload stays a few thousand points whether the curve is 1M or 100M samples.

- `src/api.ts` — backend client; Arrow parsing and the epoch-ns ↔ epoch-seconds
  conversion (the backend's int64-ns timestamps exceed JS's safe-integer range).
- `src/Chart.tsx` — the uPlot instance and the debounced viewport-fetch loop.
- `src/wheelZoom.ts` — wheel-zoom + drag-pan plugin (uPlot ships neither).
- `src/App.tsx` — load-a-file form, curve picker, decimation toggle, fetch stats.

## Run

Start the backend (from the repo root):

```bash
uv run --extra server uvicorn graphysio.server.app:app --reload
```

Then the frontend:

```bash
cd web
npm install
npm run dev          # http://localhost:5173
```

The frontend calls the backend at `http://localhost:8000` by default (CORS is open
for localhost). Override with `VITE_API_BASE`, e.g. `VITE_API_BASE=/api npm run dev`
to use the same-origin Vite proxy instead.

Load a file by entering a **server-side** path (the backend opens it directly), pick
a curve, then scroll to zoom, drag to pan, shift-drag to box-zoom, double-click to
reset.
