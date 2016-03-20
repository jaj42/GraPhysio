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
            super(PlotWidget, self).__init__(parent=parent,
                                             axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        else:
            super(PlotWidget, self).__init__(parent=parent)

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
            curve = pg.PlotDataItem(x   = plotinfo.xvalues,
                                    y   = series.values,
                                    pen = color)
            self.addItem(curve)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return map(lambda x: datetime.strftime("%H:%M:%S.%f", x), values)

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
        self.xfields = set(xfields)
        self.yfields = set(yfields)
        self.datetime_format = str(datetime_format)
        self.xisdate = xisdate
        self.isunixtime = isunixtime
        self.plotdata = None

    @property
    def fields(self):
        return self.xfields | self.yfields

    @property
    def xvalues(self):
        if len(self.xfields) > 0:
            return self.plotdata[list(self.xfields)]
        else:
            return np.array(self.plotdata.index)

    @property
    def yvalues(self):
        return self.plotdata[list(self.yfields)]

    @property
    def datetime_parser(self):
        def conv_datetime(datestr):
            return datetime.strptime(datestr, self.datetime_format)
        return conv_datetime

    @property
    def plotname(self):
        plotname, ext = os.path.splitext(os.path.basename(self.filename))
        return plotname
