/**
 * Generic form for a reader's declarative parameter schema.
 *
 * The web analog of the desktop's `askUserValue` type switch: it renders any list
 * of `ParamSpec` (sent by the backend as JSON) into inputs by `kind` and hands the
 * collected answers back. The same component drives file-load params now and will
 * drive filter/transform params in Phase 4 -- adding a reader/filter stays a
 * one-line backend registry entry with no frontend change.
 */
import { useState } from 'react';

import type { ParamSpec } from './api';

interface ParamFormProps {
  params: ParamSpec[];
  title?: string;
  submitLabel?: string;
  onSubmit: (answers: Record<string, unknown>) => void;
  onCancel?: () => void;
  busy?: boolean;
}

type Value = string | number | boolean | string[] | null;

function initialValue(p: ParamSpec): Value {
  if (p.default !== null && p.default !== undefined) return p.default as Value;
  if (p.kind === 'multichoice') return [...(p.choices ?? [])];
  if (p.kind === 'bool') return false;
  return null;
}

export default function ParamForm({
  params,
  title,
  submitLabel = 'Load',
  onSubmit,
  onCancel,
  busy,
}: ParamFormProps) {
  const [values, setValues] = useState<Record<string, Value>>(() =>
    Object.fromEntries(params.map((p) => [p.name, initialValue(p)])),
  );
  const [error, setError] = useState<string | null>(null);

  const set = (name: string, v: Value) => setValues((prev) => ({ ...prev, [name]: v }));

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const missing = params.find(
      (p) => p.required && (values[p.name] == null || values[p.name] === ''),
    );
    if (missing) {
      setError(`"${missing.label}" is required.`);
      return;
    }
    setError(null);
    onSubmit(values);
  }

  return (
    <form onSubmit={submit} style={styles.form}>
      {title && <h2 style={styles.h2}>{title}</h2>}
      {params.map((p) => (
        <div key={p.name} style={styles.field}>
          <label style={styles.label}>
            {p.label}
            {!p.required && <span style={styles.optional}> (optional)</span>}
          </label>
          <Field spec={p} value={values[p.name]} onChange={(v) => set(p.name, v)} />
        </div>
      ))}
      {error && <div style={styles.error}>{error}</div>}
      <div style={styles.actions}>
        <button type="submit" disabled={busy} style={styles.btn}>
          {busy ? 'Loading…' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} disabled={busy} style={styles.btnGhost}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

function Field({
  spec,
  value,
  onChange,
}: {
  spec: ParamSpec;
  value: Value;
  onChange: (v: Value) => void;
}) {
  switch (spec.kind) {
    case 'choice':
      return (
        <select
          style={styles.input}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : e.target.value)}
        >
          {!spec.required && <option value="">(none)</option>}
          {(spec.choices ?? []).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      );

    case 'multichoice': {
      const selected = new Set((value as string[]) ?? []);
      return (
        <div style={styles.checks}>
          {(spec.choices ?? []).map((c) => (
            <label key={c} style={styles.check}>
              <input
                type="checkbox"
                checked={selected.has(c)}
                onChange={(e) => {
                  const next = new Set(selected);
                  if (e.target.checked) next.add(c);
                  else next.delete(c);
                  onChange([...next]);
                }}
              />
              {c}
            </label>
          ))}
        </div>
      );
    }

    case 'bool':
      return (
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
        />
      );

    case 'int':
    case 'float':
      return (
        <input
          type="number"
          step={spec.kind === 'int' ? 1 : 'any'}
          style={styles.input}
          value={value == null ? '' : String(value)}
          onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        />
      );

    case 'datetime':
      // Local wall-clock picker; backend pre-fills/parses as local time (e.g. DWC
      // shows the patient's available range and queries dwclib in the local zone).
      return (
        <input
          type="datetime-local"
          step="1"
          style={styles.input}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : e.target.value)}
        />
      );

    case 'time':
    case 'str':
    default:
      return (
        <input
          type="text"
          style={styles.input}
          placeholder={spec.kind === 'time' ? 'e.g. 500ms, 2s' : undefined}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : e.target.value)}
        />
      );
  }
}

const styles: Record<string, React.CSSProperties> = {
  form: { border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, maxWidth: 520 },
  h2: { fontSize: 16, margin: '0 0 12px' },
  field: { marginBottom: 12 },
  label: { display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 },
  optional: { fontWeight: 400, color: '#9ca3af' },
  input: { width: '100%', padding: '6px 8px', fontSize: 14, boxSizing: 'border-box' },
  checks: { display: 'flex', flexWrap: 'wrap', gap: '4px 16px', maxHeight: 180, overflowY: 'auto' },
  check: { display: 'flex', gap: 6, alignItems: 'center', fontSize: 14, fontWeight: 400 },
  actions: { display: 'flex', gap: 8, marginTop: 8 },
  btn: { padding: '6px 16px', fontSize: 14, cursor: 'pointer' },
  btnGhost: { padding: '6px 16px', fontSize: 14, cursor: 'pointer', background: 'none', border: '1px solid #d1d5db' },
  error: { color: '#b91c1c', background: '#fef2f2', padding: '8px 12px', borderRadius: 4, marginBottom: 8 },
};
