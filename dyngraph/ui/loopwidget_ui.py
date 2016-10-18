# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\designer\loopwidget.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_LoopWidget(object):
    def setupUi(self, LoopWidget):
        LoopWidget.setObjectName(_fromUtf8("LoopWidget"))
        LoopWidget.resize(763, 619)
        self.horizontalLayout_2 = QtGui.QHBoxLayout(LoopWidget)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.graphicsView = PlotWidget(LoopWidget)
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.horizontalLayout_2.addWidget(self.graphicsView)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnPrev = QtGui.QPushButton(LoopWidget)
        self.btnPrev.setObjectName(_fromUtf8("btnPrev"))
        self.horizontalLayout.addWidget(self.btnPrev)
        self.btnNext = QtGui.QPushButton(LoopWidget)
        self.btnNext.setObjectName(_fromUtf8("btnNext"))
        self.horizontalLayout.addWidget(self.btnNext)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(LoopWidget)
        QtCore.QMetaObject.connectSlotsByName(LoopWidget)

    def retranslateUi(self, LoopWidget):
        LoopWidget.setWindowTitle(_translate("LoopWidget", "Form", None))
        self.btnPrev.setText(_translate("LoopWidget", "<", None))
        self.btnNext.setText(_translate("LoopWidget", ">", None))

from pyqtgraph import PlotWidget
