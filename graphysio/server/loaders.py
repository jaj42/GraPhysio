"""Bridge the Qt-free readers to the web backend.

The server uses the *same* readers as the desktop (``graphysio.readdata``), now
that they are Qt-free and expose a declarative ``get_params`` schema. This module
just builds a reader for a path and flattens the resulting ``PlotData`` into the
``name -> Series`` curve dict the session works with.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from graphysio.readdata import file_readers
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

__all__ = [
    "UnsupportedFormatError",
    "make_reader",
    "plotdata_to_curves",
    "SUPPORTED_SUFFIXES",
]

SUPPORTED_SUFFIXES = tuple(f".{ext}" for ext in file_readers)


class UnsupportedFormatError(ValueError):
    """Raised when no reader is registered for a file's extension."""


def make_reader(path: Path) -> BaseReader:
    """Build a reader for ``path`` with its filepath set, ready for get_params/call."""
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)
    ext = path.suffix.lstrip(".").lower()
    cls = file_readers.get(ext)
    if cls is None:
        msg = (
            f"Unsupported file type {path.suffix!r}; "
            f"supported: {', '.join(SUPPORTED_SUFFIXES)}"
        )
        raise UnsupportedFormatError(msg)
    reader = cls()
    reader.set_data({"filepath": path})
    return reader


def plotdata_to_curves(
    result: PlotData | list[PlotData] | None,
) -> dict[str, pd.Series]:
    """Flatten reader output into sanitized ``name -> Series`` curves.

    Mirrors ``CurveItem.sanitize_data``: drop NaNs, unique sorted timestamps
    (mean over duplicates), and require at least two points so the curve is
    plottable. Names clashing across PlotData blocks are disambiguated.
    """
    if result is None:
        return {}
    plotdatas = result if isinstance(result, list) else [result]

    curves: dict[str, pd.Series] = {}
    for pdata in plotdatas:
        for col in pdata.data.columns:
            series = pdata.data[col].dropna()
            series = series.groupby(level=0).mean().sort_index()
            if len(series) < 2:
                continue
            name = str(col)
            if name in curves:
                name = f"{pdata.name}-{col}"
            curves[name] = series.rename(name)
    return curves
