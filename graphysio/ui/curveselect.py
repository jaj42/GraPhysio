# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'curveselect.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CurveSelection(object):
    def setupUi(self, CurveSelection):
        CurveSelection.setObjectName("CurveSelection")
        CurveSelection.resize(292, 329)
        self.verticalLayout = QtWidgets.QVBoxLayout(CurveSelection)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lstCurves = QtWidgets.QListWidget(CurveSelection)
        self.lstCurves.setObjectName("lstCurves")
        self.verticalLayout.addWidget(self.lstCurves)
        self.btnProperties = QtWidgets.QPushButton(CurveSelection)
        self.btnProperties.setObjectName("btnProperties")
        self.verticalLayout.addWidget(self.btnProperties)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.okButton = QtWidgets.QPushButton(CurveSelection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okButton.sizePolicy().hasHeightForWidth())
        self.okButton.setSizePolicy(sizePolicy)
        self.okButton.setChecked(False)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(CurveSelection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cancelButton.sizePolicy().hasHeightForWidth())
        self.cancelButton.setSizePolicy(sizePolicy)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CurveSelection)
        QtCore.QMetaObject.connectSlotsByName(CurveSelection)

    def retranslateUi(self, CurveSelection):
        _translate = QtCore.QCoreApplication.translate
        CurveSelection.setWindowTitle(_translate("CurveSelection", "Select visible curves"))
        self.btnProperties.setText(_translate("CurveSelection", "Curve Properties"))
        self.okButton.setText(_translate("CurveSelection", "Ok"))
        self.cancelButton.setText(_translate("CurveSelection", "Cancel"))
