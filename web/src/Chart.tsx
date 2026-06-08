/**
 * uPlot chart with the viewport-fetch loop — the core of Phase 3.
 *
 * The full curves are never shipped to the browser. Whenever the visible x-range
 * changes (zoom, pan, resize) we ask the backend for an M4-decimated window of
 * *each* curve, sized to the plot's pixel width, and swap the arrays in. This is
 * the server-side equivalent of pyqtgraph's local auto-downsampling.
 *
 * All curves share one overlaid plot (one x-axis). Since each curve is sampled and
 * decimated independently, their timestamps don't line up, so we merge the windows
 * onto a union-x axis and mark the gaps `null`; `spanGaps` makes each series draw a
 * continuous line through its own real samples, ignoring the foreign timestamps.
 *
 * ── Unified view model ──────────────────────────────────────────────────────────
 * There is ONE source of truth for the viewport: `view` = { x0, x1, yMode }, where
 * yMode is either 'auto' (y refits the visible, *shown* data on every fetch) or
 * 'manual' (an explicit y-range, set by a box-zoom, that pans/zooms preserve). Every
 * gesture (pan, wheel, box-zoom, dbl-click reset, resize) does the same two things
 * through `applyView`: (1) set the scale(s) immediately for a responsive feel, and
 * (2) schedule a single debounced refetch for the new x-window. The fetch is driven
 * *directly* from here — not from uPlot's setScale hook — so there is no feedback
 * loop and no per-gesture special-casing. This is what keeps pan / zoom / dbl-click
 * consistent (they were diverging when each mutated scales + autofit on its own).
 */
import { useEffect, useRef, useState } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

import { fetchWindow, type Curve, type Window } from './api';
import { wheelZoomPlugin, type ViewController } from './wheelZoom';

interface ChartProps {
  curves: Curve[];
  onStats?: (s: { points: number; ms: number }) => void;
}

const DEBOUNCE_MS = 120;

// The viewport: x-window plus how the y-axis is governed.
type View =
  | { x0: number; x1: number; yMode: 'auto' }
  | { x0: number; x1: number; yMode: 'manual'; y0: number; y1: number };

// Distinguishable line colors, cycled across curves.
const PALETTE = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2', '#ca8a04', '#db2777'];

// Identity scale range: use exactly the min/max we set, with no uPlot padding. The
// [0,1] fallback only matters for the brief empty-data moment before the first fetch.
const passthrough = (_u: uPlot, min: number, max: number): [number, number] =>
  Number.isFinite(min) && Number.isFinite(max) ? [min, max] : [0, 1];

/** Merge per-curve windows onto a shared, sorted union-x axis (gaps -> null). */
function mergeWindows(windows: Window[]): { x: number[]; ys: (number | null)[][] } {
  let total = 0;
  for (const w of windows) total += w.x.length;

  const flat = new Float64Array(total);
  let k = 0;
  for (const w of windows) {
    flat.set(w.x, k);
    k += w.x.length;
  }
  flat.sort(); // typed-array sort is numeric

  const x: number[] = [];
  for (let i = 0; i < flat.length; i++) {
    if (i === 0 || flat[i] !== flat[i - 1]) x.push(flat[i]);
  }
  const index = new Map<number, number>();
  for (let i = 0; i < x.length; i++) index.set(x[i], i);

  const ys = windows.map((w) => {
    const col: (number | null)[] = new Array(x.length).fill(null);
    for (let i = 0; i < w.x.length; i++) col[index.get(w.x[i])!] = w.y[i];
    return col;
  });
  return { x, ys };
}

/**
 * Fit the y-scale to the data currently in uPlot that falls within [x0, x1],
 * ignoring nulls AND series the user has hidden via the legend (`series.show ===
 * false`). Reading from `u.data` (the points already in memory) lets us refit y
 * *live* during a pan/wheel gesture — before the debounced refetch lands — so y
 * tracks the visible data instead of lagging a frame behind on the old window.
 * If no loaded point falls in range (e.g. panning into a not-yet-fetched region),
 * we leave y untouched until the fetch fills it in.
 */
function refitY(u: uPlot, x0: number, x1: number): void {
  const xs = u.data[0] as number[];
  let min = Infinity;
  let max = -Infinity;
  for (let s = 1; s < u.data.length; s++) {
    if (u.series[s]?.show === false) continue; // skip legend-hidden curves
    const col = u.data[s] as (number | null)[];
    for (let i = 0; i < xs.length; i++) {
      if (xs[i] < x0 || xs[i] > x1) continue;
      const v = col[i];
      if (v == null) continue;
      if (v < min) min = v;
      if (v > max) max = v;
    }
  }
  if (min > max) return; // nothing loaded in range — keep current y
  if (min === max) {
    u.setScale('y', { min: min - 1, max: max + 1 });
    return;
  }
  const pad = (max - min) * 0.05;
  u.setScale('y', { min: min - pad, max: max + pad });
}

