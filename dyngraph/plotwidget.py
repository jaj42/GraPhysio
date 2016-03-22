import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

import exporter

class PlotWidget(pg.PlotWidget):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

    def __init__(self, plotinfo, parent=None):
        if plotinfo.xisdate:
            xvalues = plotinfo.xvalues.apply(lambda x: x.timestamp())
            axisItems = {'bottom': TimeAxisItem(orientation='bottom')}
        else:
            xvalues = plotinfo.xvalues
            axisItems = None

        super(PlotWidget, self).__init__(parent=parent, axisItems=axisItems)

        vb = self.getViewBox()
        vb.setMouseMode(vb.RectMode)
        #vb.menu = None
        self.exporter = exporter.Exporter(plotinfo, vb)

        self.addLegend()

        for n, column in enumerate(plotinfo.yvalues.iteritems()):
            if n >= len(self.colors):
                color = 'w'
            else:
                color = self.colors[n]
            colname, series = column
            curve = pg.PlotDataItem(x    = xvalues.values,
                                    y    = series.values,
                                    name = series.name,
                                    pen  = color)
            self.addItem(curve)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        dates = map(datetime.fromtimestamp, values)
        return [datetime.strftime(date, "%H:%M:%S.%f") for date in dates]

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
    def xvalues(self):
        if len(self.xfields) > 0:
            return self.plotdata[self.xfields[0]]
        else:
            return self.plotdata.index

    @property
    def yvalues(self):
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
