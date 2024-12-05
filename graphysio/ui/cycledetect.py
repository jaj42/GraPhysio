# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cycledetect.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QHeaderView,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_CycleDetection(object):
    def setupUi(self, CycleDetection):
        if not CycleDetection.objectName():
            CycleDetection.setObjectName(u"CycleDetection")
        CycleDetection.resize(387, 371)
        self.verticalLayout = QVBoxLayout(CycleDetection)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.table = QTableWidget(CycleDetection)
        if (self.table.columnCount() < 2):
            self.table.setColumnCount(2)
        self.table.setObjectName(u"table")
        self.table.setColumnCount(2)

        self.verticalLayout.addWidget(self.table)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.okButton = QPushButton(CycleDetection)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton(CycleDetection)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CycleDetection)

        QMetaObject.connectSlotsByName(CycleDetection)
    # setupUi

    def retranslateUi(self, CycleDetection):
        CycleDetection.setWindowTitle(QCoreApplication.translate("CycleDetection", u"Cycle Detection", None))
        self.okButton.setText(QCoreApplication.translate("CycleDetection", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("CycleDetection", u"Cancel", None))
    # retranslateUi

