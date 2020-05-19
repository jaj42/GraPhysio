from collections import namedtuple
from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtWidgets

from graphysio import ui
from graphysio.writedata import exporter

Point = namedtuple('Point', ['x', 'y'])
Cardinals = namedtuple('Cardinals', ['A', 'B', 'C'])
Angles = namedtuple('Angles', ['alpha', 'beta', 'gala'])


class LoopWidget(ui.Ui_LoopWidget, QtWidgets.QWidget):
    def __init__(self, u, p, subsetrange, parent):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.properties = {}

        self.subsetrange = subsetrange

        self.exporter = exporter.PuExporter(self, p.name())

        self.btnPrev.clicked.connect(self.prevloop)
        self.btnNext.clicked.connect(self.nextloop)
        self.btnDelete.clicked.connect(self.delloop)

        self.curidx = 0
        self.loops = []
        self.pen = p.opts['pen']
        self.graphicsView.setBackground('w')

        plotitem = self.graphicsView.getPlotItem()
        vb = plotitem.getViewBox()
        vb.setAspectLocked(lock=True, ratio=1)

        self.curveitem = pg.PlotCurveItem()
        self.scatteritem = pg.ScatterPlotItem()
        plotitem.addItem(self.scatteritem)
        plotitem.addItem(self.curveitem)

        self.initloopdata(u, p)

        if len(self.loops) > 0:
            self.lblTot.setText(str(len(self.loops)))
            self.renderloop(0)

    def initloopdata(self, u, p):
        ubegins, udurations = u.getCycleIndices(self.subsetrange)
        pbegins, pdurations = p.getCycleIndices(self.subsetrange)
        durations = map(min, zip(udurations, pdurations))
        for ubegin, pbegin, duration in zip(ubegins, pbegins, durations):
            loopu = u.series.loc[ubegin : ubegin + duration]
            loopp = p.series.loc[pbegin : pbegin + duration]
            self.loops.append(PULoop(loopu, loopp))

    def renderloop(self, idx=None):
        if idx is None:
            idx = self.curidx

        try:
            curloop = self.loops[idx]
        except IndexError:
            return

        self.lblIdx.setText(str(idx + 1))

        delay = int(curloop.offset / 1e6)  # ns to ms
        self.lblDelay.setText(str(delay))

        round1 = partial(round, ndigits=1)
        alpha, beta, gala = map(round1, curloop.angles)
        self.lblAlpha.setText(str(alpha))
        self.lblBeta.setText(str(beta))
        self.lblGala.setText(str(gala))

        card = curloop.cardpoints
        cardx, cardy = zip(*card)

        self.curveitem.setData(curloop.u.values, curloop.p.values, pen=self.pen)
        self.scatteritem.setData(np.array(cardx), np.array(cardy))

    def prevloop(self):
        idx = self.curidx - 1
        if idx >= 0:
            self.curidx = idx
            self.renderloop()

    def nextloop(self):
        idx = self.curidx + 1
        if idx < len(self.loops):
            self.curidx = idx
            self.renderloop()

    def delloop(self):
        try:
            self.loops.pop(self.curidx)
        except IndexError:
            return
        if self.curidx >= len(self.loops):
            # Handle the case where we deleted the last item
            self.curidx = len(self.loops) - 1
        self.lblTot.setText(str(len(self.loops)))
        self.renderloop()

    @property
    def menu(self):
        m = {'Export': {'&Loop Data to CSV directory': self.exporter.exportloops}}
        return m


class PULoop(object):
    def __init__(self, u, p):
        self.__angles = None
        self.__cardpoints = None

        # Realign pressure and flow
        offset = p.index[0] - u.index[0]
        u.index += offset
        self.offset = abs(offset)

        df = pd.concat([u, p], axis=1)
        self.df = df.interpolate(method='index')

        self.u = self.df[u.name]
        self.p = self.df[p.name]

    @property
    def cardpoints(self):
        if self.__cardpoints is None:
            idxpmax = self.p.idxmax()
            idxvmax = self.u.idxmax()
            A = Point(self.u.iloc[0], self.p.iloc[0])
            B = Point(self.u.loc[idxvmax], self.p.loc[idxvmax])
            C = Point(self.u.loc[idxpmax], self.p.loc[idxpmax])
            self.__cardpoints = Cardinals(A, B, C)
        return self.__cardpoints

    @property
    def angles(self):
        if self.__angles is None:
            card = self.cardpoints
            alpha = calcangle(card.A, card.B)
            beta = calcangle(card.A, card.B, card.C)
            gala = calcangle(card.A, card.C)
            self.__angles = Angles(alpha, beta, gala)
        return self.__angles


def calcangle(looporigin, pointb, pointa=None):
    orig = complex(looporigin.x, looporigin.y)
    cb = complex(pointb.x, pointb.y) - orig
    if pointa is None:
        ca = complex(1, 0)
    else:
        ca = complex(pointa.x, pointa.y) - orig
    angca = np.angle(ca, deg=True)
    angcb = np.angle(cb, deg=True)
    return abs(angca - angcb)
