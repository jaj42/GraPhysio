from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils, dialogs
from graphysio.types import CycleId, Parameter

from graphysio.plotwidgets.plotwidget import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.plotwidgets.poiselector import POISelectorWidget


class TSWidget(PlotWidget):
    def __init__(self, plotdata, parent=None):
        super().__init__(parent=parent)
        self.exporter = exporter.TsExporter(self, plotdata.name)
        self.appendData(plotdata)

    def filterCurve(self, oldcurve, filtername, asnew=False):
        newseries, newsamplerate = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
        if asnew:
            newcurve = self.addSeriesAsCurve(series=newseries)
            newcurve.samplerate = newsamplerate
        else:
            oldname = oldcurve.series.name
            newseries.name = oldname
            oldcurve.series = newseries
            oldcurve.samplerate = newsamplerate
            oldcurve.render()

    def filterFeet(self, curve, filtername, asnew=False):
        oldstarts = curve.feet['start']
        oldstops = curve.feet['stop']
        starts, stops = algorithms.filterFeet(oldstarts, oldstops, filtername, dialogs.askUserValue)
        curve.feet['start'] = starts
        curve.feet['stop'] = stops
        curve.feetitem.render()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.curves.values():
                curve.feetitem.removeSelection()

    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(parent=self, visible=self.curves.values(), hidden=self.hiddenitems)
        if not dlgCurveSelection.exec_():
            return
        visible, invisible = dlgCurveSelection.result
        newvisible = [item for item in visible if item not in self.curves.values()]
        newinvisible = [item for item in invisible if item not in self.hiddenitems]
        for item in newvisible:
            self.addCurve(item)
            if item in self.hiddenitems:
                self.hiddenitems.remove(item)

        for item in newinvisible:
            self.removeCurve(item)
            if item not in self.hiddenitems:
                self.hiddenitems.append(item)

    def launchPOIWidget(self):
        curvenames = list(self.curves.keys())
        q = Parameter('Select Curve', curvenames)
        curvename = dialogs.askUserValue(q)
        curve = self.curves[curvename]
        poiselector = POISelectorWidget(curve.series, parent=self.parent)
        tabindex = self.parent.tabWidget.addTab(poiselector, curve.name())
        self.parent.tabWidget.setCurrentIndex(tabindex)

    @property
    def exportMenu(self):
        menu = super().exportMenu.copy()
        newm = {'&Series to CSV'           : self.exporter.seriestocsv
               ,'&Time info to CSV'        : self.exporter.periodstocsv
               ,'&Cycle info to CSV'       : self.exporter.cyclepointstocsv
               ,'&Cycles to CSV directory' : self.exporter.cyclestocsv
               ,'&POI Selector'            : self.launchPOIWidget
               }
        menu.update(newm)
        return menu