import sys

from pyqtgraph.Qt import QtWidgets

from graphysio.mainui import MainUi


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    sys.exit(app.exec_())
