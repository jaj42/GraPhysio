import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import pyqtgraph as pg
import numpy as np

import exporter

class PlotWidget(pg.PlotWidget):
    #colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
    colors = [Qt.red, Qt.green, Qt.blue,
              Qt.cyan, Qt.magenta, Qt.yellow,
              Qt.darkRed, Qt.darkGreen, Qt.darkBlue,
              Qt.darkCyan, Qt.darkMagenta, Qt.darkYellow]
              #Qt.gray, Qt.darkGray, Qt.lightGray, Qt.white]

    def __init__(self, plotdescr, parent=None):
        self._parent = parent

        if plotdescr.xisdate:
            axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        else:
            axisItems = None

        super(PlotWidget, self).__init__(parent=parent, axisItems=axisItems)

        vb = self.getViewBox()
        vb.setMouseMode(vb.RectMode)
        #vb.menu = None
        self.exporter = exporter.Exporter(plotdescr, vb)

        self.addLegend()

        for n, column in enumerate(plotdescr.ycols.iteritems()):
            _, series = column
            if n >= len(self.colors):
                color = Qt.white
            else:
                color = self.colors[n]
            try:
                curve = pg.PlotDataItem(x    = plotdescr.xvalues,
                                        y    = series.values.astype(np.float64),
                                        name = series.name,
                                        pen  = QtGui.QColor(color))
            except ValueError as e:
                self._parent.haserror.emit(str(e))
            else:
                self.addItem(curve)
                #self.addItem(PulseFeetItem(series))

class PulseFeetItem(pg.ScatterPlotItem):
    def __init__(self, series):
        feet = self.findPressureFeet(series)
        super(PulseFeetItem, self).__init__(x    = feet.index.astype(np.int64),
                                            y    = feet.values.astype(np.float64),
                                            name = "{}-feet".format(series.name),
                                            pen  = 'w')

    def findPressureFeet(self, series):
        sndderiv = series.diff().diff()
        try:
            threshold = np.percentile(sndderiv.dropna(), 98)
        except IndexError:
            return pd.Series()

        peaks = np.diff((sndderiv > threshold).astype(int))
        peakStarts = np.flatnonzero(peaks > 0)
        peakStops  = np.flatnonzero(peaks < 0)

        def locateMaxima():
            try:
                iterator = np.nditer((peakStarts, peakStops))
            except ValueError as e:
                print("nditer error: {}".format(e))
                return
            for start, stop in iterator:
                idxstart = sndderiv.index.values[start]
                idxstop  = sndderiv.index.values[stop]
                maximum = sndderiv[idxstart:idxstop].idxmax()
                # Shift by 2 to account for the fact that .diff() removes samples
                maxloc = sndderiv.index.get_loc(maximum)
                yield sndderiv.index.values[maxloc - 2]

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
        if self.xfield is not None:
            return self.xfield
        else:
            return False

    @property
    def xvalues(self):
        if self.xisdate:
            # Return timestamp of the datetime in ns
            values = self.data.index.values
            return values.astype(np.int64)
        elif self.xfield is not None:
            values = self.data[self.xfield].values
            return values.astype(np.float64)
        else:
            return self.data.index.values

    @property
    def ycols(self):
        return self.data[self.yfields]

    @property
    def datetime_parser(self):
        def conv_datetime(datestr):
            return datetime.strptime(datestr, self.datetime_format)
        return conv_datetime

    @property
    def name(self):
        name, ext = os.path.splitext(os.path.basename(self.filename))
        return name
