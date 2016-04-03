# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/periodexport.ui'
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

class Ui_PeriodExport(object):
    def setupUi(self, PeriodExport):
        PeriodExport.setObjectName(_fromUtf8("PeriodExport"))
        PeriodExport.resize(255, 237)
        self.verticalLayout = QtGui.QVBoxLayout(PeriodExport)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(PeriodExport)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout_3 = QtGui.QFormLayout(self.groupBox)
        self.formLayout_3.setObjectName(_fromUtf8("formLayout_3"))
        self.btnBrowse = QtGui.QPushButton(self.groupBox)
        self.btnBrowse.setObjectName(_fromUtf8("btnBrowse"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.btnBrowse)
        self.txtFile = QtGui.QLineEdit(self.groupBox)
        self.txtFile.setObjectName(_fromUtf8("txtFile"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.txtFile)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(PeriodExport)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lblPeriodStart = QtGui.QLabel(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPeriodStart.sizePolicy().hasHeightForWidth())
        self.lblPeriodStart.setSizePolicy(sizePolicy)
        self.lblPeriodStart.setAlignment(QtCore.Qt.AlignCenter)
        self.lblPeriodStart.setObjectName(_fromUtf8("lblPeriodStart"))
        self.horizontalLayout_2.addWidget(self.lblPeriodStart)
        self.lblPeriodStop = QtGui.QLabel(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPeriodStop.sizePolicy().hasHeightForWidth())
        self.lblPeriodStop.setSizePolicy(sizePolicy)
        self.lblPeriodStop.setAlignment(QtCore.Qt.AlignCenter)
        self.lblPeriodStop.setObjectName(_fromUtf8("lblPeriodStop"))
        self.horizontalLayout_2.addWidget(self.lblPeriodStop)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(PeriodExport)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.txtPatient = QtGui.QLineEdit(PeriodExport)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtPatient.sizePolicy().hasHeightForWidth())
        self.txtPatient.setSizePolicy(sizePolicy)
        self.txtPatient.setObjectName(_fromUtf8("txtPatient"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.txtPatient)
        self.label_7 = QtGui.QLabel(PeriodExport)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_7)
        self.txtPeriod = QtGui.QComboBox(PeriodExport)
        self.txtPeriod.setEditable(True)
        self.txtPeriod.setObjectName(_fromUtf8("txtPeriod"))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.txtPeriod.addItem(_fromUtf8(""))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.txtPeriod)
        self.label_2 = QtGui.QLabel(PeriodExport)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_2)
        self.txtComment = QtGui.QLineEdit(PeriodExport)
        self.txtComment.setObjectName(_fromUtf8("txtComment"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.txtComment)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.btnOk = QtGui.QPushButton(PeriodExport)
        self.btnOk.setObjectName(_fromUtf8("btnOk"))
        self.horizontalLayout_3.addWidget(self.btnOk)
        self.btnCancel = QtGui.QPushButton(PeriodExport)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_3.addWidget(self.btnCancel)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(PeriodExport)
        QtCore.QMetaObject.connectSlotsByName(PeriodExport)

    def retranslateUi(self, PeriodExport):
        PeriodExport.setWindowTitle(_translate("PeriodExport", "Export period information", None))
        self.groupBox.setTitle(_translate("PeriodExport", "Destination file", None))
        self.btnBrowse.setText(_translate("PeriodExport", "Browse", None))
        self.groupBox_2.setTitle(_translate("PeriodExport", "Period", None))
        self.lblPeriodStart.setText(_translate("PeriodExport", "Beginning", None))
        self.lblPeriodStop.setText(_translate("PeriodExport", "End", None))
        self.label.setText(_translate("PeriodExport", "Patient", None))
        self.label_7.setText(_translate("PeriodExport", "Period Identification", None))
        self.txtPeriod.setItemText(0, _translate("PeriodExport", "carotid", None))
        self.txtPeriod.setItemText(1, _translate("PeriodExport", "ascending", None))
        self.txtPeriod.setItemText(2, _translate("PeriodExport", "descending", None))
        self.txtPeriod.setItemText(3, _translate("PeriodExport", "renal", None))
        self.txtPeriod.setItemText(4, _translate("PeriodExport", "iliac", None))
        self.txtPeriod.setItemText(5, _translate("PeriodExport", "bolus", None))
        self.label_2.setText(_translate("PeriodExport", "Comment", None))
        self.btnOk.setText(_translate("PeriodExport", "Ok", None))
        self.btnCancel.setText(_translate("PeriodExport", "Cancel", None))

