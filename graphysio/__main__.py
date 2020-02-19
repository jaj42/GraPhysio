#!/usr/bin/env python3

import sys
from pyqtgraph.Qt import QtGui
from graphysio.mainui import MainUi

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    status = app.exec_()
    sys.exit(status)
