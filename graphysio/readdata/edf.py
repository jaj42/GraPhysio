import os

import pyedflib
import numpy as np
import pandas as pd

from pyqtgraph.Qt import QtGui, QtCore

from graphysio.structures import PlotData


class EdfReader(QtCore.QRunnable):
    def __init__(self, datarequest, sigdata, sigerror):
        super().__init__()
        self.filepath = datarequest.filepath
        self.sigdata = sigdata
        self.sigerror = sigerror

    def run(self) -> None:
        try:
            data = self.getdata()
        except Exception as e:
            self.sigerror.emit(e)
        else:
            self.sigdata.emit(data)

    def getdata(self) -> PlotData:
        edf = pyedflib.EdfReader(self.filepath)
        beginns = edf.getStartdatetime().timestamp() * 1e9
        nsamplesPerChannel = edf.getNSamples()

        signals = []
        for i in range(edf.signals_in_file):
            h = edf.getSignalHeader(i)
            fs = h['sample_rate']
            n = nsamplesPerChannel[i]
            endns = beginns + n * 1e9 / fs
            idx = np.linspace(beginns, endns, num=n, dtype=np.int64)
            s = pd.Series(edf.readSignal(i), index=idx, name=h['label'])
            signals.append(s)
        edf.close()

        df = pd.concat(signals, axis=1)
        plotdata = PlotData(data=df, filepath=self.filepath)

        return plotdata


class DataRequest:
    def __init__(self, filepath=""):
        self.filepath = filepath

    @property
    def name(self):
        name, _ = os.path.splitext(os.path.basename(self.filepath))
        return name

    @property
    def folder(self):
        folder = os.path.dirname(self.filepath)
        return folder


class DlgNewPlotEdf(QtCore.QObject):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, title="New Plot", directory=""):
        super().__init__(parent=parent)
        self.datarequest = DataRequest()
        self.dircache = directory

    def exec_(self):
        filepath = QtGui.QFileDialog.getOpenFileName(
            parent=None, caption="Open Edf file", directory=self.dircache
        )
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if filepath:
            self.datarequest.filepath = filepath
            self.dlgdata.emit(self.datarequest)
