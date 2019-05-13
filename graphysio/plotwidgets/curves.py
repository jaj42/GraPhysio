from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, utils
from graphysio.types import CycleId
from graphysio.utils import estimateSampleRate

class CurveItem(pg.PlotDataItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    def __init__(self, series, parent, pen=None):
        self.parent = parent
        self.series = series.dropna()
        self.samplerate = estimateSampleRate(self.series)

        if pen is None:
            pen = QtGui.QColor(QtCore.Qt.black)

        super().__init__(name = series.name,
                         pen  = pen,
                         antialias = True)
        self.render()

    def render(self):
        self.setData(x = self.series.index.values,
                     y = self.series.values)

    def extend(self, newseries):
        merged1 = self.series.append(newseries)
        merged2 = merged1.sort_index()
        self.series = merged2
        self.render()


class POIItem(pg.ScatterPlotItem):
    sym = {'start' : 'star', 'stop' : 's', 'diastole' : 't1', 'systole' : 't', 'dicrotic' : 'd', 'point' : 'o'}
    #Symbols = OrderedDict([(name, QtGui.QPainterPath()) for name in ['o', 's', 't', 't1', 't2', 't3','d', '+', 'x', 'p', 'h', 'star']])

    def __init__(self, parent, name, pen=None):
        super().__init__(pen=pen)
        self.parent = parent
        self.indices = {}
        self.selected = []
        self.resym = {value : key for key, value in self.sym.items()}
        self.__name = name
        self.render()

    def addPointsByLocation(self, key, locations):
        if not key in self.indices:
            self.indices[key] = pd.Index([])
        oldidx = self.indices[key]
        newidx = oldidx.append(pd.Index(locations))
        self.indices[key] = newidx.unique().sort_values()
        self.render()

    def removePointsByLocation(self, key, locations):
        if not key in self.indices:
            return
        oldidx = self.indices[key]
        dellocs = []
        for loc in locations:
            locidx = oldidx.get_loc(loc, method='nearest')
            dellocs.append(locidx)
        newidx = oldidx.delete(dellocs)
        self.indices[key] = newidx
        self.render()

    def removePoints(self, points):
        for point in points:
            try:
                sym = self.resym[point.symbol()]
                idx = self.indices[sym]
            except KeyError:
                # Should not happen
                continue
            nidx = idx.get_loc(point.pos().x(), method='nearest')
            self.indices[sym] = idx.delete(nidx)
        self.render()

    def render(self):
        data = []
        for key, idx in self.indices.items():
            if len(idx) < 1:
                continue
            idxnona = idx.dropna()
            points = self.parent.series.loc[idxnona]
            tmp = pd.DataFrame({'points' : points, 'sym' : self.sym[key]}, index=idxnona)
            data.append(tmp)
        if len(data) < 1:
            self.clear()
            return
        feet = pd.concat(data)
        self.setData(x = feet.index.values,
                     y = feet['points'].values,
                     symbol = feet['sym'].values)

    def isPointSelected(self, point):
        return point in self.selected

    def selectPoint(self, point):
        if not self.isPointSelected(point):
            self.selected.append(point)
        point.setPen('r')
        point.setBrush('r')

    def unselectPoint(self, point):
        if self.isPointSelected(point):
            self.selected.remove(point)
        point.resetPen()
        point.resetBrush()

    def removeSelection(self):
        self.removePoints(self.selected)
        self.selected = []
        self.render()

    def name(self):
        # Method needed for compat with CurveItem
        return self.__name


class CurveItemWithPOI(CurveItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    @staticmethod
    def sigPointClicked(feetitem, points):
        point = points[0] # only one point per click
        if not feetitem.isPointSelected(point):
            feetitem.selectPoint(point)
        else:
            feetitem.unselectPoint(point)

    def __init__(self, series, parent, pen=None):
        super().__init__(series, parent, pen)
        feetname = '{}-feet'.format(series.name)
        self.feetitem = POIItem(self, name=feetname, pen=pen)
        parent.addItem(self.feetitem)
        self.feetitem.sigClicked.connect(self.sigPointClicked)
        self.visible.connect(self.__becameVisible)
        self.invisible.connect(self.__becameInvisible)

    def __becameVisible(self):
        if not self.feetitem in self.parent.listDataItems():
            self.parent.addItem(self.feetitem)
        self.render()
        self.feetitem.render()

    def __becameInvisible(self):
        self.parent.removeItem(self.feetitem)

    def addFeet(self, cycleid):
        if cycleid is CycleId.none:
            return
        elif cycleid is CycleId.velocity:
            starts, stops = algorithms.findFlowCycles(self)
            self.feetitem.indices['start'] = starts
            self.feetitem.indices['stop'] = stops
        elif cycleid is CycleId.foot:
            foot = algorithms.findPressureFeet(self)
            self.feetitem.indices['start'] = foot
        elif cycleid is CycleId.pressure:
            if not 'start' in self.feetitem.indices:
                self.addFeet(CycleId.foot)
            dia, sbp, dic = algorithms.findPressureFull(self)
            self.feetitem.indices['diastole'] = dia
            self.feetitem.indices['systole']  = sbp
            self.feetitem.indices['dicrotic'] = dic
        else:
            raise ValueError(cycleid)
        self.feetitem.render()

    def getCycleIndices(self, vrange=None):
        s = self.series
        clip = partial(utils.clip, vrange=vrange)
        hasstarts = ('start' in self.feetitem.indices) and self.feetitem.indices['start'].size > 0
        hasstops = ('stop' in self.feetitem.indices) and self.feetitem.indices['stop'].size > 0
        if vrange:
            xmin, xmax = vrange
        else:
            xmin = s.index[0]
            xmax = s.index[-1]
        if not hasstarts:
            # We have no feet, treat the whole signal as one cycle
            locs = (s.index.get_loc(i, method='nearest') for i in [xmin, xmax])
            indices = (s.index[l] for l in locs)
            begins, ends = [np.array([i]) for i in indices]
        elif not hasstops:
            # We have no stops, starts serve as stops for previous cycle
            begins = clip(self.feetitem.indices['start'].values)
            endloc = s.index.get_loc(xmax, method='nearest')
            end = s.index[endloc]
            ends = np.append(begins[1:], end)
        else:
            # We have starts and stops, use them
            begins = self.feetitem.indices['start'].values
            ends = self.feetitem.indices['stop'].values
            begins, ends = map(clip, [begins, ends])

        # Handle the case where we start in the middle of a cycle
        while ends[0] <= begins[0]:
            ends = ends[1:]

        begins, ends = utils.truncatevecs([begins, ends])
        durations = ends - begins
        return (begins, durations)

    def getFeetPoints(self, feetname):
        feetidx = self.feetitem.indices[feetname]
        feetnona = feetidx[pd.notnull(feetidx)]
        return self.series.loc[feetnona]
