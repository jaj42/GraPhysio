"""Tests for graphysio.core.downsample.

The decisive property for clinical waveforms is **peak preservation**: a sharp
transient that lasts only a few samples must survive aggressive decimation. The
rest verify the contract (subset of real samples, sorted, bounded size, slicing,
edge cases).
"""

import numpy as np
import pandas as pd
import pytest

from graphysio.core.downsample import (
    POINTS_PER_PIXEL,
    decimate_indices,
    downsample_series,
)

METHODS = ["m4", "minmax"]


def make_series(n=200_000, fs=125):
    """A 125 Hz-style series on an int64 epoch-ns index, like GraPhysio's curves."""
    step_ns = int(1e9 / fs)
    index = np.arange(n, dtype="int64") * step_ns
    t = np.arange(n) / fs
    y = np.sin(2 * np.pi * 1.2 * t) + 0.1 * np.sin(2 * np.pi * 17 * t)
    return pd.Series(y, index=index, name="pressure")


@pytest.mark.parametrize("method", METHODS)
def test_preserves_global_extrema(method):
    """The signal-wide min and max must appear in the output (peaks survive)."""
    s = make_series()
    out = downsample_series(s, px=800, method=method)
    assert out.max() == pytest.approx(s.max())
    assert out.min() == pytest.approx(s.min())


@pytest.mark.parametrize("method", METHODS)
def test_preserves_sharp_spike(method):
    """A single-sample spike inside a heavily-decimated window is not lost."""
    s = make_series(n=100_000)
    spike_pos = 54_321
    spike_val = 1000.0
    s.iloc[spike_pos] = spike_val
    out = downsample_series(s, px=500, method=method)
    assert spike_val in out.to_numpy()
    # And it keeps its exact timestamp.
    assert s.index[spike_pos] in out.index


@pytest.mark.parametrize("method", METHODS)
def test_output_is_subset_with_exact_values(method):
    """Output samples are real recorded samples, not resampled/filtered values."""
    s = make_series(n=50_000)
    out = downsample_series(s, px=400, method=method)
    # Every (timestamp, value) pair in the output exists unchanged in the input.
    merged = s.reindex(out.index)
    assert np.array_equal(out.to_numpy(), merged.to_numpy())


@pytest.mark.parametrize("method", METHODS)
def test_output_index_unique(method):
    """No repeated timestamps -- safe to slice/interpolate/feed to filters."""
    s = make_series(n=300_000)
    out = downsample_series(s, px=1000, method=method)
    assert out.index.is_unique


@pytest.mark.parametrize("method", METHODS)
def test_output_sorted_and_bounded(method):
    s = make_series(n=300_000)
    px = 1000
    out = downsample_series(s, px=px, method=method)
    assert out.index.is_monotonic_increasing
    # At most ~points-per-pixel per column (allow the group rounding slack).
    assert len(out) <= px * POINTS_PER_PIXEL[method] + POINTS_PER_PIXEL[method]


@pytest.mark.parametrize("method", METHODS)
def test_small_input_returned_unchanged(method):
    """When the data already fits the budget, keep every point."""
    s = make_series(n=100)
    out = downsample_series(s, px=1000, method=method)
    pd.testing.assert_series_equal(out, s)


@pytest.mark.parametrize("method", METHODS)
def test_slicing_window(method):
    s = make_series(n=100_000)
    t0 = s.index[20_000]
    t1 = s.index[60_000]
    out = downsample_series(s, t0=t0, t1=t1, px=500, method=method)
    assert out.index.min() >= t0
    assert out.index.max() <= t1
    # Decimating the same slice directly must agree.
    expected = downsample_series(s.loc[t0:t1], px=500, method=method)
    pd.testing.assert_series_equal(out, expected)


@pytest.mark.parametrize("method", METHODS)
def test_decimate_indices_sorted_and_in_range(method):
    rng = np.random.default_rng(0)
    n = 80_000
    x = np.arange(n, dtype="int64")
    y = rng.standard_normal(n)
    idx = decimate_indices(x, y, n_out=2000, method=method)
    assert idx.ndim == 1
    # Strictly increasing: sorted and unique (adjacent duplicates collapsed).
    assert np.all(np.diff(idx.astype("int64")) > 0)
    assert idx.min() >= 0
    assert idx.max() < n


def test_unknown_method_raises():
    x = np.arange(10, dtype="int64")
    y = np.zeros(10)
    with pytest.raises(ValueError, match="Unknown method"):
        decimate_indices(x, y, n_out=4, method="bogus")


def test_mismatched_shapes_raise():
    with pytest.raises(ValueError, match="same shape"):
        decimate_indices(np.arange(10), np.arange(9), n_out=4)


def test_first_and_last_points_kept():
    """Endpoints anchor the visible line; M4 in particular must keep them."""
    s = make_series(n=120_000)
    out = downsample_series(s, px=600, method="m4")
    assert out.index[0] == s.index[0]
    assert out.index[-1] == s.index[-1]
