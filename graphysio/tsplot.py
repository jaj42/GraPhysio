import sys
from itertools import cycle, islice

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils, dialogs, legend

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotdata, parent=None):
        self.parent = parent
        self.colors = utils.Colors()
        self.hiddenitems = []

        axisItems = {'bottom': TimeAxisItem(orientation='bottom')}

        super().__init__(parent=parent, axisItems=axisItems, background='w')

        self.legend = legend.MyLegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

        self.exporter = exporter.TsExporter(self, plotdata.name)

        allSeries = (plotdata.data[c] for c in plotdata.fields)
        for series in allSeries:
            self.addCurve(series)

    def appendData(self, newplotdata, dorealign=False):
        allSeries = (newplotdata.data[c] for c in newplotdata.fields)
        for series in allSeries:
            self.addCurve(series, dorealign=dorealign)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    @property
    def feetitems(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, FeetItem)}

    def addCurve(self, series, pen=None, dorealign=False):
        if pen is None:
            pen = next(self.colors)

        # Timeshift new curves to make the beginnings coincide
        if dorealign:
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset

        curve = CurveItem(series = series,
                          pen    = pen)
        self.addItem(curve)
        self.legend.addItem(curve, curve.name())
        return curve

    def addFeet(self, curve, foottype):
        if foottype is utils.FootType.none:
            return
        elif foottype is utils.FootType.velocity:
            starts, stops = algorithms.findFlowCycles(curve)
        else:
            starts = algorithms.findPressureFeet(curve)
            stops = None

        feet = FeetItem(curve, starts, stops)
        curve.feetitem = feet
        feet.sigClicked.connect(self.sigPointClicked)
        self.addItem(feet)

    def filterCurve(self, oldcurve, filtername, asnew=False):
        newseries, newsamplerate = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
        if asnew:
            newcurve = self.addCurve(series=newseries)
            newcurve.samplerate = newsamplerate
        else:
            oldcurve.setData(x = newseries.index,
                             y = newseries.values)
            oldcurve.samplerate = newsamplerate

    def sigPointClicked(self, curve, points):
        point = points[0] # keep the first point
        if not curve.isPointSelected(point):
            curve.selectPoint(point)
        else:
            curve.unselectPoint(point)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.feetitems.values():
                curve.removeSelection()

    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(parent=self, visible=self.listDataItems(), hidden=self.hiddenitems)
        if not dlgCurveSelection.exec_():
            return
        visible, invisible = dlgCurveSelection.result
        newvisible = [item for item in visible if item not in self.listDataItems()]
        newinvisible = [item for item in invisible if item not in self.hiddenitems]
        self.hiddenitems = invisible
        for item in newvisible:
            self.addItem(item)
            self.legend.addItem(item, item.name())
            if item in self.hiddenitems:
                self.hiddenitems.remove(item)

        for item in newinvisible:
            self.removeItem(item)
            self.legend.removeItem(item.name())
            if item not in self.hiddenitems:
                self.hiddenitems.append(item)

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)


class CurveItem(pg.PlotDataItem):
    def __init__(self, series, pen=QtGui.QColor(QtCore.Qt.black), *args, **kwargs):
        self.series = series
        self.feetitem = None
        self.pen = pen
        self.samplerate = utils.estimateSampleRate(self.series)
        super().__init__(x    = self.series.index,
                         y    = self.series.values,
                         name = self.series.name,
                         pen  = self.pen,
                         antialias = True,
                         *args, **kwargs)


class FeetItem(pg.ScatterPlotItem):
    symPoint, symStart, symStop = ('o', 't', 's')

    def __init__(self, curve, starts, stops=None, namesuffix='feet', *args, **kwargs):
        self.selected = []
        pen = curve.opts['pen']
        self._name = "{}-{}".format(curve.name(), namesuffix)
        super().__init__(pen = pen, *args, **kwargs)
        if stops is None:
            self.starts = pd.DataFrame({'points' : starts, 'sym' : self.symPoint}, index=starts.index)
            self.stops  = pd.DataFrame({'points' : [], 'sym' : self.symStop})
        else:
            self.starts = pd.DataFrame({'points' : starts, 'sym' : self.symStart}, index=starts.index)
            self.stops  = pd.DataFrame({'points' : stops, 'sym' : self.symStop}, index=stops.index)
        self.render()

    def removePoints(self, points):
        for point in points:
            if point.symbol() in [self.symPoint, self.symStart]:
                # should be in starts
                nidx = self.starts.index.get_loc(point.pos().x(), method='nearest')
                idx = self.starts.index[nidx]
                self.starts.drop(idx, inplace=True)
            elif point.symbol() == self.symStop:
                # should be in stops
                nidx = self.stops.index.get_loc(point.pos().x(), method='nearest')
                idx = self.stops.index[nidx]
                self.stops.drop(idx, inplace=True)
            else:
                # should not happen
                pass

    def render(self):
        feet = pd.concat([self.starts, self.stops])
        self.setData(x = feet.index.values,
                     y = feet['points'].values,
                     symbol = feet['sym'].values)

    def isPointSelected(self, point):
        return (point in self.selected)

    def selectPoint(self, point):
        if not self.isPointSelected(point):
            self.selected.append(point)
        point.setBrush('r')

    def unselectPoint(self, point):
        if self.isPointSelected(point):
            self.selected.remove(point)
        point.resetBrush()

    def removeSelection(self):
        self.removePoints(self.selected)
        self.selected = []
        self.render()

    def name(self):
        # Method needed for compat with CurveItem
        return self._name


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for value in values:
            value = value / 1e6 # convert from ns to ms
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(QtCore.Qt.UTC)
            datestr = date.toString("hh:mm:ss.zzz")
            ret.append(datestr)
        return ret
