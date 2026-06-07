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

### Phase 1 — Extract the Qt-free core  ✅ DONE (reader decoupling)

- Reader decoupling complete: all readers (`csv, parquet, parquet_dir, edf, mne,
  iceberg, dwc, excel`) import **Qt-free** and expose a declarative
  `get_params() -> list[ParamSpec]` schema instead of opening Qt dialogs.
- `graphysio/core/params.py`: `ParamSpec` (name/label/kind/choices/default/required,
  `to_dict` for JSON) + `default_answers()` + `gather()` staged driver.
- `readdata/baseclass.py`: Qt-free `BaseReader` (`set_data`/`get_params`/`__call__`,
  `get_plotdata` alias). `readdata/__init__.py` Qt-free (file dialog imported lazily).
- Desktop adapter in `dialogs.py`: `ask_params_qt()` renders a `ParamSpec` list with
  Qt dialogs; `drive_reader_qt()` drives any reader (CSV/DWC keep their bespoke rich
  dialogs; `DlgNewPlotCsv` moved here from `csv.py`). `mainui.py` wired to it; desktop
  still works.
- Server now uses the **real readers** (`server/loaders.py`: `make_reader` +
  `plotdata_to_curves`), so all four file formats (parquet/edf/mne/csv) are supported.
  New staged endpoints `POST /files` (schema) + `POST /files/{id}` (answers→curves);
  `POST /session/load` kept as default-answer one-shot.
- Tests: `tests/test_readers.py` (5) + staged-flow tests in `test_server.py`. Full
  suite 35 passing. Whole server import chain re-verified Qt-free.
- Multi-step prompting supported (iceberg: connection → columns) via repeated
  `get_params()`.
- DEFERRED: moving the rest of the analytical modules (`transformations/`,
  `algorithms/`, `writedata/`) physically under `graphysio/core/` — they are already
  Qt-free in place; the move is cosmetic and can happen later.

### Phase 2 — FastAPI skeleton  ✅ DONE

- File load → curve list → the windowed Arrow endpoint. Data path proven.
- `graphysio/server/`: `app.py` (FastAPI), `session.py` (in-memory `SessionStore`
  + `CurveMeta`), `loaders.py` (Qt-free parquet/CSV loaders), `arrow.py` (Arrow IPC).
- Endpoints: `GET /health`, `POST /session/load`, `GET /curves`,
  `GET /curves/{name}/window?t0&t1&px&method`, `DELETE /session`.
- Window endpoint returns Arrow IPC (`t` int64-ns, `v` float64), decimated via
  `core.downsample`. Verified Qt-free; 8 server tests in `tests/test_server.py`.
- Added `graphysio/core/timeseries.py` (`estimate_samplerate`, Qt-free clone of the
  one stuck in the Qt-importing `utils.py`).
- Deps: `server` optional extra (fastapi, uvicorn[standard], pyarrow); httpx (dev).
- Run: `uvicorn graphysio.server.app:app --reload`.
- NOTE: the original bespoke minimal loaders were REPLACED in Phase 1 — the server
  now uses the real `graphysio.readdata` readers (parquet/edf/mne/csv) via the
  param-schema flow.

### Phase 3 — React + uPlot read-only viewer  ✅ DONE

- New `web/` frontend: **Vite + React + TypeScript + uPlot** (read-only viewer).
- **Viewport-fetch loop** implemented in `web/src/Chart.tsx`: on zoom/pan/resize it
  reads uPlot's visible x-range + plot pixel width, debounces (120 ms), and fetches a
  min/max-decimated window of that exact range. `setData(data, false)` swaps the typed
  arrays without auto-ranging; a `{t0,t1,px}` dedupe guard + AbortController defeat the
  `setScale`-hook feedback loop and cancel stale in-flight requests.
- `web/src/api.ts` is the backend boundary: parses the Arrow IPC window
  (`apache-arrow` JS) straight into `Float64Array` pairs uPlot renders, and converts
  the backend's **int64 epoch-ns ↔ epoch-seconds** (ns exceeds JS safe-int; uPlot's
  time axis wants seconds). Talks to the backend directly via CORS (configurable
  `VITE_API_BASE`, default `http://localhost:8000`; `/api` Vite proxy alternative).
- `web/src/wheelZoom.ts`: the plugin **owns all gestures** (uPlot's built-in
  `cursor.drag` is turned off so the two can't fight over the same mousedown — that
  conflict made a plain drag both zoom and pan): plain-drag **pan**, shift-drag **2D
  box-zoom** (sets x *and* y, with a live `setSelect` rectangle), wheel **zoom**,
  double-click **reset to the full curve** (not the decimated-window extent).
