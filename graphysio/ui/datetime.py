# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'datetime.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SetDateTime(object):
    def setupUi(self, SetDateTime):
        SetDateTime.setObjectName("SetDateTime")
        SetDateTime.resize(574, 366)
        self.gridLayout = QtWidgets.QGridLayout(SetDateTime)
        self.gridLayout.setObjectName("gridLayout")
        self.widgetCalendar = QtWidgets.QCalendarWidget(SetDateTime)
        self.widgetCalendar.setFirstDayOfWeek(QtCore.Qt.Monday)
        self.widgetCalendar.setGridVisible(True)
        self.widgetCalendar.setObjectName("widgetCalendar")
        self.gridLayout.addWidget(self.widgetCalendar, 0, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.edDate = QtWidgets.QDateEdit(SetDateTime)
        self.edDate.setObjectName("edDate")
        self.gridLayout.addWidget(self.edDate, 1, 2, 1, 1)
        self.edTime = QtWidgets.QTimeEdit(SetDateTime)
        self.edTime.setObjectName("edTime")
        self.gridLayout.addWidget(self.edTime, 2, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(SetDateTime)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(SetDateTime)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.btnOk = QtWidgets.QPushButton(SetDateTime)
        self.btnOk.setObjectName("btnOk")
        self.horizontalLayout.addWidget(self.btnOk)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.btnCancel = QtWidgets.QPushButton(SetDateTime)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout_2.addWidget(self.btnCancel)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 2, 1, 1)
        self.widgetCalendar.raise_()
        self.edTime.raise_()
        self.label_2.raise_()
        self.label.raise_()
        self.edDate.raise_()

        self.retranslateUi(SetDateTime)
        self.widgetCalendar.clicked['QDate'].connect(self.edDate.setDate)
        QtCore.QMetaObject.connectSlotsByName(SetDateTime)

    def retranslateUi(self, SetDateTime):
        _translate = QtCore.QCoreApplication.translate
        SetDateTime.setWindowTitle(_translate("SetDateTime", "Set Date and Time"))
        self.edDate.setDisplayFormat(_translate("SetDateTime", "dd/MM/yyyy"))
        self.edTime.setDisplayFormat(_translate("SetDateTime", "hh:mm:ss.zzz"))
        self.label_2.setText(_translate("SetDateTime", "Time"))
        self.label.setText(_translate("SetDateTime", "Date"))
        self.btnOk.setText(_translate("SetDateTime", "Ok"))
        self.btnCancel.setText(_translate("SetDateTime", "Cancel"))
