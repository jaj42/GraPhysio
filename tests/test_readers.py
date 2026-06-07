"""Tests for the Qt-free reader decoupling (Phase 1).

Verify that readers import without Qt, expose a declarative get_params() schema,
and load headless via the gather() driver into int64-ns indexed PlotData.
"""

import sys

import numpy as np
import pandas as pd
import pytest

from graphysio.core.params import default_answers, gather
from graphysio.readdata import CsvReader, ParquetReader

FS = 125
N = 4000


@pytest.fixture
def df():
    ts = pd.Timestamp("2025-01-01") + pd.to_timedelta(np.arange(N) / FS, unit="s")
    return pd.DataFrame(
        {
            "t": ts,
            "abp": np.sin(np.arange(N) / 50.0),
            "ecg": np.cos(np.arange(N) / 30.0),
        }
    )


def test_readdata_imports_without_qt():
    # Importing the readers must not drag in any GUI toolkit.
    import graphysio.readdata  # noqa: F401

    assert not [m for m in sys.modules if any(k in m for k in ("PySide", "pyqtgraph", "PyQt"))]


def test_parquet_get_params_schema(tmp_path, df):
    path = tmp_path / "s.parquet"
    df.to_parquet(path, index=False)
    reader = ParquetReader()
    reader.set_data({"filepath": path})

    params = reader.get_params()
    by_name = {p.name: p for p in params}
    assert set(by_name) == {"columns", "index"}
    assert by_name["columns"].kind == "multichoice"
    assert set(by_name["columns"].choices) == {"t", "abp", "ecg"}
    assert by_name["index"].required is False
    # Once columns are set, the reader needs nothing more.
    reader.set_data({"columns": ["abp", "ecg"], "index": "t"})
    assert reader.get_params() == []


def test_parquet_headless_load(tmp_path, df):
    path = tmp_path / "s.parquet"
    df.to_parquet(path, index=False)
    reader = ParquetReader()
    reader.set_data({"filepath": path})
    ok = gather(reader, lambda params: {**default_answers(params), "index": "t"})
    assert ok
    plotdata = reader()
    assert list(plotdata.data.columns) == ["abp", "ecg"]
    assert plotdata.data.index.dtype == np.int64
    assert len(plotdata.data) == N


def test_csv_headless_with_datetime_column(tmp_path, df):
    path = tmp_path / "s.csv"
    df.to_csv(path, index=False)
    reader = CsvReader()
    reader.set_data({"filepath": path})

    def ask(params):
        a = default_answers(params)
        a["dtfield"] = "t"
        a["datetime_format"] = "<infer>"
        return a

    assert gather(reader, ask)
    out = reader()
    assert len(out) == 1
    assert set(out[0].data.columns) == {"abp", "ecg"}
    assert out[0].data.index.dtype == np.int64


def test_csv_headless_generate_x_from_rate(tmp_path):
    # No datetime column: generate the index from a sampling rate.
    plain = pd.DataFrame({"abp": np.sin(np.arange(N) / 50.0)})
    path = tmp_path / "plain.csv"
    plain.to_csv(path, index=False)
    reader = CsvReader()
    reader.set_data({"filepath": path})

    def ask(params):
        a = default_answers(params)
        a["dtfield"] = None  # -> generatex
        a["samplerate"] = FS
        return a

    assert gather(reader, ask)
    out = reader()
    assert out[0].data.index.dtype == np.int64
    # Index step should reflect the sampling rate (1/FS seconds in ns).
    step = np.diff(out[0].data.index.to_numpy())[0]
    assert step == pytest.approx(1e9 / FS, rel=1e-6)
