import sys,csv,os

import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

import plotwidget

from newplot_ui     import Ui_NewPlot
from mainwindow_ui  import Ui_MainWindow
from cycledetect_ui import Ui_CycleDetection

class MainUi(QtGui.QMainWindow, Ui_MainWindow):
    hasdata  = QtCore.pyqtSignal(object)
    haserror = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        self.menuFile.addAction('&New Plot', self.launchNewPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

        self.menuData.addAction('Cycle &Detection', self.launchCycleDetection, Qt.CTRL + Qt.Key_D)

        self.menuExport.addAction('&Series to CSV', self.exportCsv)
        self.menuExport.addAction('&Time info to CSV', self.exportPeriod)
        self.menuExport.addAction('&Cycle info to CSV', self.exportCycles)

        self.hasdata.connect(self.createNewPlotWithData)
        self.haserror.connect(self.displayError)

    def launchCycleDetection(self):
        dlgCycles = DlgCycleDetection(parent = self)
        if not dlgCycles.exec_(): return
        choices = dlgCycles.result
        plotframe = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotframe.curves[curvename]
            plotframe.addFeet(curve, plotwidget.FootType(choice))

    def launchNewPlot(self):
        dlgNewplot = DlgNewPlot(parent=self, directory=self.dircache)
        if not dlgNewplot.exec_(): return
        plotdata = dlgNewplot.result
        self.dircache = plotdata.folder
        self.statusBar.showMessage("Loading... {}...".format(plotdata.name))

        reader = Reader(self, plotdata)
        QtCore.QThreadPool.globalInstance().start(reader)

    def createNewPlotWithData(self, plotdata):
        plotframe = plotwidget.PlotFrame(plotdata=plotdata, parent=self)
        tabindex = self.tabWidget.addTab(plotframe, plotdata.name)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def exportCsv(self):
        plotframe = self.tabWidget.currentWidget()
        if plotframe is None: return
        plotframe.exporter.seriestocsv()

    def exportPeriod(self):
        plotframe = self.tabWidget.currentWidget()
        if plotframe is None: return
        plotframe.exporter.periodstocsv()

    def exportCycles(self):
        plotframe = self.tabWidget.currentWidget()
        if plotframe is None: return
        plotframe.exporter.cyclepointstocsv()

    def fileQuit(self):
        self.close()

    def closeTab(self, i):
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.close()
        w.deleteLater()
        del w

    def displayError(self, errmsg):
        msgbox = QtGui.QMessageBox()
        msgbox.setWindowTitle("Error creating plot")
        msgbox.setText(str(errmsg))
        msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
        msgbox.setIcon(QtGui.QMessageBox.Critical)
        msgbox.exec_()


class Reader(QtCore.QRunnable):
    def __init__(self, parent, plotdata):
        super().__init__()
        self._parent = parent
        self._plotdata = plotdata

    def run(self):
        try:
            data = self.getdata()
        except ValueError as e:
            self._parent.haserror.emit(str(e))
        else:
            self._plotdata.data = data
            self._parent.hasdata.emit(self._plotdata)

    def getdata(self):
        if self._plotdata.loadall:
            # usecols = None loads all columns
            usecols = None
        else:
            usecols = self._plotdata.fields
        data = pd.read_csv(self._plotdata.filepath,
                           sep       = self._plotdata.seperator,
                           usecols   = usecols,
                           decimal   = self._plotdata.decimal,
                           index_col = False,
                           encoding  = 'latin1',
                           engine    = 'c')
        if self._plotdata.xisdate:
            if self._plotdata.isunixtime:
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield],
                                                    unit = 'ms')
            else:
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield],
                                                    format = self._plotdata.datetime_format)
            data = data.set_index('nsdatetime')
        return data


