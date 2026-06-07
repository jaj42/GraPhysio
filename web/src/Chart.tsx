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
 * Feedback-loop guard: `setData(data, false)` keeps the x-scale fixed, but the
 * `setScale` hook still fires on our own programmatic scale changes. We debounce
 * and skip a fetch whose [t0, t1, px] matches the one already on screen.
 */
import { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

import { fetchWindow, type Curve, type Window } from './api';
import { wheelZoomPlugin } from './wheelZoom';

interface ChartProps {
  curves: Curve[];
  onStats?: (s: { points: number; ms: number }) => void;
}

const DEBOUNCE_MS = 120;

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

/** Min/max over all series, ignoring nulls — for fitting the y-scale to the view. */
function yExtent(ys: (number | null)[][]): [number, number] | null {
  let min = Infinity;
  let max = -Infinity;
  for (const col of ys) {
    for (const v of col) {
      if (v == null) continue;
      if (v < min) min = v;
      if (v > max) max = v;
    }
  }
  if (min > max) return null;
  if (min === max) return [min - 1, max + 1];
  const pad = (max - min) * 0.05;
  return [min - pad, max + pad];
}

export default function Chart({ curves, onStats }: ChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);
  const lastReq = useRef<{ t0: number; t1: number; px: number } | null>(null);
  const firstLoad = useRef(true);
  // Whether each fetch refits the y-scale to the visible data. Pan/wheel/reset keep
  // it on; box-zoom turns it off so its manual y-range isn't immediately clobbered.
  const autoFitY = useRef(true);
  const debounceId = useRef<number | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);
  const onStatsRef = useRef(onStats);
  onStatsRef.current = onStats;

  const namesKey = curves.map((c) => c.name).join('\n');
  const fullT0 = Math.min(...curves.map((c) => c.t0sec));
  const fullT1 = Math.max(...curves.map((c) => c.t1sec));

  useEffect(() => {
    if (!curves.length) return;
    const host = hostRef.current!;
    lastReq.current = null;
    firstLoad.current = true;
    autoFitY.current = true;

    const plotWidthPx = () => Math.max(1, Math.round(plotRef.current?.bbox.width ?? host.clientWidth));

    async function refetch(t0sec: number | null, t1sec: number | null) {
      const px = plotWidthPx();
      const t0 = t0sec ?? fullT0;
      const t1 = t1sec ?? fullT1;
      const prev = lastReq.current;
      if (prev && prev.t0 === t0 && prev.t1 === t1 && prev.px === px) return;
      lastReq.current = { t0, t1, px };

      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;

      const started = performance.now();
      try {
        const windows = await Promise.all(
          curves.map((c) => fetchWindow(c.name, t0sec, t1sec, px, ac.signal)),
        );
        const u = plotRef.current;
        if (!u) return;
        const { x, ys } = mergeWindows(windows);
        if (firstLoad.current) {
          // First paint: let uPlot establish valid scales from real data
          // (resetScales=true), then snap x to the exact full-curve bounds.
          u.setData([x, ...ys]);
          u.setScale('x', { min: fullT0, max: fullT1 });
          firstLoad.current = false;
        } else {
          u.setData([x, ...ys], false); // keep the user's x-scale
        }
        if (autoFitY.current) {
          const ext = yExtent(ys);
          if (ext) u.setScale('y', { min: ext[0], max: ext[1] });
        }
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

    function scheduleRefetch(t0: number | null, t1: number | null) {
      window.clearTimeout(debounceId.current);
      debounceId.current = window.setTimeout(() => refetch(t0, t1), DEBOUNCE_MS);
    }

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
      plugins: [
        wheelZoomPlugin({
          xMin: fullT0,
          xMax: fullT1,
          onAutoY: (auto) => {
            autoFitY.current = auto;
          },
        }),
      ],
      // Identity range on both scales: uPlot's *default* range pads/rounds the
      // min/max we set, so the displayed range would be wider than the window we
      // fetched data for (data filling only the middle). Passing min/max straight
      // through keeps displayed range == fetched range. (Identity reflects the
      // requested values, so unlike a constant range fn it does not pin/revert zoom.)
      scales: {
        x: { time: true, range: passthrough },
        y: { range: passthrough },
      },
      series,
      // Disable uPlot's built-in drag-zoom: the plugin owns all gestures (plain-drag
      // pan, shift-drag box-zoom), so the two can't fight over the same mousedown.
      cursor: { drag: { x: false, y: false } },
      hooks: {
        setScale: [
          (u: uPlot, key: string) => {
            if (key !== 'x') return;
            scheduleRefetch(u.scales.x.min!, u.scales.x.max!);
          },
        ],
      },
    };

    const u = new uPlot(opts, emptyData, host);
    plotRef.current = u;
    refetch(null, null); // first fetch seeds the scales (see firstLoad above)

    const ro = new ResizeObserver(() => {
      u.setSize({ width: host.clientWidth, height: Math.max(360, host.clientHeight) });
      scheduleRefetch(u.scales.x.min!, u.scales.x.max!);
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

  return <div ref={hostRef} style={{ width: '100%', height: '70vh' }} />;
}
