import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import numpy as np
import pyqtgraph as pg

import exporter

class PlotFrame(QtGui.QWidget):
    layout = property(QtGui.QWidget.layout, QtGui.QWidget.setLayout)
    colors = [Qt.red, Qt.green, Qt.blue,
              Qt.cyan, Qt.magenta, Qt.yellow,
              Qt.darkRed, Qt.darkGreen, Qt.darkBlue,
              Qt.darkCyan, Qt.darkMagenta, Qt.darkYellow]

    def __init__(self, plotdata, parent=None):
        super(PlotFrame, self).__init__(parent=parent)
        self.curves = {}
        self.footpoints = {}

        self.parent = parent
        self.plotdata = plotdata

        self.layout = QtGui.QHBoxLayout(self)

        if self.plotdata.xisdate:
            axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        else:
            axisItems = None

        self.plotw = pg.PlotWidget(parent=self, axisItems=axisItems)
        self.plotw.addLegend()
        self.layout.addWidget(self.plotw)

        self.tabs = QtGui.QTabWidget(parent=self)
        self.layout.addWidget(self.tabs)
        self.tabs.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.vb = self.plotw.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)
        self.exporter = exporter.Exporter(self.plotdata, self.vb)

        self.addAllCurves()

    def addAllCurves(self):
        allSeries = (self.plotdata.data[c] for c in self.plotdata.yfields)
        for series in allSeries:
            self.addCurve(series)

    def addCurve(self, series):
        n = len(self.curves)
        if n >= len(self.colors):
            color = Qt.white
        else:
            color = self.colors[n]

        try:
            curve = PlotDataItem(series = series,
                                 pen    = QtGui.QColor(color))
        except ValueError as e:
            self.parent.haserror.emit(e)
        else:
            self.curves[series.name] = curve
            self.plotw.addItem(curve)
            self.addFeet(series)

    def addFeet(self, series):
        feet = PulseFeetItem(series)
        feet.sigClicked.connect(self.pointClicked)
        lst = QtGui.QListWidget(self)
        lst.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.footpoints[feet] = {}
        for foot in feet.points():
            item = QtGui.QListWidgetItem()
            item.setText(str(foot.pos()))
            lst.addItem(item)
            self.footpoints[feet][foot] = item
        self.tabs.addTab(lst, series.name)
        self.plotw.addItem(feet)

    def pointClicked(self, curve, points):
        point = points[0] # more than 1 point can be given
        try:
            lstpoint = self.footpoints[curve][point]
        except IndexError as e:
            print("Point not in list: {}".format(e), sys.stderr)
            return
            
        if not curve.isSelected(point):
            curve.select(point)
            lstpoint.setSelected(True)
        else:
            curve.unselect(point)
            lstpoint.setSelected(False)


class PlotDataItem(pg.PlotDataItem):
    def __init__(self, series, pen=QtGui.QColor(Qt.white)):
        super(PlotDataItem, self).__init__(x    = series.index.astype(np.int64),
                                           y    = series.values.astype(np.float64),
                                           name = series.name,
                                           pen  = pen)


class PulseFeetItem(pg.ScatterPlotItem):
    def __init__(self, series):
        self.selected = []
        self.feet = self.findPressureFeet(series)
        super(PulseFeetItem, self).__init__(x    = self.feet.index.astype(np.int64),
                                            y    = self.feet.values.astype(np.float64),
                                            name = "{}-feet".format(series.name),
                                            pen  = 'w')

    def isSelected(self, point):
        return point in self.selected

    def select(self, point):
        if not self.isSelected(point):
            self.selected.append(point)
        point.setBrush('r')

    def unselect(self, point):
        if self.isSelected(point):
            self.selected.remove(point)
        point.resetBrush()

    def remove(self, point):
        datapoints = [pg.Point(p[0], p[1]) for p in self.data]
        try:
            idx = datapoints.index(point.pos())
        except IndexError as e:
            print("Point not found: {}".format(e), sys.stderr)
            return
        self.data = np.delete(self.data, idx)
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.bounds = [None, None]
        self.invalidate()
        self.updateSpots()
        self.sigPlotChanged.emit(self)

    def findPressureFeet(self, series):
        sndderiv = series.diff().diff().shift(-2)
        try:
            threshold = np.percentile(sndderiv.dropna(), 98)
        except IndexError as e:
            print("percentile error: {}".format(e), sys.stderr)
            return pd.Series()

        peaks = np.diff((sndderiv > threshold).astype(int))
        peakStarts = np.flatnonzero(peaks > 0)
        peakStops  = np.flatnonzero(peaks < 0)

        def locateMaxima():
            try:
                iterator = np.nditer((peakStarts, peakStops))
            except ValueError as e:
                print("nditer error: {}".format(e), sys.stderr)
                return
            for start, stop in iterator:
                idxstart = sndderiv.index.values[start]
                idxstop  = sndderiv.index.values[stop]
                maximum = sndderiv[idxstart:idxstop].idxmax()
                yield maximum

        return series[list(locateMaxima())]

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

class PlotDescription():
    def __init__(self, filename  = "",
                       seperator = ",",
                       decimal   = ".",
                       xfield  = None,
                       yfields = [],
                       xisdate = False,
                       isunixtime = False,
                       loadall = False,
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filename = filename
        self.seperator = seperator
        self.decimal = decimal
        self.xfield  = xfield
        self.yfields = yfields
        self.loadall = loadall
        self.datetime_format = datetime_format
        self.xisdate = xisdate
        self.isunixtime = isunixtime
        self.data = None

    @property
    def fields(self):
        xfields = [] if self.xfield is None else [self.xfield]
        return xfields + self.yfields

    @property
    def datefield(self):
        if not self.xisdate: return False
        return self.xfield if self.xfield is not None else False

    @property
    def xvalues(self):
        if not self.xisdate and self.xfield is not None:
            values = self.data[self.xfield].values
            return values.astype(np.float64)
        else:
            return None

    @property
    def name(self):
        name, _ = os.path.splitext(os.path.basename(self.filename))
        return name
