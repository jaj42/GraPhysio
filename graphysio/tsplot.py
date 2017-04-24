from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, exporter, utils, dialogs, legend
from graphysio.types import FootType

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
            self.addCurve(series, dorealign=dorealign)

    @property
    def curves(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, CurveItem)}

    @property
    def feetitems(self):
        return {item.name() : item for item in self.listDataItems() if isinstance(item, FeetItem)}

    def addCurve(self, series, pen=None, dorealign=False):
        # TODO handle name clashes
        if pen is None:
            pen = next(self.colors)

        # Timeshift new curves to make the beginnings coincide
        if dorealign:
            begins = (curve.series.index[0] for curve in self.curves.values() if len(curve.series.index) > 0)
            offset = min(begins) - series.index[0]
            series.index += offset

        curve = CurveItem(series = series, pen = pen)
        self.addItem(curve)
        self.legend.addItem(curve, curve.name())
        return curve

    def addFeet(self, curve, foottype):
        if foottype is FootType.none:
            return

        # XXX use dictionary and check for foot type
        #if curve.feetitem is not None:
        #    replace = dialogs.userConfirm('Curve already has feet. Replace?', title='Replace feet')
        #    if not replace:
        #        return
        #    else:
        #        self.removeItem(curve.feetitem)
        #        curve.feetitem = None

        if foottype is FootType.velocity:
            starts, stops = algorithms.findFlowCycles(curve)
            feet = FeetItem(curve, starts, stops)
            curve.feetitem = feet
        elif foottype is FootType.pressure:
            starts = algorithms.findPressureFeet(curve)
            feet = FeetItem(curve, starts)
            curve.feetitem = feet
        elif foottype is FootType.dicrotic:
            starts = algorithms.findDicrotics(curve)
            feet = DicroticItem(curve, starts)
        else:
            raise ValueError(foottype)

        feet.sigClicked.connect(self.sigPointClicked)
        self.addItem(feet)

    def filterCurve(self, oldcurve, filtername, asnew=False):
        newseries, newsamplerate = algorithms.filter(oldcurve, filtername, dialogs.askUserValue)
        if asnew:
            newcurve = self.addCurve(series=newseries)
            newcurve.samplerate = newsamplerate
        else:
            oldname = oldcurve.series.name
            newseries.name = oldname
            oldcurve.series = newseries
            oldcurve.samplerate = newsamplerate
            oldcurve.render()

    def filterFeet(self, feetitem, filtername):
        starts, stops = algorithms.filterFeet(feetitem, filtername, dialogs.askUserValue)
        feetitem.starts = starts
        feetitem.stops = stops
        feetitem.render()

    def sigPointClicked(self, curve, points):
        point = points[0] # keep the first point
        if not curve.isPointSelected(point):
            curve.selectPoint(point)
        else:
            curve.unselectPoint(point)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.feetitems.values():
                curve.removeSelection()

    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(parent=self, visible=self.listDataItems(), hidden=self.hiddenitems)
        if not dlgCurveSelection.exec_():
            return
        visible, invisible = dlgCurveSelection.result
        newvisible = [item for item in visible if item not in self.listDataItems()]
        newinvisible = [item for item in invisible if item not in self.hiddenitems]
        for item in newvisible:
            self.addItem(item)
            if isinstance(item, pg.PlotCurveItem):
                self.legend.addItem(item, item.name())
            if item in self.hiddenitems:
                self.hiddenitems.remove(item)

        for item in newinvisible:
            self.removeItem(item)
            self.legend.removeItem(item.name())
            if item not in self.hiddenitems:
                self.hiddenitems.append(item)

    @property
    def vbrange(self):
        vbrange = self.vb.viewRange()
        xmin, xmax = map(int, vbrange[0])
        return (xmin, xmax)


