import string
from functools import partial

import numexpr as ne
import pandas as pd
from pyqtgraph.Qt import QtCore, QtWidgets

from graphysio import dialogs, transformations
from graphysio.algorithms import filters
from graphysio.plotwidgets import (
    LoopWidget,
    PlotWidget,
    POISelectorWidget,
    SpectrogramWidget,
)
from graphysio.structures import CycleId, Parameter, PlotData
from graphysio.writedata import exporter


class TSWidget(PlotWidget):
    def __init__(self, plotdata, parent=None, properties=None) -> None:
        if properties is None:
            properties = {}
        super().__init__(plotdata.name, parent=parent, properties=properties)
        self.exporter = exporter.TsExporter(self, plotdata.name)
        self.appendData(plotdata)

    def filterCurve(self, oldcurve, filtername, asnew=False) -> None:
        newseries, newsamplerate = filters.filter(
            oldcurve,
            filtername,
            dialogs.askUserValue,
        )
        if asnew:
            newname = self.validateNewCurveName(newseries.name)
            if newname != newseries.name:
                newseries = newseries.rename(newname)
            newcurve = self.addSeriesAsCurve(series=newseries)
            if newsamplerate and newcurve:
                newcurve.set_samplerate(newsamplerate)
        else:
            newseries = newseries.rename(oldcurve.series.name)
            oldcurve.replace_data(newseries)
            if newsamplerate:
                oldcurve.set_samplerate(newsamplerate)

    def filterFeet(self, curve, filtername, asnew=False) -> None:
        new_feetdict = filters.filter_feet(curve, filtername, dialogs.askUserValue)
        curve.feetitem.indices = new_feetdict
        curve.feetitem.render()

    def keyPressEvent(self, event) -> None:
        if event.key() == QtCore.Qt.Key_Delete:
            for curve in self.curves.values():
                curve.feetitem.removeSelection()

    # Menu Curves
    def showCurveList(self) -> None:
        dlgCurveSelection = dialogs.DlgCurveSelection(
            parent=self.parent,
            visible=self.curves.values(),
            hidden=self.hiddencurves,
        )

        def cb(result) -> None:
            currently_visible = set(self.curves.values())
            currently_hidden = self.hiddencurves
            allcurves = currently_visible | currently_hidden
            newly_visible, curveproperties = result
            newly_hidden = allcurves - newly_visible

            for c in curveproperties:
                self.applyCurveProperties(c, curveproperties[c])

            for c in newly_visible:
                self.addCurve(c)

            for c in newly_hidden:
                self.removeCurve(c)

            self.hiddencurves = newly_hidden
            self.rebuildLegend()

        dlgCurveSelection.dlgdata.connect(cb)
        dlgCurveSelection.exec()

    def launchCycleDetection(self) -> None:
        dlgCycles = dialogs.DlgCycleDetection(parent=self.parent)

        def cb(choices) -> None:
            for curvename, choice in choices.items():
                curve = self.curves[curvename]
                curve.addFeet(CycleId(choice))

        dlgCycles.dlgdata.connect(cb)
        dlgCycles.exec()

    def launchFilter(self, filterfeet) -> None:
        dlgFilter = dialogs.DlgFilter(parent=self.parent, filterfeet=filterfeet)

        def cb(result) -> None:
            createnew, curvechoices = result
            filterfunc = self.filterFeet if filterfeet else self.filterCurve
            for curvename, choice in curvechoices.items():
                if choice == "None":
                    continue
                curve = self.curves[curvename]
                filterfunc(curve, choice, asnew=createnew)

        dlgFilter.dlgdata.connect(cb)
        dlgFilter.exec()

    def setDateTime(self) -> None:
        if len(self.curves) < 1:
            return
        sortedcurves = sorted(
            self.curves.values(),
            key=lambda curve: curve.series.index[0],
        )
        fstcurve = sortedcurves[0]
        curtimestamp = fstcurve.series.index[0]
        dlg = dialogs.DlgSetDateTime(prevdatetime=curtimestamp)
        dlg.exec()
        newtimestamp = dlg.dlgdata
        if not newtimestamp:
            return
        offset = newtimestamp - curtimestamp
        for curve in self.curves.values():
            curve.series.index += offset
            curve.render()

    def launchTransformation(self) -> None:
        param = Parameter(
            "Choose Transformation",
            list(transformations.Transformations.keys()),
        )
        qresult = dialogs.askUserValue(param)
        if qresult is None:
            return
        trans = transformations.Transformations[qresult]
        plotdatas = trans(self)
        for plotdata in plotdatas:
            self.parent.appendToPlotWithData(plotdata, do_timeshift=False)

    # Menu Plot
    def launchPOIWidget(self) -> None:
        curvenames = list(self.curves.keys())
        q = Parameter("Select Curve", curvenames)
        curvename = dialogs.askUserValue(q)
        if not curvename:
            return
        curve = self.curves[curvename]
        poiselector = POISelectorWidget(
            curve.series,
            parent=self.parent,
            properties=self.properties,
        )
        self.parent.addTab(poiselector, curve.name())

    def launchSpectrogram(self) -> None:
        curvenames = list(self.curves.keys())
        q = Parameter("Select Curve", curvenames)
        curvename = dialogs.askUserValue(q)
        q = Parameter("Enter time window", "time")
        window = dialogs.askUserValue(q)
        if not curvename:
            return
        curve = self.curves[curvename]
        spectro = SpectrogramWidget(
            curve.series,
            curve.samplerate,
            window,
            parent=self.parent,
        )
        self.parent.addTab(spectro, curve.name())

    def launchCurveAlgebra(self) -> None:
        curvecorr = dict(zip(string.ascii_lowercase, self.curves.keys()))
        dlgCurveAlgebra = dialogs.DlgCurveAlgebra(self, curvecorr)

        def cb(formula) -> None:
            symbols = list(ne.NumExpr(formula).input_names)
            curvenames = [curvecorr[x] for x in symbols]
            sers = [self.curves[c].series for c in curvenames]
            if not len(sers):
                return

            argsdf = pd.concat(sers, axis=1, keys=symbols)
            argsdf = argsdf.interpolate()
            args = argsdf.to_dict(orient="series")

            newvals = ne.evaluate(formula, local_dict=args)
            newname = self.validateNewCurveName(formula, True)
            newseries = pd.Series(
                newvals,
                index=argsdf.index,
                name=newname,
                dtype="float64",
            )
            self.addSeriesAsCurve(newseries)

        dlgCurveAlgebra.dlgdata.connect(cb)
        dlgCurveAlgebra.exec()

    # Menu Selection
    def launchNewPlotFromSelection(self) -> None:
        xmin, xmax = self.vbrange
        sers = []
        for c in self.curves.values():
            series = c.series.loc[xmin:xmax]
            sers.append(series)
        df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
        newname = f"{self.name}-sub"
        plotdata = PlotData(data=df, name=newname)
        self.parent.createNewPlotWithData(plotdata)

    def launchAppendToPlotFromSelection(self) -> None:
        tabWidget = self.parent.tabWidget
        ntabs = tabWidget.count()
        tabdict = {tabWidget.tabText(idx): idx for idx in range(ntabs)}
        desttabname, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Select destination",
            "Destination plot",
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
        newname = f"{self.name}-sub"
        plotdata = PlotData(data=df, name=newname)
        self.parent.appendToPlotWithData(plotdata, destidx=tabdict[desttabname])

    def launchLoop(self) -> None:
        dlgSetupPU = dialogs.DlgSetupPULoop(self, parent=self.parent)

        def cb(result) -> None:
            uname, pname = result
            u = self.curves[uname]
            p = self.curves[pname]
            loopwidget = LoopWidget(u, p, self.vbrange, parent=self.parent)
            newname = f"{self.name}-{p.name()}-loops"
            self.parent.addTab(loopwidget, newname)

        dlgSetupPU.dlgdata.connect(cb)
        dlgSetupPU.exec()

    @property
    def menu(self):
        mcurves = {
            "Visible Curves": self.showCurveList,
            "Cycle Detection": self.launchCycleDetection,
            "Filter Curve": partial(self.launchFilter, filterfeet=False),
            "Filter Feet": partial(self.launchFilter, filterfeet=True),
            "Transformation": self.launchTransformation,
            "Set Date / Time": self.setDateTime,
        }
        mselect = {
            "As new plot": self.launchNewPlotFromSelection,
            "Append to other plot": self.launchAppendToPlotFromSelection,
            "Generate PU-Loops": self.launchLoop,
        }
        mplot = {
            "POI Selector": self.launchPOIWidget,
            "Spectrogram": self.launchSpectrogram,
            "Curve Algebra": self.launchCurveAlgebra,
        }
        mexport = {
            "Curves": self.exporter.curves,
            "Time info": self.exporter.periods,
            "Cycle info": self.exporter.cyclepoints,
            "Cycles to directory": self.exporter.cycles,
        }
        return {
            "Curves": mcurves,
            "Plot": mplot,
            "Seletion": mselect,
            "Export": mexport,
        }
