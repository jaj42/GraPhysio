import argparse

from pyshortcuts import make_shortcut

from .main import main as graphysio_main


def mk_shortscuts():
    pycmd = "_ -m graphysio"
    make_shortcut(pycmd, name="GraPhysio", terminal=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GraPhysio")
    parser.add_argument(
        "-S", "--shortcuts", action="store_true", help="Install Desktop shortcuts."
    )
    args = parser.parse_args()

    if args.shortcuts:
        mk_shortscuts()
    else:
        graphysio_main()