class CurveItem(pg.PlotCurveItem):
    def __init__(self, series, pen=QtGui.QColor(QtCore.Qt.black), *args, **kwargs):
        self.series = series
        self.feetitem = None
        self.pen = pen
        self.samplerate = utils.estimateSampleRate(self.series)
        super().__init__(name = self.series.name,
                         pen  = self.pen,
                         antialias = True,
                         *args, **kwargs)
        self.render()

    def render(self):
        self.setData(x = self.series.index.values,
                     y = self.series.values)

    def getCycleIndices(self, vrange=None):
        s = self.series
        fi = self.feetitem
        clip = partial(utils.clip, vrange=vrange)
        if vrange:
            xmin, xmax = vrange
        else:
            xmin = s.index[0]
            xmax = s.index[-1]
        if fi is None or fi.starts.size < 1:
            # We have no feet, treat the whole signal as one cycle
            locs = (s.index.get_loc(i, method='nearest') for i in [xmin, xmax])
            indices = (s.index[l] for l in locs)
            begins, ends = [np.array([i]) for i in indices]
        elif fi.stops.size < 1:
            # We have no stops, starts serve as stops for previous cycle
            begins = clip(fi.starts.index.values)
            endloc = s.index.get_loc(xmax, method='nearest')
            end = s.index[endloc]
            ends = np.append(begins[1:], end)
        else:
            # We have starts and stops, use them
            begins = fi.starts.index.values
            ends   = fi.stops.index.values
            begins, ends = map(clip, [begins, ends])

        # Handle the case where we start in the middle of a cycle
        while ends[0] <= begins[0]:
            ends = ends[1:]

        begins, ends = utils.truncatevecs([begins, ends])
        durations = ends - begins
        return (begins, durations)


class FeetItem(pg.ScatterPlotItem):
    symStart, symStop = ['t', 's']
    # Available symbols: o, s, t, d, +, or any QPainterPath
    def __init__(self, curve, starts, stops=None, namesuffix='feet', *args, **kwargs):
        self.selected = []
        pen = curve.opts['pen']
        self._name = "{}-{}".format(curve.name(), namesuffix)
        super().__init__(pen = pen, *args, **kwargs)
        if stops is None:
            self.starts = pd.DataFrame({'points' : starts, 'sym' : self.symStart}, index=starts.index)
            self.stops  = pd.DataFrame({'points' : [], 'sym' : self.symStop})
        else:
            self.starts = pd.DataFrame({'points' : starts, 'sym' : self.symStart}, index=starts.index)
            self.stops  = pd.DataFrame({'points' : stops, 'sym' : self.symStop}, index=stops.index)
        self.render()

    def removePoints(self, points):
        for point in points:
            if point.symbol() == self.symStart:
                # should be in starts
                nidx = self.starts.index.get_loc(point.pos().x(), method='nearest')
                idx = self.starts.index[nidx]
                self.starts.drop(idx, inplace=True)
            elif point.symbol() == self.symStop:
                # should be in stops
                nidx = self.stops.index.get_loc(point.pos().x(), method='nearest')
                idx = self.stops.index[nidx]
                self.stops.drop(idx, inplace=True)
            else:
                # should not happen
                pass

    def render(self):
        feet = pd.concat([self.starts, self.stops])
        self.setData(x = feet.index.values,
                     y = feet['points'].values,
                     symbol = feet['sym'].values)

    def isPointSelected(self, point):
        return point in self.selected

    def selectPoint(self, point):
        if not self.isPointSelected(point):
            self.selected.append(point)
        point.setBrush('r')

    def unselectPoint(self, point):
        if self.isPointSelected(point):
            self.selected.remove(point)
        point.resetBrush()

    def removeSelection(self):
        self.removePoints(self.selected)
        self.selected = []
        self.render()

    def name(self):
        # Method needed for compat with CurveItem
        return self._name

class DicroticItem(FeetItem):
    symStart = ['o']
    def __init__(self, curve, dicrotics, *args, **kwargs):
        super().__init__(curve, starts=dicrotics, namesuffix='dic', *args, **kwargs)

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
