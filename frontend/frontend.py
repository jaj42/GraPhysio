#!/usr/local/bin/python2.7

#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
#plt.gca().xaxis.set_major_locator(mdates.DayLocator())

import sys
from PyQt4 import QtGui, QtCore
from ui_init import MainUi

qApp = QtGui.QApplication(sys.argv)

wMain = MainUi()
wMain.show()

sys.exit(qApp.exec_())
