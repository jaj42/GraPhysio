"""In-memory session state for the (self-hosted, single/few-user) web backend.

A ``Session`` holds the loaded curves at full resolution. Curves are kept in
memory; this is fine for the single-user deployment target. The store is a thin
keyed collection so a future multi-user setup can add per-user isolation and
on-disk Arrow/Parquet spillover without changing call sites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from graphysio.core.timeseries import estimate_samplerate
from graphysio.server.loaders import load_file

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
    """A single user's loaded curves."""

    curves: dict[str, pd.Series] = field(default_factory=dict)

    def load(self, path: str | Path) -> list[CurveMeta]:
        """Load a file and add its curves to the session (later names win on clash)."""
        new = load_file(path)
        self.curves.update(new)
        return [CurveMeta.from_series(n, new[n]) for n in new]

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
