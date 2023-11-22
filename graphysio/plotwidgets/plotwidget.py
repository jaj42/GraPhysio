from datetime import timedelta
from functools import partial
from typing import Optional

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from graphysio.legend import LegendItem
from graphysio.plotwidgets.curves import CurveItem, CurveItemWithPOI
from graphysio.utils import Colors


class TimeAxisItem(pg.AxisItem):
    @staticmethod
    def conv_absolute(value, mainwindow=False):
        value = int(value * 1e-6)  # convert from ns to ms
        date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
        date = date.toLocalTime()
        if mainwindow:
            timestr = date.toString("dd/MM/yyyy hh:mm:ss.zzz")
        else:
            timestr = date.toString("dd/MM/yyyy\nhh:mm:ss.zzz")
        return timestr

    @staticmethod
    def conv_relative(value):
        value = int(value * 1e-6)  # convert from ns to ms
        td = timedelta(milliseconds=value)
        return str(td)

    @staticmethod
    def is_relative_time(val):
        return val < 5e14  # Nov 1985

    def tickStrings(self, values, _scale, _spacing):
        if not values:
            return []
        if self.is_relative_time(values[0]):
            conv = self.conv_relative
        else:
            conv = self.conv_absolute
        return [conv(v) for v in values]


class PlotWidget(pg.PlotWidget):
    @staticmethod
    def mouseMoved(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.getViewBox().mapSceneToView(pos)
            self.parent.setcoords.emit(mousePoint.x(), mousePoint.y())

    def __init__(self, name, parent=None, properties=None):
        self.parent = parent
        self.name = name
        self.colors = Colors()
        self.hiddencurves = set()
        self.properties = properties if properties is not None else {}

        axisItems = {"bottom": TimeAxisItem(orientation="bottom")}
        super().__init__(parent=parent, axisItems=axisItems, background="w")

        self.legend = LegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

        self.setCursor(QtCore.Qt.CrossCursor)

        mouseMoved = partial(self.mouseMoved, self)
        self.sigproxy = pg.SignalProxy(
            self.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved
        )

    def appendData(self, newplotdata, dorealign=False):
        for seriesname in newplotdata.data:
            self.addSeriesAsCurve(newplotdata.data[seriesname], dorealign=dorealign)

    @property
    def curves(self):
        return {
            item.name(): item
            for item in self.listDataItems()
            if isinstance(item, CurveItem)
        }

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(
        self, series, pen=None, dorealign=False, withfeet=True
    ) -> Optional[CurveItem]:
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
            Curve = CurveItemWithPOI if withfeet else CurveItem
            try:
                curve = Curve(series=series, parent=self, pen=pen)
            except ValueError:
                return None
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
        for _, curve in self.curves.items():
            if isinstance(curve, pg.PlotDataItem):
                self.legend.addItem(curve, curve.name())

    def validateNewCurveName(
        self, proposedname: str, alwaysShow: bool = False
    ) -> Optional[str]:
        if proposedname not in self.curves and not alwaysShow:
            return proposedname
        newname, okPressed = QtWidgets.QInputDialog.getText(
            self,
            "Series name",
            "Series with identical names will be merged.",
            text=proposedname,
        )
        if not okPressed:
            return None
        return newname

    def applyCurveProperties(self, curve, properties: dict) -> None:
        # Setting Symbol and Connect does not work. TODO dig into pyqtgraph
        # curve.setData(symbol=properties['symbol'])
        # curve.setData(connect=properties['connect'], symbol=properties['symbol'])
        curve.setPen(properties["color"], width=properties["width"])
        curve.rename(properties["name"])

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)

    @property
    def menu(self):
        return {}
