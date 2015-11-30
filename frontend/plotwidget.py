from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

import rpc

class PlotWidget(pg.PlotWidget):
    def __init__(self, rpcobj, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        self.__oldcursor     = None
        self.__rpc           = None
        self.__qthread       = None
        self.__dynamicUpdate = False
        self.__childPlots    = []
        self.__parent        = parent     # Needed for the statusbar, as parent() won't work

        self.__vb = self.getViewBox()
        self.__vb.setMouseMode(self.__vb.RectMode)

        self.addLegend()

        self.attachRpc(rpcobj)
        self.start()

    def attachRpc(self, rpcobj):
        """
        Declare the rpc object and create the associated thread.
        """
        self.__rpc = rpcobj
        self.__qthread = QtCore.QThread()
        self.__rpc.moveToThread(self.__qthread)

    def start(self):
        """
        Initialize the plot. Connect thread signals to the GUI.
        """
        if self.__rpc is None: return
        if len(self.__childPlots) > 0: return

        self.__rpc.sigNewData.connect(self.slotDraw)
        self.__rpc.sigUpdated.connect(self.slotUpdate)

        self.__rpc.sigFinished.connect(self.slotPostIPC)
        self.__rpc.sigFinished.connect(self.__qthread.quit)

        self.__qthread.started.connect(self.slotPreIPC)
        self.__qthread.started.connect(self.__rpc.execute)

        self.__qthread.start()

    def slotDraw(self):
        data = self.__rpc.data
        if data is None: return

        if len(self.__childPlots) > 0:
            # Plots already exist. Updating is not the job of this function.
            return

        # Create one curve per channel
        nCh = data.shape[2]
        for n in range(nCh):
            curve = DynPlot(data, n, name=self.__rpc.yfields[n])
            self.__childPlots.append(curve)
            self.addItem(curve)

        # Attach the view update function
        self.__dynamicUpdate = True

    def slotUpdate(self):
        if len(self.__childPlots) < 0: return

        for childPlot in self.__childPlots:
            childPlot.plotUpdate(self.__rpc.data)

    def viewRangeChanged(self):
        if not self.__dynamicUpdate: return
            # XXX need to calculate range if X axis is set
        self.__rpc.requestedrange = self.__vb.viewRange()[0]
        self.__qthread.start()

    def slotPreIPC(self):
        #self.__dynamicUpdate = False
        self.__parent.statusmessage = "Busy"
        self.__oldcursor = self.cursor()
        self.setCursor(QtCore.Qt.BusyCursor)

    def slotPostIPC(self, hasNoError):
        self.__parent.statusmessage = None
        if not hasNoError:
            QtGui.QMessageBox.critical(self, "Error", self.__rpc.error)
        if self.__oldcursor is not None:
            self.setCursor(self.__oldcursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
        self.__dynamicUpdate = True

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

    def plotUpdate(self, plotdata):
        #x,y = plotdata[:, :, self.plotnumber]
        self.setData(x = plotdata[:, 0, self.plotnumber],
                     y = plotdata[:, 1, self.plotnumber])
