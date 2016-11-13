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
    def __init__(self, u, p, subsetrange=None, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.btnPrev.clicked.connect(self.prevloop)
        self.btnNext.clicked.connect(self.nextloop)
        self.btnDelete.clicked.connect(self.delloop)

        self.curidx = 0
        self.loops = []
        self.pen = p.pen
        self.graphicsView.setBackground('w')
        self.plotitem = self.graphicsView.getPlotItem()

        self.scatteritem = pg.ScatterPlotItem()
        self.graphicsView.addItem(self.scatteritem)

        if p.feetitem is None or u.feetitem is None:
            parent.haserror.emit('No feet for this curve')
            return

        pfeet = p.feetitem.feet.index
        uperiods = [fi.feet.index for fi in u.feetitem]

        u = u.series; p = p.series
        for ubegin, uend, pf in zip(*uperiods, pfeet):
            # Don't miss the last flow point XXX this is hacky
            endloc = u.index.get_loc(uend) + 1
            uend = u.index[endloc]

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
            parent.haserror.emit('Missing loop: {}'.format(e))
        else:
            self.plotitem.plot(curloop.u, curloop.p, clear=True, pen=self.pen)
            alpha, beta, gamma = map(lambda theta: round(theta, 1), curloop.angles)
            self.lblAlpha.setText(str(alpha))
            self.lblBeta.setText(str(beta))
            self.lblGamma.setText(str(gamma))
            # XXX TODO
#            cardpoints = curloop.cardpoints
#            cardx, cardy = zip(*cardpoints)
#            self.scatteritem.setData(np.array(cardx), np.array(cardy))
        
    def prevloop(self):
        idx = self.curidx - 1
        if idx >= 0:
            self.curidx = idx
            self.lblIdx.setText(str(self.curidx + 1))
            self.renderloop()

    def nextloop(self):
        idx = self.curidx + 1
        if idx < len(self.loops):
            self.curidx = idx
            self.lblIdx.setText(str(self.curidx + 1))
            self.renderloop()

    def delloop(self):
        self.loops.pop(self.curidx)
        self.lblTot.setText(str(len(self.loops)))
        self.renderloop()


class PULoop(object):
    def __init__(self, u, p):
        self.card = None
        self.ang = None
        # Ensure both arrays have the same length
        maxidx = min(len(u), len(p)) - 1
        self.u = u.values[0:maxidx]
        self.p = p.values[0:maxidx]

    @property
    def cardpoints(self):
        if self.card is None:
            idxpmax = self.p.argmax()
            idxvmax = self.u.argmax()
            A = Point(self.u[0],  self.p[0])
            B = Point(self.u[idxvmax], self.p[idxvmax])
            C = Point(self.u[idxpmax], self.p[idxpmax])
            self.card = Cardinals(A, B, C)
        return self.card

    @property
    def angles(self):
        if self.ang is None:
            card = self.cardpoints
            alpha = self.calcangle(card.B)
            beta  = self.calcangle(card.C)
            gamma = self.calcangle(card.B, card.C)
            self.ang = Angles(alpha, beta, gamma)
        return self.ang

    def calcangle(self, pointb, pointa=Point(1,0)):
        ca = complex(pointa.x, pointa.y)
        cb = complex(pointb.x, pointb.y)
        angca = np.angle(ca, deg=True)
        angcb = np.angle(cb, deg=True)
        return abs(angca - angcb)