export default function Chart({ curves, onStats }: ChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);
  const view = useRef<View>({ x0: 0, x1: 1, yMode: 'auto' });
  const lastReq = useRef<{ x0: number; x1: number; px: number } | null>(null);
  const firstLoad = useRef(true);
  const debounceId = useRef<number | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);
  const onStatsRef = useRef(onStats);
  onStatsRef.current = onStats;

  const namesKey = curves.map((c) => c.name).join('\n');
  const fullT0 = Math.min(...curves.map((c) => c.t0sec));
  const fullT1 = Math.max(...curves.map((c) => c.t1sec));

  // Per-curve visibility, driven by the custom legend. Reset when the set of curves
  // changes. Showing/hiding a curve must leave the current zoom exactly as it was.
  const [visible, setVisible] = useState<boolean[]>(() => curves.map(() => true));
  useEffect(() => {
    setVisible(curves.map(() => true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey]);

  function toggleCurve(i: number) {
    const u = plotRef.current;
    const next = !(visible[i] ?? true);
    if (u) {
      // uPlot's setSeries re-evaluates the scales and resets them (to the data
      // range, or to non-finite -> our [0,1] fallback when it momentarily sees no
      // data) even with auto:false — which jumps the zoom. Snapshot the scales and
      // restore them right after; uPlot batches both into one frame, so no flicker.
      const xMin = u.scales.x.min!;
      const xMax = u.scales.x.max!;
      const yMin = u.scales.y.min!;
      const yMax = u.scales.y.max!;
      u.setSeries(i + 1, { show: next }); // series 0 is the x-axis
      u.setScale('x', { min: xMin, max: xMax });
      u.setScale('y', { min: yMin, max: yMax });
    }
    setVisible((vis) => {
      const copy = vis.slice();
      copy[i] = next;
      return copy;
    });
  }

  useEffect(() => {
    if (!curves.length) return;
    const host = hostRef.current!;
    lastReq.current = null;
    firstLoad.current = true;
    view.current = { x0: fullT0, x1: fullT1, yMode: 'auto' };

    const plotWidthPx = () => Math.max(1, Math.round(plotRef.current?.bbox.width ?? host.clientWidth));

    /** Fetch the decimated window for the *current* view and swap it in. */
    async function fetchView() {
      const u = plotRef.current;
      if (!u) return;
      const v = view.current;
      const px = plotWidthPx();
      const prev = lastReq.current;
      if (prev && prev.x0 === v.x0 && prev.x1 === v.x1 && prev.px === px) return;
      lastReq.current = { x0: v.x0, x1: v.x1, px };

      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;

      // null t0/t1 == full curve: avoids ns->sec->ns rounding at the exact bounds.
      const t0arg = v.x0 <= fullT0 ? null : v.x0;
      const t1arg = v.x1 >= fullT1 ? null : v.x1;

      const started = performance.now();
      try {
        const windows = await Promise.all(
          curves.map((c) => fetchWindow(c.name, t0arg, t1arg, px, ac.signal)),
        );
        if (!plotRef.current) return;
        const { x, ys } = mergeWindows(windows);
        if (firstLoad.current) {
          // First paint: let uPlot establish valid scales from real data
          // (resetScales=true), then snap to the exact requested bounds below.
          u.setData([x, ...ys]);
          firstLoad.current = false;
        } else {
          u.setData([x, ...ys], false); // keep the user's scales
        }
        u.setScale('x', { min: v.x0, max: v.x1 }); // exact x bounds, no uPlot pad
        if (view.current.yMode === 'auto') refitY(u, v.x0, v.x1);
        const points = windows.reduce((s, w) => s + w.points, 0);
        onStatsRef.current?.({ points, ms: Math.round(performance.now() - started) });
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          // eslint-disable-next-line no-console
          console.error('window fetch failed', err);
          lastReq.current = prev; // allow a retry on the next interaction
        }
      }
    }

    function scheduleFetch() {
      window.clearTimeout(debounceId.current);
      debounceId.current = window.setTimeout(fetchView, DEBOUNCE_MS);
    }

    /**
     * The single entry point for changing the viewport. Updates the view model,
     * applies the scales now (responsive), and schedules one refetch. Every gesture
     * goes through here, so pan / zoom / box / reset can't drift apart.
     */
    function applyView(next: View) {
      view.current = next;
      const u = plotRef.current;
      if (u) {
        u.setScale('x', { min: next.x0, max: next.x1 });
        // Refit y live from the points already loaded so y doesn't lag the gesture;
        // the debounced fetch then refines it. Box-zoom sets its own explicit y.
        if (next.yMode === 'manual') u.setScale('y', { min: next.y0, max: next.y1 });
        else refitY(u, next.x0, next.x1);
      }
      scheduleFetch();
    }

    const controller: ViewController = {
      pan: (x0, x1, y0, y1) => {
        const cur = view.current;
        // 2D pan only when the user is already navigating an explicit (box-zoomed)
        // y-range; in auto mode y stays owned by the auto-fit, so pan x only.
        if (cur.yMode === 'manual') applyView({ x0, x1, yMode: 'manual', y0, y1 });
        else applyView({ x0, x1, yMode: 'auto' });
      },
      zoomXY: (x0, x1, y0, y1) => applyView({ x0, x1, yMode: 'manual', y0, y1 }),
      reset: () => applyView({ x0: fullT0, x1: fullT1, yMode: 'auto' }),
    };

    const series: uPlot.Series[] = [
      {},
      ...curves.map((c, i) => ({
        label: c.name,
        stroke: PALETTE[i % PALETTE.length],
        width: 1,
        spanGaps: true,
        points: { show: false },
      })),
    ];
    const emptyData: uPlot.AlignedData = [[], ...curves.map(() => [])];

    const opts: uPlot.Options = {
      width: host.clientWidth,
      height: Math.max(360, host.clientHeight),
      plugins: [wheelZoomPlugin({ xMin: fullT0, xMax: fullT1, controller })],
      // `auto: false` on BOTH scales: uPlot's built-in auto-ranging otherwise
      // re-fits y to the full data extent on every x-scale change (i.e. on every
      // pan/wheel step), fighting our own refitY and causing a transiently-wrong y
      // during the gesture. With auto off, the scales are *only* whatever we set via
      // setScale — x from the view model, y from refitY. The identity `range` fn
      // then keeps displayed bounds == the exact values we set (uPlot's default
      // range otherwise pads/rounds them, leaving data filling only the middle).
      scales: {
        x: { time: true, auto: false, range: passthrough },
        y: { auto: false, range: passthrough },
      },
      series,
      // We render our own vertical legend to the right (see below). uPlot's built-in
      // legend sits underneath, streams cursor values (constant flicker) and rescales
      // the view when a series is toggled — all unwanted here.
      legend: { show: false },
      // Disable uPlot's built-in drag-zoom: the plugin owns all gestures (plain-drag
      // pan, shift-drag box-zoom), so the two can't fight over the same mousedown.
      cursor: { drag: { x: false, y: false } },
    };

    const u = new uPlot(opts, emptyData, host);
    plotRef.current = u;
    fetchView(); // first fetch seeds the scales (see firstLoad above)

    const ro = new ResizeObserver(() => {
      u.setSize({ width: host.clientWidth, height: Math.max(360, host.clientHeight) });
      scheduleFetch(); // px changed -> re-decimate at the new width
    });
    ro.observe(host);

    return () => {
      window.clearTimeout(debounceId.current);
      abortRef.current?.abort();
      ro.disconnect();
      u.destroy();
      plotRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey]);

  return (
    <div style={styles.wrap}>
      <div ref={hostRef} style={styles.plot} />
      <ul style={styles.legend}>
        {curves.map((c, i) => {
          const on = visible[i] ?? true;
          return (
            <li key={c.name} style={styles.item} onClick={() => toggleCurve(i)} title={c.name}>
              <span style={{ ...styles.swatch, background: PALETTE[i % PALETTE.length], opacity: on ? 1 : 0.3 }} />
              <span style={{ ...styles.label, opacity: on ? 1 : 0.4, textDecoration: on ? 'none' : 'line-through' }}>
                {c.name}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: 'flex', gap: 12, width: '100%', height: '70vh' },
  plot: { flex: 1, minWidth: 0, height: '100%' },
  legend: {
    width: 180,
    flexShrink: 0,
    overflowY: 'auto',
    margin: 0,
    padding: '0 0 0 10px',
    listStyle: 'none',
    borderLeft: '1px solid #e5e7eb',
    fontSize: 13,
  },
  item: { display: 'flex', alignItems: 'center', gap: 8, padding: '3px 4px', cursor: 'pointer', userSelect: 'none', borderRadius: 4 },
  swatch: { width: 16, height: 4, borderRadius: 1, flexShrink: 0 },
  label: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
};
