import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import pyqtgraph as pg
import numpy as np

import exporter

class PlotWidget(pg.PlotWidget):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

    def __init__(self, plotinfo, parent=None):
        if plotinfo.xisdate:
            axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        else:
            axisItems = None

        super(PlotWidget, self).__init__(parent=parent, axisItems=axisItems)

        vb = self.getViewBox()
        vb.setMouseMode(vb.RectMode)
        #vb.menu = None
        self.exporter = exporter.Exporter(plotinfo, vb)

        self.addLegend()

        for n, column in enumerate(plotinfo.ycols.iteritems()):
            if n >= len(self.colors):
                color = 'w'
            else:
                color = self.colors[n]
            colname, series = column
            curve = pg.PlotDataItem(x    = plotinfo.xvalues,
                                    y    = series.values,
                                    name = series.name,
                                    pen  = color)
            self.addItem(curve)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for value in values:
            value = value / 1e6 # convert from ns to msec
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(Qt.UTC)
            datestr = date.toString("hh:mm:ss.zzz")
            ret.append(datestr)
        return ret

class PlotInfo():
    def __init__(self, filename  = "",
                       seperator = ",",
                       decimal   = ".",
                       xfields = [],
                       yfields = [],
                       xisdate = False,
                       isunixtime = False,
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filename = str(filename)
        self.seperator = str(seperator)
        self.decimal = str(decimal)
        self.xfields = xfields
        self.yfields = yfields
        self.datetime_format = str(datetime_format)
        self.xisdate = xisdate
        self.isunixtime = isunixtime
        self.plotdata = None

    @property
    def fields(self):
        return self.xfields + self.yfields

    @property
    def datefield(self):
        if not self.xisdate: return False
        if len(self.xfields) > 0:
            return self.xfields[0]
        else:
            return False

    @property
    def xvalues(self):
        if self.xisdate:
            return self.plotdata.index.values.astype(np.int64)
        elif len(self.xfields) > 0:
            return self.plotdata[self.xfields[0]].values
        else:
            return self.plotdata.index.values

    @property
    def ycols(self):
        return self.plotdata[self.yfields]

    @property
    def datetime_parser(self):
        def conv_datetime(datestr):
            return datetime.strptime(datestr, self.datetime_format)
        return conv_datetime

    @property
    def plotname(self):
        plotname, ext = os.path.splitext(os.path.basename(self.filename))
        return plotname
