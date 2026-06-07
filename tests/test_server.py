"""Tests for the Phase 2 FastAPI data path: load -> list -> windowed Arrow."""

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from graphysio.server.app import app
from graphysio.server.session import STORE

FS = 125
N = 60_000  # ~8 min at 125 Hz


@pytest.fixture(autouse=True)
def _clean_store():
    """Each test starts with an empty session (the store is process-wide)."""
    STORE.reset()
    yield
    STORE.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def parquet_file(tmp_path):
    """A 125 Hz parquet file with a datetime index and two numeric curves."""
    start = pd.Timestamp("2025-01-01 00:00:00")
    index = start + pd.to_timedelta(np.arange(N) / FS, unit="s")
    t = np.arange(N) / FS
    df = pd.DataFrame(
        {
            "abp": 80 + 40 * np.sin(2 * np.pi * 1.2 * t),
            "ecg": np.sin(2 * np.pi * 1.2 * t) + 0.1 * np.sin(2 * np.pi * 17 * t),
        },
        index=index,
    )
    path = tmp_path / "signals.parquet"
    df.to_parquet(path)
    return path


def _read_arrow(content: bytes) -> pa.Table:
    return pa.ipc.open_stream(content).read_all()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert ".parquet" in r.json()["supported_formats"]


def test_load_lists_curves_with_metadata(client, parquet_file):
    r = client.post("/session/load", json={"path": str(parquet_file)})
    assert r.status_code == 200
    curves = {c["name"]: c for c in r.json()["curves"]}
    assert set(curves) == {"abp", "ecg"}
    assert curves["abp"]["n_samples"] == N
    assert curves["abp"]["samplerate"] == FS
    assert curves["abp"]["t0"] < curves["abp"]["t1"]

    # /curves returns the same metadata.
    r2 = client.get("/curves")
    assert {c["name"] for c in r2.json()} == {"abp", "ecg"}


def test_window_returns_arrow_decimated(client, parquet_file):
    client.post("/session/load", json={"path": str(parquet_file)})
    px = 400
    r = client.get(f"/curves/abp/window", params={"px": px, "method": "m4"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.apache.arrow")

    table = _read_arrow(r.content)
    assert table.column_names == ["t", "v"]
    t = table.column("t").to_numpy()
    v = table.column("v").to_numpy()

    # Decimated well below the raw sample count, bounded by the pixel budget.
    assert len(t) < N
    assert len(t) <= px * 4 + 4
    assert int(r.headers["X-Points"]) == len(t)
    # Sorted, unique timestamps.
    assert np.all(np.diff(t) > 0)
    # Peaks preserved: the window's extrema match the source's *sampled* extrema
    # (not the continuous 80+-40, since the crest falls between 125 Hz samples).
    raw = 80 + 40 * np.sin(2 * np.pi * 1.2 * (np.arange(N) / FS))
    assert v.max() == pytest.approx(raw.max())
    assert v.min() == pytest.approx(raw.min())


def test_window_slicing(client, parquet_file):
    client.post("/session/load", json={"path": str(parquet_file)})
    full = client.get("/curves").json()
    abp = next(c for c in full if c["name"] == "abp")
    span = abp["t1"] - abp["t0"]
    t0 = abp["t0"] + span // 4
    t1 = abp["t0"] + span // 2

    r = client.get("/curves/abp/window", params={"t0": t0, "t1": t1, "px": 300})
    table = _read_arrow(r.content)
    t = table.column("t").to_numpy()
    assert t.min() >= t0
    assert t.max() <= t1


def test_unknown_curve_404(client, parquet_file):
    client.post("/session/load", json={"path": str(parquet_file)})
    r = client.get("/curves/nope/window")
    assert r.status_code == 404


def test_missing_file_404(client):
    r = client.post("/session/load", json={"path": "/no/such/file.parquet"})
    assert r.status_code == 404


def test_unsupported_format_415(client, tmp_path):
    bad = tmp_path / "data.xyz"
    bad.write_text("nope")
    r = client.post("/session/load", json={"path": str(bad)})
    assert r.status_code == 415


def test_clear_session(client, parquet_file):
    client.post("/session/load", json={"path": str(parquet_file)})
    assert client.get("/curves").json()
    r = client.delete("/session")
    assert r.status_code == 204
    assert client.get("/curves").json() == []
