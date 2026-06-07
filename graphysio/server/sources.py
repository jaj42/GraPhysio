"""Non-file data sources for the web "New Plot" menu.

Loading from a file is only one way in; GraPhysio also reads from live sources
(DWC, Iceberg) and from a directory of parquet files. Those readers take no file
path -- they drive their whole configuration (connection, table, columns, ...)
through the same staged ``get_params``/``set_data`` loop as file readers, so once
created they ride the existing ``POST /files/{id}`` answer flow.

Each source declares a ``kind`` that tells the frontend how to start it:

* ``"file"``      -- pick a file in the server-side browser (handled by ``/files``).
* ``"directory"`` -- pick a folder in the browser; the path seeds the reader.
* ``"params"``    -- no path at all; go straight to the parameter form.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from graphysio.readdata import DwcReader, IcebergReader, ParquetDirReader
from graphysio.readdata.baseclass import BaseReader

__all__ = ["Source", "UnknownSourceError", "available_sources", "make_source_reader"]


class UnknownSourceError(KeyError):
    """Raised for an unregistered or unavailable source id."""


@dataclass(frozen=True)
class _SourceDef:
    label: str
    reader_cls: type[BaseReader]
    kind: str  # "directory" | "params"


# Non-file sources, in menu order. Availability follows the reader's optional deps.
_SOURCES: dict[str, _SourceDef] = {
    "dwc": _SourceDef("DWC", DwcReader, "params"),
    "iceberg": _SourceDef("Iceberg", IcebergReader, "params"),
    "parquet_dir": _SourceDef("Parquet directory", ParquetDirReader, "directory"),
}


@dataclass(frozen=True)
class Source:
    id: str
    label: str
    kind: str


def available_sources() -> list[Source]:
    """The selectable sources: always 'file', plus any installed live sources."""
    sources = [Source("file", "File", "file")]
    sources += [
        Source(sid, d.label, d.kind)
        for sid, d in _SOURCES.items()
        if d.reader_cls.is_available
    ]
    return sources


def make_source_reader(source_id: str, path: str | None = None) -> BaseReader:
    """Build a reader for a non-file source, seeding the directory path if needed."""
    try:
        sdef = _SOURCES[source_id]
    except KeyError as e:
        msg = f"Unknown source: {source_id!r}"
        raise UnknownSourceError(msg) from e
    if not sdef.reader_cls.is_available:
        msg = f"Source not available (missing dependency): {source_id!r}"
        raise UnknownSourceError(msg)

    reader = sdef.reader_cls()
    if sdef.kind == "directory":
        if not path:
            msg = f"Source {source_id!r} needs a directory path"
            raise ValueError(msg)
        reader.set_data({"path": Path(path)})
    return reader
