import sys
from enum import Enum

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import numpy as np
import pandas as pd
import pyqtgraph as pg

from dyngraph import algorithms, exporter, utils, legend

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotdata, parent=None):
        self.parent = parent
        self.plotdata = plotdata
        self.colors = utils.Colors()

        if self.plotdata.xisdate:
            axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        else:
            axisItems = None

        super().__init__(parent=parent, axisItems=axisItems, background='w')

        self.legend = legend.MyLegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

        self.exporter = exporter.TsExporter(self)

        self.addAllCurves()

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    @property
    def feetitems(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, FeetItem)}

    def addAllCurves(self):
        allSeries = (self.plotdata.data[c] for c in self.plotdata.yfields)
        for series in allSeries:
            self.addCurve(series)

    def addCurve(self, series, pen=None):
        if pen is None:
            pen = next(self.colors)

        try:
            curve = CurveItem(series = series,
                              pen    = pen)
        except ValueError as e:
            self.parent.haserror.emit(e)
        else:
            self.addItem(curve)
            self.legend.addItem(curve, curve.name())

    def addFeet(self, curve, foottype):
        if foottype is utils.FootType.pressure:
            feet = pressureFeetItem(curve)
            curve.feetitem = feet
            feet.sigClicked.connect(self.sigPointClicked)
            self.addItem(feet)
        elif foottype is utils.FootType.velocity:
            starts, stops = velocityFeetItems(curve)
            curve.feetitem = (starts, stops)
            starts.sigClicked.connect(self.sigPointClicked)
            self.addItem(starts)
            stops.sigClicked.connect(self.sigPointClicked)
            self.addItem(stops)
        else:
            return

    def addFiltered(self, oldcurve, filtername):
        series = oldcurve.series
        newseries = algorithms.filter(series, filtername)
        if newseries is not None:
            newcurve = self.addCurve(series = newseries,
                                     pen    = oldcurve.pen.lighter())

    def sigPointClicked(self, curve, points):
        point = points[0] # keep the first point
        if not curve.isPointSelected(point):
            curve.selectPoint(point)
        else:
            curve.unselectPoint(point)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for curve in self.feetitems.values():
                curve.removeSelection()


class CurveItem(pg.PlotDataItem):
    def __init__(self, series, pen=QtGui.QColor(Qt.black), parent=None, *args, **kwargs):
        self.series = series
        self.feetitem = None
        self.pen = pen
        super().__init__(x    = self.series.index.astype(np.int64),
                         y    = self.series.values.astype(np.float64),
                         name = self.series.name,
                         pen  = self.pen,
                         antialias      = True,
                         #autoDownsample = True,
                         *args, **kwargs)


class FeetItem(pg.ScatterPlotItem):
    def __init__(self, feet, curve, namesuffix='feet', *args, **kwargs):
        pen = curve.opts['pen']
        self.selected = []
        self.curve = curve
        self._name = "{}-{}".format(curve.name(), namesuffix)
        self.xisdate = type(feet.index) == pd.tseries.index.DatetimeIndex
        super().__init__(x    = feet.index.astype(np.int64),
                         y    = feet.values.astype(np.float64),
                         pen  = pen,
                         *args, **kwargs)

    def name(self):
        return self._name

    @property
    def feet(self):
        time = [point.pos().x() for point in self.points()]
        if self.xisdate:
            time = pd.to_datetime(time, unit='ns')

        # Sometimes points are a bit off due to rounding errors
        indices = [self.curve.series.index.get_loc(t, method='nearest') for t in time]
        elements = self.curve.series.iloc[indices]

        return elements.rename(self.name())

    def isPointSelected(self, point):
        return point in self.selected

    def selectPoint(self, point):
        if not self.isPointSelected(point):
            self.selected.append(point)
        point.setBrush('r')

    def unselectPoint(self, point):
        if self.isPointSelected(point):
            self.selected.remove(point)
        point.resetBrush()

    def removePoints(self, points):
        datapoints = self.points().tolist()
        for point in points:
            try:
                datapoints.remove(point)
            except ValueError as e:
                print("Point not found: {}".format(e), file=sys.stderr)
                continue
        self.setData(pos = [(p.pos().x(), p.pos().y()) for p in datapoints])
        self.selected = []

    def removeSelection(self):
        return self.removePoints(self.selected)


def pressureFeetItem(curve):
    feet = algorithms.findPressureFeet(curve.series)
    return FeetItem(feet, curve)


def velocityFeetItems(curve):
    starts, stops = algorithms.findFlowCycles(curve.series)
    startitem = FeetItem(starts, curve, namesuffix='velstart', symbol='t')
    stopitem  = FeetItem(stops,  curve, namesuffix='velstop',  symbol='s')
    return (startitem, stopitem)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for value in values:
            value = value / 1e6 # convert from ns to ms
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(Qt.UTC)
            datestr = date.toString("hh:mm:ss.zzz")
            ret.append(datestr)
        return ret
