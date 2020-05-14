import os

import numpy as np
import pandas as pd

from pyqtgraph.Qt import QtGui, QtCore

from graphysio.structures import PlotData


class ParquetReader(QtCore.QRunnable):
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
        data = pd.read_parquet(self.filepath)

        data = data.dropna(axis='columns', how='all')
        data = data.sort_index()
        data.index = data.index.astype(np.int64)

        plotdata = PlotData(data=data, filepath=self.filepath)
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


class DlgNewPlotParquet(QtCore.QObject):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, title="New Plot", directory=""):
        super().__init__(parent=parent)
        self.datarequest = DataRequest()
        self.dircache = directory

    def exec_(self):
        filepath = QtGui.QFileDialog.getOpenFileName(
            parent=None, caption="Open Parquet file", directory=self.dircache
        )
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if filepath:
            self.datarequest.filepath = filepath
            self.dlgdata.emit(self.datarequest)
