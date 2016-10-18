# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\designer\filter.ui'
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

class Ui_Filter(object):
    def setupUi(self, Filter):
        Filter.setObjectName(_fromUtf8("Filter"))
        Filter.resize(387, 371)
        self.verticalLayout = QtGui.QVBoxLayout(Filter)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.table = QtGui.QTableWidget(Filter)
        self.table.setColumnCount(2)
        self.table.setObjectName(_fromUtf8("table"))
        self.table.setRowCount(0)
        self.verticalLayout.addWidget(self.table)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.okButton = QtGui.QPushButton(Filter)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton(Filter)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Filter)
        QtCore.QMetaObject.connectSlotsByName(Filter)

    def retranslateUi(self, Filter):
        Filter.setWindowTitle(_translate("Filter", "Filter", None))
        self.okButton.setText(_translate("Filter", "Ok", None))
        self.cancelButton.setText(_translate("Filter", "Cancel", None))

