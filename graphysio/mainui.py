import sys,csv,os
from functools import partial

import pandas as pd
import numpy as np

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import tsplot, puplot, dialogs, utils, csvio

class MainUi(*utils.loadUiFile('mainwindow.ui')):
    hasdata  = QtCore.pyqtSignal(object)
    haserror = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.tabWidget.tabCloseRequested.connect(self.closeTab)

        launchNewPlot = partial(self.launchReadData, newwidget=True)
        launchAppendPlot = partial(self.launchReadData, newwidget=False)
        self.menuFile.addAction('&New Plot', launchNewPlot, QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.menuFile.addAction('&Append to Plot', launchAppendPlot, QtCore.Qt.CTRL + QtCore.Qt.Key_A)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        self.menuData.addAction('&Set sampling rate', self.launchSetSamplerate, QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.menuData.addAction('&Filter', self.launchFilter, QtCore.Qt.CTRL + QtCore.Qt.Key_F)
        self.menuData.addAction('Cycle &Detection', self.launchCycleDetection, QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        self.menuData.addAction('Generate PU-&Loops', self.launchLoop, QtCore.Qt.CTRL + QtCore.Qt.Key_L)

        self.menuExport.addAction('&Series to CSV', self.exportCsv)
        self.menuExport.addAction('&Time info to CSV', self.exportPeriod)
        self.menuExport.addAction('&Cycle info to CSV', self.exportCycles)
        self.menuExport.addAction('&Loop Data', self.exportLoops)

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

    def launchReadData(self, newwidget=True):
        if newwidget:
            title = "New Plot"
            try:
                self.hasdata.disconnect()
            except TypeError:
                pass
            finally:
                self.hasdata.connect(self.createNewPlotWithData)
        else:
            title = "Append to Plot"
            try:
                self.hasdata.disconnect()
            except TypeError:
                pass
            finally:
                self.hasdata.connect(self.appendToPlotWithData)
        dlgNewplot = dialogs.DlgNewPlot(parent=self, title=title, directory=self.dircache)
        if not dlgNewplot.exec_(): return
        plotdata = dlgNewplot.result
        self.dircache = plotdata.folder
        self.statusBar.showMessage("Loading... {}...".format(plotdata.name))

        reader = csvio.Reader(plotdata, self.hasdata, self.haserror)
        QtCore.QThreadPool.globalInstance().start(reader)

    def appendToPlotWithData(self, plotdata):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            self.haserror.emit('No plot selected.')
            return
        plotwidget.appendData(plotdata)
        self.statusBar.showMessage("Loading... done")

    def createNewPlotWithData(self, plotdata):
        plotwidget = tsplot.PlotWidget(plotdata=plotdata, parent=self)
        tabindex = self.tabWidget.addTab(plotwidget, plotdata.name)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def exportCsv(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
        try:
            plotwidget.exporter.seriestocsv()
        except AttributeError:
            self.haserror.emit('Method available for this plot.')

    def exportPeriod(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
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
