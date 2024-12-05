# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'datetime.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCalendarWidget, QDateEdit, QDialog,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTimeEdit, QWidget)

class Ui_SetDateTime(object):
    def setupUi(self, SetDateTime):
        if not SetDateTime.objectName():
            SetDateTime.setObjectName(u"SetDateTime")
        SetDateTime.resize(574, 366)
        self.gridLayout = QGridLayout(SetDateTime)
        self.gridLayout.setObjectName(u"gridLayout")
        self.widgetCalendar = QCalendarWidget(SetDateTime)
        self.widgetCalendar.setObjectName(u"widgetCalendar")
        self.widgetCalendar.setFirstDayOfWeek(Qt.Monday)
        self.widgetCalendar.setGridVisible(True)

        self.gridLayout.addWidget(self.widgetCalendar, 0, 2, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 0, 0, 1, 1)

        self.edDate = QDateEdit(SetDateTime)
        self.edDate.setObjectName(u"edDate")

        self.gridLayout.addWidget(self.edDate, 1, 2, 1, 1)

        self.edTime = QTimeEdit(SetDateTime)
        self.edTime.setObjectName(u"edTime")

        self.gridLayout.addWidget(self.edTime, 2, 2, 1, 1)

        self.label_2 = QLabel(SetDateTime)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.label = QLabel(SetDateTime)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_4)

        self.btnOk = QPushButton(SetDateTime)
        self.btnOk.setObjectName(u"btnOk")

        self.horizontalLayout.addWidget(self.btnOk)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_5)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnCancel = QPushButton(SetDateTime)
        self.btnCancel.setObjectName(u"btnCancel")

        self.horizontalLayout_2.addWidget(self.btnCancel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 2, 1, 1)

        self.widgetCalendar.raise_()
        self.edTime.raise_()
        self.label_2.raise_()
        self.label.raise_()
        self.edDate.raise_()

        self.retranslateUi(SetDateTime)
        self.widgetCalendar.clicked.connect(self.edDate.setDate)

        QMetaObject.connectSlotsByName(SetDateTime)
    # setupUi

    def retranslateUi(self, SetDateTime):
        SetDateTime.setWindowTitle(QCoreApplication.translate("SetDateTime", u"Set Date and Time", None))
        self.edDate.setDisplayFormat(QCoreApplication.translate("SetDateTime", u"dd/MM/yyyy", None))
        self.edTime.setDisplayFormat(QCoreApplication.translate("SetDateTime", u"hh:mm:ss.zzz", None))
        self.label_2.setText(QCoreApplication.translate("SetDateTime", u"Time", None))
        self.label.setText(QCoreApplication.translate("SetDateTime", u"Date", None))
        self.btnOk.setText(QCoreApplication.translate("SetDateTime", u"Ok", None))
        self.btnCancel.setText(QCoreApplication.translate("SetDateTime", u"Cancel", None))
    # retranslateUi

