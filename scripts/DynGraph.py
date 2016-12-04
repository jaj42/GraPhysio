import sys
from PyQt4 import QtGui
from dyngraph.mainui import MainUi

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    sys.exit(app.exec_())
