"""FastAPI application exposing the GraPhysio data path.

Endpoints (Phase 2 skeleton):

* ``GET  /health``                      -- liveness probe
* ``POST /session/load``                -- load a server-side file into the session
* ``GET  /curves``                      -- list loaded curves + metadata
* ``GET  /curves/{name}/window``        -- decimated window as Arrow IPC binary
* ``DELETE /session``                   -- clear the session

The window endpoint is the performance-critical one: it slices the full-resolution
curve to the requested time range and min/max-decimates it to the viewport width
(see ``graphysio.core.downsample``), returning a compact Arrow stream.

Run with::

    uvicorn graphysio.server.app:app --reload
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graphysio.core.downsample import POINTS_PER_PIXEL, downsample_series
from graphysio.server.arrow import ARROW_MEDIA_TYPE, series_to_arrow_ipc
from graphysio.server.loaders import SUPPORTED_SUFFIXES, UnsupportedFormatError
from graphysio.server.session import STORE, CurveMeta

app = FastAPI(title="GraPhysio", version="0.1.0")

# Allow the local React dev server to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoadRequest(BaseModel):
    path: str


class LoadResponse(BaseModel):
    curves: list[CurveMeta]


class OpenResponse(BaseModel):
    """Result of a staged open step: either more params are needed, or curves loaded."""

    file_id: str
    ready: bool
    params: list[dict] = []
    curves: list[CurveMeta] = []


class AnswerRequest(BaseModel):
    answers: dict


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "supported_formats": list(SUPPORTED_SUFFIXES)}


@app.post("/session/load", response_model=LoadResponse)
def load(req: LoadRequest) -> LoadResponse:
    session = STORE.get()
    try:
        session.load(req.path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=415, detail=str(e)) from e
    except Exception as e:  # malformed file, parse error, ...
        raise HTTPException(status_code=422, detail=f"Could not load file: {e}") from e
    return LoadResponse(curves=session.metadata())


@app.post("/files", response_model=OpenResponse)
def open_file(req: LoadRequest) -> OpenResponse:
    """Register a file and return the parameter schema its reader needs."""
    session = STORE.get()
    try:
        file_id, params = session.open_file(req.path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=415, detail=str(e)) from e
    return OpenResponse(
        file_id=file_id,
        ready=not params,
        params=[p.to_dict() for p in params],
    )


@app.post("/files/{file_id}", response_model=OpenResponse)
def answer_file(file_id: str, req: AnswerRequest) -> OpenResponse:
    """Supply answers for a pending file; returns the next stage or the loaded curves."""
    session = STORE.get()
    try:
        params, curves = session.answer(file_id, req.answers)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:  # parse/load failure with the given answers
        raise HTTPException(status_code=422, detail=f"Could not load file: {e}") from e
    return OpenResponse(
        file_id=file_id,
        ready=not params,
        params=[p.to_dict() for p in params],
        curves=curves,
    )


@app.get("/curves", response_model=list[CurveMeta])
def list_curves() -> list[CurveMeta]:
    return STORE.get().metadata()


@app.delete("/session", status_code=204)
def clear_session() -> Response:
    STORE.reset()
    return Response(status_code=204)


@app.get("/curves/{name}/window")
def curve_window(
    name: str,
    t0: Optional[int] = Query(None, description="window start, int64 epoch-ns"),
    t1: Optional[int] = Query(None, description="window end, int64 epoch-ns"),
    px: int = Query(1000, gt=0, le=20000, description="viewport width in pixels"),
    method: str = Query("m4", pattern="^(m4|minmax)$"),
) -> Response:
    """Return the decimated [t0, t1] window of a curve as Arrow IPC binary."""
    try:
        series = STORE.get().get(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    window = downsample_series(series, t0=t0, t1=t1, px=px, method=method)
    payload = series_to_arrow_ipc(window)
    return Response(
        content=payload,
        media_type=ARROW_MEDIA_TYPE,
        headers={
            "X-Points": str(len(window)),
            "X-Points-Per-Pixel": str(POINTS_PER_PIXEL[method]),
        },
    )
