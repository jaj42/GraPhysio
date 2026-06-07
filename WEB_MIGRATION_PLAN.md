# GraPhysio Web Migration Plan

> Converting GraPhysio from a PySide6/pyqtgraph desktop application into a web
> application, keeping the Python analytical backend and building a new,
> performant, extensible web frontend.
>
> Status: planning. Last updated 2026-06-05.

---

## 1. Context & Goals

GraPhysio is a Python GUI program that reads time series (biometric/physiological
signals) from many file formats, displays them, lets the user manipulate them
(filters, transformations, cycle/feet detection, manual point editing) and exports
the results.

**Goal:** turn it into a web application for easier deployment, keeping the Python
backend and adding a web frontend.

### Hard requirements

- **Performance.** Handles high-frequency data: multiple concurrent time series at
  125 Hz over several hours. That is roughly **1–5 million points per curve**,
  several curves at once. The frontend must stay smooth at this scale.
- **Flexibility / extensibility.** Adding new filters, transformations, readers and
  exporters must stay as easy as it is today (a one-line registry entry).

### Decisions taken (2026-06-05)

| Decision | Choice | Rationale |
|---|---|---|
| Deployment model | **Self-hosted, single / few users** | Simple in-memory per-session state, no heavy auth. |
| Frontend stack | **React + uPlot** (FastAPI backend) | Max flexibility + performance with full custom interactions. Preferred over Panel/Datashader (less frontend flexibility) and Plotly/Dash (struggles past ~100k points). |
| Interactivity | **Preserve ALL interactive editing** | POI selection/deletion, rubber-band region selection, manual cycle correction are essential — this is the reason uPlot was chosen over higher-level chart libraries. |

---

## 2. Current Architecture Assessment

### 2.1 Reusable as-is (Qt-free, pure pandas/numpy/scipy)

These become the web backend's compute layer essentially untouched:

- `readdata/` — CSV, parquet, parquet_dir, EDF, MNE, iceberg, dwc readers
- `writedata/` — exporters (csv, matlab, edf, parquet, ecgplot)
- `transformations/` — perfusion index, pulse transit/arrival time, feet⇄curve, etc.
- `algorithms/filters.py`, `algorithms/waveform.py` — signal processing
- `structures.py` — `PlotData`, `CycleId`, `Filter`, `Parameter`
- `physiocurve` (external dep) — cycle / foot / wave detection

**Key asset:** the `Filter` / `Parameter` / `Transformations` registries are *already
declarative schemas*. Example:

```python
"Savitzky-Golay": Filter(name="savgol", parameters=[
    Parameter("Window duration", "time"),
    Parameter("Polynomial order", int),
])
```

Today `dialogs.askUserValue()` renders that into a Qt dialog. In the web version the
**same registry** serializes to JSON and the frontend renders it into a form. The
menu tree in `plotwidgets/tsplot.py` (`self.menu`) is likewise declarative and maps
directly to web UI. Adding a filter/transform stays a one-line dict entry, with no
frontend change.

### 2.2 Must be rewritten (Qt-coupled)

- `plotwidgets/` — the plotting widgets
- `ui/` — generated Qt widgets / dialogs
- `dialogs.py` — Qt dialogs
- `mainui.py` — main window / tab management

**Watch out:** `plotwidgets/curves.py` defines `CurveItem(pg.PlotDataItem)` — the data
model and the renderer are fused into a single object. The migration splits this into
a plain **data object** (server-side) and a **renderer** (browser-side).

### 2.3 The one structural refactor needed in the core

`readdata/__init__.py` and each reader's `askUserInput()` currently import and call
into Qt `dialogs`. Decouple them: each reader exposes its `Parameter` list as data,
the caller (Qt dialog *or* web form) collects answers and feeds them back via
`set_data()`:

```
reader.get_param_schema()  ->  frontend renders form  ->  reader.set_data(answers)  ->  reader()
```

This is small and is the only structural surgery the core needs.

---

## 3. The Core Performance Problem & Solution

125 Hz × hours × several series ≈ millions of points per curve. You cannot ship that
to a browser as JSON and render it. pyqtgraph hides this today by auto-downsampling to
screen resolution **locally**; the web version must replicate that **server-side**.

### Viewport-aware min/max decimation

```
Frontend: "give me curve X over [t0, t1] at 1200 px wide"
Backend:  return ~2400 min/max-decimated points
          (min AND max per pixel-bucket — NOT averaging)
Frontend: render; on pan/zoom, re-request (debounced)
```

- **Min/max, not mean.** Averaging would erase the systolic/diastolic peaks that
  matter clinically. For each pixel-bucket emit the extreme samples.
- **Binary transfer.** Send **Apache Arrow IPC** (or raw `Float32`), never JSON.
  pyarrow is already a dependency; uPlot consumes typed arrays directly.
- **Result:** payload stays ~tens of KB regardless of whether the curve is 1M or 100M
  points. This single pattern is what makes the web app feel as fast as the desktop.

**Implementation (done):** `graphysio/core/downsample.py`, backed by the compiled
`tsdownsample` library (the engine behind plotly-resampler) rather than hand-rolled
numpy. Default method is **M4** (keeps min, max, first and last per bucket →
provably pixel-accurate line rendering); `minmax` is available for half the points.
We deliberately do *not* use `scipy.signal.decimate`: its anti-aliasing low-pass
smooths away the very peaks we need, it wants an integer factor (not pixel-adaptive),
and it returns filtered surrogate values instead of real recorded samples.
Benchmark: 1.8M samples (125 Hz × 4 h) → 6k points in ~5 ms; verified Qt-free.
API: `downsample_series(series, t0, t1, px, method)` and the `decimate_indices`
primitive. Tests in `tests/test_downsample.py`.

