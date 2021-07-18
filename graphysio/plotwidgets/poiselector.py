from enum import Enum
from functools import partial

import pandas as pd
import pyqtgraph as pg
from graphysio import ui
from graphysio.algorithms.filters import savgol
from graphysio.algorithms.waveform import findPOIGreedy
from graphysio.plotwidgets import PlotWidget
from graphysio.structures import PlotData
from graphysio.writedata import exporter
from PyQt5 import QtGui, QtWidgets


class FixIndex(Enum):
    disabled = 'Disabled'
    minimum = 'Local Minimum'
    maximum = 'Local Maximum'
    sndderiv = '2nd derivative peak'


class POISelectorWidget(ui.Ui_POISelectorWidget, QtWidgets.QWidget):
    @staticmethod
    def buttonClicked(self, qbutton):
        fixval = FixIndex(qbutton.text())
        self.poiselectorwidget.fixvalue = fixval

    def __init__(self, series, parent, properties={}):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.parent = parent

        self.poiselectorplot = POISelectorPlot(
            series, parent=self, properties=properties
        )
        self.horizontalLayout.addWidget(self.poiselectorplot)

        buttonClicked = partial(self.buttonClicked, self)
        self.buttonGroup.buttonClicked.connect(buttonClicked)

    def loadPOI(self, plotdata):
        columnname, ok = QtGui.QInputDialog.getItem(
            self, 'Select POI series', 'Load POI', plotdata.data.columns, editable=False
        )
        if not ok:
            return
        poiseries = plotdata.data[columnname].dropna().index
        self.poiselectorplot.curve.feetitem.addPointsByLocation(
            self.poiselectorplot.pointkey, poiseries
        )

    def launchNewPlotFromPOIs(self):
        srcseries = self.poiselectorplot.curve.series
        poiidx = self.poiselectorplot.curve.feetitem.indices[
            self.poiselectorplot.pointkey
        ]
        pois = srcseries[poiidx.dropna()].rename('poi')
        sname = f'{srcseries.name}-poi'
        df = pd.DataFrame({sname: pois})
        plotdata = PlotData(data=df, name=sname)
        self.parent.createNewPlotWithData(plotdata)

    @property
    def menu(self):
        return {
            'Plot': {
                'Import POIs': partial(
                    self.parent.launchOpenFile, datahandler=self.loadPOI
                ),
                'POIs to New Plot': self.launchNewPlotFromPOIs,
            },
            'Export': {'POI to CSV': self.poiselectorplot.exporter.poi},
        }


class POISelectorPlot(PlotWidget):
    pointkey = 'point'

    @staticmethod
    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.getViewBox().mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
        # super().mouseMoved(self, evt)

    @staticmethod
    def clicked(self, evt):
        button = evt.button()
        pos = self.vLine.value()
        if button == 1:
            correctedpos = self.fixpos(pos)
            self.curve.feetitem.addPointsByLocation(self.pointkey, [correctedpos])
        elif button == 2:
            self.curve.feetitem.removePointsByLocation(self.pointkey, [pos])

    def __init__(self, series, parent, properties={}):
        super().__init__(name=series.name, parent=parent)
        self.vb.setMouseMode(self.vb.PanMode)
        self.setMenuEnabled(False)
        self.properties = properties

        self.__sndderiv = None
        self.fixvalue = FixIndex.disabled

        self.curve = self.addSeriesAsCurve(series)
        self.exporter = exporter.POIExporter(self, self.name)

        pen = pg.mkPen('k', width=2)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pen)
        self.addItem(self.vLine, ignoreBounds=True)

        clicked = partial(self.clicked, self)
        self.scene().sigMouseClicked.connect(clicked)

    def fixpos(self, pos):
        # Need to go through get_loc, otherwise strange things happen
        correctedpos = pos
        xmin, xmax = self.vbrange
        if self.fixvalue is FixIndex.minimum:
            s = self.curve.series.loc[xmin:xmax]
            posprop = findPOIGreedy(s, pos, 'min')
            fixedposloc = s.index.get_loc(posprop, method='nearest')
        elif self.fixvalue is FixIndex.maximum:
            s = self.curve.series.loc[xmin:xmax]
            posprop = findPOIGreedy(s, pos, 'max')
            fixedposloc = s.index.get_loc(posprop, method='nearest')
        elif self.fixvalue is FixIndex.sndderiv:
            s = self.sndderiv.loc[xmin:xmax]
            posprop = findPOIGreedy(s, pos, 'max')
            fixedposloc = s.index.get_loc(posprop, method='nearest')
        else:
            s = self.curve.series.loc[xmin:xmax]
            fixedposloc = s.index.get_loc(pos, method='nearest')
        correctedpos = s.index[fixedposloc]
        return correctedpos

    @property
    def sndderiv(self):
        if self.__sndderiv is None:
            sndderiv = self.curve.series.diff().diff().iloc[1:]
            sndderiv, _ = savgol(sndderiv, self.curve.samplerate, (0.16, 2))
            self.__sndderiv = sndderiv.dropna()
        return self.__sndderiv
