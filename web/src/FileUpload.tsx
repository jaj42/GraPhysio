/**
 * Local-file uploader.
 *
 * The server-side {@link FileBrowser} covers data already on the box; this is the
 * other case -- an ad-hoc file on the *user's* machine. Pick (or drag-drop) a file
 * and it is POSTed to `/upload`, which stores it server-side and hands it to the
 * same staged reader flow as a server-side file.
 */
import { useEffect, useRef, useState } from 'react';

import { supportedFormats } from './api';

interface FileUploadProps {
  onUpload: (file: File) => void;
  onCancel: () => void;
  busy: boolean;
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

export default function FileUpload({ onUpload, onCancel, busy }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [accept, setAccept] = useState<string>('');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // The accepted extensions are whatever readers the backend has registered.
  useEffect(() => {
    supportedFormats()
      .then((exts) => setAccept(exts.join(',')))
      .catch(() => {/* leave the picker unfiltered */});
  }, []);

  return (
    <div style={styles.box}>
      <div style={styles.bar}>
        <strong>Upload a file</strong>
        <button style={styles.cancel} disabled={busy} onClick={onCancel}>
          Cancel
        </button>
      </div>

      <div
        style={{ ...styles.drop, ...(dragging ? styles.dropActive : null) }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const dropped = e.dataTransfer.files[0];
          if (dropped) setFile(dropped);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept || undefined}
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <span style={styles.fileName}>
            📄 {file.name} <span style={styles.size}>({humanSize(file.size)})</span>
          </span>
        ) : (
          <span style={styles.placeholder}>
            Click to choose a file, or drop one here.
          </span>
        )}
      </div>

      <div style={styles.footer}>
        <button style={styles.open} disabled={!file || busy} onClick={() => file && onUpload(file)}>
          {busy ? 'Uploading…' : 'Open'}
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  box: { border: '1px solid #e5e7eb', borderRadius: 8, maxWidth: 520, overflow: 'hidden' },
  bar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, padding: '10px 12px', background: '#f9fafb', borderBottom: '1px solid #e5e7eb' },
  cancel: { padding: '4px 10px', fontSize: 13, cursor: 'pointer', background: 'none', border: '1px solid #d1d5db', borderRadius: 4 },
  drop: { margin: 16, padding: 32, border: '2px dashed #d1d5db', borderRadius: 8, textAlign: 'center', cursor: 'pointer', background: '#fafafa' },
  dropActive: { borderColor: '#2563eb', background: '#eff6ff' },
  placeholder: { color: '#6b7280', fontSize: 14 },
  fileName: { fontSize: 14, wordBreak: 'break-all' },
  size: { color: '#9ca3af', fontSize: 12, fontVariantNumeric: 'tabular-nums' },
  footer: { display: 'flex', justifyContent: 'flex-end', padding: '0 16px 16px' },
  open: { padding: '8px 18px', fontSize: 14, cursor: 'pointer', border: '1px solid #2563eb', borderRadius: 6, background: '#2563eb', color: '#fff' },
};
