from typing import Optional

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from graphysio.legend import LegendItem
from graphysio.utils import Colors
from graphysio.plotwidgets import curves


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for i, value in enumerate(values):
            value = value / 1e6  # convert from ns to ms
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(QtCore.Qt.UTC)
            datestr = date.toString("dd/MM/yyyy\nhh:mm:ss.zzz")
            ret.append(datestr)
        return ret


class PlotWidget(pg.PlotWidget):
    def __init__(self, name, parent=None):
        self.parent = parent
        self.name = name
        self.colors = Colors()
        self.hiddencurves = set()
        self.properties = {}

        axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        super().__init__(parent=parent, axisItems=axisItems, background='w')

        self.legend = LegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

        self.setCursor(QtCore.Qt.CrossCursor)

    def appendData(self, newplotdata, dorealign=False):
        for seriesname in newplotdata.data:
            self.addSeriesAsCurve(newplotdata.data[seriesname], dorealign=dorealign)

    @property
    def curves(self):
        return {
            item.name(): item
            for item in self.listDataItems()
            if isinstance(item, curves.CurveItem)
        }

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(self, series, pen=None, dorealign=False, withfeet=True):
        if len(series) < 1:
            return
        if dorealign and self.curves:
            # Timeshift new curves to make the beginnings coincide
            begins = [curve.series.index[0] for curve in self.curves.values()]
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
        if curve.name() in self.curves:
            return
        if pen is not None:
            curve.setPen(pen)
        self.addItem(curve)
        self.rebuildLegend()
        curve.visible.emit()

    def removeCurve(self, curve):
        if curve.name() not in self.curves:
            return
        self.removeItem(curve)
        self.rebuildLegend()
        curve.invisible.emit()

    def rebuildLegend(self):
        self.legend.clear()
        for name, curve in self.curves.items():
            if isinstance(curve, pg.PlotDataItem):
                self.legend.addItem(curve, curve.name())

    def validateNewCurveName(
        self, proposedname: str, alwaysShow: bool = False
    ) -> Optional[str]:
        if proposedname not in self.curves and not alwaysShow:
            return proposedname
        newname, okPressed = QtGui.QInputDialog.getText(
            self,
            "Series name",
            "Series with identical names will be merged.",
            text=proposedname,
        )
        if not okPressed:
            return None
        return newname

    def applyCurveProperties(self, curve, properties: dict) -> None:
        curve.setData(symbol=properties['symbol'])
        # curve.setData(connect=properties['connect'], symbol=properties['symbol'])
        curve.setPen(properties['color'], width=properties['width'])
        curve.rename(properties['name'])

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)

    @property
    def menu(self):
        return {}
