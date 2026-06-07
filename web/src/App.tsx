/**
 * GraPhysio web viewer (Phase 3, read-only).
 *
 * Load a server-side file, pick a curve, and pan/zoom it. All heavy lifting is
 * server-side decimation — the browser only ever holds a few thousand points.
 */
import { useEffect, useState } from 'react';

import { listCurves, loadFile, type Curve, type Method } from './api';
import Chart from './Chart';

export default function App() {
  const [path, setPath] = useState('');
  const [curves, setCurves] = useState<Curve[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [method, setMethod] = useState<Method>('m4');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ points: number; ms: number } | null>(null);

  // Pick up any curves already loaded in the session on first mount.
  useEffect(() => {
    listCurves()
      .then((cs) => {
        if (cs.length) {
          setCurves(cs);
          setSelected((s) => s || cs[0].name);
        }
      })
      .catch(() => {/* empty session is fine */});
  }, []);

  async function onLoad(e: React.FormEvent) {
    e.preventDefault();
    if (!path.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const cs = await loadFile(path.trim());
      setCurves(cs);
      setSelected(cs[0]?.name ?? '');
      if (!cs.length) setError('File loaded but produced no plottable curves.');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const current = curves.find((c) => c.name === selected) ?? null;

  return (
    <div style={styles.app}>
      <h1 style={styles.h1}>GraPhysio</h1>

      <form onSubmit={onLoad} style={styles.row}>
        <input
          style={styles.input}
          placeholder="server-side file path (e.g. /data/run.parquet)"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
        <button style={styles.btn} disabled={loading} type="submit">
          {loading ? 'Loading…' : 'Load'}
        </button>
      </form>

      {error && <div style={styles.error}>{error}</div>}

      {curves.length > 0 && (
        <div style={styles.row}>
          <label>
            Curve:{' '}
            <select value={selected} onChange={(e) => setSelected(e.target.value)} style={styles.select}>
              {curves.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.n_samples.toLocaleString()} pts, {c.samplerate.toFixed(1)} Hz)
                </option>
              ))}
            </select>
          </label>
          <label>
            Decimation:{' '}
            <select value={method} onChange={(e) => setMethod(e.target.value as Method)} style={styles.select}>
              <option value="m4">M4 (pixel-accurate)</option>
              <option value="minmax">min/max</option>
            </select>
          </label>
          {stats && (
            <span style={styles.stats}>
              {stats.points.toLocaleString()} pts · {stats.ms} ms
            </span>
          )}
        </div>
      )}

      {current ? (
        <Chart key={current.name} curve={current} method={method} onStats={setStats} />
      ) : (
        <p style={styles.hint}>
          Load a file above. Then scroll to zoom, drag to pan, shift-drag to box-zoom,
          double-click to reset.
        </p>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: { fontFamily: 'system-ui, sans-serif', maxWidth: 1400, margin: '0 auto', padding: 16 },
  h1: { fontSize: 22, margin: '4px 0 16px' },
  row: { display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 },
  input: { flex: 1, minWidth: 280, padding: '6px 8px', fontSize: 14 },
  select: { padding: '4px 6px', fontSize: 14 },
  btn: { padding: '6px 16px', fontSize: 14, cursor: 'pointer' },
  error: { color: '#b91c1c', background: '#fef2f2', padding: '8px 12px', borderRadius: 4, marginBottom: 12 },
  stats: { marginLeft: 'auto', color: '#6b7280', fontSize: 13, fontVariantNumeric: 'tabular-nums' },
  hint: { color: '#6b7280' },
};
