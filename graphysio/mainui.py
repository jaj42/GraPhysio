import sys, csv, os
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
        getshell = partial(utils.getshell, ui=self)

        self.menuFile.addAction('&New Plot',       self.errguard(launchNewPlot),    QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.menuFile.addAction('&Append to Plot', self.errguard(launchAppendPlot), QtCore.Qt.CTRL + QtCore.Qt.Key_A)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Load plugin', self.errguard(utils.loadmodule))
        self.menuFile.addAction('Get &shell', self.errguard(getshell))
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.errguard(self.fileQuit), QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        self.menuCurves.addAction('Visible &Curves',    self.errguard(self.launchCurveList),      QtCore.Qt.CTRL + QtCore.Qt.Key_C)
        self.menuCurves.addAction('&Filter',            self.errguard(self.launchFilter),         QtCore.Qt.CTRL + QtCore.Qt.Key_F)
        self.menuCurves.addAction('Cycle &Detection',   self.errguard(self.launchCycleDetection), QtCore.Qt.CTRL + QtCore.Qt.Key_D)

        self.menuSelection.addAction('As &new plot', self.errguard(self.launchNewPlotFromSelection))
        self.menuSelection.addAction('&Append to other plot', self.errguard(self.launchAppendToPlotFromSelection))
        self.menuSelection.addAction('Generate PU-&Loops', self.errguard(self.launchLoop), QtCore.Qt.CTRL + QtCore.Qt.Key_L)

        self.menuExport.addAction('&Series to CSV',     self.errguard(self.exportSeries))
        self.menuExport.addAction('&Time info to CSV',  self.errguard(self.exportPeriod))
        self.menuExport.addAction('&Cycle info to CSV', self.errguard(self.exportCycles))
        self.menuExport.addAction('&Loop Data',         self.errguard(self.exportLoops))

        self.haserror.connect(self.displayError)

    def errguard(self, f):
        # Lift exceptions to UI reported errors
        def wrapped():
            try:
                f()
            except Exception as e:
                # Re-raise errors here for DEBUG
                #raise e
                self.haserror.emit(e)
        return wrapped

    def launchLoop(self):
        tabindex = self.tabWidget.currentIndex()
        sourcewidget = self.tabWidget.widget(tabindex)

        if sourcewidget is None:
            return

        dlgSetupPU = dialogs.DlgSetupPULoop(sourcewidget, parent = self)
        if not dlgSetupPU.exec_(): return

        uname, pname = dlgSetupPU.result

        curves = sourcewidget.curves
        u = curves[uname]
        p = curves[pname]
        subsetrange = sourcewidget.vbrange
        loopwidget = puplot.LoopWidget(u, p, subsetrange, parent=self)

        oldname = self.tabWidget.tabText(tabindex)
        newtabindex = self.tabWidget.addTab(loopwidget, '{}-loops'.format(oldname))
        self.tabWidget.setCurrentIndex(newtabindex)

    def launchCurveList(self):
        plotwidget = self.tabWidget.currentWidget()
        plotwidget.showCurveList()

    def launchCycleDetection(self):
        dlgCycles = dialogs.DlgCycleDetection(parent = self)
        if not dlgCycles.exec_(): return
        choices = dlgCycles.result
        plotwidget = self.tabWidget.currentWidget()
        for curvename, choice in choices.items():
            curve = plotwidget.curves[curvename]
            plotwidget.addFeet(curve, utils.FootType(choice))

    def launchFilter(self):
        dlgFilter = dialogs.DlgFilter(parent = self)
        if not dlgFilter.exec_(): return
        createnew, curvechoices, feetchoices = dlgFilter.result
        plotwidget = self.tabWidget.currentWidget()
        for curvename, choice in curvechoices.items():
            if choice == 'None':
                continue
            curve = plotwidget.curves[curvename]
            plotwidget.filterCurve(curve, choice, asnew=createnew)
        for feetname, choice in feetchoices.items():
            if choice == 'None':
                continue
            feet = plotwidget.feetitems[feetname]
            plotwidget.filterFeet(feet, choice)

    def launchReadData(self, newwidget=True):
        if newwidget:
            title = "New Plot"
            try:
                self.hasdata.disconnect()
            except:
                pass
            finally:
                self.hasdata.connect(self.createNewPlotWithData)
        else:
            title = "Append to Plot"
            try:
                self.hasdata.disconnect()
            except:
                pass
            finally:
                self.hasdata.connect(self.appendToPlotWithData)

        dlgNewplot = dialogs.DlgNewPlot(parent=self, title=title, directory=self.dircache)
        if not dlgNewplot.exec_(): return
        csvrequest = dlgNewplot.result
        self.dircache = csvrequest.folder
        self.statusBar.showMessage("Loading... {}...".format(csvrequest.name))

        reader = csvio.Reader(csvrequest, self.hasdata, self.haserror)
        QtCore.QThreadPool.globalInstance().start(reader)

    def appendToPlotWithData(self, plotdata):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            self.haserror.emit('No plot selected.')
            return

        qmsg = "Timeshift new curves to make the beginnings coincide?"
        reply = QtGui.QMessageBox.question(self, 'Append to plot', qmsg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        dorealign = (reply == QtGui.QMessageBox.Yes)

        plotwidget.appendData(plotdata, dorealign)
        self.statusBar.showMessage("Loading... done")

    def createNewPlotWithData(self, plotdata):
        plotwidget = tsplot.PlotWidget(plotdata=plotdata, parent=self)
        tabindex = self.tabWidget.addTab(plotwidget, plotdata.name)
        self.tabWidget.setCurrentIndex(tabindex)
        self.statusBar.showMessage("Loading... done")

    def launchNewPlotFromSelection(self):
        oldtabindex = self.tabWidget.currentIndex()
        oldname = self.tabWidget.tabText(oldtabindex)
        sourcewidget = self.tabWidget.widget(oldtabindex)
        xmin, xmax = sourcewidget.vbrange

        newname = '{}-sub'.format(oldname)
        plotdata = utils.PlotData(name=newname)

        plotwidget = tsplot.PlotWidget(plotdata=plotdata, parent=self)
        newtabindex = self.tabWidget.addTab(plotwidget, plotdata.name)
        for c in sourcewidget.curves.values():
            series = c.series.loc[xmin:xmax]
            plotwidget.addCurve(series)
        self.tabWidget.setCurrentIndex(newtabindex)

    def launchAppendToPlotFromSelection(self):
        ntabs = self.tabWidget.count()
        tabnames = [self.tabWidget.tabText(idx) for idx in range(ntabs)]
        desttabname, ok = QtGui.QInputDialog.getItem(self, 'Select destination', 'Destination plot', tabnames, editable=False)
        if not ok:
            return
        destidx = tabnames.index(desttabname)
        destwidget = self.tabWidget.widget(destidx)

        qmsg = "Timeshift new curves to make the beginnings coincide?"
        reply = QtGui.QMessageBox.question(self, 'Append to plot', qmsg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        dorealign = (reply == QtGui.QMessageBox.Yes)

        oldtabindex = self.tabWidget.currentIndex()
        oldname = self.tabWidget.tabText(oldtabindex)
        sourcewidget = self.tabWidget.widget(oldtabindex)
        xmin, xmax = sourcewidget.vbrange

        for c in sourcewidget.curves.values():
            series = c.series.loc[xmin:xmax]
            destwidget.addCurve(series, dorealign=dorealign)
        self.tabWidget.setCurrentIndex(destidx)

    def exportSeries(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
        if hasattr(plotwidget.exporter, 'seriestocsv'):
            plotwidget.exporter.seriestocsv()
        else:
            self.haserror.emit('Method not available for this plot.')

    def exportPeriod(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
        if hasattr(plotwidget.exporter, 'periodstocsv'):
            plotwidget.exporter.periodstocsv()
        else:
            self.haserror.emit('Method not available for this plot.')

    def exportCycles(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
        if hasattr(plotwidget.exporter, 'cyclepointstocsv'):
            plotwidget.exporter.cyclepointstocsv()
        else:
            self.haserror.emit('Method not available for this plot.')

    def exportLoops(self):
        plotwidget = self.tabWidget.currentWidget()
        if plotwidget is None:
            return
        if hasattr(plotwidget.exporter, 'exportloops'):
            plotwidget.exporter.exportloops()
        else:
            self.haserror.emit('Method not available for this plot.')

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
        msgbox.setWindowTitle("Error")
        msgbox.setText(str(errmsg))
        msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
        msgbox.setIcon(QtGui.QMessageBox.Critical)
        msgbox.exec_()
