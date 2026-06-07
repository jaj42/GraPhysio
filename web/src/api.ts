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
 *
 * Decimation is always M4 (provably pixel-accurate) -- deliberately not exposed
 * as a user option.
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

/** A decimated window: parallel x (epoch-seconds) / y arrays, uPlot-ready. */
export interface Window {
  x: Float64Array;
  y: Float64Array;
  /** Points actually returned by the server (`X-Points` header). */
  points: number;
}

/** One declarative input a reader needs (mirrors `core.params.ParamSpec`). */
export interface ParamSpec {
  name: string;
  label: string;
  kind: 'int' | 'float' | 'str' | 'bool' | 'time' | 'datetime' | 'choice' | 'multichoice';
  choices: string[] | null;
  default: unknown;
  required: boolean;
}

/** Result of a staged open/answer step. */
export interface OpenResponse {
  file_id: string;
  ready: boolean;
  params: ParamSpec[];
  curves: CurveMeta[];
}

/** A selectable data source for the "New Plot" menu. */
export interface Source {
  id: string;
  label: string;
  /** 'file' & 'directory' need a path from the browser; 'params' goes to the form. */
  kind: 'file' | 'directory' | 'params';
}

/** A directory entry from the server-side file browser. */
export interface BrowseEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  suffix: string;
}

export interface BrowseListing {
  root: string;
  path: string;
  parent: string | null;
  entries: BrowseEntry[];
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

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) await failOn(res);
  return res.json() as Promise<T>;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) await failOn(res);
  return res.json() as Promise<T>;
}

/** List server-side directory contents (sub-dirs + loadable files). */
export function browse(path?: string | null): Promise<BrowseListing> {
  const q = path ? `?path=${encodeURIComponent(path)}` : '';
  return getJSON<BrowseListing>(`/browse${q}`);
}

/** The "New Plot" menu: file plus any installed live sources (DWC, Iceberg, …). */
export function listSources(): Promise<Source[]> {
  return getJSON<Source[]>('/sources');
}

/** Register a server-side file; returns its first param schema (or ready). */
export function openFile(path: string): Promise<OpenResponse> {
  return postJSON<OpenResponse>('/files', { path });
}

/** Start a non-file source (DWC/Iceberg/parquet dir); returns its first schema. */
export function openSource(sourceId: string, path?: string | null): Promise<OpenResponse> {
  return postJSON<OpenResponse>(`/sources/${encodeURIComponent(sourceId)}`, { path: path ?? null });
}

/** Feed answers to a pending file; returns the next stage or the loaded curves. */
export function answerFile(fileId: string, answers: Record<string, unknown>): Promise<OpenResponse> {
  return postJSON<OpenResponse>(`/files/${encodeURIComponent(fileId)}`, { answers });
}

/** List the curves currently loaded in the session. */
export async function listCurves(): Promise<Curve[]> {
  const metas = await getJSON<CurveMeta[]>('/curves');
  return metas.map(withSeconds);
}

/**
 * Fetch a decimated (M4) window of a curve.
 *
 * @param t0sec,t1sec  Visible range in epoch-seconds (omit for the full curve).
 * @param px           Viewport width in pixels -- the decimation target.
 */
export async function fetchWindow(
  name: string,
  t0sec: number | null,
  t1sec: number | null,
  px: number,
  signal?: AbortSignal,
): Promise<Window> {
  const q = new URLSearchParams({ px: String(Math.round(px)), method: 'm4' });
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

export function withSeconds(m: CurveMeta): Curve {
  return { ...m, t0sec: nsToSec(m.t0), t1sec: nsToSec(m.t1) };
}
