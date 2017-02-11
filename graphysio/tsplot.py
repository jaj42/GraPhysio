import sys
from enum import Enum

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils, dialogs, legend

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

        allSeries = (self.plotdata.data[c] for c in self.plotdata.fields)
        for series in allSeries:
            self.addCurve(series)


    def appendData(self, newplotdata):
        # Make sure indices are compatible
        newidxtype = type(newplotdata.data.index)
        oldidxtype = type(self.plotdata.data.index)
        if oldidxtype is not newidxtype:
            self.parent.haserror.emit("Index type mismatch: {} vs. {}".format(newidxtype, oldidxtype))
            return

        # Merge plotdata.data with current
        self.plotdata.data = pd.concat([self.plotdata.data, newplotdata.data], axis=1).sort_index()

        # addCurve() everything in new fields
        allSeries = (self.plotdata.data[c] for c in newplotdata.fields)
        for series in allSeries:
            self.addCurve(series)

        # Merge fields
        self.plotdata.fields = list(set(self.plotdata.fields) | set(newplotdata.fields))

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    @property
    def feetitems(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, FeetItem)}

    def addCurve(self, series, pen=None):
        if pen is None:
            pen = next(self.colors)

        try:
            curve = CurveItem(series   = series,
                              plotdata = self.plotdata,
                              pen      = pen)
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
        newseries = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
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
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.feetitems.values():
                curve.removeSelection()

    def askSamplerate(self):
        initvalue = self.plotdata.samplerate
        if initvalue is None:
            initvalue = 100

        Fs, isok = QtGui.QInputDialog.getInt(self.parent, 'Enter sampling rate', 'Sampling rate in Hz',
                                             value = initvalue, min = 1)
        if isok:
            self.plotdata.samplerate = Fs

    @property
    def vbrange(plotwidget):
        vbrange = plotwidget.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)


class CurveItem(pg.PlotDataItem):
    def __init__(self, series, plotdata, pen=QtGui.QColor(QtCore.Qt.black), *args, **kwargs):
        self.series = series
        self.plotdata = plotdata
        self.feetitem = None
        self._samplerate = None
        self.pen = pen
        super().__init__(x    = self.series.index,
                         y    = self.series.values,
                         name = self.series.name,
                         pen  = self.pen,
                         antialias = True,
                         *args, **kwargs)

    def setSamplerate(self, samplerate):
        self._samplerate = samplerate

    def getSamplerate(self):
        if self._samplerate is not None:
            return self._samplerate
        else:
            return self.plotdata.samplerate

    samplerate = property(getSamplerate, setSamplerate)


class FeetItem(pg.ScatterPlotItem):
    def __init__(self, feet, curve, namesuffix='feet', *args, **kwargs):
        pen = curve.opts['pen']
        self.selected = []
        self.curve = curve
        self._name = "{}-{}".format(curve.name(), namesuffix)
        super().__init__(x    = feet.index,
                         y    = feet.values,
                         pen  = pen,
                         *args, **kwargs)

    def name(self):
        return self._name

    @property
    def feet(self):
        time = [point.pos().x() for point in self.points()]

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
    feet = algorithms.findPressureFeet(curve)
    return FeetItem(feet, curve)


def velocityFeetItems(curve):
    starts, stops = algorithms.findFlowCycles(curve)
    startitem = FeetItem(starts, curve, namesuffix='velstart', symbol='t')
    stopitem  = FeetItem(stops,  curve, namesuffix='velstop',  symbol='s')
    return (startitem, stopitem)


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
