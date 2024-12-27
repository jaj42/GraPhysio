import sys
from pathlib import Path

# Make sure pyqtgraph uses this instead of another installed version
import PySide6  # noqa

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCommandLineParser, QCommandLineOption
from graphysio.mainui import MainUi

import multiprocessing

try:
    from pyshortcuts import make_shortcut

    shorcuts_avail = True
except ImportError:
    shorcuts_avail = False


def mk_shortscuts() -> None:
    if shorcuts_avail:
        pycmd = "_ -m graphysio"
        make_shortcut(pycmd, name="GraPhysio", terminal=False)


def parse(app):
    parser = QCommandLineParser()
    parser.addHelpOption()
    # parser.addVersionOption()

    parser.addPositionalArgument("file", "File to open.", "[file]")

    shortcuts_option = QCommandLineOption(
        ["S", "shortcuts"], "Generate desktop shortcuts."
    )
    if shorcuts_avail:
        parser.addOption(shortcuts_option)

    parser.process(app)
    if parser.isSet(shortcuts_option):
        mk_shortscuts()
    arguments = parser.positionalArguments()
    if len(arguments) > 0:
        return Path(arguments[0])
    else:
        return None


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("GraPhysio")

    input_file = parse(app)
    winmain = MainUi(input_file=input_file)
    winmain.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
