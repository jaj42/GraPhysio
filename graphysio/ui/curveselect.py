# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'curveselect.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_CurveSelection(object):
    def setupUi(self, CurveSelection):
        if not CurveSelection.objectName():
            CurveSelection.setObjectName(u"CurveSelection")
        CurveSelection.resize(292, 329)
        self.verticalLayout = QVBoxLayout(CurveSelection)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lstCurves = QListWidget(CurveSelection)
        self.lstCurves.setObjectName(u"lstCurves")

        self.verticalLayout.addWidget(self.lstCurves)

        self.btnProperties = QPushButton(CurveSelection)
        self.btnProperties.setObjectName(u"btnProperties")

        self.verticalLayout.addWidget(self.btnProperties)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.okButton = QPushButton(CurveSelection)
        self.okButton.setObjectName(u"okButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okButton.sizePolicy().hasHeightForWidth())
        self.okButton.setSizePolicy(sizePolicy)
        self.okButton.setChecked(False)

        self.horizontalLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton(CurveSelection)
        self.cancelButton.setObjectName(u"cancelButton")
        sizePolicy.setHeightForWidth(self.cancelButton.sizePolicy().hasHeightForWidth())
        self.cancelButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CurveSelection)

        QMetaObject.connectSlotsByName(CurveSelection)
    # setupUi

    def retranslateUi(self, CurveSelection):
        CurveSelection.setWindowTitle(QCoreApplication.translate("CurveSelection", u"Select visible curves", None))
        self.btnProperties.setText(QCoreApplication.translate("CurveSelection", u"Curve Properties", None))
        self.okButton.setText(QCoreApplication.translate("CurveSelection", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("CurveSelection", u"Cancel", None))
    # retranslateUi

