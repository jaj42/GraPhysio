import sys
from pathlib import Path

# Make sure pyqtgraph uses this instead of another installed version
import PySide6  # noqa

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCommandLineParser
from graphysio.mainui import MainUi


def parse(app):
    parser = QCommandLineParser()
    parser.addHelpOption()
    # parser.addVersionOption()
    parser.addPositionalArgument("file", "File to open.", "[file]")
    parser.process(app)
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

    sys.exit(app.exec_())
