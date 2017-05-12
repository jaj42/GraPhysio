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
        allSeries = (newplotdata.data[c] for c in newplotdata.fields)
        for series in allSeries:
            self.addSeriesAsCurve(series, dorealign=dorealign)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    def getPen(self):
        return next(self.colors)

    def addSeriesAsCurve(self, series, pen=None, dorealign=False):
        # Timeshift new curves to make the beginnings coincide
        if dorealign:
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset
        if pen is None:
            pen = self.getPen()
        curve = CurveItem(series=series, parent=self, pen=pen)
        self.addCurve(curve)
        return curve

    def addCurve(self, curve, pen=None):
        # TODO handle name clashes
        if pen is not None:
            curve.setPen(pen)
        self.addItem(curve)
        if isinstance(curve, pg.PlotCurveItem):
            self.legend.addItem(curve, curve.name())

    def removeCurve(self, curve):
        self.removeItem(curve)
        self.legend.removeItem(curve.name())

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

    def filterFeet(self, feetitem, filtername):
        raise NotImplementedError
        #starts, stops = algorithms.filterFeet(feetitem, filtername, dialogs.askUserValue)
        #feetitem.starts = starts
        #feetitem.stops = stops
        #feetitem.render()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.curves.values():
                curve.feetitem.removeSelection()

    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(parent=self, visible=self.listDataItems(), hidden=self.hiddenitems)
        if not dlgCurveSelection.exec_():
            return
        visible, invisible = dlgCurveSelection.result
        newvisible = [item for item in visible if item not in self.listDataItems()]
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

class CurveItem(pg.PlotCurveItem):
    def __init__(self, parent, series, pen=None):
        self.parent = parent
        self.series = series
        self.samplerate = utils.estimateSampleRate(self.series)

        if pen is None:
            self.pen = QtGui.QColor(QtCore.Qt.black)
        else:
            self.pen = pen

        self.feet = {}
        feetname = '{}-feet'.format(series.name)
        self.feetitem = FeetItem(self.feet, name=feetname, pen=self.pen)
        parent.addItem(self.feetitem)
        self.feetitem.sigClicked.connect(sigPointClicked)

        super().__init__(name = series.name,
                         pen  = self.pen,
                         antialias = True)
        self.render()

    def render(self):
        self.setData(x = self.series.index.values,
                     y = self.series.values)

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
            begins = clip(self.feet['start'].index.values)
            endloc = s.index.get_loc(xmax, method='nearest')
            end = s.index[endloc]
            ends = np.append(begins[1:], end)
        else:
            # We have starts and stops, use them
            begins = self.feet['start'].index.values
            ends = self.feet['stop'].index.values
            begins, ends = map(clip, [begins, ends])

        # Handle the case where we start in the middle of a cycle
        while ends[0] <= begins[0]:
            ends = ends[1:]

        begins, ends = utils.truncatevecs([begins, ends])
        durations = ends - begins
        return (begins, durations)


class FeetItem(pg.ScatterPlotItem):
    sym = {'start' : 'star', 'stop' : 's', 'diastole' : 't1', 'systole' : 't', 'dicrotic' : 'o'}
    #Symbols = OrderedDict([(name, QtGui.QPainterPath()) for name in ['o', 's', 't', 't1', 't2', 't3','d', '+', 'x', 'p', 'h', 'star']])

    def __init__(self, content, name, pen=None):
        super().__init__(pen=pen)
        self.selected = []
        self.content = content
        self.__name = name
        self.resym = {value : key for key, value in self.sym.items()}
        self.render()

    def removePoints(self, points):
        for point in points:
            try:
                sym = self.resym[point.symbol()]
                s = self.content[sym]
            except KeyError:
                # Should not happen
                continue
            nidx = s.index.get_loc(point.pos().x(), method='nearest')
            idx = s.index[nidx]
            self.content[sym] = s.drop(idx)
        self.render()

    def render(self):
        data = []
        for key, values in self.content.items():
            tmp = pd.DataFrame({'points' : values, 'sym' : self.sym[key]}, index=values.index)
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