- **uPlot scale-range caveats (each cost a bug):** (1) a *constant* `scales.x.range`
  fn *pins* the scale (uPlot calls it inside `setScale`) and reverts every zoom — but
  (2) *no* range fn is also wrong, because uPlot's default range *pads/rounds* the
  min/max you set, so the displayed range ends up wider than the window you fetched →
  data fills only the middle ("xrange off"). FIX: an **identity** range fn
  `(_u,min,max)=>[min,max]` on **both** axes — exact bounds, no pad, no pin. (3)
  Blank-on-first-load: `setScale` on *empty* data doesn't take effect; seed scales
  from the first real fetch via `setData(data)` (resetScales) then snap x.
- Decimation is **always M4** — no user toggle (deliberately; fewer knobs).
- **All curves shown overlaid** on one shared x-axis (no curve dropdown). Since each
  curve is decimated independently, `Chart.tsx` merges the per-curve windows onto a
  union-x axis with `spanGaps` so each line draws through its own real samples. The
  y-scale auto-fits the visible data each fetch (`autoFitY` flag), *except* after a
  box-zoom, which sets y explicitly and disables auto-fit until the next pan/wheel/
  reset. (Trade-off the user accepted: very different units, e.g. ABP mmHg vs ECG mV,
  share one y-axis.)
- **Server-side file picker** (`web/src/FileBrowser.tsx` + backend `GET /browse`,
  `graphysio/server/browse.py`): the native file dialog can't give the page a server
  path and the data already lives on the box, so the user navigates the *server's*
  filesystem (confined to `GRAPHYSIO_DATA_ROOT`, default `$HOME`; `..`-escape blocked
  → 403; hidden dotfiles/dotdirs and unsupported extensions filtered out) and clicks a
  file. No upload.
- **`<ParamForm>` pulled forward from Phase 4** (`web/src/ParamForm.tsx`): generic
  renderer for a reader's `ParamSpec` schema (choice/multichoice/int/float/bool/time/
  datetime/str), driving the staged `POST /files` → `POST /files/{id}` load. So CSV
  (which needs time-column/sample-rate choices) and parquet (column/index) now load
  interactively, not just self-describing formats. This is the same component Phase 4
  will use for filter/transform forms.
- `web/src/App.tsx`: orchestrates browse → param form (staged, multi-stage capable) →
  overlaid view; live `points · ms` fetch stats. `web/README.md` documents running it.
- **Validated** (backend, via TestClient) on a 2 h × 125 Hz × 2-curve parquet (900k
  samples each): browse → staged open (`columns` multichoice + `index` choice) → both
  curves load → multi-curve windows decimate correctly (full → 4800 pts/curve, 10 s
  zoom → 1251 pts), peaks preserved. `npm run build` (tsc + vite) green; **44 backend
  tests pass** (browse, sources, CSV-staging tests in `tests/test_server.py`). The
  uPlot interaction fixes above were reasoned + compiled, then confirmed by the user
  in the live app (no headless browser available in this env to automate canvas
  gestures).
- **"New Plot" source menu** (`GET /sources`, `graphysio/server/sources.py`): loading
  from a file is one source among several. The menu lists `file` plus any installed
  live sources — `dwc`, `iceberg` (pure param-form sources, no path) and `parquet_dir`
  (needs a *folder*, so `FileBrowser` has a directory-select mode). `POST /sources/{id}`
  registers the non-file reader and rides the same staged `POST /files/{id}` answer
  flow. The browser appears only for `file`/`directory` sources.
- **CSV staged-load fix**: the CSV reader read its header with hard-coded UTF-8 inside
  `get_params()` — *before* the encoding could be answered — so a latin1 file (e.g. a
  `µ`/0xb5 byte) crashed on click. `readdata/csv.py` now stages: stage 1 asks
  encoding/separator/decimal/skip-lines (no file read → can't decode-error); stage 2,
  once the encoding is known, reads the header and offers the columns/time setup. The
  desktop is unaffected (it uses the bespoke `DlgNewPlotCsv`, which `drive_reader_qt`
  special-cases and which bypasses `get_params`).
- DEFERRED: browser file *upload* (for ad-hoc local files not on the server); a
  per-curve y-axis / stacked option if shared-y overlay proves unreadable in practice.

### Phase 4 — Filters / transforms / export

- `<ParamForm>` already exists (built in Phase 3); reuse it for filter/transform forms.
- Add `GET /filters`, `GET /transforms` to serialize the registries → drive menus.
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
