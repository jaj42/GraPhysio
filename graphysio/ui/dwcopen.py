# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dwcopen.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDateTimeEdit,
    QDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_DWCOpen(object):
    def setupUi(self, DWCOpen):
        if not DWCOpen.objectName():
            DWCOpen.setObjectName(u"DWCOpen")
        DWCOpen.resize(564, 511)
        self.verticalLayout_2 = QVBoxLayout(DWCOpen)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.txtPatientId = QLineEdit(DWCOpen)
        self.txtPatientId.setObjectName(u"txtPatientId")

        self.gridLayout.addWidget(self.txtPatientId, 0, 1, 1, 1)

        self.label = QLabel(DWCOpen)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.searchButton = QPushButton(DWCOpen)
        self.searchButton.setObjectName(u"searchButton")

        self.gridLayout.addWidget(self.searchButton, 0, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.lblFound = QLabel(DWCOpen)
        self.lblFound.setObjectName(u"lblFound")

        self.verticalLayout_2.addWidget(self.lblFound)

        self.cmbTypeofData = QComboBox(DWCOpen)
        self.cmbTypeofData.addItem("")
        self.cmbTypeofData.addItem("")
        self.cmbTypeofData.setObjectName(u"cmbTypeofData")

        self.verticalLayout_2.addWidget(self.cmbTypeofData)

        self.lstLabels = QListWidget(DWCOpen)
        self.lstLabels.setObjectName(u"lstLabels")
        self.lstLabels.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        self.verticalLayout_2.addWidget(self.lstLabels)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(DWCOpen)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.dtFrom = QDateTimeEdit(DWCOpen)
        self.dtFrom.setObjectName(u"dtFrom")
        self.dtFrom.setCalendarPopup(True)

        self.horizontalLayout_2.addWidget(self.dtFrom)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(DWCOpen)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.dtTo = QDateTimeEdit(DWCOpen)
        self.dtTo.setObjectName(u"dtTo")
        self.dtTo.setCalendarPopup(True)

        self.horizontalLayout_3.addWidget(self.dtTo)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.okButton = QPushButton(DWCOpen)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancelButton = QPushButton(DWCOpen)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.retranslateUi(DWCOpen)

        self.cmbTypeofData.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DWCOpen)
    # setupUi

    def retranslateUi(self, DWCOpen):
        DWCOpen.setWindowTitle(QCoreApplication.translate("DWCOpen", u"Load DWC data", None))
        self.label.setText(QCoreApplication.translate("DWCOpen", u"Patient ID", None))
        self.searchButton.setText(QCoreApplication.translate("DWCOpen", u"Search", None))
        self.lblFound.setText("")
        self.cmbTypeofData.setItemText(0, QCoreApplication.translate("DWCOpen", u"Numerics", None))
        self.cmbTypeofData.setItemText(1, QCoreApplication.translate("DWCOpen", u"Waves", None))

        self.label_2.setText(QCoreApplication.translate("DWCOpen", u"From", None))
        self.label_3.setText(QCoreApplication.translate("DWCOpen", u"To", None))
        self.okButton.setText(QCoreApplication.translate("DWCOpen", u"Ok", None))
        self.cancelButton.setText(QCoreApplication.translate("DWCOpen", u"Cancel", None))
    # retranslateUi

