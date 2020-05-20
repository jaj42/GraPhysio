# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filter.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Filter(object):
    def setupUi(self, Filter):
        Filter.setObjectName("Filter")
        Filter.resize(387, 371)
        self.verticalLayout = QtWidgets.QVBoxLayout(Filter)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table = QtWidgets.QTableWidget(Filter)
        self.table.setColumnCount(2)
        self.table.setObjectName("table")
        self.table.setRowCount(0)
        self.verticalLayout.addWidget(self.table)
        self.chkNewcurve = QtWidgets.QCheckBox(Filter)
        self.chkNewcurve.setObjectName("chkNewcurve")
        self.verticalLayout.addWidget(self.chkNewcurve)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.okButton = QtWidgets.QPushButton(Filter)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(Filter)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Filter)
        QtCore.QMetaObject.connectSlotsByName(Filter)

    def retranslateUi(self, Filter):
        _translate = QtCore.QCoreApplication.translate
        Filter.setWindowTitle(_translate("Filter", "Filter"))
        self.chkNewcurve.setText(_translate("Filter", "Create new curve"))
        self.okButton.setText(_translate("Filter", "Ok"))
        self.cancelButton.setText(_translate("Filter", "Cancel"))
