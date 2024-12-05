# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'curveproperties.ui'
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
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_CurveProperties(object):
    def setupUi(self, CurveProperties):
        if not CurveProperties.objectName():
            CurveProperties.setObjectName(u"CurveProperties")
        CurveProperties.resize(342, 280)
        self.verticalLayout = QVBoxLayout(CurveProperties)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.grpName = QGroupBox(CurveProperties)
        self.grpName.setObjectName(u"grpName")
        self.formLayout = QFormLayout(self.grpName)
        self.formLayout.setObjectName(u"formLayout")
        self.txtName = QLineEdit(self.grpName)
        self.txtName.setObjectName(u"txtName")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txtName)

        self.label_3 = QLabel(self.grpName)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_3)

        self.btnColor = QPushButton(self.grpName)
        self.btnColor.setObjectName(u"btnColor")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.btnColor)

        self.label_4 = QLabel(self.grpName)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_4)

        self.lblSamplerate = QLabel(self.grpName)
        self.lblSamplerate.setObjectName(u"lblSamplerate")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.lblSamplerate)

        self.cmbSymbol = QComboBox(self.grpName)
        self.cmbSymbol.addItem("")
        self.cmbSymbol.addItem("")
        self.cmbSymbol.addItem("")
        self.cmbSymbol.addItem("")
        self.cmbSymbol.addItem("")
        self.cmbSymbol.addItem("")
        self.cmbSymbol.setObjectName(u"cmbSymbol")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.cmbSymbol)

        self.label_6 = QLabel(self.grpName)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_6)

        self.label_2 = QLabel(self.grpName)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_2)

        self.spnWidth = QSpinBox(self.grpName)
        self.spnWidth.setObjectName(u"spnWidth")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.spnWidth)

        self.label_5 = QLabel(self.grpName)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_5)

        self.label = QLabel(self.grpName)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.cmbConnect = QComboBox(self.grpName)
        self.cmbConnect.addItem("")
        self.cmbConnect.addItem("")
        self.cmbConnect.addItem("")
        self.cmbConnect.addItem("")
        self.cmbConnect.setObjectName(u"cmbConnect")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.cmbConnect)


        self.verticalLayout.addWidget(self.grpName)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.okButton = QPushButton(CurveProperties)
        self.okButton.setObjectName(u"okButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okButton.sizePolicy().hasHeightForWidth())
        self.okButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton(CurveProperties)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CurveProperties)

        QMetaObject.connectSlotsByName(CurveProperties)
    # setupUi

    def retranslateUi(self, CurveProperties):
        CurveProperties.setWindowTitle(QCoreApplication.translate("CurveProperties", u"Dialog", None))
        self.grpName.setTitle(QCoreApplication.translate("CurveProperties", u"GroupBox", None))
        self.label_3.setText(QCoreApplication.translate("CurveProperties", u"Color", None))
        self.btnColor.setText(QCoreApplication.translate("CurveProperties", u"Change Color", None))
        self.label_4.setText(QCoreApplication.translate("CurveProperties", u"Sampling rate", None))
        self.lblSamplerate.setText(QCoreApplication.translate("CurveProperties", u"TextLabel", None))
        self.cmbSymbol.setItemText(0, QCoreApplication.translate("CurveProperties", u"None", None))
        self.cmbSymbol.setItemText(1, QCoreApplication.translate("CurveProperties", u"o", None))
        self.cmbSymbol.setItemText(2, QCoreApplication.translate("CurveProperties", u"s", None))
        self.cmbSymbol.setItemText(3, QCoreApplication.translate("CurveProperties", u"t", None))
        self.cmbSymbol.setItemText(4, QCoreApplication.translate("CurveProperties", u"d", None))
        self.cmbSymbol.setItemText(5, QCoreApplication.translate("CurveProperties", u"+", None))

        self.label_6.setText(QCoreApplication.translate("CurveProperties", u"Connect Points", None))
        self.label_2.setText(QCoreApplication.translate("CurveProperties", u"Line width", None))
        self.label_5.setText(QCoreApplication.translate("CurveProperties", u"Symbol", None))
        self.label.setText(QCoreApplication.translate("CurveProperties", u"Name", None))
        self.cmbConnect.setItemText(0, QCoreApplication.translate("CurveProperties", u"None", None))
        self.cmbConnect.setItemText(1, QCoreApplication.translate("CurveProperties", u"All", None))
        self.cmbConnect.setItemText(2, QCoreApplication.translate("CurveProperties", u"Pairs", None))
        self.cmbConnect.setItemText(3, QCoreApplication.translate("CurveProperties", u"Finite", None))

        self.okButton.setText(QCoreApplication.translate("CurveProperties", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("CurveProperties", u"Cancel", None))
    # retranslateUi

