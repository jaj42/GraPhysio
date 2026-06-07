"""Viewport-aware downsampling for high-frequency time series.

High-frequency physiological signals (e.g. 125 Hz over several hours) produce
millions of samples per curve -- far more than a browser can transfer or render.
The desktop app relies on pyqtgraph's local auto-downsampling; the web backend
must reproduce that server-side.

The strategy is **min/max-style decimation**: the visible sample range is split
into buckets and, for each bucket, the extreme samples are kept. Unlike averaging
or anti-aliased decimation (``scipy.signal.decimate``), this *preserves* the
systolic/diastolic peaks, R-waves and dicrotic notches that matter clinically,
while bounding the output to a few points per horizontal pixel regardless of input
size. The actual recorded samples (and their exact timestamps) are returned -- no
filtering, no resampling onto a synthetic grid.

The heavy lifting is delegated to the compiled, SIMD-accelerated ``tsdownsample``
library (the engine behind plotly-resampler). Two methods are exposed:

* ``"m4"`` (default) keeps the min, max, first and last sample of each bucket. This
  is provably pixel-accurate for line charts -- the rendered result is visually
  indistinguishable from plotting every point.
* ``"minmax"`` keeps only the min and max of each bucket: half the points, still
  peak-preserving, slightly cheaper.

Inputs are assumed NaN-free (the readers/curves sanitize beforehand) and sorted by
time. The time axis is the int64 epoch-nanosecond index used throughout GraPhysio,
but the primitives are dtype-agnostic and work on any numeric x.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from tsdownsample import M4Downsampler, MinMaxDownsampler

__all__ = ["Method", "POINTS_PER_PIXEL", "decimate_indices", "downsample_series"]

Method = Literal["m4", "minmax"]

# Output points kept per horizontal pixel, and the n_out granularity each method
# requires (M4 emits groups of 4, MinMax groups of 2).
POINTS_PER_PIXEL: dict[str, int] = {"m4": 4, "minmax": 2}

_DOWNSAMPLERS = {"m4": M4Downsampler(), "minmax": MinMaxDownsampler()}


def decimate_indices(
    x: np.ndarray,
    y: np.ndarray,
    n_out: int,
    method: Method = "m4",
) -> np.ndarray:
    """Return the sorted indices of the samples to keep when decimating to ``n_out``.

    Thin wrapper over ``tsdownsample`` that rounds ``n_out`` to the granularity the
    chosen method requires and short-circuits inputs that are already small enough.

    Parameters
    ----------
    x, y:
        Parallel 1-D arrays of equal length; ``x`` is expected sorted ascending.
    n_out:
        Approximate target number of output points. Rounded down to a multiple of
        the method's group size (4 for ``"m4"``, 2 for ``"minmax"``).
    method:
        ``"m4"`` or ``"minmax"``.

    Returns
    -------
    A strictly increasing, unique array of integer indices into ``x``/``y``. When
    the input already has no more points than the (rounded) target,
    ``arange(len(x))`` is returned -- i.e. keep everything.

    Notes
    -----
    M4 selects the min, max, first and last of each bucket and can therefore name
    the same sample twice (e.g. the bucket's first sample is also its minimum).
    Such adjacent duplicates are collapsed so the index stays unique -- this is
    visually lossless (a point plotted twice draws the same line) and keeps the
    output safe to slice, interpolate or feed to filters.
    """
    if method not in _DOWNSAMPLERS:
        msg = f"Unknown method {method!r}; expected one of {list(_DOWNSAMPLERS)}"
        raise ValueError(msg)
    x = np.asarray(x)
    y = np.asarray(y)
    if x.shape != y.shape or x.ndim != 1:
        msg = "x and y must be 1-D arrays of the same shape"
        raise ValueError(msg)

    n = x.size
    group = POINTS_PER_PIXEL[method]
    # Round down to the granularity the downsampler requires; never below one group.
    n_out = max(group, (int(n_out) // group) * group)

    # Already small enough: decimation cannot reduce it, so keep every sample.
    if n <= n_out:
        return np.arange(n)

    idx = _DOWNSAMPLERS[method].downsample(x, y, n_out=n_out)
    # tsdownsample returns sorted indices; M4 may repeat one (first/last == min/max).
    # Collapse adjacent duplicates so the result is strictly increasing and unique.
    if idx.size > 1:
        keep = np.ones(idx.size, dtype=bool)
        keep[1:] = idx[1:] != idx[:-1]
        idx = idx[keep]
    return idx


def downsample_series(
    series: pd.Series,
    t0=None,
    t1=None,
    px: int = 1000,
    method: Method = "m4",
) -> pd.Series:
    """Slice ``series`` to ``[t0, t1]`` and decimate it for a ``px``-wide viewport.

    Parameters
    ----------
    series:
        A pandas Series indexed by time (the int64 epoch-ns index used by
        GraPhysio). Assumed sorted and NaN-free.
    t0, t1:
        Inclusive bounds of the visible window, in the same units as the index.
        ``None`` means "from the start" / "to the end" (equivalent to
        ``series.loc[t0:t1]``).
    px:
        Viewport width in pixels. The result keeps ~``POINTS_PER_PIXEL[method]``
        points per pixel.
    method:
        ``"m4"`` (default, pixel-accurate) or ``"minmax"`` (fewer points).

    Returns
    -------
    A new Series (same ``name`` and index name) holding the kept samples with their
    original timestamps and values -- a subset of the input, never resampled.
    """
    if t0 is not None or t1 is not None:
        series = series.loc[t0:t1]

    x = series.index.to_numpy()
    y = series.to_numpy()
    n_out = max(1, int(px)) * POINTS_PER_PIXEL[method]
    idx = decimate_indices(x, y, n_out, method=method)

    return series.iloc[idx]
