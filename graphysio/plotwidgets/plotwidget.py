import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio.legend import LegendItem
from graphysio.utils import Colors
from graphysio.plotwidgets import curves


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for i, value in enumerate(values):
            value = value / 1e6 # convert from ns to ms
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(QtCore.Qt.UTC)
            if i < 1:
                datestr = date.toString("dd/MM/yyyy\nhh:mm:ss.zzz")
            else:
                datestr = date.toString("hh:mm:ss.zzz")
            ret.append(datestr)
        return ret


class PlotWidget(pg.PlotWidget):
    def __init__(self, name, parent=None):
        self.parent = parent
        self.name = name
        self.colors = Colors()
        self.hiddenitems = []

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
        return {item.name() : item for item in self.listDataItems() if isinstance(item, curves.CurveItem)}

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(self, series, pen=None, dorealign=False, withfeet=True):
        if dorealign and self.curves:
            # Timeshift new curves to make the beginnings coincide
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset
        try:
            # Append to existing curve?
            curve = self.curves[series.name]
            curve.extend(series)
        except KeyError:
            # New curve
            if pen is None:
                pen = self.getPen()
            if withfeet:
                Curve = curves.CurveItemWithPOI
            else:
                Curve = curves.CurveItem
            curve = Curve(series=series, parent=self, pen=pen)
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

    def validateNewCurveName(self, proposedname, alwaysShow=False):
        if proposedname not in self.curves and not alwaysShow:
            return proposedname
        newname, okPressed = QtGui.QInputDialog.getText(self, "Series name", "Series with identical names will be merged.", text=proposedname)
        if not okPressed:
            return None
        return newname

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)
