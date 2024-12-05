# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'loopwidget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_LoopWidget(object):
    def setupUi(self, LoopWidget):
        if not LoopWidget.objectName():
            LoopWidget.setObjectName(u"LoopWidget")
        LoopWidget.resize(763, 601)
        self.horizontalLayout = QHBoxLayout(LoopWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.graphicsView = PlotWidget(LoopWidget)
        self.graphicsView.setObjectName(u"graphicsView")

        self.horizontalLayout.addWidget(self.graphicsView)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.lblDelay = QLabel(LoopWidget)
        self.lblDelay.setObjectName(u"lblDelay")

        self.gridLayout.addWidget(self.lblDelay, 5, 1, 1, 1)

        self.btnPrev = QPushButton(LoopWidget)
        self.btnPrev.setObjectName(u"btnPrev")

        self.gridLayout.addWidget(self.btnPrev, 1, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 4, 0, 1, 1)

        self.label_2 = QLabel(LoopWidget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 1, 1, 1)

        self.label = QLabel(LoopWidget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)

        self.lblGala = QLabel(LoopWidget)
        self.lblGala.setObjectName(u"lblGala")

        self.gridLayout.addWidget(self.lblGala, 8, 1, 1, 1)

        self.label_4 = QLabel(LoopWidget)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 5, 0, 1, 1)

        self.lblIdx = QLabel(LoopWidget)
        self.lblIdx.setObjectName(u"lblIdx")
        self.lblIdx.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.lblIdx, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 0, 0, 1, 1)

        self.label_3 = QLabel(LoopWidget)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 6, 0, 1, 1)

        self.label_5 = QLabel(LoopWidget)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 7, 0, 1, 1)

        self.lblBeta = QLabel(LoopWidget)
        self.lblBeta.setObjectName(u"lblBeta")

        self.gridLayout.addWidget(self.lblBeta, 7, 1, 1, 1)

        self.label_7 = QLabel(LoopWidget)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 8, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_3, 0, 1, 1, 1)

        self.btnNext = QPushButton(LoopWidget)
        self.btnNext.setObjectName(u"btnNext")

        self.gridLayout.addWidget(self.btnNext, 1, 1, 1, 1)

        self.lblAlpha = QLabel(LoopWidget)
        self.lblAlpha.setObjectName(u"lblAlpha")

        self.gridLayout.addWidget(self.lblAlpha, 6, 1, 1, 1)

        self.lblTot = QLabel(LoopWidget)
        self.lblTot.setObjectName(u"lblTot")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblTot.sizePolicy().hasHeightForWidth())
        self.lblTot.setSizePolicy(sizePolicy)
        self.lblTot.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.lblTot, 3, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_4, 4, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.comboSeries = QComboBox(LoopWidget)
        self.comboSeries.setObjectName(u"comboSeries")

        self.verticalLayout_2.addWidget(self.comboSeries)

        self.btnDelete = QPushButton(LoopWidget)
        self.btnDelete.setObjectName(u"btnDelete")

        self.verticalLayout_2.addWidget(self.btnDelete)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.retranslateUi(LoopWidget)

        QMetaObject.connectSlotsByName(LoopWidget)
    # setupUi

    def retranslateUi(self, LoopWidget):
        LoopWidget.setWindowTitle(QCoreApplication.translate("LoopWidget", u"Form", None))
        self.lblDelay.setText("")
        self.btnPrev.setText(QCoreApplication.translate("LoopWidget", u"<", None))
        self.label_2.setText(QCoreApplication.translate("LoopWidget", u"of", None))
        self.label.setText(QCoreApplication.translate("LoopWidget", u"Loop #", None))
        self.lblGala.setText("")
        self.label_4.setText(QCoreApplication.translate("LoopWidget", u"Delay (ms)", None))
        self.lblIdx.setText(QCoreApplication.translate("LoopWidget", u"0", None))
        self.label_3.setText(QCoreApplication.translate("LoopWidget", u"\u03b1", None))
        self.label_5.setText(QCoreApplication.translate("LoopWidget", u"\u03b2", None))
        self.lblBeta.setText("")
        self.label_7.setText(QCoreApplication.translate("LoopWidget", u"GALA", None))
        self.btnNext.setText(QCoreApplication.translate("LoopWidget", u">", None))
        self.lblAlpha.setText("")
        self.lblTot.setText(QCoreApplication.translate("LoopWidget", u"0", None))
        self.btnDelete.setText(QCoreApplication.translate("LoopWidget", u"Delete current Loop", None))
    # retranslateUi

