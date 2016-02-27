#!/usr/bin/env python2.7

import sys
from PyQt4 import QtCore, QtGui
from ui_init import MainUi

qApp = QtGui.QApplication(sys.argv)

wMain = MainUi()
wMain.show()

sys.exit(qApp.exec_())
