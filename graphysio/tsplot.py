from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils, dialogs, legend
from graphysio.types import CycleId

class PlotWidget(pg.PlotWidget):
    def __init__(self, plotdata, parent=None):
        self.parent = parent
        self.colors = utils.Colors()
        self.hiddenitems = []

        axisItems = {'bottom': TimeAxisItem(orientation='bottom')}

        super().__init__(parent=parent, axisItems=axisItems, background='w')

        self.legend = legend.MyLegendItem()
        self.legend.setParentItem(self.getPlotItem())

        self.vb = self.getViewBox()
        self.vb.setMouseMode(self.vb.RectMode)

        self.exporter = exporter.TsExporter(self, plotdata.name)

        self.appendData(plotdata)

    def appendData(self, newplotdata, dorealign=False):
        for seriesname in newplotdata.data:
            self.addSeriesAsCurve(newplotdata.data[seriesname], dorealign=dorealign)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(self, series, pen=None, dorealign=False):
        if dorealign:
            # Timeshift new curves to make the beginnings coincide
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset
        try:
            curve = self.curves[series.name]
            curve.extend(series)
        except KeyError:
            if pen is None:
                pen = self.getPen()
            curve = CurveItem(series=series, parent=self, pen=pen)
            self.addCurve(curve)
        return curve

    def addCurve(self, curve, pen=None):
        if pen is not None:
            curve.setPen(pen)
        self.addItem(curve)
        if isinstance(curve, pg.PlotDataItem):
            self.legend.addItem(curve, curve.name())
        curve.visible.emit()

    def removeCurve(self, curve):
        self.removeItem(curve)
        self.legend.removeItem(curve.name())
        curve.invisible.emit()

    def filterCurve(self, oldcurve, filtername, asnew=False):
        newseries, newsamplerate = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
        if asnew:
            newcurve = self.addSeriesAsCurve(series=newseries)
            newcurve.samplerate = newsamplerate
        else:
            oldname = oldcurve.series.name
            newseries.name = oldname
            oldcurve.series = newseries
            oldcurve.samplerate = newsamplerate
            oldcurve.render()

    def filterFeet(self, curve, filtername, asnew=False):
        oldstarts = curve.feet['start']
        oldstops = curve.feet['stop']
        starts, stops = algorithms.filterFeet(oldstarts, oldstops, filtername, dialogs.askUserValue)
        curve.feet['start'] = starts
        curve.feet['stop'] = stops
        curve.feetitem.render()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.curves.values():
                curve.feetitem.removeSelection()

    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(parent=self, visible=self.curves.values(), hidden=self.hiddenitems)
        if not dlgCurveSelection.exec_():
            return
        visible, invisible = dlgCurveSelection.result
        newvisible = [item for item in visible if item not in self.curves.values()]
        newinvisible = [item for item in invisible if item not in self.hiddenitems]
        for item in newvisible:
            self.addCurve(item)
            if item in self.hiddenitems:
                self.hiddenitems.remove(item)

        for item in newinvisible:
            self.removeCurve(item)
            if item not in self.hiddenitems:
                self.hiddenitems.append(item)

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)


def sigPointClicked(curve, points):
    point = points[0] # only one point per click
    if not curve.isPointSelected(point):
        curve.selectPoint(point)
    else:
        curve.unselectPoint(point)

class CurveItem(pg.PlotDataItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    def __init__(self, series, parent, pen=None):
        self.parent = parent
        self.series = series.dropna()
        self.samplerate = utils.estimateSampleRate(self.series)

        if pen is None:
            pen = QtGui.QColor(QtCore.Qt.black)

        self.feet = {}
        feetname = '{}-feet'.format(series.name)
        self.feetitem = FeetItem(self, self.feet, name=feetname, pen=pen)
        parent.addItem(self.feetitem)
        self.feetitem.sigClicked.connect(sigPointClicked)

        super().__init__(name = series.name,
                         pen  = pen,
                         antialias = True)

        self.visible.connect(self.__becameVisible)
        self.invisible.connect(self.__becameInvisible)
        self.render()

    def __becameVisible(self):
        if not self.feetitem in self.parent.listDataItems():
            self.parent.addItem(self.feetitem)
        self.render()
        self.feetitem.render()

    def __becameInvisible(self):
        self.parent.removeItem(self.feetitem)

    def render(self):
        self.setData(x = self.series.index.values,
                     y = self.series.values)

    def extend(self, newseries):
        merged1 = self.series.append(newseries)
        merged2 = merged1.sort_index()
        self.series = merged2
        self.render()

    def addFeet(self, cycleid):
        if cycleid is CycleId.none:
            return
        elif cycleid is CycleId.velocity:
            starts, stops = algorithms.findFlowCycles(self)
            self.feet['start'] = starts
            self.feet['stop'] = stops
        elif cycleid is CycleId.foot:
            foot = algorithms.findPressureFeet(self)
            self.feet['start'] = foot
        elif cycleid is CycleId.pressure:
            if not 'start' in self.feet:
                self.addFeet(CycleId.foot)
            dia, sbp, dic = algorithms.findPressureFull(self)
            self.feet['diastole'] = dia
            self.feet['systole']  = sbp
            self.feet['dicrotic'] = dic
        else:
            raise ValueError(cycleid)
        self.feetitem.render()

    def getCycleIndices(self, vrange=None):
        s = self.series
        clip = partial(utils.clip, vrange=vrange)
        hasstarts = ('start' in self.feet) and self.feet['start'].size > 0
        hasstops = ('stop' in self.feet) and self.feet['stop'].size > 0
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
            begins = clip(self.feet['start'].values)
            endloc = s.index.get_loc(xmax, method='nearest')
            end = s.index[endloc]
            ends = np.append(begins[1:], end)
        else:
            # We have starts and stops, use them
            begins = self.feet['start'].values
            ends = self.feet['stop'].values
            begins, ends = map(clip, [begins, ends])

        # Handle the case where we start in the middle of a cycle
        while ends[0] <= begins[0]:
            ends = ends[1:]

        begins, ends = utils.truncatevecs([begins, ends])
        durations = ends - begins
        return (begins, durations)

    def getFeetPoints(self, feetname):
        feetidx = self.feet[feetname]
        feetnona = feetidx[pd.notnull(feetidx)]
        return self.series.loc[feetnona]


class FeetItem(pg.ScatterPlotItem):
    sym = {'start' : 'star', 'stop' : 's', 'diastole' : 't1', 'systole' : 't', 'dicrotic' : 'd'}
    #Symbols = OrderedDict([(name, QtGui.QPainterPath()) for name in ['o', 's', 't', 't1', 't2', 't3','d', '+', 'x', 'p', 'h', 'star']])

    def __init__(self, parent, indices, name, pen=None):
        super().__init__(pen=pen)
        self.selected = []
        self.parent = parent
        self.indices = indices
        self.__name = name
        self.resym = {value : key for key, value in self.sym.items()}
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
            idxnona = idx.dropna()
            points = self.parent.series[idxnona]
            tmp = pd.DataFrame({'points' : points, 'sym' : self.sym[key]}, index=idxnona)
            data.append(tmp)
        if len(data) < 1:
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

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        ret = []
        for value in values:
            value = value / 1e6 # convert from ns to ms
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(QtCore.Qt.UTC)
            datestr = date.toString("hh:mm:ss.zzz")
            ret.append(datestr)
        return ret
