from functools import partial
from typing import Optional

import numpy as np
import pandas as pd
import pyqtgraph as pg
from physiocurve.pandas import ECG, Pressure
from pyqtgraph.Qt import QtCore, QtGui

from graphysio import utils
from graphysio.algorithms import waveform
from graphysio.structures import CycleId
from graphysio.utils import estimateSampleRate


class CurveItem(pg.PlotDataItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    def __init__(self, series, parent, pen=None):
        self.parent = parent
        self.series = self.sanitize_data(series)
        if self.series is None:
            raise ValueError("Not enough data")
        self.samplerate = estimateSampleRate(self.series)
        if pen is None:
            pen = QtGui.QColor(QtCore.Qt.black)
        super().__init__(name=series.name, pen=pen, antialias=True)
        self.render()

    def replace_data(self, newdata):
        newdata = self.sanitize_data(newdata)
        if newdata is None:
            # XXX report error
            return
        self.clear()
        self.series = newdata.rename(self.opts["name"])
        self.samplerate = estimateSampleRate(self.series)
        self.render()

    def extend(self, newseries):
        merged = self.series.append(newseries)
        newdata = self.sanitize_data(merged)
        if newdata is None:
            # XXX report error
            return
        self.series = newdata
        self.render()

    def render(self):
        self.setData(x=self.series.index.to_numpy(), y=self.series.to_numpy())

    def set_samplerate(self, newsamplerate):
        self.samplerate = newsamplerate

    def rename(self, newname: str):
        self.opts["name"] = newname
        self.series = self.series.rename(newname)

    def sanitize_data(self, series: pd.Series) -> Optional[pd.Series]:
        series = series.dropna()
        series = series.sort_index()
        # Less than 2 points are not visible
        if len(series) < 2:
            return None
        # Make timestamp unique and use mean of values on duplicates
        series = series.groupby(level=0).mean()
        return series


class POIItem(pg.ScatterPlotItem):
    sym = {
        "start": "star",
        "stop": "s",
        "diastole": "t1",
        "systole": "t",
        "dicrotic": "d",
        "qwave": "t1",
        "rwave": "x",
        "swave": "t",
        "twave": "o",
    }
    # Symbols = OrderedDict([(name, QtGui.QPainterPath()) for name in
    # ['o', 's', 't', 't1', 't2', 't3','d', '+', 'x', 'p', 'h', 'star']])

    def __init__(self, parent, name, pen=None):
        super().__init__(pen=pen, name=name)
        self.parent = parent
        self.indices = {}
        self.selected = []
        self.resym = {value: key for key, value in self.sym.items()}
        self.render()

    def addPointsByLocation(self, key, locations):
        if key not in self.indices:
            self.indices[key] = pd.Index([])
        oldidx = self.indices[key]
        newidx = oldidx.append(pd.Index(locations))
        self.indices[key] = newidx.unique().sort_values()
        self.render()

    def removePointsByLocation(self, key, locations):
        if key not in self.indices:
            return
        oldidx = self.indices[key]
        dellocs = oldidx.get_indexer(locations, method="nearest")
        newidx = oldidx.delete(dellocs)
        self.indices[key] = newidx
        self.render()

    def removePoints(self, points):
        for point in points:
            try:
                sym = self.resym[point.symbol()]
                idx = self.indices[sym]
            except KeyError as e:
                raise KeyError("Point not found") from e
            nidx = idx.get_indexer([point.pos().x()], method="nearest")
            self.indices[sym] = idx.delete(nidx)
        self.render()

    def render(self):
        data = []
        for key, idx in self.indices.items():
            if len(idx) < 1:
                continue
            idxnona = idx.dropna()
            points = self.parent.series.loc[idxnona]
            tmp = pd.DataFrame({"points": points, "sym": self.sym[key]}, index=idxnona)
            data.append(tmp)
        if len(data) < 1:
            self.clear()
            return
        feet = pd.concat(data)
        self.setData(
            x=feet.index.values, y=feet["points"].values, symbol=feet["sym"].values
        )

    def isPointSelected(self, point):
        return point in self.selected

    def selectPoint(self, point):
        if not self.isPointSelected(point):
            self.selected.append(point)
        point.setPen("r")
        point.setBrush("r")

    def unselectPoint(self, point):
        if self.isPointSelected(point):
            self.selected.remove(point)
        point.resetPen()
        point.resetBrush()

    def removeSelection(self):
        self.removePoints(self.selected)
        self.selected = []

    def rename(self, newname: str):
        self.opts["name"] = newname


class CurveItemWithPOI(CurveItem):
    visible = QtCore.pyqtSignal()
    invisible = QtCore.pyqtSignal()

    @staticmethod
    def sigPointClicked(feetitem, points):
        point = points[0]  # only one point per click
        if not feetitem.isPointSelected(point):
            feetitem.selectPoint(point)
        else:
            feetitem.unselectPoint(point)

    def __init__(self, series, parent, pen=None):
        super().__init__(series, parent, pen)
        feetname = f"{series.name}-feet"
        self.feetitem = POIItem(self, name=feetname, pen=pen)
        parent.addItem(self.feetitem)
        self.feetitem.sigClicked.connect(self.sigPointClicked)
        self.visible.connect(self.__becameVisible)
        self.invisible.connect(self.__becameInvisible)

    def __becameVisible(self):
        if self.feetitem not in self.parent.listDataItems():
            self.parent.addItem(self.feetitem)
        self.render()
        self.feetitem.render()

    def __becameInvisible(self):
        self.parent.removeItem(self.feetitem)

    def addFeet(self, cycleid):
        if cycleid is CycleId.none:
            return
        elif cycleid is CycleId.velocity:
            starts, stops = waveform.findFlowCycles(self)
            self.feetitem.indices["start"] = starts
            self.feetitem.indices["stop"] = stops
        elif cycleid is CycleId.foot:
            foot = waveform.findPressureFeet(self)
            self.feetitem.indices["start"] = foot
        elif cycleid is CycleId.pressure:
            if "start" not in self.feetitem.indices:
                self.addFeet(CycleId.foot)
            dia, sbp, dic = waveform.findPressureFull(self)
            self.feetitem.indices["diastole"] = dia
            self.feetitem.indices["systole"] = sbp
            self.feetitem.indices["dicrotic"] = dic
        elif cycleid is CycleId.rwave:
            ecg = ECG(self.series)
            self.feetitem.indices["rwave"] = ecg.idxrwave
        elif cycleid is CycleId.ecg:
            ecg = ECG(self.series)
            self.feetitem.indices["start"] = ecg.idxpwave
            self.feetitem.indices["qwave"] = ecg.idxqwave
            self.feetitem.indices["rwave"] = ecg.idxrwave
            self.feetitem.indices["swave"] = ecg.idxswave
            self.feetitem.indices["twave"] = ecg.idxtwave
        elif cycleid is CycleId.foottan:
            p = Pressure(self.series)
            self.feetitem.indices["start"] = p.idxtanfeet
        elif cycleid is CycleId.pressurebis:
            p = Pressure(self.series)
            self.feetitem.indices["start"] = p.idxfeet
            self.feetitem.indices["diastole"] = p.idxdia
            self.feetitem.indices["systole"] = p.idxsys
            self.feetitem.indices["dicrotic"] = p.idxdic
        else:
            raise ValueError(cycleid)
        self.feetitem.render()

    def getCycleIndices(self, vrange=None):
        s = self.series
        clip = partial(utils.clip, vrange=vrange)
        hasstarts = ("start" in self.feetitem.indices) and self.feetitem.indices[
            "start"
        ].size > 0
        hasstops = ("stop" in self.feetitem.indices) and self.feetitem.indices[
            "stop"
        ].size > 0
        if vrange:
            xmin, xmax = vrange
        else:
            xmin = s.index[0]
            xmax = s.index[-1]
        if not hasstarts:
            # We have no feet, treat the whole signal as one cycle
            locs = s.index.get_indexer([xmin, xmax], method="nearest")
            indices = s.index[locs]
            begins, ends = [np.array([i]) for i in indices]
        elif not hasstops:
            # We have no stops, starts serve as stops for previous cycle
            begins = clip(self.feetitem.indices["start"].values)
            endloc = s.index.get_indexer([xmax], method="nearest")
            end = s.index[endloc]
            ends = np.append(begins[1:], end)
        else:
            # We have starts and stops, use them
            begins = self.feetitem.indices["start"].values
            ends = self.feetitem.indices["stop"].values
            begins, ends = map(clip, [begins, ends])

        # Handle the case where we start in the middle of a cycle
        while ends[0] <= begins[0]:
            ends = ends[1:]

        begins, ends = utils.truncatevecs([begins, ends])
        durations = ends - begins
        return (begins, durations)

    def getFeetPoints(self, feetname) -> Optional[pd.Series]:
        if feetname not in self.feetitem.indices:
            return None
        feetidx = self.feetitem.indices[feetname]
        feetnona = feetidx[pd.notnull(feetidx)]
        return self.series.loc[feetnona]
