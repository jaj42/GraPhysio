/**
 * uPlot chart with the viewport-fetch loop — the core of Phase 3.
 *
 * The full curve is never shipped to the browser. Instead, whenever the visible
 * x-range changes (zoom, pan, resize), we ask the backend for a min/max-decimated
 * window sized to the plot's pixel width and swap the typed arrays in. This is the
 * server-side equivalent of pyqtgraph's local auto-downsampling.
 *
 * Feedback-loop guard: `setData(data, false)` keeps the x-scale fixed, but the
 * `setScale` hook still fires on our own programmatic scale changes. We debounce
 * and skip a fetch whose [t0, t1, px] matches the one already on screen.
 */
import { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

import { fetchWindow, type Curve, type Method } from './api';
import { wheelZoomPlugin } from './wheelZoom';

interface ChartProps {
  curve: Curve;
  method: Method;
  onStats?: (s: { points: number; ms: number }) => void;
}

const DEBOUNCE_MS = 120;

export default function Chart({ curve, method, onStats }: ChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);
  // Last range/width we fetched, to suppress redundant requests.
  const lastReq = useRef<{ t0: number; t1: number; px: number } | null>(null);
  const debounceId = useRef<number | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);

  // Keep the latest method/callback accessible inside the long-lived plot hooks.
  const methodRef = useRef(method);
  methodRef.current = method;
  const onStatsRef = useRef(onStats);
  onStatsRef.current = onStats;

  // (Re)build the plot when the selected curve changes.
  useEffect(() => {
    const host = hostRef.current!;
    lastReq.current = null;

    const plotWidthPx = () => Math.max(1, Math.round(plotRef.current?.bbox.width ?? host.clientWidth));

    async function refetch(t0sec: number | null, t1sec: number | null) {
      const px = plotWidthPx();
      const t0 = t0sec ?? curve.t0sec;
      const t1 = t1sec ?? curve.t1sec;
      const prev = lastReq.current;
      if (prev && prev.t0 === t0 && prev.t1 === t1 && prev.px === px) return;
      lastReq.current = { t0, t1, px };

      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;

      const started = performance.now();
      try {
        const w = await fetchWindow(curve.name, t0sec, t1sec, px, methodRef.current, ac.signal);
        const u = plotRef.current;
        if (!u) return;
        u.setData([w.x, w.y], false); // false: keep the current x-scale, don't auto-range
        onStatsRef.current?.({ points: w.points, ms: Math.round(performance.now() - started) });
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

    const opts: uPlot.Options = {
      title: curve.name,
      width: host.clientWidth,
      height: Math.max(320, host.clientHeight),
      plugins: [wheelZoomPlugin()],
      scales: {
        x: { time: true, range: () => [curve.t0sec, curve.t1sec] as [number, number] },
      },
      series: [
        {},
        { label: curve.name, stroke: '#2563eb', width: 1, points: { show: false } },
      ],
      cursor: { drag: { x: true, y: false } },
      hooks: {
        setScale: [
          (u: uPlot, key: string) => {
            if (key !== 'x') return;
            scheduleRefetch(u.scales.x.min!, u.scales.x.max!);
          },
        ],
      },
    };

    const u = new uPlot(opts, [new Float64Array(0), new Float64Array(0)], host);
    plotRef.current = u;

    // Initial full-range load.
    refetch(null, null);

    const ro = new ResizeObserver(() => {
      u.setSize({ width: host.clientWidth, height: Math.max(320, host.clientHeight) });
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
  }, [curve.name]);

  // Re-fetch with the new decimation method without rebuilding the plot. Clearing
  // lastReq defeats the dedupe guard so the same range is fetched again.
  useEffect(() => {
    const u = plotRef.current;
    if (!u || !lastReq.current) return;
    lastReq.current = null;
    u.setScale('x', { min: u.scales.x.min!, max: u.scales.x.max! });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [method]);

  return <div ref={hostRef} style={{ width: '100%', height: '70vh' }} />;
}
