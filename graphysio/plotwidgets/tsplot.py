import string
from functools import partial

import pandas as pd
import pyqtgraph as pg
import sympy

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import dialogs, transformations
from graphysio.writedata import exporter
from graphysio.structures import CycleId, Parameter, PlotData
from graphysio.algorithms import filters

from graphysio.plotwidgets import (
    PlotWidget,
    LoopWidget,
    POISelectorWidget,
    SpectrogramWidget,
)


class TSWidget(PlotWidget):
    @staticmethod
    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.getViewBox().mapSceneToView(pos)
            self.parent.setcoords.emit(mousePoint.x(), mousePoint.y())

    def __init__(self, plotdata, parent=None):
        super().__init__(plotdata.name, parent=parent)
        self.exporter = exporter.TsExporter(self, plotdata.name)
        self.appendData(plotdata)
        mouseMoved = partial(self.mouseMoved, self)
        self.sigproxy = pg.SignalProxy(
            self.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved
        )

    def filterCurve(self, oldcurve, filtername, asnew=False):
        newseries, newsamplerate = filters.filter(
            oldcurve, filtername, dialogs.askUserValue
        )
        if asnew:
            newname = self.validateNewCurveName(newseries.name)
            if newname != newseries.name:
                newseries = newseries.rename(newname)
            newcurve = self.addSeriesAsCurve(series=newseries)
            newcurve.samplerate = newsamplerate
        else:
            newseries = newseries.rename(oldcurve.series.name)
            newseries = newseries.dropna()
            if len(newseries) < 1:
                return
            newseries = newseries.groupby(newseries.index).mean()
            oldcurve.clear()
            oldcurve.series = newseries
            oldcurve.samplerate = newsamplerate
            oldcurve.render()

    def filterFeet(self, curve, filtername, asnew=False):
        feetdict = curve.feetitem.indices
        oldstarts = feetdict['start']
        oldstops = feetdict['stop']
        starts, stops = filters.filterFeet(
            oldstarts, oldstops, filtername, dialogs.askUserValue
        )
        feetdict['start'] = starts
        feetdict['stop'] = stops
        curve.feetitem.render()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.curves.values():
                curve.feetitem.removeSelection()

    # Menu Curves
    def showCurveList(self):
        dlgCurveSelection = dialogs.DlgCurveSelection(
            parent=self.parent, visible=self.curves.values(), hidden=self.hiddencurves
        )

        def cb(result):
            currently_visible = set(self.curves.values())
            currently_hidden = self.hiddencurves
            allcurves = currently_visible | currently_hidden
            newly_visible, curveproperties = result
            newly_hidden = allcurves - newly_visible

            for c in newly_visible:
                if c in curveproperties:
                    self.applyCurveProperties(c, curveproperties[c])
                self.addCurve(c)

            for c in newly_hidden:
                self.removeCurve(c)

            self.hiddencurves = newly_hidden
            self.rebuildLegend()

        dlgCurveSelection.dlgdata.connect(cb)
        dlgCurveSelection.exec_()

    def launchCycleDetection(self):
        dlgCycles = dialogs.DlgCycleDetection(parent=self.parent)

        def cb(choices):
            for curvename, choice in choices.items():
                curve = self.curves[curvename]
                curve.addFeet(CycleId(choice))

        dlgCycles.dlgdata.connect(cb)
        dlgCycles.exec_()

    def launchFilter(self, filterfeet):
        dlgFilter = dialogs.DlgFilter(parent=self.parent, filterfeet=filterfeet)

        def cb(result):
            createnew, curvechoices = result
            if filterfeet:
                filterfunc = self.filterFeet
            else:
                filterfunc = self.filterCurve
            for curvename, choice in curvechoices.items():
                if choice == 'None':
                    continue
                curve = self.curves[curvename]
                filterfunc(curve, choice, asnew=createnew)

        dlgFilter.dlgdata.connect(cb)
        dlgFilter.exec_()

    def setDateTime(self):
        if len(self.curves) < 1:
            return
        sortedcurves = sorted(
            self.curves.values(), key=lambda curve: curve.series.index[0]
        )
        fstcurve = sortedcurves[0]
        curtimestamp = fstcurve.series.index[0]
        dlg = dialogs.DlgSetDateTime(prevdatetime=curtimestamp)

        def cb(newtimestamp):
            offset = newtimestamp - curtimestamp
            for curve in self.curves.values():
                curve.series.index += offset
                curve.render()

        dlg.dlgdata.connect(cb)
        dlg.exec_()

    def launchTransformation(self):
        param = Parameter(
            "Choose Transformation", list(transformations.Transformations.keys())
        )
        qresult = dialogs.askUserValue(param)
        if qresult is None:
            return
        trans = transformations.Transformations[qresult]
        for curve in trans(self):
            self.addCurve(curve)

    # Menu Plot
    def launchPOIWidget(self):
        curvenames = list(self.curves.keys())
        q = Parameter('Select Curve', curvenames)
        curvename = dialogs.askUserValue(q)
        if not curvename:
            return
        curve = self.curves[curvename]
        poiselector = POISelectorWidget(curve.series, parent=self.parent)
        self.parent.addTab(poiselector, curve.name())

    def launchSpectrogram(self):
        curvenames = list(self.curves.keys())
        q = Parameter('Select Curve', curvenames)
        curvename = dialogs.askUserValue(q)
        q = Parameter('Enter time window', 'time')
        window = dialogs.askUserValue(q)
        if not curvename:
            return
        curve = self.curves[curvename]
        spectro = SpectrogramWidget(
            curve.series, curve.samplerate, window, parent=self.parent
        )
        self.parent.addTab(spectro, curve.name())

    def launchCurveAlgebra(self):
        curvecorr = {n: c for n, c in zip(string.ascii_lowercase, self.curves.keys())}
        dlgCurveAlgebra = dialogs.DlgCurveAlgebra(self, curvecorr)

        def cb(formula):
            expr = sympy.sympify(formula)
            symbols = list(expr.free_symbols)
            schar = sorted([str(x) for x in symbols])
            curvenames = [curvecorr[x] for x in schar]
            sers = [self.curves[c].series for c in curvenames]
            if len(sers) < 1:
                # Scalar
                return
            df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
            df = df.dropna(how='all').interpolate()
            args = [df[c].values for c in curvenames]
            l = sympy.lambdify(symbols, expr, 'numpy')
            newvals = l(*args)
            newname = self.validateNewCurveName(formula, True)
            newseries = pd.Series(newvals, index=df.index, name=newname, dtype='double')
            self.addSeriesAsCurve(newseries)

        dlgCurveAlgebra.dlgdata.connect(cb)
        dlgCurveAlgebra.exec_()

    # Menu Selection
    def launchNewPlotFromSelection(self):
        xmin, xmax = self.vbrange
        sers = []
        for c in self.curves.values():
            series = c.series.loc[xmin:xmax]
            sers.append(series)
        df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
        newname = f'{self.name}-sub'
        plotdata = PlotData(data=df, name=newname)
        self.parent.createNewPlotWithData(plotdata)

    def launchAppendToPlotFromSelection(self):
        tabWidget = self.parent.tabWidget
        ntabs = tabWidget.count()
        tabdict = {tabWidget.tabText(idx): idx for idx in range(ntabs)}
        desttabname, ok = QtGui.QInputDialog.getItem(
            self,
            'Select destination',
            'Destination plot',
            list(tabdict.keys()),
            editable=False,
        )
        if not ok:
            return
        xmin, xmax = self.vbrange
        sers = []
        for c in self.curves.values():
            series = c.series.loc[xmin:xmax]
            sers.append(series)
        df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
        newname = f'{self.name}-sub'
        plotdata = PlotData(data=df, name=newname)
        self.parent.appendToPlotWithData(plotdata, destidx=tabdict[desttabname])

    def launchLoop(self):
        dlgSetupPU = dialogs.DlgSetupPULoop(self, parent=self.parent)

        def cb(result):
            uname, pname = result
            u = self.curves[uname]
            p = self.curves[pname]
            loopwidget = LoopWidget(u, p, self.vbrange, parent=self.parent)
            newname = f'{self.name}-{p.name()}-loops'
            self.parent.addTab(loopwidget, newname)

        dlgSetupPU.dlgdata.connect(cb)
        dlgSetupPU.exec_()

    @property
    def menu(self):
        mcurves = {
            'Visible Curves': self.showCurveList,
            'Cycle Detection': self.launchCycleDetection,
            'Filter Curve': partial(self.launchFilter, filterfeet=False),
            'Filter Feet': partial(self.launchFilter, filterfeet=True),
            'Transformation': self.launchTransformation,
            'Set Date / Time': self.setDateTime,
        }
        mselect = {
            'As new plot': self.launchNewPlotFromSelection,
            'Append to other plot': self.launchAppendToPlotFromSelection,
            'Generate PU-Loops': self.launchLoop,
        }
        mplot = {
            'POI Selector': self.launchPOIWidget,
            'Spectrogram': self.launchSpectrogram,
            'Curve Algebra': self.launchCurveAlgebra,
        }
        mexport = {
            'Curves': self.exporter.curves,
            'Time info': self.exporter.periods,
            'Cycle info': self.exporter.cyclepoints,
            'Cycles to directory': self.exporter.cycles,
        }
        m = {'Curves': mcurves, 'Plot': mplot, 'Seletion': mselect, 'Export': mexport}
        return m
