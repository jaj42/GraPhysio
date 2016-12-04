from collections import namedtuple

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import numpy as np
import pandas as pd
import pyqtgraph as pg

from dyngraph import algorithms, exporter
from dyngraph.ui import Ui_LoopWidget

Point     = namedtuple('Point', ['x', 'y'])
Cardinals = namedtuple('Cardinals', ['A', 'B', 'C'])
Angles    = namedtuple('Angles', ['alpha', 'beta', 'gamma'])


class LoopWidget(QtGui.QWidget, Ui_LoopWidget):
    def __init__(self, u, p, plotdata, subsetrange=None, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        xmin, xmax = subsetrange
        self.parent = parent

        self.plotdata = plotdata
        self.exporter = exporter.PuExporter(self)

        self.btnPrev.clicked.connect(self.prevloop)
        self.btnNext.clicked.connect(self.nextloop)
        self.btnDelete.clicked.connect(self.delloop)

        self.curidx = 0
        self.loops = []
        self.pen = p.pen
        self.graphicsView.setBackground('w')

        self.curveitem = pg.PlotCurveItem()
        self.scatteritem = pg.ScatterPlotItem()
        plotitem = self.graphicsView.getPlotItem()
        plotitem.addItem(self.scatteritem)
        plotitem.addItem(self.curveitem)

        if p.feetitem is None or u.feetitem is None:
            self.parent.haserror.emit('No feet for this curve')
            return

        pfeet = p.feetitem.feet.index
        uperiods = [fi.feet.index for fi in u.feetitem]

        u = u.series; p = p.series
        for ubegin, uend, pf in zip(*uperiods, pfeet):
            if ubegin < xmin or uend > xmax:
                # Only keep visible cycles
                continue

            # Don't miss the last flow point XXX this is hacky
            #endloc = u.index.get_loc(uend) + 1
            #uend = u.index[endloc]

            loopu = u[ubegin:uend]
            duration = (uend - ubegin) * 2
            loopp = p[pf:pf+duration]
            self.loops.append(PULoop(loopu, loopp))

        if len(self.loops) > 0:
            self.lblTot.setText(str(len(self.loops)))
            self.renderloop(0)

    def renderloop(self, idx=None):
        if idx is None:
            idx = self.curidx
        try:
            curloop = self.loops[idx]
        except IndexError as e:
            self.parent.haserror.emit('Missing loop: {}'.format(e))
        else:
            self.lblIdx.setText(str(idx + 1))

            alpha, beta, gamma = map(lambda theta: round(theta, 1), curloop.angles)
            self.lblAlpha.setText(str(alpha))
            self.lblBeta.setText(str(beta))
            self.lblGamma.setText(str(gamma))

            card = curloop.cardpoints
            cardx, cardy = zip(*card)

            # Set visible range with quadratic aspect ratio
            bottomleft = QtCore.QPointF(card.A.x, card.A.y)
            size = max(card.B.x - card.A.x, card.C.y - card.A.y)
            qsize = QtCore.QSizeF(size, size)
            rect = QtCore.QRectF(bottomleft, qsize)
            self.graphicsView.setRange(rect=rect)

            self.curveitem.setData(curloop.u, curloop.p, pen=self.pen)
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
        self.loops.pop(self.curidx)
        self.lblTot.setText(str(len(self.loops)))
        self.renderloop()


class PULoop(object):
    def __init__(self, u, p):
        self.__angles = None
        self.__cardpoints = None
        u = u.dropna()
        p = p.dropna()
        # Ensure both arrays have the same length
        maxidx = min(len(u), len(p)) - 1
        self.u = u.values[0:maxidx]
        self.p = p.values[0:maxidx]

    @property
    def cardpoints(self):
        if self.__cardpoints is None:
            idxpmax = self.p.argmax()
            idxvmax = self.u.argmax()
            A = Point(self.u[0], self.p[0])
            B = Point(self.u[idxvmax], self.p[idxvmax])
            C = Point(self.u[idxpmax], self.p[idxpmax])
            self.__cardpoints = Cardinals(A, B, C)
        return self.__cardpoints

    @property
    def angles(self):
        if self.__angles is None:
            card = self.cardpoints
            alpha = self.calcangle(card.B)
            beta  = self.calcangle(card.C)
            gamma = self.calcangle(card.B, card.C)
            self.__angles = Angles(alpha, beta, gamma)
        return self.__angles

    def calcangle(self, pointb, pointa=Point(1,0)):
        ca = complex(pointa.x, pointa.y)
        cb = complex(pointb.x, pointb.y)
        angca = np.angle(ca, deg=True)
        angcb = np.angle(cb, deg=True)
        return abs(angca - angcb)
