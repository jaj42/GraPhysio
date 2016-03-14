import os
from datetime import datetime

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotinfo, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        vb = self.getViewBox()
        vb.setMouseMode(vb.RectMode)
        #vb.menu = None

        self.addLegend()

        for n, column in enumerate(plotinfo.plotdata.iteritems()):
            colname, series = column
            curve = DynPlot(series, n, name=colname)
            self.addItem(curve)


class DynPlot(pg.PlotCurveItem):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w']

    def __init__(self, plotdata, plotnumber, *args, **kwds):
        self.plotnumber = plotnumber
        if plotnumber >= len(self.colors):
            color = 'w'
        else:
            color = self.colors[plotnumber]
    
        super(DynPlot, self).__init__(x   = np.array(plotdata.index),
                                      y   = plotdata.values,
                                      pen = color,
                                      *args, **kwds)

class PlotInfo():
    def __init__(self, filename  = "",
                       seperator = ",",
                       decimal   = ".",
                       xfields = [],
                       yfields = [],
                       xisdate = False,
                       isunixtime = False,
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filename = filename
        self.seperator = seperator
        self.decimal = decimal
        self.xfields = set(xfields)
        self.yfields = set(yfields)
        self.xisdate = xisdate
        self.datetime_format = datetime_format
        self.isunixtime = isunixtime
        self.plotdata = None

    @property
    def datetime_parser(self):
        def conv_datetime(datestr):
            return datetime.strptime(datestr, self.datetime_format)
        return conv_datetime

    @property
    def fields(self):
        return self.xfields | self.yfields

    @property
    def plotname(self):
        plotname, ext = os.path.splitext(os.path.basename(self.filename))
        return plotname
