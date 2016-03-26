from __future__ import print_function

import sys,csv

import pandas as pd

# Hack for Python 2 compat
import sip
sip.setapi('QVariant', 1)

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

        self.menuExport.addAction('&CSV', self.exportCsv)

        self.hasdata.connect(self.createNewPlotWithData)

    def requestNewPlot(self):
        dlgNewplot = DlgNewPlot(parent = self)
        if not dlgNewplot.exec_(): return
        plotinfo = dlgNewplot.result
        self.statusBar.showMessage("Loading... {}...".format(plotinfo.plotname))

        reader = Reader(self, plotinfo)
        QtCore.QThreadPool.globalInstance().start(reader)

    def createNewPlotWithData(self, plotinfo):
        plot = plotwidget.PlotWidget(plotinfo=plotinfo)
        #plot.setAttribute(Qt.WA_DeleteOnClose)
        tabindex = self.tabWidget.addTab(plot, plotinfo.plotname)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def exportCsv(self):
        i = self.tabWidget.currentIndex()
        if i < 0: return
        plotwidget = self.tabWidget.widget(i)
        filename = QtGui.QFileDialog.getSaveFileName(parent  = self,
                                                     caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)")
        plotwidget.exporter.tocsv(filename)


    def fileQuit(self):
        self.close()

    def closeTab(self, i):
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.close()
        w.deleteLater()


class Reader(QtCore.QRunnable):
    def __init__(self, parent, _plotinfo):
        super(Reader, self).__init__()
        self._parent = parent
        self._plotinfo = _plotinfo

    def run(self):
        data = pd.read_csv(self._plotinfo.filename,
                           sep     = self._plotinfo.seperator,
                           usecols = self._plotinfo.fields,
                           decimal = self._plotinfo.decimal,
                           index_col = False,
                           encoding = 'latin1',
                           engine  = 'c')
        if self._plotinfo.xisdate:
            if self._plotinfo.isunixtime:
                data['dt'] = pd.to_datetime(data[self._plotinfo.datefield],
                                            format = self._plotinfo.datetime_format)
            else:
                data['dt'] = pd.to_datetime(data[self._plotinfo.datefield],
                                            unit = 'ms')
            data = data.set_index('dt')
        self._plotinfo.plotdata = data
        self._parent.hasdata.emit(self._plotinfo)


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
        self.txtFile.setText(QtGui.QFileDialog.getOpenFileName(parent = self))

    def loadCsvFields(self):
        sep = str(self.txtSep.currentText())
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
        yRows = [str(i.text()) for i in self.lstY.findItems("", Qt.MatchContains)]
        xRows = [str(i.text()) for i in self.lstX.findItems("", Qt.MatchContains)]
        xState = [i.checkState() for i in self.lstX.findItems("", Qt.MatchContains)]
        for s in xState:
            self.plotinfo.xisdate = s > Qt.Unchecked
            break
        self.plotinfo.xfields = xRows
        self.plotinfo.yfields = yRows
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
