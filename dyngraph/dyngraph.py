from __future__ import print_function

import sys,csv

import pandas

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

import plotwidget

from newplot_ui    import Ui_NewPlot
from mainwindow_ui import Ui_MainWindow

class MainUi(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainUi, self).__init__(parent=parent)
        self.setupUi(self)

        self.__workers = []

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        self.menuFile.addAction('&New Plot', self.requestNewPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

    def requestNewPlot(self):
        dlgNewplot = DlgNewPlot()
        if not dlgNewplot.exec_(): return

        workerthread = QtCore.QThread()
        csvreader = dlgNewplot.result
        self.__workers.append((workerthread, csvreader))

        csvreader.sigData.connect(self.createNewPlotWithData)
        csvreader.moveToThread(workerthread)
        workerthread.started.connect(csvreader.start)
        workerthread.start()

    def createNewPlotWithData(self, data):
        plot = plotwidget.PlotWidget(parent=self, plotdata=data)
        tabindex = self.tabWidget.addTab(plot, "test")
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


class Reader(QtCore.QObject):
    sigData = QtCore.pyqtSignal(object)

    def __init__(self, filename, seperator, fields):
        super(Reader, self).__init__()
        self.filename  = filename
        self.seperator = seperator
        self.fields    = fields

    def start(self):
        data = pandas.read_csv(self.filename,
                               sep     = self.seperator,
                               usecols = self.fields,
                               engine  = 'c')
        self.sigData.emit(data)


class DlgNewPlot(QtGui.QDialog, Ui_NewPlot):
    def __init__(self, parent=None):
        super(DlgNewPlot, self).__init__(parent=parent)
        self.setupUi(self)

        self.xfields = []
        self.yfields = []
        self.filename = ""
        self.sep = ""

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
        self.xfields = map(str, xRows)
        self.yfields = map(str, yRows)
        self.filename = str(self.txtFile.text())
        self.sep = str(self.txtSep.currentText())
        self.accept()

    @property
    def result(self):
        return Reader(self.filename, self.sep, self.xfields + self.yfields)


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)

    wMain = MainUi()
    wMain.show()

    sys.exit(qApp.exec_())
