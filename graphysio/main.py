import sys

from pyqtgraph.Qt import QtGui

from graphysio.mainui import MainUi


def main():
    app = QtGui.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    sys.exit(app.exec_())