---

## 4. Target Repository Structure

Keep the desktop app working during migration by sharing the extracted core.

```
graphysio/
  core/                ← extracted, Qt-free (reusable backend)
    structures.py      (PlotData, CycleId, Filter, Parameter)
    readdata/          (decoupled from dialogs)
    writedata/
    transformations/
    algorithms/
    downsample.py      ← NEW: viewport min/max decimation
  desktop/             ← current Qt app (plotwidgets/, ui/, dialogs.py, mainui.py)
  server/              ← NEW: FastAPI app
    main.py
    session.py         (loaded PlotData, curves, POI indices; on-disk Arrow/Parquet)
    schema.py          (serialize Filter/Parameter/Transformations registries)
    routes/
web/                   ← NEW: React + uPlot frontend
```

---

## 5. Backend Design (FastAPI)

Single-user self-hosted → keep state simple: an in-memory **session** object holding
loaded `PlotData`, curves and POI indices. Persist the raw signal to an on-disk
**Arrow/Parquet** file per session (pyarrow already a dep) so RAM stays bounded and
min/max window queries are fast.

### Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /files` + `GET /files/{id}/schema` | upload file, return the reader's `Parameter` schema |
| `POST /curves` | load with answered params → returns curve metadata (name, t-range, samplerate) |
| `GET /curves/{name}/window?t0&t1&px` | **min/max-decimated** window as **Arrow binary** |
| `POST /curves/{name}/filter` / `/transform` | run `algorithms.filters` / `transformations`, return new curve metadata |
| `POST /curves/{name}/feet` | cycle detection (`addFeet` logic → `physiocurve`) |
| `GET` / `PATCH /curves/{name}/poi` | fetch / edit POI indices (manual editing) |
| `GET /filters`, `GET /transforms` | serialized registries → drive frontend menus/forms |
| `POST /export` | reuse `writedata` exporters |

### WebSocket channel

Add a WebSocket for POI edits and long-running ops (large-file load, heavy
transforms) so the UI streams progress instead of blocking on HTTP.

---

## 6. Frontend Design (React + uPlot)

- **uPlot** for the waveform canvas — handles millions of points and exposes the
  low-level hooks needed for custom interaction.
- **Viewport → fetch loop:** on zoom/pan read uPlot's x-range + pixel width, debounce,
  fetch the decimated window, swap in the typed arrays.
- **POI layer:** render feet / systole / diastole / wave markers as a uPlot overlay
  (second series or custom draw hook). Click-to-select, shift-drag rubber-band,
  Delete-to-remove → uPlot mouse hooks calling `PATCH /poi`. Heaviest frontend piece,
  and the main reason uPlot beats Plotly here (raw mouse/canvas control).
- **Region selection** (the "new plot from selection" feature) → uPlot's built-in
  select rectangle → posts the `[t0, t1]` range.
- **State:** React Query for the server cache + a light store (e.g. Zustand) for the
  curve/tab model mirroring today's tabbed `mainui`.
- **Forms:** a generic `<ParamForm schema={...}>` component renders any `Parameter`
  list — the web analog of `askUserValue`'s type switch
  (`int` / `float` / `time` / `datetime` / list / `str`).

---

## 7. Phased Roadmap

### Phase 0 — Vertical slice (derisk performance first)

The biggest unknown is whether server-side-downsample → uPlot feels as smooth as
pyqtgraph on real data. Build a thin end-to-end slice before anything else:

1. `graphysio/core/downsample.py` — min/max decimation + tests against a synthetic
   waveform proving peaks survive.
2. Minimal FastAPI app exposing `GET /curves/{name}/window` returning Arrow binary.
3. A bare uPlot page loading one real multi-hour curve end to end.

Built alongside the existing app without touching desktop code. If it's fast,
the rest is wiring; if not, we learn it on day one.

### Phase 1 — Extract the Qt-free core

- Move reusable modules into `graphysio/core/`.
- Decouple readers from `dialogs` (the `get_param_schema()` / `set_data()` refactor).
- Keep the desktop app running on the new core.

### Phase 2 — FastAPI skeleton

- File load → curve list → the windowed Arrow endpoint. Prove the data path.

### Phase 3 — React + uPlot read-only viewer

- Implement the viewport-fetch loop. Validate performance on real 125 Hz multi-hour
  data.

### Phase 4 — Filters / transforms / export

- Drive menus and forms from the serialized registries via `<ParamForm>`.
- Wire filter/transform/export endpoints to the existing `algorithms` / `writedata`.

### Phase 5 — POI detection + manual editing

- Cycle/feet detection endpoints (`physiocurve`).
- The interaction-heavy editing layer (select / delete / manual correction).

### Phase 6 — Polish

- Spectrogram, PU-loops, multi-tab workspace, and remaining desktop features.

---

## 8. Open Design Questions (to settle as we go)

- Exact session lifecycle / cleanup policy for on-disk Arrow files.
- Whether to keep the desktop app long-term or retire it once the web app reaches
  parity.
- Auth/hardening if the "single user" assumption ever changes to multi-user.
- Concurrency model for heavy transforms (background workers vs. inline async).
