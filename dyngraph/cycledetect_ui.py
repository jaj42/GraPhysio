# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\cycledetect.ui'
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

class Ui_CycleDetection(object):
    def setupUi(self, CycleDetection):
        CycleDetection.setObjectName(_fromUtf8("CycleDetection"))
        CycleDetection.resize(387, 371)
        self.verticalLayout = QtGui.QVBoxLayout(CycleDetection)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.table = QtGui.QTableWidget(CycleDetection)
        self.table.setColumnCount(2)
        self.table.setObjectName(_fromUtf8("table"))
        self.table.setRowCount(0)
        self.verticalLayout.addWidget(self.table)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.okButton = QtGui.QPushButton(CycleDetection)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton(CycleDetection)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CycleDetection)
        QtCore.QMetaObject.connectSlotsByName(CycleDetection)

    def retranslateUi(self, CycleDetection):
        CycleDetection.setWindowTitle(_translate("CycleDetection", "Cycle Detection", None))
        self.okButton.setText(_translate("CycleDetection", "Ok", None))
        self.cancelButton.setText(_translate("CycleDetection", "Cancel", None))

