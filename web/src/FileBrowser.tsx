/**
 * Server-side file browser.
 *
 * The browser's native file dialog can't hand the page a real server path, and the
 * (often multi-GB) data already lives on the self-hosted box -- so instead of
 * uploading, we navigate the *server's* filesystem via `GET /browse` and post back
 * the chosen path. Browsing is confined server-side to a configured data root.
 */
import { useEffect, useState } from 'react';

import { browse, type BrowseListing } from './api';

interface FileBrowserProps {
  /** 'file': click a file to pick it. 'directory': pick the folder you're in. */
  mode?: 'file' | 'directory';
  onPick: (path: string) => void;
  onCancel?: () => void;
}

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let v = bytes / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${units[i]}`;
}

export default function FileBrowser({ mode = 'file', onPick, onCancel }: FileBrowserProps) {
  const [listing, setListing] = useState<BrowseListing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const pickingDir = mode === 'directory';

  function go(path: string | null) {
    setLoading(true);
    setError(null);
    browse(path)
      .then(setListing)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  // Initial listing at the data root.
  useEffect(() => go(null), []);

  return (
    <div style={styles.box}>
      <div style={styles.bar}>
        <strong>{pickingDir ? 'Choose a folder' : 'Open file'}</strong>
        <span style={styles.path}>{listing?.path ?? '…'}</span>
        <span style={styles.barActions}>
          {pickingDir && listing && (
            <button style={styles.pickDir} disabled={loading} onClick={() => onPick(listing.path)}>
              Open this folder
            </button>
          )}
          {onCancel && (
            <button style={styles.cancel} disabled={loading} onClick={onCancel}>
              Cancel
            </button>
          )}
        </span>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      <div style={styles.list}>
        {listing?.parent != null && (
          <button style={styles.row} onClick={() => go(listing.parent)} disabled={loading}>
            <span style={styles.icon}>📁</span> ..
          </button>
        )}
        {listing?.entries.map((e) => {
          // In directory mode files are context-only (you pick the folder, not a file).
          const disabled = loading || (pickingDir && !e.is_dir);
          return (
            <button
              key={e.path}
              style={{ ...styles.row, ...(disabled && !loading ? styles.rowDisabled : null) }}
              disabled={disabled}
              onClick={() => (e.is_dir ? go(e.path) : onPick(e.path))}
            >
              <span style={styles.icon}>{e.is_dir ? '📁' : '📄'}</span>
              <span style={styles.name}>{e.name}</span>
              {!e.is_dir && <span style={styles.size}>{humanSize(e.size)}</span>}
            </button>
          );
        })}
        {listing && listing.entries.length === 0 && (
          <div style={styles.empty}>
            {pickingDir
              ? 'No sub-folders here.'
              : listing.parent == null
                ? 'No loadable files under the data root.'
                : 'Empty folder.'}
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  box: { border: '1px solid #e5e7eb', borderRadius: 8, maxWidth: 640, overflow: 'hidden' },
  bar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, padding: '10px 12px', background: '#f9fafb', borderBottom: '1px solid #e5e7eb' },
  path: { flex: 1, color: '#6b7280', fontSize: 12, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  barActions: { display: 'flex', gap: 8, flexShrink: 0 },
  pickDir: { padding: '4px 10px', fontSize: 13, cursor: 'pointer' },
  cancel: { padding: '4px 10px', fontSize: 13, cursor: 'pointer', background: 'none', border: '1px solid #d1d5db', borderRadius: 4 },
  list: { maxHeight: 360, overflowY: 'auto' },
  row: { display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '7px 12px', border: 'none', borderBottom: '1px solid #f3f4f6', background: 'none', textAlign: 'left', fontSize: 14, cursor: 'pointer' },
  rowDisabled: { color: '#9ca3af', cursor: 'default' },
  icon: { width: 18 },
  name: { flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  size: { color: '#9ca3af', fontSize: 12, fontVariantNumeric: 'tabular-nums' },
  empty: { padding: 16, color: '#9ca3af', fontSize: 14 },
  error: { color: '#b91c1c', background: '#fef2f2', padding: '8px 12px' },
};
