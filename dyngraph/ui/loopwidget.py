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
        self.horizontalLayout = QtGui.QHBoxLayout(LoopWidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.graphicsView = PlotWidget(LoopWidget)
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.horizontalLayout.addWidget(self.graphicsView)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 1)
        self.lblIdx = QtGui.QLabel(LoopWidget)
        self.lblIdx.setAlignment(QtCore.Qt.AlignCenter)
        self.lblIdx.setObjectName(_fromUtf8("lblIdx"))
        self.gridLayout.addWidget(self.lblIdx, 3, 0, 1, 1)
        self.btnPrev = QtGui.QPushButton(LoopWidget)
        self.btnPrev.setObjectName(_fromUtf8("btnPrev"))
        self.gridLayout.addWidget(self.btnPrev, 1, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 0, 0, 1, 1)
        self.btnNext = QtGui.QPushButton(LoopWidget)
        self.btnNext.setObjectName(_fromUtf8("btnNext"))
        self.gridLayout.addWidget(self.btnNext, 1, 1, 1, 1)
        self.btnDelete = QtGui.QPushButton(LoopWidget)
        self.btnDelete.setObjectName(_fromUtf8("btnDelete"))
        self.gridLayout.addWidget(self.btnDelete, 4, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 5, 1, 1, 1)
        self.lblTot = QtGui.QLabel(LoopWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblTot.sizePolicy().hasHeightForWidth())
        self.lblTot.setSizePolicy(sizePolicy)
        self.lblTot.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTot.setObjectName(_fromUtf8("lblTot"))
        self.gridLayout.addWidget(self.lblTot, 3, 1, 1, 1)
        self.label = QtGui.QLabel(LoopWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtGui.QLabel(LoopWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(LoopWidget)
        QtCore.QMetaObject.connectSlotsByName(LoopWidget)

    def retranslateUi(self, LoopWidget):
        LoopWidget.setWindowTitle(_translate("LoopWidget", "Form", None))
        self.lblIdx.setText(_translate("LoopWidget", "1", None))
        self.btnPrev.setText(_translate("LoopWidget", "<", None))
        self.btnNext.setText(_translate("LoopWidget", ">", None))
        self.btnDelete.setText(_translate("LoopWidget", "Delete", None))
        self.lblTot.setText(_translate("LoopWidget", "1", None))
        self.label.setText(_translate("LoopWidget", "Loop #", None))
        self.label_2.setText(_translate("LoopWidget", "of", None))

from pyqtgraph import PlotWidget
