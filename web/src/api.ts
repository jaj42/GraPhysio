/**
 * Thin client for the GraPhysio FastAPI backend.
 *
 * Two boundary concerns live here so the rest of the app stays oblivious:
 *
 *  - **Time units.** The backend speaks int64 epoch-*nanoseconds* (its pandas
 *    index dtype). Those values (~1.75e18 today) exceed JS's safe-integer range,
 *    and uPlot's time axis wants epoch-*seconds*. We convert at this boundary:
 *    seconds (float) for everything frontend-facing, ns (rounded) when calling
 *    the backend. Sub-second precision survives; we never carry raw ns as Number.
 *
 *  - **Binary transfer.** The window endpoint returns Apache Arrow IPC, not JSON.
 *    We parse it into the `[x[], y[]]` typed-array pair uPlot consumes directly.
 */
import { tableFromIPC } from 'apache-arrow';

const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000').replace(/\/$/, '');

export const NS_PER_SEC = 1e9;
export const nsToSec = (ns: number | bigint): number => Number(ns) / NS_PER_SEC;
export const secToNs = (sec: number): number => Math.round(sec * NS_PER_SEC);

/** Curve metadata as returned by `GET /curves` (timestamps in epoch-ns). */
export interface CurveMeta {
  name: string;
  t0: number;
  t1: number;
  n_samples: number;
  samplerate: number;
}

/** Like {@link CurveMeta} but with the time range pre-converted to seconds. */
export interface Curve extends CurveMeta {
  t0sec: number;
  t1sec: number;
}

export type Method = 'm4' | 'minmax';

/** A decimated window: parallel x (epoch-seconds) / y arrays, uPlot-ready. */
export interface Window {
  x: Float64Array;
  y: Float64Array;
  /** Points actually returned by the server (`X-Points` header). */
  points: number;
}

async function failOn(res: Response): Promise<never> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    if (body?.detail) detail = body.detail;
  } catch {
    /* non-JSON error body */
  }
  throw new Error(`${res.status} ${detail}`);
}

/** Load a server-side file into the session and return its curves. */
export async function loadFile(path: string): Promise<Curve[]> {
  const res = await fetch(`${API_BASE}/session/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!res.ok) await failOn(res);
  const body: { curves: CurveMeta[] } = await res.json();
  return body.curves.map(withSeconds);
}

/** List the curves currently loaded in the session. */
export async function listCurves(): Promise<Curve[]> {
  const res = await fetch(`${API_BASE}/curves`);
  if (!res.ok) await failOn(res);
  const metas: CurveMeta[] = await res.json();
  return metas.map(withSeconds);
}

/**
 * Fetch a decimated window of a curve.
 *
 * @param t0sec,t1sec  Visible range in epoch-seconds (omit for the full curve).
 * @param px           Viewport width in pixels — the decimation target.
 */
export async function fetchWindow(
  name: string,
  t0sec: number | null,
  t1sec: number | null,
  px: number,
  method: Method = 'm4',
  signal?: AbortSignal,
): Promise<Window> {
  const q = new URLSearchParams({ px: String(Math.round(px)), method });
  if (t0sec != null) q.set('t0', String(secToNs(t0sec)));
  if (t1sec != null) q.set('t1', String(secToNs(t1sec)));

  const res = await fetch(`${API_BASE}/curves/${encodeURIComponent(name)}/window?${q}`, { signal });
  if (!res.ok) await failOn(res);

  const table = tableFromIPC(new Uint8Array(await res.arrayBuffer()));
  const n = table.numRows;
  const tCol = table.getChild('t')!; // int64 -> BigInt64Array (epoch-ns)
  const vCol = table.getChild('v')!; // float64

  const x = new Float64Array(n);
  const y = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = nsToSec(tCol.get(i) as bigint);
    y[i] = vCol.get(i) as number;
  }
  const points = Number(res.headers.get('X-Points') ?? n);
  return { x, y, points };
}

function withSeconds(m: CurveMeta): Curve {
  return { ...m, t0sec: nsToSec(m.t0), t1sec: nsToSec(m.t1) };
}
