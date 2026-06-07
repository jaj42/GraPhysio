"""Server-side file browsing for the web file picker.

The self-hosted backend keeps the data files; the browser cannot read a real
server path from its native file dialog, so instead the frontend navigates the
*server's* filesystem through this endpoint and posts back the path it picks.

Browsing is confined to a configured root (``GRAPHYSIO_DATA_ROOT``, default the
user's home) and every requested path is resolved and checked to be inside it, so
a crafted ``..`` cannot escape the root.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from graphysio.server.loaders import SUPPORTED_SUFFIXES

__all__ = ["BrowseEntry", "BrowseListing", "data_root", "list_dir"]


def data_root() -> Path:
    """The directory browsing is confined to."""
    return Path(os.environ.get("GRAPHYSIO_DATA_ROOT", Path.home())).resolve()


@dataclass(frozen=True)
class BrowseEntry:
    name: str
    path: str  # absolute, resolved
    is_dir: bool
    size: int  # bytes; 0 for directories
    suffix: str  # lowercased extension, "" for directories


@dataclass(frozen=True)
class BrowseListing:
    root: str
    path: str  # directory being listed
    parent: str | None  # parent dir, or None when at the root
    entries: list[BrowseEntry]


def _resolve_within_root(path: str | None) -> Path:
    """Resolve ``path`` and ensure it stays inside the data root."""
    root = data_root()
    target = root if not path else Path(path).resolve()
    if target != root and root not in target.parents:
        msg = f"Path outside the browsable root: {path!r}"
        raise PermissionError(msg)
    return target


def list_dir(path: str | None = None) -> BrowseListing:
    """List sub-directories and supported files under ``path`` (default: root).

    Hidden entries (dotfiles/dotdirs) and unsupported files are skipped, to keep the
    picker focused on loadable data. Entries are sorted directories-first, then
    case-insensitively by name.
    """
    root = data_root()
    target = _resolve_within_root(path)
    if not target.is_dir():
        msg = f"Not a directory: {target}"
        raise NotADirectoryError(msg)

    entries: list[BrowseEntry] = []
    for child in target.iterdir():
        if child.name.startswith("."):
            continue  # hidden file/dir
        try:
            is_dir = child.is_dir()
            suffix = child.suffix.lower()
            if not is_dir and suffix not in SUPPORTED_SUFFIXES:
                continue
            size = 0 if is_dir else child.stat().st_size
        except OSError:
            continue  # unreadable entry, skip it
        entries.append(
            BrowseEntry(
                name=child.name,
                path=str(child),
                is_dir=is_dir,
                size=size,
                suffix="" if is_dir else suffix,
            )
        )

    entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
    parent = None if target == root else str(target.parent)
    return BrowseListing(root=str(root), path=str(target), parent=parent, entries=entries)
