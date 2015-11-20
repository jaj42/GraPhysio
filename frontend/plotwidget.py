from PyQt4.QtGui import *
import pyqtgraph as pg

import rpc

class PlotWidget(pg.PlotWidget):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w']

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__()
        self.__queryobj = None
        self.__vb = self.getViewBox()
        self.__vb.setMouseMode(self.__vb.RectMode)

    def doPlot(self):
        if self.__queryobj is None: return
        data = self.__queryobj.execute()
        if data is None: return

        nplot = data.shape[2]
        for n in range(nplot):
            curve = DynPlot(x   = data[:,0,n],
                            y   = data[:,1,n],
                            pen = self.colors[n])
            self.addItem(curve)

    def attachQuery(self, query):
        self.__queryobj = query

class DynPlot(pg.PlotCurveItem):
    def __init__(self, *args, **kwds):
        super(DynPlot, self).__init__(*args, **kwds)
