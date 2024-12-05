# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'csvrequest.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QListView,
    QPushButton, QSizePolicy, QSpinBox, QTableView,
    QVBoxLayout, QWidget)

class Ui_NewPlot(object):
    def setupUi(self, NewPlot):
        if not NewPlot.objectName():
            NewPlot.setObjectName(u"NewPlot")
        NewPlot.resize(942, 792)
        NewPlot.setSizeGripEnabled(False)
        self.verticalLayout_4 = QVBoxLayout(NewPlot)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(NewPlot)
        self.label.setObjectName(u"label")
        self.label.setFrameShape(QFrame.NoFrame)
        self.label.setFrameShadow(QFrame.Plain)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.txtSep = QComboBox(NewPlot)
        self.txtSep.addItem("")
        self.txtSep.addItem("")
        self.txtSep.addItem("")
        self.txtSep.setObjectName(u"txtSep")
        self.txtSep.setEditable(True)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txtSep)

        self.label_2 = QLabel(NewPlot)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.txtDecimal = QComboBox(NewPlot)
        self.txtDecimal.addItem("")
        self.txtDecimal.addItem("")
        self.txtDecimal.setObjectName(u"txtDecimal")
        self.txtDecimal.setEditable(True)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.txtDecimal)

        self.label_3 = QLabel(NewPlot)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.spnLinedrop = QSpinBox(NewPlot)
        self.spnLinedrop.setObjectName(u"spnLinedrop")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.spnLinedrop)

        self.label_4 = QLabel(NewPlot)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.txtEncoding = QComboBox(NewPlot)
        self.txtEncoding.addItem("")
        self.txtEncoding.addItem("")
        self.txtEncoding.setObjectName(u"txtEncoding")
        self.txtEncoding.setEditable(True)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.txtEncoding)

        self.label_5 = QLabel(NewPlot)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.txtTimezone = QComboBox(NewPlot)
        self.txtTimezone.addItem("")
        self.txtTimezone.addItem("")
        self.txtTimezone.setObjectName(u"txtTimezone")
        self.txtTimezone.setEditable(True)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.txtTimezone)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.btnLoad = QPushButton(NewPlot)
        self.btnLoad.setObjectName(u"btnLoad")

        self.verticalLayout_3.addWidget(self.btnLoad)

        self.line = QFrame(NewPlot)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line)


        self.horizontalLayout_4.addLayout(self.verticalLayout_3)

        self.groupBox_2 = QGroupBox(NewPlot)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lstVAll = QTableView(self.groupBox_2)
        self.lstVAll.setObjectName(u"lstVAll")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lstVAll.sizePolicy().hasHeightForWidth())
        self.lstVAll.setSizePolicy(sizePolicy1)
        self.lstVAll.setSelectionMode(QAbstractItemView.MultiSelection)

        self.verticalLayout.addWidget(self.lstVAll)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btnToX = QPushButton(self.groupBox_2)
        self.btnToX.setObjectName(u"btnToX")

        self.horizontalLayout.addWidget(self.btnToX)

        self.btnToY = QPushButton(self.groupBox_2)
        self.btnToY.setObjectName(u"btnToY")

        self.horizontalLayout.addWidget(self.btnToY)


        self.verticalLayout_11.addLayout(self.horizontalLayout)

        self.btnToCluster = QPushButton(self.groupBox_2)
        self.btnToCluster.setObjectName(u"btnToCluster")

        self.verticalLayout_11.addWidget(self.btnToCluster)


        self.verticalLayout.addLayout(self.verticalLayout_11)


        self.horizontalLayout_4.addWidget(self.groupBox_2)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox_6 = QGroupBox(NewPlot)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_7 = QLabel(self.groupBox_6)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.txtDateTime = QComboBox(self.groupBox_6)
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.addItem("")
        self.txtDateTime.setObjectName(u"txtDateTime")
        self.txtDateTime.setEditable(True)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.txtDateTime)

        self.lstVX = QComboBox(self.groupBox_6)
        self.lstVX.setObjectName(u"lstVX")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lstVX.sizePolicy().hasHeightForWidth())
        self.lstVX.setSizePolicy(sizePolicy2)
        self.lstVX.setMaxCount(4)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.lstVX)

        self.btnRemoveX = QPushButton(self.groupBox_6)
        self.btnRemoveX.setObjectName(u"btnRemoveX")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btnRemoveX.sizePolicy().hasHeightForWidth())
        self.btnRemoveX.setSizePolicy(sizePolicy3)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.btnRemoveX)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.chkGenX = QCheckBox(self.groupBox_6)
        self.chkGenX.setObjectName(u"chkGenX")
        self.chkGenX.setChecked(True)

        self.horizontalLayout_2.addWidget(self.chkGenX)

        self.spnFs = QSpinBox(self.groupBox_6)
        self.spnFs.setObjectName(u"spnFs")
        self.spnFs.setMinimum(1)
        self.spnFs.setMaximum(1000000)
        self.spnFs.setValue(180)

        self.horizontalLayout_2.addWidget(self.spnFs)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout_8.addLayout(self.verticalLayout_2)


        self.verticalLayout_5.addWidget(self.groupBox_6)

        self.groupBox_5 = QGroupBox(NewPlot)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.lstVY = QListView(self.groupBox_5)
        self.lstVY.setObjectName(u"lstVY")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.lstVY.sizePolicy().hasHeightForWidth())
        self.lstVY.setSizePolicy(sizePolicy4)
        self.lstVY.setSelectionMode(QAbstractItemView.MultiSelection)

        self.verticalLayout_6.addWidget(self.lstVY)

        self.btnRemoveY = QPushButton(self.groupBox_5)
        self.btnRemoveY.setObjectName(u"btnRemoveY")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.btnRemoveY.sizePolicy().hasHeightForWidth())
        self.btnRemoveY.setSizePolicy(sizePolicy5)

        self.verticalLayout_6.addWidget(self.btnRemoveY)


        self.verticalLayout_7.addLayout(self.verticalLayout_6)


        self.verticalLayout_5.addWidget(self.groupBox_5)

        self.groupBox = QGroupBox(NewPlot)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_10 = QVBoxLayout(self.groupBox)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.lstVCluster = QComboBox(self.groupBox)
        self.lstVCluster.setObjectName(u"lstVCluster")
        self.lstVCluster.setEditable(False)

        self.verticalLayout_9.addWidget(self.lstVCluster)

        self.btnRemoveCluster = QPushButton(self.groupBox)
        self.btnRemoveCluster.setObjectName(u"btnRemoveCluster")

        self.verticalLayout_9.addWidget(self.btnRemoveCluster)


        self.verticalLayout_10.addLayout(self.verticalLayout_9)


        self.verticalLayout_5.addWidget(self.groupBox)


        self.horizontalLayout_4.addLayout(self.verticalLayout_5)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        self.line_2 = QFrame(NewPlot)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.btnOk = QPushButton(NewPlot)
        self.btnOk.setObjectName(u"btnOk")
        sizePolicy3.setHeightForWidth(self.btnOk.sizePolicy().hasHeightForWidth())
        self.btnOk.setSizePolicy(sizePolicy3)

        self.horizontalLayout_3.addWidget(self.btnOk)

        self.btnCancel = QPushButton(NewPlot)
        self.btnCancel.setObjectName(u"btnCancel")
        sizePolicy3.setHeightForWidth(self.btnCancel.sizePolicy().hasHeightForWidth())
        self.btnCancel.setSizePolicy(sizePolicy3)

        self.horizontalLayout_3.addWidget(self.btnCancel)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)


        self.retranslateUi(NewPlot)
        self.chkGenX.clicked["bool"].connect(self.lstVX.setDisabled)

        QMetaObject.connectSlotsByName(NewPlot)
    # setupUi

    def retranslateUi(self, NewPlot):
        NewPlot.setWindowTitle(QCoreApplication.translate("NewPlot", u"New Plot", None))
        self.label.setText(QCoreApplication.translate("NewPlot", u"Field Seperator", None))
        self.txtSep.setItemText(0, QCoreApplication.translate("NewPlot", u";", None))
        self.txtSep.setItemText(1, QCoreApplication.translate("NewPlot", u",", None))
        self.txtSep.setItemText(2, QCoreApplication.translate("NewPlot", u"<tab>", None))

        self.label_2.setText(QCoreApplication.translate("NewPlot", u"Decimal Seperator", None))
        self.txtDecimal.setItemText(0, QCoreApplication.translate("NewPlot", u",", None))
        self.txtDecimal.setItemText(1, QCoreApplication.translate("NewPlot", u".", None))

        self.label_3.setText(QCoreApplication.translate("NewPlot", u"Drop n first lines", None))
        self.label_4.setText(QCoreApplication.translate("NewPlot", u"Encoding", None))
        self.txtEncoding.setItemText(0, QCoreApplication.translate("NewPlot", u"latin1", None))
        self.txtEncoding.setItemText(1, QCoreApplication.translate("NewPlot", u"utf8", None))

        self.label_5.setText(QCoreApplication.translate("NewPlot", u"Timezone", None))
        self.txtTimezone.setItemText(0, QCoreApplication.translate("NewPlot", u"UTC", None))
        self.txtTimezone.setItemText(1, QCoreApplication.translate("NewPlot", u"Europe/Paris", None))

        self.btnLoad.setText(QCoreApplication.translate("NewPlot", u"Load Fields", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("NewPlot", u"Loaded Fields", None))
        self.btnToX.setText(QCoreApplication.translate("NewPlot", u"Move to X", None))
        self.btnToY.setText(QCoreApplication.translate("NewPlot", u"Move to Y", None))
        self.btnToCluster.setText(QCoreApplication.translate("NewPlot", u"Use as Cluster Id", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("NewPlot", u"X axis (Time)", None))
        self.label_7.setText(QCoreApplication.translate("NewPlot", u"Date/Time Format", None))
        self.txtDateTime.setItemText(0, QCoreApplication.translate("NewPlot", u"%Y-%m-%d %H:%M:%S,%f", None))
        self.txtDateTime.setItemText(1, QCoreApplication.translate("NewPlot", u"%Y-%m-%d %H:%M:%S.%f", None))
        self.txtDateTime.setItemText(2, QCoreApplication.translate("NewPlot", u"%H:%M", None))
        self.txtDateTime.setItemText(3, QCoreApplication.translate("NewPlot", u"<seconds>", None))
        self.txtDateTime.setItemText(4, QCoreApplication.translate("NewPlot", u"<milliseconds>", None))
        self.txtDateTime.setItemText(5, QCoreApplication.translate("NewPlot", u"<nanoseconds>", None))
        self.txtDateTime.setItemText(6, QCoreApplication.translate("NewPlot", u"<infer>", None))

        self.btnRemoveX.setText(QCoreApplication.translate("NewPlot", u"Remove", None))
        self.chkGenX.setText(QCoreApplication.translate("NewPlot", u"Manual sample rate (Hz):", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("NewPlot", u"Y axis", None))
        self.btnRemoveY.setText(QCoreApplication.translate("NewPlot", u"Remove", None))
        self.groupBox.setTitle(QCoreApplication.translate("NewPlot", u"Cluster Id", None))
        self.btnRemoveCluster.setText(QCoreApplication.translate("NewPlot", u"Remove", None))
        self.btnOk.setText(QCoreApplication.translate("NewPlot", u"OK", None))
        self.btnCancel.setText(QCoreApplication.translate("NewPlot", u"Cancel", None))
    # retranslateUi

