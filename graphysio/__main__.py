import argparse
import sys

# Make sure pyqtgraph uses this instead of another installed version
import PySide6  # noqa  # pyright: ignore[reportUnusedImport]

from graphysio.desktop import install_xdg
from graphysio.main import main as graphysio_main

try:
    from pyshortcuts import make_shortcut

    shortcuts_avail = True
except ImportError:
    shortcuts_avail = False


def mk_shortscuts() -> None:
    pycmd = "_ -m graphysio"
    _ = make_shortcut(pycmd, name="GraPhysio", terminal=False)  # pyright: ignore[reportPossiblyUnboundVariable]


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GraPhysio")
    _ = parser.add_argument(
        "-S",
        "--shortcuts",
        action="store_true",
        help="Install Desktop shortcuts and XDG MIME type associations.",
    )
    args = parser.parse_args()

    if args.shortcuts:
        if sys.platform == "linux":
            install_xdg()
        elif shortcuts_avail:
            mk_shortscuts()
        else:
            print("No shortcut installer available on this platform.")
    else:
        graphysio_main()
