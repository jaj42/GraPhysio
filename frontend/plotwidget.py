from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

import rpc

class PlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        self.__childPlots = []
        self.__queryobj = None
        self.__qthread  = None
        self.__parent = parent     # Needed for the statusbar, as parent() won't work
        self.__vb = self.getViewBox()
        self.__vb.setMouseMode(self.__vb.RectMode)
        self.addLegend()

    def attachQuery(self, query):
        self.__queryobj = query

    def doPlot(self):
        if self.__queryobj is None: return
        self.__parent.statusmessage = "Busy"
        self.__qthread = QueryThread(self.__queryobj)
        self.__qthread.sigData.connect(self.__draw)
        self.__qthread.start()

    def __draw(self, data):
        self.__qthread.sigData.disconnect()
        self.__qthread = None
        if data is None: return
        if len(self.__childPlots) > 0:
            # We're updating the plot.
            for childPlot in self.__childPlots:
                childPlot.plotUpdate(data)
        else:
            # No plot yet, create it.
            for n in range(data.shape[2]):
                curve = DynPlot(data, n, name=self.__queryobj.yfields[n])
                self.__childPlots.append(curve)
                self.addItem(curve)
        # Recurse if we skipped lines
        #this is to skip this step for now
        self.__queryobj.skiplines = 1
        #this is to skip this step for now
        if self.__queryobj.skiplines > 1:
            self.__queryobj.skiplines = 1
            self.__qthread = QueryThread(self.__queryobj)
            self.__qthread.sigData.connect(self.__draw)
            self.__qthread.start()
        else:
            self.__parent.statusmessage = None

    # XXX implement this
    def viewRangeChanged(self):
        pass
        #print "PlotWidget viewRangeChanged"

class DynPlot(pg.PlotCurveItem):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w']

    def __init__(self, plotdata, plotnumber, *args, **kwds):
        self.plotnumber = plotnumber
        if plotnumber >= len(self.colors):
            color = 'w'
        else:
            color = self.colors[plotnumber]

        super(DynPlot, self).__init__(x   = plotdata[:,0,plotnumber],
                                      y   = plotdata[:,1,plotnumber],
                                      pen = color,
                                      *args, **kwds)

    def plotUpdate(self, plotdata):
        self.setData(x = plotdata[:, 0, self.plotnumber],
                     y = plotdata[:, 1, self.plotnumber])

# XXX Some people say the right way to use QThreads is *not* to subclass them
class QueryThread(QtCore.QThread):
    sigData = QtCore.pyqtSignal(object)

    def __init__(self, queryobj):
        super(QueryThread, self).__init__()
        self.__queryobj = queryobj

    def run(self):
        if self.__queryobj is None: return
        data = self.__queryobj.execute()
        self.sigData.emit(data)
