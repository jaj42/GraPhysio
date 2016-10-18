# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\designer\setuppuloop.ui'
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

class Ui_SetupPULoop(object):
    def setupUi(self, SetupPULoop):
        SetupPULoop.setObjectName(_fromUtf8("SetupPULoop"))
        SetupPULoop.resize(387, 371)
        self.verticalLayout = QtGui.QVBoxLayout(SetupPULoop)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout_2 = QtGui.QFormLayout()
        self.formLayout_2.setSizeConstraint(QtGui.QLayout.SetMaximumSize)
        self.formLayout_2.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.label = QtGui.QLabel(SetupPULoop)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.comboU = QtGui.QComboBox(SetupPULoop)
        self.comboU.setObjectName(_fromUtf8("comboU"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.comboU)
        self.label_2 = QtGui.QLabel(SetupPULoop)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.comboP = QtGui.QComboBox(SetupPULoop)
        self.comboP.setObjectName(_fromUtf8("comboP"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.comboP)
        self.verticalLayout.addLayout(self.formLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.okButton = QtGui.QPushButton(SetupPULoop)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton(SetupPULoop)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(SetupPULoop)
        QtCore.QMetaObject.connectSlotsByName(SetupPULoop)

    def retranslateUi(self, SetupPULoop):
        SetupPULoop.setWindowTitle(_translate("SetupPULoop", "Set up PU-Loop", None))
        self.label.setText(_translate("SetupPULoop", "Velocity (U)", None))
        self.label_2.setText(_translate("SetupPULoop", "Pressure (P)", None))
        self.okButton.setText(_translate("SetupPULoop", "Ok", None))
        self.cancelButton.setText(_translate("SetupPULoop", "Cancel", None))

