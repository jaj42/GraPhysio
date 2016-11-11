import sys,csv,os

import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

from dyngraph import dialogs

from dyngraph.plotwidget import PlotWidget
from dyngraph.puloop import LoopWidget
from dyngraph.utils import PlotDescription, FootType, FilterType
from dyngraph.ui import Ui_MainWindow, Ui_NewPlot, Ui_CycleDetection, Ui_Filter

class MainUi(QtGui.QMainWindow, Ui_MainWindow):
    hasdata  = QtCore.pyqtSignal(object)
    haserror = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        self.menuFile.addAction('&New Plot', self.launchNewPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

        self.menuData.addAction('&Filter', self.launchFilter, Qt.CTRL + Qt.Key_F)
        self.menuData.addAction('Cycle &Detection', self.launchCycleDetection, Qt.CTRL + Qt.Key_D)
        self.menuData.addAction('Generate PU-&Loops', self.launchLoop, Qt.CTRL + Qt.Key_L)

        self.menuExport.addAction('&Series to CSV', self.exportCsv)
        self.menuExport.addAction('&Time info to CSV', self.exportPeriod)
        self.menuExport.addAction('&Cycle info to CSV', self.exportCycles)

        self.hasdata.connect(self.createNewPlotWithData)
        self.haserror.connect(self.displayError)

    def launchLoop(self):
        sourcewidget = self.tabWidget.currentWidget()
        dlgSetupPU = dialogs.DlgSetupPULoop(sourcewidget, parent = self)
        if not dlgSetupPU.exec_(): return

        uname, pname = dlgSetupPU.result

        curves = sourcewidget.curves
        plotdata = sourcewidget.plotdata
        u = curves[uname]
        ufeet = u.feet
        p = curves[pname]
        pfeet = p.feet

        if type(ufeet) is not tuple:
            self.haserror.emit("Incorrect Velocity feet")
            return

        if type(pfeet) is tuple:
            self.haserror.emit("Incorrect Pressure feet")
            return

        ## XXX todo check existance / correctness of data
        loopwidget = LoopWidget(u, p, ufeet, pfeet, parent=self)
        tabindex = self.tabWidget.addTab(loopwidget, '{}-loops'.format(plotdata.name))
        self.tabWidget.setCurrentIndex(tabindex)

    def launchCycleDetection(self):
        dlgCycles = dialogs.DlgCycleDetection(parent = self)
        if not dlgCycles.exec_(): return
        choices = dlgCycles.result
        plotframe = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotframe.curves[curvename]
            plotframe.addFeet(curve, FootType(choice))

    def launchFilter(self):
        dlgFilter = dialogs.DlgFilter(parent = self)
        if not dlgFilter.exec_(): return
        choices = dlgFilter.result
        plotframe = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotframe.curves[curvename]
            plotframe.addFiltered(curve, FilterType(choice))

    def launchNewPlot(self):
        dlgNewplot = dialogs.DlgNewPlot(parent=self, directory=self.dircache)
        if not dlgNewplot.exec_(): return
        plotdata = dlgNewplot.result
        self.dircache = plotdata.folder
        self.statusBar.showMessage("Loading... {}...".format(plotdata.name))

        reader = Reader(self, plotdata)
        QtCore.QThreadPool.globalInstance().start(reader)

    def createNewPlotWithData(self, plotdata):
        plotframe = PlotWidget(plotdata=plotdata, parent=self)
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
            self._parent.haserror.emit(e)
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

        # Coerce all columns to numeric and remove empty columns
        tonum = lambda x: pd.to_numeric(x, errors='coerce')
        data = data.apply(tonum).dropna(axis='columns', how='all')

        # Don't try requested fields that are empty
        self._plotdata.yfields = [f for f in self._plotdata.yfields if f in data.columns]

        return data
