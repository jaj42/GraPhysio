# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'poiwidget.ui'
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
from PySide6.QtWidgets import (QApplication, QButtonGroup, QGroupBox, QHBoxLayout,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_POISelectorWidget(object):
    def setupUi(self, POISelectorWidget):
        if not POISelectorWidget.objectName():
            POISelectorWidget.setObjectName(u"POISelectorWidget")
        POISelectorWidget.resize(763, 601)
        self.horizontalLayout = QHBoxLayout(POISelectorWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(POISelectorWidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.radioFixDisabled = QRadioButton(self.groupBox)
        self.buttonGroup = QButtonGroup(POISelectorWidget)
        self.buttonGroup.setObjectName(u"buttonGroup")
        self.buttonGroup.addButton(self.radioFixDisabled)
        self.radioFixDisabled.setObjectName(u"radioFixDisabled")
        self.radioFixDisabled.setChecked(True)

        self.verticalLayout.addWidget(self.radioFixDisabled)

        self.radioFixMinimum = QRadioButton(self.groupBox)
        self.buttonGroup.addButton(self.radioFixMinimum)
        self.radioFixMinimum.setObjectName(u"radioFixMinimum")

        self.verticalLayout.addWidget(self.radioFixMinimum)

        self.radioFixMaximum = QRadioButton(self.groupBox)
        self.buttonGroup.addButton(self.radioFixMaximum)
        self.radioFixMaximum.setObjectName(u"radioFixMaximum")

        self.verticalLayout.addWidget(self.radioFixMaximum)

        self.radioFixSecondDerivative = QRadioButton(self.groupBox)
        self.buttonGroup.addButton(self.radioFixSecondDerivative)
        self.radioFixSecondDerivative.setObjectName(u"radioFixSecondDerivative")

        self.verticalLayout.addWidget(self.radioFixSecondDerivative)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.retranslateUi(POISelectorWidget)

        QMetaObject.connectSlotsByName(POISelectorWidget)
    # setupUi

    def retranslateUi(self, POISelectorWidget):
        POISelectorWidget.setWindowTitle(QCoreApplication.translate("POISelectorWidget", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("POISelectorWidget", u"Fix Position", None))
        self.radioFixDisabled.setText(QCoreApplication.translate("POISelectorWidget", u"Disabled", None))
        self.radioFixMinimum.setText(QCoreApplication.translate("POISelectorWidget", u"Local Minimum", None))
        self.radioFixMaximum.setText(QCoreApplication.translate("POISelectorWidget", u"Local Maximum", None))
        self.radioFixSecondDerivative.setText(QCoreApplication.translate("POISelectorWidget", u"2nd derivative peak", None))
    # retranslateUi

