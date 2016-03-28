import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import pyqtgraph as pg
import numpy as np

import exporter

class PlotWidget(pg.PlotWidget):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

    def __init__(self, plotdescr, parent=None):
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
            if n >= len(self.colors):
                color = 'w'
            else:
                color = self.colors[n]
            colname, series = column
            curve = pg.PlotDataItem(x    = plotdescr.xvalues,
                                    y    = series.values.astype(np.float64),
                                    name = series.name,
                                    pen  = color)
            self.addItem(curve)


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
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filename = str(filename)
        self.seperator = str(seperator)
        self.decimal = str(decimal)
        self.xfield  = xfield
        self.yfields = yfields
        self.datetime_format = str(datetime_format)
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
