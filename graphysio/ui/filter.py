# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'filter.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QHeaderView, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_Filter(object):
    def setupUi(self, Filter):
        if not Filter.objectName():
            Filter.setObjectName(u"Filter")
        Filter.resize(387, 371)
        self.verticalLayout = QVBoxLayout(Filter)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.table = QTableWidget(Filter)
        if (self.table.columnCount() < 2):
            self.table.setColumnCount(2)
        self.table.setObjectName(u"table")
        self.table.setColumnCount(2)

        self.verticalLayout.addWidget(self.table)

        self.chkNewcurve = QCheckBox(Filter)
        self.chkNewcurve.setObjectName(u"chkNewcurve")

        self.verticalLayout.addWidget(self.chkNewcurve)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.okButton = QPushButton(Filter)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton(Filter)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Filter)

        QMetaObject.connectSlotsByName(Filter)
    # setupUi

    def retranslateUi(self, Filter):
        Filter.setWindowTitle(QCoreApplication.translate("Filter", u"Filter", None))
        self.chkNewcurve.setText(QCoreApplication.translate("Filter", u"Create new curve", None))
        self.okButton.setText(QCoreApplication.translate("Filter", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("Filter", u"Cancel", None))
    # retranslateUi

