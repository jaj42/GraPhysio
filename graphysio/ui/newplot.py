# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'newplot.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_NewPlot(object):
    def setupUi(self, NewPlot):
        NewPlot.setObjectName("NewPlot")
        NewPlot.resize(942, 792)
        NewPlot.setSizeGripEnabled(False)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(NewPlot)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox = QtWidgets.QGroupBox(NewPlot)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.txtFile = QtWidgets.QLineEdit(self.groupBox)
        self.txtFile.setObjectName("txtFile")
        self.horizontalLayout.addWidget(self.txtFile)
        self.btnBrowse = QtWidgets.QPushButton(self.groupBox)
        self.btnBrowse.setObjectName("btnBrowse")
        self.horizontalLayout.addWidget(self.btnBrowse)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(NewPlot)
        self.label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.txtSep = QtWidgets.QComboBox(NewPlot)
        self.txtSep.setEditable(True)
        self.txtSep.setObjectName("txtSep")
        self.txtSep.addItem("")
        self.txtSep.addItem("")
        self.txtSep.addItem("")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txtSep)
        self.label_2 = QtWidgets.QLabel(NewPlot)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.txtDecimal = QtWidgets.QComboBox(NewPlot)
        self.txtDecimal.setEditable(True)
        self.txtDecimal.setObjectName("txtDecimal")
        self.txtDecimal.addItem("")
        self.txtDecimal.addItem("")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txtDecimal)
        self.label_7 = QtWidgets.QLabel(NewPlot)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.txtDateTime = QtWidgets.QComboBox(NewPlot)
        self.txtDateTime.setEditable(True)
        self.txtDateTime.setObjectName("txtDateTime")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.txtDateTime)
        self.label_3 = QtWidgets.QLabel(NewPlot)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.spnLinedrop = QtWidgets.QSpinBox(NewPlot)
        self.spnLinedrop.setObjectName("spnLinedrop")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.spnLinedrop)
        self.label_4 = QtWidgets.QLabel(NewPlot)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.txtEncoding = QtWidgets.QComboBox(NewPlot)
        self.txtEncoding.setEditable(True)
        self.txtEncoding.setObjectName("txtEncoding")
        self.txtEncoding.addItem("")
        self.txtEncoding.addItem("")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.txtEncoding)
        self.label_5 = QtWidgets.QLabel(NewPlot)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.txtTimezone = QtWidgets.QComboBox(NewPlot)
        self.txtTimezone.setEditable(True)
        self.txtTimezone.setObjectName("txtTimezone")
        self.txtTimezone.addItem("")
        self.txtTimezone.addItem("")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.txtTimezone)
        self.verticalLayout_3.addLayout(self.formLayout)
        self.btnLoad = QtWidgets.QPushButton(NewPlot)
        self.btnLoad.setObjectName("btnLoad")
        self.verticalLayout_3.addWidget(self.btnLoad)
        self.line = QtWidgets.QFrame(NewPlot)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout_3.addWidget(self.line)
        self.groupBox_6 = QtWidgets.QGroupBox(NewPlot)
        self.groupBox_6.setObjectName("groupBox_6")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.groupBox_6)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.lstVX = QtWidgets.QComboBox(self.groupBox_6)
        self.lstVX.setMaxCount(4)
        self.lstVX.setObjectName("lstVX")
        self.horizontalLayout_5.addWidget(self.lstVX)
        self.btnRemoveX = QtWidgets.QPushButton(self.groupBox_6)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnRemoveX.sizePolicy().hasHeightForWidth())
        self.btnRemoveX.setSizePolicy(sizePolicy)
        self.btnRemoveX.setObjectName("btnRemoveX")
        self.horizontalLayout_5.addWidget(self.btnRemoveX)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.chkGenX = QtWidgets.QCheckBox(self.groupBox_6)
        self.chkGenX.setChecked(True)
        self.chkGenX.setObjectName("chkGenX")
        self.horizontalLayout_2.addWidget(self.chkGenX)
        self.spnFs = QtWidgets.QSpinBox(self.groupBox_6)
        self.spnFs.setMinimum(1)
        self.spnFs.setMaximum(1000000)
        self.spnFs.setProperty("value", 180)
        self.spnFs.setObjectName("spnFs")
        self.horizontalLayout_2.addWidget(self.spnFs)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_8.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addWidget(self.groupBox_6)
        self.groupBox_5 = QtWidgets.QGroupBox(NewPlot)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.lstVY = QtWidgets.QListView(self.groupBox_5)
        self.lstVY.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.lstVY.setObjectName("lstVY")
        self.horizontalLayout_6.addWidget(self.lstVY)
        self.btnRemoveY = QtWidgets.QPushButton(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnRemoveY.sizePolicy().hasHeightForWidth())
        self.btnRemoveY.setSizePolicy(sizePolicy)
        self.btnRemoveY.setObjectName("btnRemoveY")
        self.horizontalLayout_6.addWidget(self.btnRemoveY)
        self.verticalLayout_7.addLayout(self.horizontalLayout_6)
        self.verticalLayout_3.addWidget(self.groupBox_5)
        self.horizontalLayout_4.addLayout(self.verticalLayout_3)
        self.groupBox_2 = QtWidgets.QGroupBox(NewPlot)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lstVAll = QtWidgets.QTableView(self.groupBox_2)
        self.lstVAll.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.lstVAll.setObjectName("lstVAll")
        self.verticalLayout.addWidget(self.lstVAll)
        self.horizontalLayout1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout1.setObjectName("horizontalLayout1")
        self.btnToX = QtWidgets.QPushButton(self.groupBox_2)
        self.btnToX.setObjectName("btnToX")
        self.horizontalLayout1.addWidget(self.btnToX)
        self.btnToY = QtWidgets.QPushButton(self.groupBox_2)
        self.btnToY.setObjectName("btnToY")
        self.horizontalLayout1.addWidget(self.btnToY)
        self.verticalLayout.addLayout(self.horizontalLayout1)
        self.horizontalLayout_4.addWidget(self.groupBox_2)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.line_2 = QtWidgets.QFrame(NewPlot)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_4.addWidget(self.line_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.btnOk = QtWidgets.QPushButton(NewPlot)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnOk.sizePolicy().hasHeightForWidth())
        self.btnOk.setSizePolicy(sizePolicy)
        self.btnOk.setObjectName("btnOk")
        self.horizontalLayout_3.addWidget(self.btnOk)
        self.btnCancel = QtWidgets.QPushButton(NewPlot)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnCancel.sizePolicy().hasHeightForWidth())
        self.btnCancel.setSizePolicy(sizePolicy)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout_3.addWidget(self.btnCancel)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.retranslateUi(NewPlot)
        self.chkGenX.clicked['bool'].connect(self.lstVX.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(NewPlot)

    def retranslateUi(self, NewPlot):
        _translate = QtCore.QCoreApplication.translate
        NewPlot.setWindowTitle(_translate("NewPlot", "New Plot"))
        self.groupBox.setTitle(_translate("NewPlot", "Open File"))
        self.btnBrowse.setText(_translate("NewPlot", "Browse"))
        self.label.setText(_translate("NewPlot", "Field Seperator"))
        self.txtSep.setItemText(0, _translate("NewPlot", ";"))
        self.txtSep.setItemText(1, _translate("NewPlot", ","))
        self.txtSep.setItemText(2, _translate("NewPlot", "<tab>"))
        self.label_2.setText(_translate("NewPlot", "Decimal Seperator"))
        self.txtDecimal.setItemText(0, _translate("NewPlot", ","))
        self.txtDecimal.setItemText(1, _translate("NewPlot", "."))
        self.label_7.setText(_translate("NewPlot", "Date/Time Format"))
        self.txtDateTime.setItemText(0, _translate("NewPlot", "%Y-%m-%d %H:%M:%S,%f"))
        self.txtDateTime.setItemText(1, _translate("NewPlot", "%Y-%m-%d %H:%M:%S.%f"))
        self.txtDateTime.setItemText(2, _translate("NewPlot", "%H:%M"))
        self.txtDateTime.setItemText(3, _translate("NewPlot", "<seconds>"))
        self.txtDateTime.setItemText(4, _translate("NewPlot", "<milliseconds>"))
        self.txtDateTime.setItemText(5, _translate("NewPlot", "<nanoseconds>"))
        self.txtDateTime.setItemText(6, _translate("NewPlot", "<infer>"))
        self.label_3.setText(_translate("NewPlot", "Drop n first lines"))
        self.label_4.setText(_translate("NewPlot", "Encoding"))
        self.txtEncoding.setItemText(0, _translate("NewPlot", "latin1"))
        self.txtEncoding.setItemText(1, _translate("NewPlot", "utf8"))
        self.label_5.setText(_translate("NewPlot", "Timezone"))
        self.txtTimezone.setItemText(0, _translate("NewPlot", "UTC"))
        self.txtTimezone.setItemText(1, _translate("NewPlot", "CET"))
        self.btnLoad.setText(_translate("NewPlot", "Load Fields"))
        self.groupBox_6.setTitle(_translate("NewPlot", "Time axis"))
        self.btnRemoveX.setText(_translate("NewPlot", "Remove"))
        self.chkGenX.setText(_translate("NewPlot", "Generate with sample rate (Hz):"))
        self.groupBox_5.setTitle(_translate("NewPlot", "Y axis"))
        self.btnRemoveY.setText(_translate("NewPlot", "Remove"))
        self.groupBox_2.setTitle(_translate("NewPlot", "Loaded Fields"))
        self.btnToX.setText(_translate("NewPlot", "Move to X"))
        self.btnToY.setText(_translate("NewPlot", "Move to Y"))
        self.btnOk.setText(_translate("NewPlot", "OK"))
        self.btnCancel.setText(_translate("NewPlot", "Cancel"))


