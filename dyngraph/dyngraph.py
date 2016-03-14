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
        plotinfo = dlgNewplot.result
        csvreader = Reader(plotinfo)
        self.__workers.append((workerthread, csvreader))
        self.statusBar.showMessage("Loading... {}...".format(plotinfo.plotname))
        csvreader.sigData.connect(self.createNewPlotWithData)
        csvreader.moveToThread(workerthread)
        workerthread.started.connect(csvreader.start)
        workerthread.start()

    def createNewPlotWithData(self, plotinfo):
        plot = plotwidget.PlotWidget(parent=self, plotinfo=plotinfo)
        tabindex = self.tabWidget.addTab(plot, plotinfo.plotname)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done".format(plotinfo.plotname))

    def fileQuit(self):
        self.close()

    def closeTab(self, i):
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.destroy()


class Reader(QtCore.QObject):
    sigData = QtCore.pyqtSignal(object)

    def __init__(self, plotinfo):
        super(Reader, self).__init__()
        self.plotinfo = plotinfo

    def start(self):
        if self.plotinfo.xisdate:
            datefield = self.plotinfo.xfields
        else:
            datefield = False
        data = pandas.read_csv(self.plotinfo.filename,
                               sep     = self.plotinfo.seperator,
                               usecols = self.plotinfo.fields,
                               decimal = self.plotinfo.decimal,
                               parse_dates = datefield,
                               date_parser = self.plotinfo.datetime_parser,
                               index_col = False,
                               engine  = 'c')
        self.plotinfo.plotdata = data
        self.sigData.emit(self.plotinfo)


class DlgNewPlot(QtGui.QDialog, Ui_NewPlot):
    def __init__(self, parent=None):
        super(DlgNewPlot, self).__init__(parent=parent)
        self.setupUi(self)

        self.plotinfo = plotwidget.PlotInfo()

        # Attach models to ListViews
        self.lstX = QtGui.QStandardItemModel()
        self.lstY = QtGui.QStandardItemModel()
        self.lstAll = QtGui.QStandardItemModel()
        self.lstVX.setModel(self.lstX)
        self.lstVY.setModel(self.lstY)
        self.lstVAll.setModel(self.lstAll)

        # Connect callbacks
        self.btnBrowse.clicked.connect(self.selectFile)
        self.btnLoad.clicked.connect(self.loadCsvFields)
        self.btnOk.clicked.connect(self.loadPlot)
        self.btnCancel.clicked.connect(self.reject)
        self.btnToX.clicked.connect(self.moveToX)
        self.btnToY.clicked.connect(self.moveToY)
        self.btnRemoveX.clicked.connect(self.delFromX)
        self.btnRemoveY.clicked.connect(self.delFromY)
        self.chkUnixTime.stateChanged.connect(self.boolUnixtime)

    # Methods / Callbacks
    def boolUnixtime(self, state):
        self.txtDateTime.setEnabled(not self.chkUnixTime.isChecked())

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
        # Clear all lsts, then add new fields
        map(lambda lst: lst.clear(), [self.lstAll, self.lstX, self.lstY])
        for field in fields:
            if field is None: continue
            item = QtGui.QStandardItem(field)
            self.lstAll.appendRow(item)

    def moveToX(self):
        # Only allow one element in X for now.
        if self.lstX.rowCount() > 0: return
        rows = [index.row() for index in self.lstVAll.selectedIndexes()]
        for row in rows:
            rowItems = self.lstAll.takeRow(row)
            item = rowItems[0]
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setData(QtCore.QVariant(Qt.Unchecked), Qt.CheckStateRole)
            self.lstX.appendRow(item)
            break

    def moveToY(self):
        while True:
            rowindexes = self.lstVAll.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            self.lstY.appendRow(self.lstAll.takeRow(row))

    def delFromX(self):
        while True:
            rowindexes = self.lstVX.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            rowItems = self.lstX.takeRow(row)
            item = rowItems[0]
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
            item.setData(QtCore.QVariant(), Qt.CheckStateRole)
            self.lstAll.appendRow(item)

    def delFromY(self):
        while True:
            rowindexes = self.lstVY.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            self.lstAll.appendRow(self.lstY.takeRow(row))

    def loadPlot(self):
        yRows = [i.text() for i in self.lstY.findItems("", Qt.MatchContains)]
        xRows = [i.text() for i in self.lstX.findItems("", Qt.MatchContains)]
        xState = [i.checkState() for i in self.lstX.findItems("", Qt.MatchContains)]
        for s in xState:
            self.plotinfo.xisdate = s > Qt.Unchecked
            break
        self.plotinfo.xfields = set(map(str, xRows))
        self.plotinfo.yfields = set(map(str, yRows))
        self.plotinfo.filename = str(self.txtFile.text())
        self.plotinfo.seperator = str(self.txtSep.currentText())
        self.plotinfo.decimal = str(self.txtDecimal.currentText())
        self.plotinfo.datetime_format = str(self.txtDateTime.currentText())
        self.plotinfo.isunixtime = self.chkUnixTime.isChecked()
        self.accept()

    @property
    def result(self):
        return self.plotinfo


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)

    wMain = MainUi()
    wMain.show()

    sys.exit(qApp.exec_())
