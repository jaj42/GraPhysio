"""Qt-free file loaders for the web backend.

These mirror the pure-pandas ``__call__`` logic of ``graphysio.readdata`` without
the Qt ``askUserInput`` dialogs, so they can run headless in the server. They are
intentionally minimal -- enough to prove the load->plot data path. Phase 1 of the
migration will unify these with the desktop readers via a schema-driven parameter
mechanism (reader exposes its ``Parameter`` list; caller supplies answers), at
which point all formats and their options become available here too.

Every loader returns ``dict[name -> pd.Series]`` where each Series is indexed by
an int64 epoch-nanosecond timestamp -- the representation used throughout
GraPhysio.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

__all__ = ["UnsupportedFormatError", "load_file", "SUPPORTED_SUFFIXES"]

# Column names commonly used for the time axis, tried (case-insensitively) when the
# file has no usable index of its own.
_TIME_COLUMN_HINTS = ("datetime", "timestamp", "time", "date", "index")


class UnsupportedFormatError(ValueError):
    """Raised when no loader is registered for a file's extension."""


def _to_int64_ns_index(index: pd.Index) -> pd.Index:
    """Coerce a time index to int64 epoch nanoseconds (tz-naive)."""
    if is_datetime64_any_dtype(index):
        dt = pd.DatetimeIndex(index)
        if dt.tz is not None:
            dt = dt.tz_convert("UTC").tz_localize(None)
        return dt.astype("datetime64[ns]").astype("int64")
    # Already numeric: assume it is the time axis in ns and keep it as-is.
    return pd.Index(index).astype("int64")


def _frame_to_curves(data: pd.DataFrame) -> dict[str, pd.Series]:
    """Turn a time-indexed DataFrame into one sanitized Series per numeric column."""
    data = data.sort_index()
    data.index = _to_int64_ns_index(data.index)

    curves: dict[str, pd.Series] = {}
    for col in data.columns:
        series = data[col]
        if not is_numeric_dtype(series):
            continue
        series = series.dropna()
        # Unique, sorted timestamps; mean over any duplicate timestamps -- matches
        # CurveItem.sanitize_data so the server and desktop agree on the data.
        series = series.groupby(level=0).mean().sort_index()
        if len(series) < 2:
            continue
        curves[str(col)] = series.rename(str(col))
    return curves


def _pick_index(data: pd.DataFrame) -> pd.DataFrame:
    """Ensure the frame is indexed by time, using a hint column if needed."""
    if is_datetime64_any_dtype(data.index) or is_numeric_dtype(data.index):
        return data
    lower = {str(c).lower(): c for c in data.columns}
    for hint in _TIME_COLUMN_HINTS:
        if hint in lower:
            return data.set_index(lower[hint])
    # Fall back to whatever the existing index is.
    return data


def load_parquet(path: Path) -> dict[str, pd.Series]:
    data = pd.read_parquet(path)
    data = _pick_index(data)
    return _frame_to_curves(data)


def load_csv(path: Path) -> dict[str, pd.Series]:
    # Best-effort headless CSV load: comma-separated, first datetime/numeric-looking
    # column as the index. Full CSV options come with the Phase 1 reader refactor.
    data = pd.read_csv(path)
    data = _pick_index(data)
    # Try to parse a non-numeric index as datetime (e.g. ISO timestamps).
    if not is_datetime64_any_dtype(data.index) and not is_numeric_dtype(data.index):
        data.index = pd.to_datetime(data.index, errors="coerce")
        data = data[data.index.notna()]
    return _frame_to_curves(data)


_LOADERS = {
    ".parquet": load_parquet,
    ".csv": load_csv,
    ".txt": load_csv,
    ".dat": load_csv,
}

SUPPORTED_SUFFIXES = tuple(_LOADERS)


def load_file(path: str | Path) -> dict[str, pd.Series]:
    """Load ``path`` into a dict of curves, dispatching on file extension."""
    path = Path(path)
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        msg = (
            f"Unsupported file type {path.suffix!r}; "
            f"supported: {', '.join(SUPPORTED_SUFFIXES)}"
        )
        raise UnsupportedFormatError(msg)
    return loader(path)
