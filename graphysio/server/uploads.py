"""Storage for browser-uploaded files.

The server-side file browser navigates the *server's* filesystem, which covers the
common self-hosted case where the (often multi-GB) data already lives on the box.
But a user may also have an ad-hoc local file that is *not* on the server -- for
that we accept a real upload.

The uploaded bytes are streamed to a managed temp directory, keeping the original
suffix so the reader dispatch-by-extension still works, then the saved path rides
the exact same staged ``open_file`` flow as a server-side file. Uploads are scoped
to the process and cleared with the session (``DELETE /session``).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import BinaryIO

from graphysio.server.loaders import SUPPORTED_SUFFIXES, UnsupportedFormatError

__all__ = ["clear_uploads", "save_upload", "upload_root"]


def upload_root() -> Path:
    """The directory uploaded files are written to (created on demand)."""
    root = Path(
        os.environ.get(
            "GRAPHYSIO_UPLOAD_DIR", Path(tempfile.gettempdir()) / "graphysio-uploads"
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_upload(filename: str, src: BinaryIO) -> Path:
    """Stream an uploaded file to the upload dir, returning its saved path.

    The destination name is randomized to avoid collisions, but keeps the original
    (lowercased) suffix so the reader is selected correctly. Raises
    :class:`UnsupportedFormatError` for an extension no reader handles.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        msg = (
            f"Unsupported file type {suffix or filename!r}; "
            f"supported: {', '.join(SUPPORTED_SUFFIXES)}"
        )
        raise UnsupportedFormatError(msg)
    dest = upload_root() / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(src, out)
    return dest


def clear_uploads() -> None:
    """Remove every uploaded file (best-effort; called on session reset)."""
    root = upload_root()
    for child in root.iterdir():
        try:
            if child.is_file():
                child.unlink()
        except OSError:
            continue  # someone else's lock / race; leave it
