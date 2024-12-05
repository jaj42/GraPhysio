# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setuppuloop.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLayout, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_SetupPULoop(object):
    def setupUi(self, SetupPULoop):
        if not SetupPULoop.objectName():
            SetupPULoop.setObjectName(u"SetupPULoop")
        SetupPULoop.resize(387, 371)
        self.verticalLayout = QVBoxLayout(SetupPULoop)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setSizeConstraint(QLayout.SetMaximumSize)
        self.formLayout_2.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label = QLabel(SetupPULoop)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label)

        self.comboU = QComboBox(SetupPULoop)
        self.comboU.setObjectName(u"comboU")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.comboU)

        self.label_2 = QLabel(SetupPULoop)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.comboP = QComboBox(SetupPULoop)
        self.comboP.setObjectName(u"comboP")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.comboP)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.okButton = QPushButton(SetupPULoop)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton(SetupPULoop)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SetupPULoop)

        QMetaObject.connectSlotsByName(SetupPULoop)
    # setupUi

    def retranslateUi(self, SetupPULoop):
        SetupPULoop.setWindowTitle(QCoreApplication.translate("SetupPULoop", u"Set up PU-Loop", None))
        self.label.setText(QCoreApplication.translate("SetupPULoop", u"Velocity (U)", None))
        self.label_2.setText(QCoreApplication.translate("SetupPULoop", u"Pressure (P)", None))
        self.okButton.setText(QCoreApplication.translate("SetupPULoop", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("SetupPULoop", u"Cancel", None))
    # retranslateUi

