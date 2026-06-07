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


def _answers_from_params(params):
    """Echo back each param's default (full list for multichoice)."""
    out = {}
    for p in params:
        if p["default"] is not None:
            out[p["name"]] = p["default"]
        elif p["kind"] == "multichoice":
            out[p["name"]] = p["choices"]
        else:
            out[p["name"]] = None
    return out


def test_staged_open_flow(client, parquet_file):
    # Step 1: register the file, get its param schema.
    r = client.post("/files", json={"path": str(parquet_file)})
    assert r.status_code == 200
    data = r.json()
    file_id = data["file_id"]
    names = {p["name"] for p in data["params"]}
    assert {"columns", "index"} <= names

    # Step 2: answer with defaults -> curves loaded.
    answers = _answers_from_params(data["params"])
    r2 = client.post(f"/files/{file_id}", json={"answers": answers})
    assert r2.status_code == 200
    body = r2.json()
    assert body["ready"] is True
    loaded = {c["name"] for c in body["curves"]}
    assert {"abp", "ecg"} <= loaded
    # And the curves are now queryable.
    assert {"abp", "ecg"} <= {c["name"] for c in client.get("/curves").json()}


def test_open_unsupported_415(client, tmp_path):
    bad = tmp_path / "data.xyz"
    bad.write_text("nope")
    r = client.post("/files", json={"path": str(bad)})
    assert r.status_code == 415


def test_answer_unknown_file_404(client):
    r = client.post("/files/deadbeef", json={"answers": {}})
    assert r.status_code == 404


def test_clear_session(client, parquet_file):
    client.post("/session/load", json={"path": str(parquet_file)})
    assert client.get("/curves").json()
    r = client.delete("/session")
    assert r.status_code == 204
    assert client.get("/curves").json() == []


# --- Server-side file browser ---


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """A populated browsable root: a sub-dir, a supported and an unsupported file."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "run.parquet").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("hi")  # supported (.txt is a csv alias)
    (tmp_path / "image.png").write_bytes(b"x")  # unsupported -> skipped
    (tmp_path / ".hidden.parquet").write_bytes(b"x")  # dotfile -> skipped
    (tmp_path / ".cache").mkdir()  # dotdir -> skipped
    monkeypatch.setenv("GRAPHYSIO_DATA_ROOT", str(tmp_path))
    return tmp_path


def test_browse_lists_dirs_and_supported_files(client, data_root):
    body = client.get("/browse").json()
    assert body["root"] == str(data_root)
    assert body["parent"] is None  # at the root
    names = [e["name"] for e in body["entries"]]
    assert "sub" in names and "run.parquet" in names
    assert "image.png" not in names  # unsupported skipped
    assert ".hidden.parquet" not in names and ".cache" not in names  # hidden skipped
    # Directories sort before files.
    assert body["entries"][0]["is_dir"] is True


def test_browse_into_subdir_has_parent(client, data_root):
    body = client.get("/browse", params={"path": str(data_root / "sub")}).json()
    assert body["parent"] == str(data_root)
    assert body["entries"] == []


def test_browse_rejects_escape_403(client, data_root):
    r = client.get("/browse", params={"path": str(data_root.parent)})
    assert r.status_code == 403


# --- "New Plot" sources ---


def test_sources_lists_file(client):
    sources = {s["id"]: s for s in client.get("/sources").json()}
    assert sources["file"]["kind"] == "file"
    # Live sources appear only when their optional deps are installed.
    if "parquet_dir" in sources:
        assert sources["parquet_dir"]["kind"] == "directory"


def test_open_source_directory_needs_path_422(client):
    """A directory source can't be started without a folder path."""
    r = client.post("/sources/parquet_dir", json={})
    # 422 if available, 404 if the optional dep is missing -- both are non-200.
    assert r.status_code in (404, 422)


def test_open_unknown_source_404(client):
    r = client.post("/sources/nope", json={})
    assert r.status_code == 404


# --- CSV staged loading: encoding is asked before the file is read ---


@pytest.fixture
def latin1_csv(tmp_path):
    """A semicolon CSV whose header carries a non-UTF-8 byte (µ, 0xb5 in latin1)."""
    path = tmp_path / "signals.csv"
    path.write_bytes("time;pµ\n0;1,0\n1;2,0\n2;3,0\n".encode("latin1"))
    return path


def test_csv_asks_encoding_before_reading(client, latin1_csv):
    # Stage 1 must not read the file with a guessed encoding -> no decode error.
    r = client.post("/files", json={"path": str(latin1_csv)})
    assert r.status_code == 200
    stage1 = {p["name"] for p in r.json()["params"]}
    assert "encoding" in stage1 and "yfields" not in stage1


def test_csv_loads_with_chosen_encoding(client, latin1_csv):
    file_id = client.post("/files", json={"path": str(latin1_csv)}).json()["file_id"]
    # Stage 1: choose latin1.
    r1 = client.post(
        f"/files/{file_id}",
        json={"answers": {"encoding": "latin1", "seperator": ";", "decimal": ",", "droplines": 0}},
    ).json()
    cols = next(p for p in r1["params"] if p["name"] == "yfields")["choices"]
    assert "pµ" in cols  # the µ column decoded correctly
    # Stage 2: take the columns, generate a time axis.
    r2 = client.post(
        f"/files/{file_id}",
        json={"answers": {"yfields": cols, "dtfield": None, "samplerate": 100}},
    ).json()
    assert r2["ready"] is True
    assert {c["name"] for c in r2["curves"]} == set(cols)


def test_csv_wrong_encoding_surfaces_422(client, latin1_csv):
    file_id = client.post("/files", json={"path": str(latin1_csv)}).json()["file_id"]
    # Insisting on utf-8 fails when the header is read in stage 2.
    r = client.post(
        f"/files/{file_id}",
        json={"answers": {"encoding": "utf-8", "seperator": ";", "decimal": ",", "droplines": 0}},
    )
    assert r.status_code == 422
