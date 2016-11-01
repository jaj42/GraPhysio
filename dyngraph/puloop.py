from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import numpy as np
import pandas as pd
import pyqtgraph as pg

from dyngraph import algorithms, exporter
from dyngraph.ui import Ui_LoopWidget

class LoopWidget(QtGui.QWidget, Ui_LoopWidget):
    def __init__(self, u, p, uperiods, pfeet, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.btnPrev.clicked.connect(self.prevloop)
        self.btnNext.clicked.connect(self.nextloop)
        self.btnDelete.clicked.connect(self.delloop)

        self.curidx = 0
        self.loops = []
        self.plotitem = self.graphicsView.getPlotItem()

        u = u.series; p = p.series
        for ubegin, uend, pf in zip(*uperiods, pfeet):
            duration = uend - ubegin
            loopu = u[ubegin:uend]
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
            # TODO report error
            return
        else:
            self.plotitem.plot(curloop.u, curloop.p, clear=True)
        
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
        self.u = u
        self.p = p
