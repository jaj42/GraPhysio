from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotdata, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        vb = self.getViewBox()
        vb.setMouseMode(vb.RectMode)

        self.addLegend()

        for n, column in enumerate(plotdata.iteritems()):
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
