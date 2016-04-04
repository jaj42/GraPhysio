from __future__ import print_function

import sys,csv,os

import pandas as pd

# Hack for Python 2 compat
import sip
sip.setapi('QVariant', 2)
sip.setapi('QString', 2)

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

import plotwidget

from newplot_ui    import Ui_NewPlot
from mainwindow_ui import Ui_MainWindow

class MainUi(QtGui.QMainWindow, Ui_MainWindow):
    hasdata  = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(MainUi, self).__init__(parent=parent)
        self.setupUi(self)

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        self.menuFile.addAction('&New Plot', self.requestNewPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

        self.menuExport.addAction('&Period CSV', self.exportPeriod)
        self.menuExport.addAction('&CSV', self.exportCsv)

        self.hasdata.connect(self.createNewPlotWithData)

    def requestNewPlot(self):
        dlgNewplot = DlgNewPlot(parent = self)
        if not dlgNewplot.exec_(): return
        plotdescr = dlgNewplot.result
        self.statusBar.showMessage("Loading... {}...".format(plotdescr.name))

        reader = Reader(self, plotdescr)
        QtCore.QThreadPool.globalInstance().start(reader)

    def createNewPlotWithData(self, plotdescr):
        plot = plotwidget.PlotWidget(parent=self, plotdescr=plotdescr)
        tabindex = self.tabWidget.addTab(plot, plotdescr.name)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def exportCsv(self):
        i = self.tabWidget.currentIndex()
        if i < 0: return
        plotwidget = self.tabWidget.widget(i)
        plotwidget.exporter.tocsv()

    def exportPeriod(self):
        i = self.tabWidget.currentIndex()
        if i < 0: return
        plotwidget = self.tabWidget.widget(i)
        plotwidget.exporter.toperiodcsv()

    def fileQuit(self):
        self.close()

    def closeTab(self, i):
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.close()
        w.deleteLater()
        del w


class Reader(QtCore.QRunnable):
    def __init__(self, parent, plotdescr):
        super(Reader, self).__init__()
        self._parent = parent
        self._plotdescr = plotdescr

    def run(self):
        data = pd.read_csv(self._plotdescr.filename,
                           sep     = self._plotdescr.seperator,
                           #usecols = self._plotdescr.fields,
                           decimal = self._plotdescr.decimal,
                           index_col = False,
                           encoding = 'latin1',
                           engine  = 'c')
        if self._plotdescr.xisdate:
            if self._plotdescr.isunixtime:
                data['ixdatetime'] = pd.to_datetime(data[self._plotdescr.datefield],
                                                    unit = 'ms')
            else:
                data['ixdatetime'] = pd.to_datetime(data[self._plotdescr.datefield],
                                                    format = self._plotdescr.datetime_format)
            data = data.set_index('ixdatetime')
        self._plotdescr.data = data
        self._parent.hasdata.emit(self._plotdescr)


class DlgNewPlot(QtGui.QDialog, Ui_NewPlot):
    def __init__(self, parent=None):
        super(DlgNewPlot, self).__init__(parent=parent)
        self.setupUi(self)

        self.plotdescr = plotwidget.PlotDescription()
        self.dircache = ""

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
        filepath = QtGui.QFileDialog.getOpenFileName(parent = self,
                                                     caption = "Open CSV file",
                                                     directory = self.dircache)
        if not filepath: return
        self.dircache = os.path.dirname(filepath)
        self.txtFile.setText(filepath)

    def loadCsvFields(self):
        sep = self.txtSep.currentText()
        filename = self.txtFile.text()
        fields = []
        # Use the csv module to retrieve csv fields
        with open(filename, 'r') as csvfile:
            for row in csv.DictReader(csvfile, delimiter=sep):
                fields = row.keys()
                break
        # Clear all lists, then add new fields
        for lst in [self.lstAll, self.lstX, self.lstY]: lst.clear()
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
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
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
            item.setData(None, Qt.CheckStateRole)
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
            self.plotdescr.xisdate = s > Qt.Unchecked
            break
        if len(xRows) > 0:
            self.plotdescr.xfield = xRows[0]
        else:
            self.plotdescr.xfield = None
        self.plotdescr.yfields = yRows
        self.plotdescr.filename = self.txtFile.text()
        self.plotdescr.seperator = self.txtSep.currentText()
        self.plotdescr.decimal = self.txtDecimal.currentText()
        self.plotdescr.datetime_format = self.txtDateTime.currentText()
        self.plotdescr.isunixtime = self.chkUnixTime.isChecked()
        self.accept()

    @property
    def result(self):
        return self.plotdescr


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)

    wMain = MainUi()
    wMain.show()

    sys.exit(qApp.exec_())
