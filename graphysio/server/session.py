"""In-memory session state for the (self-hosted, single/few-user) web backend.

A ``Session`` holds loaded curves at full resolution plus any readers waiting for
parameters (the staged open flow). Curves are kept in memory; fine for the
single-user target. The store is a thin keyed collection so a future multi-user
setup can add per-user isolation and on-disk spillover without changing call sites.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from graphysio.core.params import ParamSpec, default_answers, gather
from graphysio.core.timeseries import estimate_samplerate
from graphysio.readdata.baseclass import BaseReader
from graphysio.server.loaders import make_reader, plotdata_to_curves
from graphysio.server.sources import make_source_reader

__all__ = ["CurveMeta", "Session", "SessionStore", "STORE"]


@dataclass(frozen=True)
class CurveMeta:
    """Lightweight description of a curve, safe to serialize to JSON."""

    name: str
    t0: int  # first timestamp, int64 epoch-ns
    t1: int  # last timestamp, int64 epoch-ns
    n_samples: int
    samplerate: float

    @classmethod
    def from_series(cls, name: str, series: pd.Series) -> "CurveMeta":
        return cls(
            name=name,
            t0=int(series.index[0]),
            t1=int(series.index[-1]),
            n_samples=int(len(series)),
            samplerate=estimate_samplerate(series),
        )


@dataclass
class Session:
    """A single user's loaded curves and any readers awaiting parameters."""

    curves: dict[str, pd.Series] = field(default_factory=dict)
    _pending: dict[str, BaseReader] = field(default_factory=dict)

    def _add(self, reader: BaseReader) -> list[CurveMeta]:
        new = plotdata_to_curves(reader())
        self.curves.update(new)
        return [CurveMeta.from_series(n, new[n]) for n in new]

    def load(self, path: str | Path) -> list[CurveMeta]:
        """One-shot load using default answers (select all curves, no index pick).

        Convenience for files that carry their own time index (e.g. parquet/edf).
        For files needing choices (CSV time column, etc.) use the staged flow.
        """
        reader = make_reader(Path(path))
        gather(reader, default_answers)
        return self._add(reader)

    # --- Staged interactive flow (web form) ---

    def open_file(self, path: str | Path) -> tuple[str, list[ParamSpec]]:
        """Register a reader for ``path`` and return its first param schema."""
        return self._register(make_reader(Path(path)))

    def open_source(
        self, source_id: str, path: str | None = None
    ) -> tuple[str, list[ParamSpec]]:
        """Register a non-file source reader and return its first param schema."""
        return self._register(make_source_reader(source_id, path))

    def _register(self, reader: BaseReader) -> tuple[str, list[ParamSpec]]:
        file_id = uuid.uuid4().hex
        self._pending[file_id] = reader
        return file_id, reader.get_params()

    def answer(
        self, file_id: str, answers: dict
    ) -> tuple[list[ParamSpec], list[CurveMeta]]:
        """Feed answers to a pending reader.

        Returns ``(next_params, [])`` if more input is needed (staging), or
        ``([], curves)`` once the reader runs and its curves are added.
        """
        try:
            reader = self._pending[file_id]
        except KeyError as e:
            msg = f"No pending file: {file_id!r}"
            raise KeyError(msg) from e
        reader.set_data(answers)
        params = reader.get_params()
        if params:
            return params, []
        curves = self._add(reader)
        del self._pending[file_id]
        return [], curves

    def metadata(self) -> list[CurveMeta]:
        return [CurveMeta.from_series(n, s) for n, s in self.curves.items()]

    def get(self, name: str) -> pd.Series:
        try:
            return self.curves[name]
        except KeyError as e:
            msg = f"No such curve: {name!r}"
            raise KeyError(msg) from e


class SessionStore:
    """Keyed collection of sessions. Single-user default lives under ``DEFAULT``."""

    DEFAULT = "default"

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str = DEFAULT) -> Session:
        return self._sessions.setdefault(session_id, Session())

    def reset(self, session_id: str = DEFAULT) -> None:
        self._sessions.pop(session_id, None)


# Process-wide store. Sufficient for the self-hosted single/few-user target.
STORE = SessionStore()
