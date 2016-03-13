import rpc,plotwidget

import csv
import os # To get file size

#import sip
#sip.setapi('QVariant', 2)
#sip.setapi('QString', 2)

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from newplot_ui    import Ui_NewPlot
from mainwindow_ui import Ui_MainWindow

class MainUi(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainUi, self).__init__(parent=parent)
        self.setupUi(self)

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        self.menuFile.addAction('&New Plot', self.newPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

    def newPlot(self):
        dlgNewplot = DlgNewPlot()
        if not dlgNewplot.exec_(): return
        query = dlgNewplot.result
        if not query: return

        plot = plotwidget.PlotWidget(parent=self, rpcobj=query)
        tabindex = self.tabWidget.addTab(plot, query.samplename)
        self.tabWidget.setCurrentIndex(tabindex)

    def fileQuit(self):
        self.close()

    def closeTab(self, i):
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.destroy()

    @property
    def statusmessage(self):
        return self.statusBar.currentMessage()

    @statusmessage.setter
    def statusmessage(self, m):
        if m is None:
            self.statusBar.clearMessage()
        else:
            self.statusBar.showMessage(m)

class DlgNewPlot(QtGui.QDialog, Ui_NewPlot):
    def __init__(self, parent=None):
        super(DlgNewPlot, self).__init__(parent=parent)
        self.__csvquery = None

        self.setupUi(self)

        self.txtSep.addItem(',')
        self.txtSep.addItem(';')

        self.txtEvery.setMinimum(1)
        self.txtEvery.setMaximum(1000)

        # Connect callbacks
        self.btnBrowse.clicked.connect(self.selectFile)
        self.btnLoad.clicked.connect(self.loadCsvFields)
        self.btnOk.clicked.connect(self.loadPlot)
        self.btnCancel.clicked.connect(self.reject)

        # Hack since you cannot pass arguments to Qt's signal connect()
        #def moveToX():   return self.moveFromTo(self.listAll, self.listX)
        def moveToY():   return self.moveFromTo(self.listAll, self.listY)
        def moveFromX(): return self.moveFromTo(self.listX,   self.listAll)
        def moveFromY(): return self.moveFromTo(self.listY,   self.listAll)
        self.btnToX.clicked.connect(self.moveToX)
        self.btnToY.clicked.connect(moveToY)
        self.btnRemoveX.clicked.connect(moveFromX)
        self.btnRemoveY.clicked.connect(moveFromY)

    # Methods
    def selectFile(self):
        self.txtFile.setText(QtGui.QFileDialog.getOpenFileName())

    def loadCsvFields(self):
        sep = str(self.txtSep.currentText())
        filename = self.txtFile.text()
        self.txtEvery.setValue(self.__estimateSkiplines(filename))
        fields = []
        # Use the csv module to retrieve csv fields
        with open(filename, 'rb') as csvfile:
            for row in csv.DictReader(csvfile, delimiter=sep):
                fields = row.keys()
                break
        # Clear all lists, then add new fields
        map(lambda lst: lst.clear(), [self.listAll, self.listX, self.listY])
        for field in fields:
            self.listAll.addItem(field)

    def moveFromTo(self, fromList, toList):
        while True:
            rowindexes = fromList.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            toList.addItem(fromList.takeItem(row))

    def moveToX(self):
        # Only allow one element in X for now.
        if self.listX.count() > 0: return
        rows = [index.row() for index in self.listAll.selectedIndexes()]
        for row in rows:
            self.listX.addItem(self.listAll.takeItem(row))
            break

    def loadPlot(self):
        xRows = [i.text() for i in self.listX.findItems("", Qt.MatchContains)]
        yRows = [i.text() for i in self.listY.findItems("", Qt.MatchContains)]
        xfields = map(str, xRows)
        yfields = map(str, yRows)
        skiplines = self.txtEvery.value()
        filename = self.txtFile.text()
        sep = str(self.txtSep.currentText())
        self.__csvquery = rpc.CSVQuery(filename  = filename,
                                       seperator = sep,
                                       xfields   = xfields,
                                       yfields   = yfields,
                                       notnull   = xfields + yfields,
                                       linerange = None,
                                       skiplines = skiplines)
        self.accept()

    def __estimateSkiplines(self, filename):
        fsize = os.path.getsize(filename)
        nlines = fsize / rpc.CHARPERLINE
        slines = nlines / rpc.MAXLINES
        if slines < 1: slines = 1
        return int(slines)

    @property
    def result(self):
        return self.__csvquery
