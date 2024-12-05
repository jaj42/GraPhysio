# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'periodexport.ui'
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
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_PeriodExport(object):
    def setupUi(self, PeriodExport):
        if not PeriodExport.objectName():
            PeriodExport.setObjectName(u"PeriodExport")
        PeriodExport.resize(255, 237)
        self.verticalLayout = QVBoxLayout(PeriodExport)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(PeriodExport)
        self.groupBox.setObjectName(u"groupBox")
        self.formLayout_3 = QFormLayout(self.groupBox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.btnBrowse = QPushButton(self.groupBox)
        self.btnBrowse.setObjectName(u"btnBrowse")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.btnBrowse)

        self.txtFile = QLineEdit(self.groupBox)
        self.txtFile.setObjectName(u"txtFile")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.txtFile)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(PeriodExport)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lblPeriodStart = QLabel(self.groupBox_2)
        self.lblPeriodStart.setObjectName(u"lblPeriodStart")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPeriodStart.sizePolicy().hasHeightForWidth())
        self.lblPeriodStart.setSizePolicy(sizePolicy)
        self.lblPeriodStart.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lblPeriodStart)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.lblPeriodStop = QLabel(self.groupBox_2)
        self.lblPeriodStop.setObjectName(u"lblPeriodStop")
        sizePolicy.setHeightForWidth(self.lblPeriodStop.sizePolicy().hasHeightForWidth())
        self.lblPeriodStop.setSizePolicy(sizePolicy)
        self.lblPeriodStop.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lblPeriodStop)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(PeriodExport)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.txtPatient = QLineEdit(PeriodExport)
        self.txtPatient.setObjectName(u"txtPatient")
        sizePolicy.setHeightForWidth(self.txtPatient.sizePolicy().hasHeightForWidth())
        self.txtPatient.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txtPatient)

        self.label_7 = QLabel(PeriodExport)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_7)

        self.txtPeriod = QComboBox(PeriodExport)
        self.txtPeriod.addItem("")
        self.txtPeriod.addItem("")
        self.txtPeriod.addItem("")
        self.txtPeriod.addItem("")
        self.txtPeriod.addItem("")
        self.txtPeriod.addItem("")
        self.txtPeriod.setObjectName(u"txtPeriod")
        self.txtPeriod.setEditable(True)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.txtPeriod)

        self.label_2 = QLabel(PeriodExport)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.txtComment = QLineEdit(PeriodExport)
        self.txtComment.setObjectName(u"txtComment")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.txtComment)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.btnOk = QPushButton(PeriodExport)
        self.btnOk.setObjectName(u"btnOk")

        self.horizontalLayout_3.addWidget(self.btnOk)

        self.btnCancel = QPushButton(PeriodExport)
        self.btnCancel.setObjectName(u"btnCancel")

        self.horizontalLayout_3.addWidget(self.btnCancel)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(PeriodExport)

        QMetaObject.connectSlotsByName(PeriodExport)
    # setupUi

    def retranslateUi(self, PeriodExport):
        PeriodExport.setWindowTitle(QCoreApplication.translate("PeriodExport", u"Export period information", None))
        self.groupBox.setTitle(QCoreApplication.translate("PeriodExport", u"Destination file", None))
        self.btnBrowse.setText(QCoreApplication.translate("PeriodExport", u"Browse", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("PeriodExport", u"Period", None))
        self.lblPeriodStart.setText(QCoreApplication.translate("PeriodExport", u"Beginning", None))
        self.label_3.setText(QCoreApplication.translate("PeriodExport", u"-", None))
        self.lblPeriodStop.setText(QCoreApplication.translate("PeriodExport", u"End", None))
        self.label.setText(QCoreApplication.translate("PeriodExport", u"Patient", None))
        self.label_7.setText(QCoreApplication.translate("PeriodExport", u"Period Identification", None))
        self.txtPeriod.setItemText(0, QCoreApplication.translate("PeriodExport", u"carotid", None))
        self.txtPeriod.setItemText(1, QCoreApplication.translate("PeriodExport", u"ascending", None))
        self.txtPeriod.setItemText(2, QCoreApplication.translate("PeriodExport", u"descending", None))
        self.txtPeriod.setItemText(3, QCoreApplication.translate("PeriodExport", u"renal", None))
        self.txtPeriod.setItemText(4, QCoreApplication.translate("PeriodExport", u"iliac", None))
        self.txtPeriod.setItemText(5, QCoreApplication.translate("PeriodExport", u"bolus", None))

        self.label_2.setText(QCoreApplication.translate("PeriodExport", u"Comment", None))
        self.btnOk.setText(QCoreApplication.translate("PeriodExport", u"Ok", None))
        self.btnCancel.setText(QCoreApplication.translate("PeriodExport", u"Cancel", None))
    # retranslateUi

