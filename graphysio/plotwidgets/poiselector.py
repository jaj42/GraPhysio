from enum import Enum
from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import exporter, utils
from graphysio.types import Parameter
from graphysio.plotwidgets import PlotWidget
from graphysio.algorithms import findPOIGreedy, savgol

class FixIndex(Enum):
    disabled = 'Disabled'
    minimum  = 'Local Minimum'
    sndderiv = '2nd derivative peak'


class POISelectorWidget(*utils.loadUiFile('poiwidget.ui')):
    @staticmethod
    def buttonClicked(self, qbutton):
        fixval = FixIndex(qbutton.text())
        self.poiselectorwidget.fixvalue = fixval

    def __init__(self, series, parent):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.parent = parent

        self.poiselectorwidget = POISelectorPlot(series, parent=self)
        self.horizontalLayout.addWidget(self.poiselectorwidget)

        buttonClicked = partial(self.buttonClicked, self)
        self.buttonGroup.buttonClicked.connect(buttonClicked)

    @property
    def menu(self):
        m = {'Plot'   : {'&Import POIs' : partial(self.parent.launchReadData, cb=self.poiselectorwidget.loadPOI)}
            ,'Export' : {'&POI to CSV'  : self.poiselectorwidget.exporter.poitocsv}
            }
        return m


class POISelectorPlot(PlotWidget):
    pointkey = 'point'

    @staticmethod
    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.getViewBox().mapSceneToView(pos)
            index = int(mousePoint.x())
            self.vLine.setPos(mousePoint.x())

    @staticmethod
    def clicked(self, evt):
        button = evt.button()
        pos = self.vLine.value()
        if button == 1:
            correctedpos = self.fixpos(pos)
            self.curve.feetitem.addPointsByLocation(self.pointkey, [correctedpos])
        elif button == 2:
            self.curve.feetitem.removePointsByLocation(self.pointkey, [pos])

    def __init__(self, series, parent=None):
        super().__init__(name=series.name, parent=parent)
        self.vb.setMouseMode(self.vb.PanMode)
        self.setMenuEnabled(False)

        self.__sndderiv = None
        self.fixvalue = FixIndex.disabled

        self.curve = self.addSeriesAsCurve(series)
        self.exporter = exporter.POIExporter(self, self.name)

        pen = pg.mkPen('k', width=2)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pen)
        self.addItem(self.vLine, ignoreBounds=True)

        mouseMoved = partial(self.mouseMoved, self)
        self.sigproxy = pg.SignalProxy(self.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)
        clicked = partial(self.clicked, self)
        self.scene().sigMouseClicked.connect(clicked)

    def loadPOI(self, plotdata):
        columnname, ok = QtGui.QInputDialog.getItem(self,
                                                    'Select POI series',
                                                    'Load POI',
                                                    plotdata.data.columns,
                                                    editable=False)
        if not ok:
            return
        poiseries = plotdata.data[columnname].dropna().index
        self.curve.feetitem.addPointsByLocation(self.pointkey, poiseries)

    def fixpos(self, pos):
        # Need to go through get_loc, otherwise strange things happen
        correctedpos = pos
        if self.fixvalue is FixIndex.minimum:
            xmin, xmax = self.vbrange
            s = self.curve.series.loc[xmin:xmax]
            posprop = findPOIGreedy(s, pos, 'min')
            fixedposloc = s.index.get_loc(posprop, method='nearest')
            correctedpos = s.index[fixedposloc]
        elif self.fixvalue is FixIndex.sndderiv:
            xmin, xmax = self.vbrange
            s = self.sndderiv.loc[xmin:xmax]
            posprop = findPOIGreedy(s, pos, 'max')
            fixedposloc = s.index.get_loc(posprop, method='nearest')
            correctedpos = s.index[fixedposloc]
        else:
            xmin, xmax = self.vbrange
            s = self.curve.series.loc[xmin:xmax]
            fixedposloc = s.index.get_loc(pos, method='nearest')
            correctedpos = s.index[fixedposloc]
        return correctedpos

    @property
    def sndderiv(self):
        if self.__sndderiv is None:
            sndderiv = self.curve.series.diff().diff().iloc[1:]
            sndderiv, _ = savgol(sndderiv, self.curve.samplerate, (.16, 2))
            self.__sndderiv = sndderiv.dropna()
        return self.__sndderiv
