# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setuppuloop.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SetupPULoop(object):
    def setupUi(self, SetupPULoop):
        SetupPULoop.setObjectName("SetupPULoop")
        SetupPULoop.resize(387, 371)
        self.verticalLayout = QtWidgets.QVBoxLayout(SetupPULoop)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.formLayout_2.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label = QtWidgets.QLabel(SetupPULoop)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.comboU = QtWidgets.QComboBox(SetupPULoop)
        self.comboU.setObjectName("comboU")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comboU)
        self.label_2 = QtWidgets.QLabel(SetupPULoop)
        self.label_2.setObjectName("label_2")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.comboP = QtWidgets.QComboBox(SetupPULoop)
        self.comboP.setObjectName("comboP")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.comboP)
        self.verticalLayout.addLayout(self.formLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.okButton = QtWidgets.QPushButton(SetupPULoop)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(SetupPULoop)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(SetupPULoop)
        QtCore.QMetaObject.connectSlotsByName(SetupPULoop)

    def retranslateUi(self, SetupPULoop):
        _translate = QtCore.QCoreApplication.translate
        SetupPULoop.setWindowTitle(_translate("SetupPULoop", "Set up PU-Loop"))
        self.label.setText(_translate("SetupPULoop", "Velocity (U)"))
        self.label_2.setText(_translate("SetupPULoop", "Pressure (P)"))
        self.okButton.setText(_translate("SetupPULoop", "Ok"))
        self.cancelButton.setText(_translate("SetupPULoop", "Cancel"))
