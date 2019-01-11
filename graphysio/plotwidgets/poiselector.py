from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import exporter
from graphysio.plotwidgets.plotwidget import PlotWidget
from graphysio.types import Parameter

class POISelectorWidget(PlotWidget):
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
            self.curve.feetitem.addPointsByLocation(self.pointkey, [pos])
        elif button == 2:
            self.curve.feetitem.removePointsByLocation(self.pointkey, [pos])

    def __init__(self, series, parent=None):
        super().__init__(parent=parent)
        vb = self.getViewBox()
        vb.setMouseMode(vb.PanMode)
        self.setMenuEnabled(False)

        self.curve = self.addSeriesAsCurve(series)
        self.exporter = exporter.POIExporter(self, self.curve.name())

        pen = pg.mkPen('k', width=2)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pen)
        self.addItem(self.vLine, ignoreBounds=True)

        mouseMoved = partial(self.mouseMoved, self)
        self.sigproxy = pg.SignalProxy(self.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)
        clicked = partial(self.clicked, self)
        self.scene().sigMouseClicked.connect(clicked)

    @property
    def exportMenu(self):
        menu = super().exportMenu.copy()
        newm = {'&POI to CSV' : self.exporter.poitocsv}
        menu.update(newm)
        return menu
