from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotdata, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        self.__vb = self.getViewBox()
        self.__vb.setMouseMode(self.__vb.RectMode)

        self.addLegend()

    def slotDraw(self):
        # Create one curve per channel
        nCh = data.shape[2]
        for n in range(nCh):
            curve = DynPlot(data, n, name=self.__rpc.yfields[n])
            self.__childPlots.append(curve)
            self.addItem(curve)

class DynPlot(pg.PlotCurveItem):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w']

    def __init__(self, plotdata, plotnumber, *args, **kwds):
        self.plotnumber = plotnumber
        if plotnumber >= len(self.colors):
            color = 'w'
        else:
            color = self.colors[plotnumber]

        super(DynPlot, self).__init__(x   = plotdata[:, 0, plotnumber],
                                      y   = plotdata[:, 1, plotnumber],
                                      pen = color,
                                      *args, **kwds)
