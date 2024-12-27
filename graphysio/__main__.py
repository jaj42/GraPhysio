import argparse

# Make sure pyqtgraph uses this instead of another installed version
import PySide6  # noqa

from graphysio.main import main as graphysio_main

try:
    from pyshortcuts import make_shortcut

    shortcuts_avail = True
except ImportError:
    shortcuts_avail = False


def mk_shortscuts() -> None:
    pycmd = "_ -m graphysio"
    make_shortcut(pycmd, name="GraPhysio", terminal=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GraPhysio")
    parser.add_argument(
        "-S",
        "--shortcuts",
        action="store_true",
        help="Install Desktop shortcuts.",
    )
    args = parser.parse_args()

    if args.shortcuts and shorcuts_avail:
        mk_shortscuts()
    else:
        graphysio_main()
