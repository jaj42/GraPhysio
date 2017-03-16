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
        # Timeshift new curves to make the beginnings coincide
        if dorealign:
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - newplotdata.data.index[0]
            newplotdata.data.index += offset

        # addCurve() everything in new fields
        allSeries = (newplotdata.data[c] for c in newplotdata.fields)
        for series in allSeries:
            self.addCurve(series)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    @property
    def feetitems(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, FeetItem)}

    def addCurve(self, series, pen=None):
        if pen is None:
            pen = next(self.colors)

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

    def addFiltered(self, oldcurve, filtername):
        newseries, newsamplerate = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
        if newseries is not None:
            newcurve = self.addCurve(series=newseries)
            newcurve.samplerate = newsamplerate

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
        self.curve = curve
        self.hasstops = (stops is not None)
        pen = curve.opts['pen']
        self._name = "{}-{}".format(curve.name(), namesuffix)
        if stops is None:
            symbols = [self.symPoint]
            feet = starts
        else:
            symbols = [self.symStart, self.symStop]
            feet = pd.concat([starts, stops]).sort_index()

        symlist = list(islice(cycle(symbols), len(feet)))
        super().__init__(x      = feet.index,
                         y      = feet.values,
                         pen    = pen,
                         symbol = symlist,
                         *args, **kwargs)

    def name(self):
        return self._name

    @property
    def starts(self):
        time = [point.pos().x() for point in self.points() if point.symbol() in [self.symPoint, self.symStart]]
        indices = np.array(time, dtype=np.int64)
        elements = self.curve.series.ix[indices]
        return elements.rename(self.name())

    @property
    def stops(self):
        if not self.hasstops:
            return None
        time = [point.pos().x() for point in self.points() if point.symbol() == self.symStop]
        indices = np.array(time, dtype=np.int64)
        elements = self.curve.series.ix[indices]
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
        spots = [{'pos' : p.pos(), 'symbol' : p.symbol()} for p in datapoints]
        self.setData(spots = spots)
        self.selected = []

    def removeSelection(self):
        return self.removePoints(self.selected)


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
