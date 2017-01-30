import sys,csv,os

import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

from graphysio import tsplot, puplot, dialogs, utils, io
from graphysio.ui import Ui_MainWindow, Ui_NewPlot, Ui_CycleDetection, Ui_Filter

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

        self.menuData.addAction('&Set sampling rate', self.launchSetSamplerate, Qt.CTRL + Qt.Key_S)
        self.menuData.addAction('&Filter', self.launchFilter, Qt.CTRL + Qt.Key_F)
        self.menuData.addAction('Cycle &Detection', self.launchCycleDetection, Qt.CTRL + Qt.Key_D)
        self.menuData.addAction('Generate PU-&Loops', self.launchLoop, Qt.CTRL + Qt.Key_L)

        self.menuExport.addAction('&Series to CSV', self.exportCsv)
        self.menuExport.addAction('&Time info to CSV', self.exportPeriod)
        self.menuExport.addAction('&Cycle info to CSV', self.exportCycles)
        self.menuExport.addAction('&Loop Data', self.exportLoops)

        self.hasdata.connect(self.createNewPlotWithData)
        self.haserror.connect(self.displayError)

    def launchLoop(self):
        sourcewidget = self.tabWidget.currentWidget()
        dlgSetupPU = dialogs.DlgSetupPULoop(sourcewidget, parent = self)
        if not dlgSetupPU.exec_(): return

        uname, pname = dlgSetupPU.result

        try:
            curves = sourcewidget.curves
            plotdata = sourcewidget.plotdata
            u = curves[uname]
            p = curves[pname]
        except Exception as e:
            self.haserror.emit('Could not create PU loops: {}', e)
            return

        subsetrange = utils.getvbrange(sourcewidget)

        loopwidget = puplot.LoopWidget(u, p, plotdata, subsetrange=subsetrange, parent=self)
        tabindex = self.tabWidget.addTab(loopwidget, '{}-loops'.format(plotdata.name))
        self.tabWidget.setCurrentIndex(tabindex)

    def launchCycleDetection(self):
        dlgCycles = dialogs.DlgCycleDetection(parent = self)
        if not dlgCycles.exec_(): return
        choices = dlgCycles.result
        plotwidget = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotwidget.curves[curvename]
            plotwidget.addFeet(curve, utils.FootType(choice))

    def launchSetSamplerate(self):
        plotwidget = self.tabWidget.currentWidget()
        plotwidget.askSamplerate()

    def launchFilter(self):
        dlgFilter = dialogs.DlgFilter(parent = self)
        if not dlgFilter.exec_(): return
        choices = dlgFilter.result
        plotwidget = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotwidget.curves[curvename]
            plotwidget.addFiltered(curve, choice)

    def launchNewPlot(self):
        dlgNewplot = dialogs.DlgNewPlot(parent=self, directory=self.dircache)
        if not dlgNewplot.exec_(): return
        plotdata = dlgNewplot.result
        self.dircache = plotdata.folder
        self.statusBar.showMessage("Loading... {}...".format(plotdata.name))

        reader = io.Reader(self, plotdata)
        QtCore.QThreadPool.globalInstance().start(reader)

    def createNewPlotWithData(self, plotdata):
        plotwidget = tsplot.PlotWidget(plotdata=plotdata, parent=self)
        tabindex = self.tabWidget.addTab(plotwidget, plotdata.name)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def exportCsv(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None: return
        try:
            plotwidget.exporter.seriestocsv()
        except AttributeError:
            self.haserror.emit('Method available for this plot.')

    def exportPeriod(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None: return
        try:
            plotwidget.exporter.periodstocsv()
        except AttributeError:
            self.haserror.emit('Method available for this plot.')

    def exportCycles(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None: return
        try:
            plotwidget.exporter.cyclepointstocsv()
        except AttributeError:
            self.haserror.emit('Method available for this plot.')

    def exportLoops(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None: return
        try:
            plotwidget.exporter.exportloops()
        except AttributeError:
            self.haserror.emit('Method available for this plot.')

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
