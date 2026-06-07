"""Small Qt-free helpers for GraPhysio's time-series representation.

GraPhysio stores every curve as a pandas Series indexed by an int64
epoch-nanosecond timestamp. These helpers operate on that representation without
pulling in any GUI dependency (unlike ``graphysio.utils``, which imports Qt).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["estimate_samplerate"]


def estimate_samplerate(series: pd.Series) -> float:
    """Estimate the sampling rate (Hz) of a series on an int64 epoch-ns index.

    Uses the median inter-sample interval, so it is robust to occasional gaps.
    Returns ``0`` for a series that has no measurable rate (constant or single
    timestamp). Whole-number rates are rounded to an int for tidy display.

    This mirrors ``graphysio.utils.estimateSampleRate`` but is import-safe for the
    Qt-free core/server.
    """
    if len(series) < 2:
        return 0
    intervals = np.diff(series.index.to_numpy())
    median = np.median(intervals)
    if median == 0:
        return 0
    fs = 1e9 / median  # ns -> Hz
    if not np.isfinite(fs):
        return 0
    if fs > 1:
        fs = int(round(fs))
    return fs