class DlgNewPlot(QtGui.QDialog, Ui_NewPlot):
    def __init__(self, parent=None, directory=""):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.dircache = directory
        self.plotdata = plotwidget.PlotDescription()

        # Attach models to ListViews
        self.lstX = QtGui.QStandardItemModel()
        self.lstY = QtGui.QStandardItemModel()
        self.lstAll = QtGui.QStandardItemModel()

        self.lstVX.setModel(self.lstX)
        self.lstVY.setModel(self.lstY)
        self.lstVAll.setModel(self.lstAll)

        # Setup Field Table
        self.lstVAll.verticalHeader().hide()
        self.lstVAll.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

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

    @property
    def result(self):
        return self.plotdata

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
        # Guesstimate CSV field and decimal seperators
        delims = self.estimateDelimiters(filepath)
        self.txtSep.setEditText(delims[0])
        self.txtDecimal.setEditText(delims[1])
        self.txtDateTime.setEditText("%Y-%m-%d %H:%M:%S{}%f".format(delims[1]))

    def estimateDelimiters(self, filepath):
        with open(filepath, 'r') as csvfile:
            line1 = next(csvfile)
            line2 = next(csvfile)
            semipos = line1.find(';')
            if semipos == -1:
                seperator = ','
            else:
                seperator = ';'
            periodpos = line2.find('.')
            if periodpos == -1:
                decimal   = ','
            else:
                decimal   = '.'
        return (seperator, decimal)

    def loadCsvFields(self):
        sep = self.txtSep.currentText()
        filepath = self.txtFile.text()
        fields = []
        # Use the csv module to retrieve csv fields
        for lst in [self.lstAll, self.lstX, self.lstY]: lst.clear()
        self.lstAll.setHorizontalHeaderLabels(["Field", "1st Line"])
        with open(filepath, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=sep)
            row = next(csvreader)
            for key, value in row.items():
                if key is None: continue
                keyitem = QtGui.QStandardItem(key)
                valueitem = QtGui.QStandardItem(value)
                self.lstAll.appendRow([keyitem, valueitem])
        self.lstAll.sort(0)

    def moveToX(self):
        if self.lstX.rowCount() > 0: return # Only allow one element allowed for X.
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.itemCheckable(row, True)
        self.lstX.appendRow(row)

    def moveToY(self):
        while True:
            selection = self.lstVAll.selectedIndexes()
            if len(selection) < 1: break
            rowindex = selection[0].row()
            self.lstY.appendRow(self.lstAll.takeRow(rowindex))

    def delFromX(self):
        while True:
            selection = self.lstVX.selectedIndexes()
            if len(selection) < 1: break
            rowindex = selection[0].row()
            row = self.lstX.takeRow(rowindex)
            self.itemCheckable(row, False)
            self.lstAll.appendRow(row)

    def delFromY(self):
        while True:
            rowindexes = self.lstVY.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            self.lstAll.appendRow(self.lstY.takeRow(row))

    def itemCheckable(self, row, checkable):
            field = row[0]
            if checkable:
                field.setFlags(field.flags() | QtCore.Qt.ItemIsUserCheckable)
                field.setData(Qt.Checked, Qt.CheckStateRole)
            else:
                field.setFlags(field.flags() ^ QtCore.Qt.ItemIsUserCheckable)
                field.setData(None, Qt.CheckStateRole)

    def loadPlot(self):
        yRows = [i.text() for i in self.lstY.findItems("", Qt.MatchContains)]
        xRows = [i.text() for i in self.lstX.findItems("", Qt.MatchContains)]
        xState = [i.checkState() for i in self.lstX.findItems("", Qt.MatchContains)]
        for s in xState:
            self.plotdata.xisdate = s > Qt.Unchecked
            break
        if len(xRows) > 0:
            self.plotdata.xfield = xRows[0]
        else:
            self.plotdata.xfield = None
        self.plotdata.yfields = yRows
        self.plotdata.filepath = self.txtFile.text()
        self.plotdata.seperator = self.txtSep.currentText()
        self.plotdata.decimal = self.txtDecimal.currentText()
        self.plotdata.datetime_format = self.txtDateTime.currentText()
        self.plotdata.isunixtime = self.chkUnixTime.isChecked()
        self.plotdata.loadall = self.chkLoadAll.isChecked()
        self.accept()


class DlgCycleDetection(QtGui.QDialog, Ui_CycleDetection):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if plotframe is None:
            return

        for n, curvename in enumerate(plotframe.curves.keys()):
            curveitem = QtGui.QTableWidgetItem(curvename)
            combo = QtGui.QComboBox()
            combo.addItems(['Pressure','Velocity','None'])
            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

    @property
    def result(self):
        return {curve: combo.currentText() for (curve, combo) in self.choices.items()}


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    sys.exit(app.exec_())
