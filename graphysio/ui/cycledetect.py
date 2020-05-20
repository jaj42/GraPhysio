# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cycledetect.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CycleDetection(object):
    def setupUi(self, CycleDetection):
        CycleDetection.setObjectName("CycleDetection")
        CycleDetection.resize(387, 371)
        self.verticalLayout = QtWidgets.QVBoxLayout(CycleDetection)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table = QtWidgets.QTableWidget(CycleDetection)
        self.table.setColumnCount(2)
        self.table.setObjectName("table")
        self.table.setRowCount(0)
        self.verticalLayout.addWidget(self.table)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.okButton = QtWidgets.QPushButton(CycleDetection)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(CycleDetection)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CycleDetection)
        QtCore.QMetaObject.connectSlotsByName(CycleDetection)

    def retranslateUi(self, CycleDetection):
        _translate = QtCore.QCoreApplication.translate
        CycleDetection.setWindowTitle(_translate("CycleDetection", "Cycle Detection"))
        self.okButton.setText(_translate("CycleDetection", "Ok"))
        self.cancelButton.setText(_translate("CycleDetection", "Cancel"))
