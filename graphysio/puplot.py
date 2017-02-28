from collections import namedtuple
from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils

Point     = namedtuple('Point', ['x', 'y'])
Cardinals = namedtuple('Cardinals', ['A', 'B', 'C'])
Angles    = namedtuple('Angles', ['alpha', 'beta', 'gala'])



def truncatevec(vecs):
    # Ensure all vectors have the same length by truncating the end
    # Not feeling so well about this function
    lengths = map(len, vecs)
    maxidx = min(lengths) - 1
    newvecs = [vec[0:maxidx] for vec in vecs]
    return newvecs

class LoopWidget(*utils.loadUiFile('loopwidget.ui')):
    def __init__(self, u, p, plotdata, subsetrange=None, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.xmin, self.xmax = subsetrange
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

        self.initloopdata(u, p)

        if len(self.loops) > 0:
            self.lblTot.setText(str(len(self.loops)))
            self.renderloop(0)


    def initloopdata(self, u, p):
        if p.feetitem is None or u.feetitem is None:
            self.parent.haserror.emit('No feet for this curve')
            return

        def clip(vec):
            # Only keep visible data based on subsetrange
            cond = (vec > self.xmin) & (vec < self.xmax)
            return vec[cond]

        pfeet   = clip(p.feetitem.starts.index)
        ubegins = clip(u.feetitem.starts.index)
        uends   = clip(u.feetitem.stops.index) if u.feetitem.stops is not None else None

        if uends is None:
            uends = ubegins[1:]

        # Handle the case where we start in the middle of a cycle
        while uends[0] <= ubegins[0]:
            uends = uends[1:]
        ubegins, uends = truncatevec([ubegins, uends])
        durations = uends - ubegins

        us = u.series; ps = p.series
        for ubegin, pfoot, duration in zip(ubegins, pfeet, durations):
            loopu = us.ix[ubegin:ubegin+duration]
            loopp = ps.ix[pfoot:pfoot+duration]
            self.loops.append(PULoop(loopu, loopp))

    def renderloop(self, idx=None):
        if idx is None:
            idx = self.curidx
        try:
            curloop = self.loops[idx]
        except IndexError as e:
            self.parent.haserror.emit('Missing loop: {}'.format(e))
            return 

        self.lblIdx.setText(str(idx + 1))

        round1 = partial(round, ndigits=1)
        alpha, beta, gala = map(round1, curloop.angles)
        self.lblAlpha.setText(str(alpha))
        self.lblBeta.setText(str(beta))
        self.lblGala.setText(str(gala))

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
        if self.curidx >= len(self.loops):
            # Handle the case where we deleted the last item
            self.curidx = len(self.loops) - 1
        self.lblTot.setText(str(len(self.loops)))
        self.renderloop()


class PULoop(object):
    def __init__(self, u, p):
        self.__angles = None
        self.__cardpoints = None
        self.u, self.p = truncatevec([u.values, p.values])

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
            alpha = self.calcangle(card.A, card.B)
            beta  = self.calcangle(card.A, card.B, card.C)
            gala  = self.calcangle(card.A, card.C)
            self.__angles = Angles(alpha, beta, gala)
        return self.__angles

    def calcangle(self, looporigin, pointb, pointa=None):
        orig = complex(looporigin.x, looporigin.y)
        cb = complex(pointb.x, pointb.y) - orig
        if pointa is None:
            ca = complex(1, 0)
        else:
            ca = complex(pointa.x, pointa.y) - orig
        angca = np.angle(ca, deg=True)
        angcb = np.angle(cb, deg=True)
        return abs(angca - angcb)
