/**
 * GraPhysio web viewer (Phase 3, read-only).
 *
 * Flow: **New Plot** menu → pick a source (file, or a live source like DWC /
 * Iceberg / a parquet directory) → (browse the server filesystem if the source
 * needs a path) → answer the reader's parameter schema (staged) → all of the
 * resulting curves are shown overlaid in one pan/zoomable plot. All heavy lifting
 * is server-side M4 decimation — the browser only ever holds a few thousand points
 * per curve.
 */
import { useEffect, useState } from 'react';

import {
  answerFile,
  listCurves,
  listSources,
  openFile,
  openSource,
  withSeconds,
  type Curve,
  type OpenResponse,
  type ParamSpec,
  type Source,
} from './api';
import Chart from './Chart';
import FileBrowser from './FileBrowser';
import ParamForm from './ParamForm';

type Step = 'source' | 'browse' | 'params' | 'viewing';

export default function App() {
  const [step, setStep] = useState<Step>('source');
  const [sources, setSources] = useState<Source[]>([]);
  const [picking, setPicking] = useState<Source | null>(null); // source awaiting a path
  const [pending, setPending] = useState<{ fileId: string; params: ParamSpec[]; name: string } | null>(null);
  const [curves, setCurves] = useState<Curve[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ points: number; ms: number } | null>(null);

  // Load the source menu, and resume into the viewer if curves are already loaded.
  useEffect(() => {
    listSources().then(setSources).catch((e: Error) => setError(e.message));
    listCurves()
      .then((cs) => {
        if (cs.length) {
          setCurves(cs);
          setStep('viewing');
        }
      })
      .catch(() => {/* empty session is fine */});
  }, []);

  /** Dispatch an open response: show the param form, or load straight away. */
  async function afterOpen(resp: OpenResponse, name: string) {
    if (resp.params.length) {
      setPending({ fileId: resp.file_id, params: resp.params, name });
      setStep('params');
      setBusy(false);
    } else {
      await submitAnswers(resp.file_id, name, {});
    }
  }

  async function submitAnswers(fileId: string, name: string, answers: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const resp = await answerFile(fileId, answers);
      if (resp.curves.length) {
        setCurves(resp.curves.map(withSeconds));
        setPending(null);
        setStep('viewing');
      } else if (resp.params.length) {
        setPending({ fileId, params: resp.params, name }); // next stage
        setStep('params');
      } else {
        setError('Loaded but produced no plottable curves.');
        setStep('source');
      }
    } catch (e) {
      setError((e as Error).message);
      setStep(picking ? 'browse' : 'source');
    } finally {
      setBusy(false);
    }
  }

  /** A source was chosen from the New Plot menu. */
  async function startSource(source: Source) {
    setError(null);
    if (source.kind === 'params') {
      setBusy(true);
      try {
        await afterOpen(await openSource(source.id), source.label);
      } catch (e) {
        setError((e as Error).message);
        setBusy(false);
      }
    } else {
      setPicking(source); // 'file' or 'directory' -> browse for a path
      setStep('browse');
    }
  }

  /** A path was picked in the browser (a file, or a folder for directory sources). */
  async function onPick(path: string) {
    if (!picking) return;
    setBusy(true);
    setError(null);
    const name = path.split('/').filter(Boolean).pop() ?? path;
    try {
      const resp = picking.kind === 'directory' ? await openSource(picking.id, path) : await openFile(path);
      await afterOpen(resp, name);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  function reset() {
    setCurves([]);
    setPending(null);
    setPicking(null);
    setStats(null);
    setError(null);
    setStep('source');
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.h1}>GraPhysio</h1>
        {step !== 'source' && (
          <button style={styles.btnGhost} onClick={reset}>
            New Plot
          </button>
        )}
      </header>

      {error && <div style={styles.error}>{error}</div>}

      {step === 'source' && (
        <div style={styles.sourceMenu}>
          <h2 style={styles.h2}>New Plot — choose a source</h2>
          <div style={styles.sourceGrid}>
            {sources.map((s) => (
              <button key={s.id} style={styles.sourceBtn} disabled={busy} onClick={() => startSource(s)}>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 'browse' && picking && (
        <FileBrowser
          mode={picking.kind === 'directory' ? 'directory' : 'file'}
          onPick={onPick}
          onCancel={reset}
        />
      )}

      {step === 'params' && pending && (
        <ParamForm
          key={pending.fileId + pending.params.map((p) => p.name).join()}
          title={`Load ${pending.name}`}
          params={pending.params}
          busy={busy}
          onSubmit={(answers) => submitAnswers(pending.fileId, pending.name, answers)}
          onCancel={reset}
        />
      )}

      {step === 'viewing' && curves.length > 0 && (
        <>
          <div style={styles.metabar}>
            {/* Curve names live in the chart's own legend now (no duplication). */}
            {stats && (
              <span style={styles.stats}>
                {stats.points.toLocaleString()} pts · {stats.ms} ms
              </span>
            )}
          </div>
          <Chart curves={curves} onStats={setStats} />
          <p style={styles.hint}>
            Scroll to zoom · drag to pan · shift-drag to box-zoom · double-click to reset.
          </p>
        </>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: { fontFamily: 'system-ui, sans-serif', maxWidth: 1400, margin: '0 auto', padding: 16 },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 },
  h1: { fontSize: 22, margin: 0 },
  h2: { fontSize: 16, margin: '0 0 12px' },
  sourceMenu: { border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, maxWidth: 520 },
  sourceGrid: { display: 'flex', flexWrap: 'wrap', gap: 8 },
  sourceBtn: { padding: '10px 18px', fontSize: 14, cursor: 'pointer', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' },
  metabar: { display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 8, fontSize: 14 },
  stats: { marginLeft: 'auto', color: '#6b7280', fontSize: 13, fontVariantNumeric: 'tabular-nums' },
  error: { color: '#b91c1c', background: '#fef2f2', padding: '8px 12px', borderRadius: 4, marginBottom: 12 },
  hint: { color: '#6b7280', fontSize: 13 },
  btnGhost: { padding: '6px 14px', fontSize: 14, cursor: 'pointer', background: 'none', border: '1px solid #d1d5db', borderRadius: 4 },
};
