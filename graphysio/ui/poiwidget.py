# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'poiwidget.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_POISelectorWidget(object):
    def setupUi(self, POISelectorWidget):
        POISelectorWidget.setObjectName("POISelectorWidget")
        POISelectorWidget.resize(763, 601)
        self.horizontalLayout = QtWidgets.QHBoxLayout(POISelectorWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.groupBox = QtWidgets.QGroupBox(POISelectorWidget)
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.radioFixDisabled = QtWidgets.QRadioButton(self.groupBox)
        self.radioFixDisabled.setChecked(True)
        self.radioFixDisabled.setObjectName("radioFixDisabled")
        self.buttonGroup = QtWidgets.QButtonGroup(POISelectorWidget)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.radioFixDisabled)
        self.verticalLayout.addWidget(self.radioFixDisabled)
        self.radioFixMinimum = QtWidgets.QRadioButton(self.groupBox)
        self.radioFixMinimum.setObjectName("radioFixMinimum")
        self.buttonGroup.addButton(self.radioFixMinimum)
        self.verticalLayout.addWidget(self.radioFixMinimum)
        self.radioFixMaximum = QtWidgets.QRadioButton(self.groupBox)
        self.radioFixMaximum.setObjectName("radioFixMaximum")
        self.buttonGroup.addButton(self.radioFixMaximum)
        self.verticalLayout.addWidget(self.radioFixMaximum)
        self.radioFixSecondDerivative = QtWidgets.QRadioButton(self.groupBox)
        self.radioFixSecondDerivative.setObjectName("radioFixSecondDerivative")
        self.buttonGroup.addButton(self.radioFixSecondDerivative)
        self.verticalLayout.addWidget(self.radioFixSecondDerivative)
        self.verticalLayout_2.addWidget(self.groupBox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.retranslateUi(POISelectorWidget)
        QtCore.QMetaObject.connectSlotsByName(POISelectorWidget)

    def retranslateUi(self, POISelectorWidget):
        _translate = QtCore.QCoreApplication.translate
        POISelectorWidget.setWindowTitle(_translate("POISelectorWidget", "Form"))
        self.groupBox.setTitle(_translate("POISelectorWidget", "Fix Position"))
        self.radioFixDisabled.setText(_translate("POISelectorWidget", "Disabled"))
        self.radioFixMinimum.setText(_translate("POISelectorWidget", "Local Minimum"))
        self.radioFixMaximum.setText(_translate("POISelectorWidget", "Local Maximum"))
        self.radioFixSecondDerivative.setText(_translate("POISelectorWidget", "2nd derivative peak"))
