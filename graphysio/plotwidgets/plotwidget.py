import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio.legend import LegendItem
from graphysio.utils import estimateSampleRate, Colors


class CurveItem(pg.PlotDataItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    def __init__(self, series, parent, pen=None):
        self.parent = parent
        self.series = series.dropna()
        self.samplerate = estimateSampleRate(self.series)

        if pen is None:
            pen = QtGui.QColor(QtCore.Qt.black)

        super().__init__(name = series.name,
                         pen  = pen,
                         antialias = True)
        self.render()

    def render(self):
        self.setData(x = self.series.index.values,
                     y = self.series.values)

    def extend(self, newseries):
        merged1 = self.series.append(newseries)
        merged2 = merged1.sort_index()
        self.series = merged2
        self.render()


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


class PlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, CurveClass=CurveItem):
        self.parent = parent
        self.colors = Colors()
        self.hiddenitems = []
        self.CurveClass = CurveClass

        axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        super().__init__(parent=parent, axisItems=axisItems, background='w')

        self.legend = LegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

    def appendData(self, newplotdata, dorealign=False):
        for seriesname in newplotdata.data:
            self.addSeriesAsCurve(newplotdata.data[seriesname], dorealign=dorealign)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(self, series, pen=None, dorealign=False):
        if dorealign:
            # Timeshift new curves to make the beginnings coincide
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset
        try:
            curve = self.curves[series.name]
            curve.extend(series)
        except KeyError:
            if pen is None:
                pen = self.getPen()
            curve = self.CurveClass(series=series, parent=self, pen=pen)
            self.addCurve(curve)
        return curve

    def addCurve(self, curve, pen=None):
        if pen is not None:
            curve.setPen(pen)
        self.addItem(curve)
        if isinstance(curve, pg.PlotDataItem):
            self.legend.addItem(curve, curve.name())
        curve.visible.emit()

    def removeCurve(self, curve):
        self.removeItem(curve)
        self.legend.removeItem(curve.name())
        curve.invisible.emit()

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)
