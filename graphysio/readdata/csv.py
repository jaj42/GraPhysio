import os
import csv
from functools import partial

import numpy as np
import pandas as pd

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from graphysio import ui
from graphysio.structures import PlotData, CsvRequest


class CsvReader(QtCore.QRunnable):
    def __init__(self, csvrequest, sigdata, sigerror):
        super().__init__()
        self.csvrequest = csvrequest
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
        data = pd.read_csv(
            self.csvrequest.filepath,
            sep=self.csvrequest.seperator,
            usecols=self.csvrequest.fields,
            decimal=self.csvrequest.decimal,
            skiprows=self.csvrequest.droplines,
            encoding=self.csvrequest.encoding,
            index_col=False,
            engine='c',
        )

        pdtonum = partial(pd.to_numeric, errors='coerce')
        dtformat = self.csvrequest.datetime_format
        if self.csvrequest.generatex:
            data.index = (1e9 * data.index / self.csvrequest.samplerate).astype(
                np.int64
            )
            # Make all data numeric and remove empty rows
            data = data.apply(pdtonum)
            data = data.dropna(axis='rows', how='all')
        else:
            timestamp = data[self.csvrequest.dtfield]
            data = data.drop(columns=self.csvrequest.dtfield)
            # Force all columns to numeric
            data = data.apply(pdtonum)

            if dtformat == '<seconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e9, unit='ns')
            elif dtformat == '<milliseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e6, unit='ns')
            elif dtformat == '<microseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e3, unit='ns')
            elif dtformat == '<nanoseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp, unit='ns')
            elif dtformat == '<infer>':
                timestamp = pd.to_datetime(timestamp, infer_datetime_format=True)
            else:
                timestamp = pd.to_datetime(timestamp, format=dtformat)

            # Convert timestamp to UTC and use as index
            timestamp = (
                pd.Index(timestamp)
                .tz_localize(self.csvrequest.timezone)
                .tz_convert('UTC')
            )
            timestamp = timestamp.astype(np.int64)
            data = data.set_index([timestamp])

        data = data.dropna(axis='columns', how='all')
        data = data.sort_index()

        plotdata = PlotData(data=data, filepath=self.csvrequest.filepath)
        return plotdata


class DlgNewPlotCsv(ui.Ui_NewPlot, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, title="New Plot", directory=""):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle(title)

        self.dircache = directory
        self.csvrequest = CsvRequest()

        # Attach models to ListViews
        self.lstX = QtGui.QStandardItemModel()
        self.lstY = QtGui.QStandardItemModel()
        self.lstAll = QtGui.QStandardItemModel()

        self.lstVX.setModel(self.lstX)
        self.lstVY.setModel(self.lstY)
        self.lstVAll.setModel(self.lstAll)

        # Setup Field Table
        self.lstVAll.verticalHeader().hide()
        self.lstVAll.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.lstVAll.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        # Connect callbacks
        self.btnBrowse.clicked.connect(self.selectFile)
        self.btnLoad.clicked.connect(self.loadCsvFields)
        self.btnOk.clicked.connect(self.loadPlot)
        self.btnCancel.clicked.connect(self.reject)
        self.btnToX.clicked.connect(self.moveToX)
        self.btnToY.clicked.connect(self.moveToY)
        self.btnRemoveX.clicked.connect(self.delFromX)
        self.btnRemoveY.clicked.connect(self.delFromY)
        self.lstVX.currentIndexChanged.connect(self.xChanged)

    # Methods / Callbacks
    def selectFile(self):
        filepath = QtGui.QFileDialog.getOpenFileName(
            parent=self, caption="Open CSV file", directory=self.dircache
        )
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if not filepath:
            return
        self.dircache = os.path.dirname(filepath)
        self.txtFile.setText(filepath)
        # Guesstimate CSV field and decimal seperators
        delims = self.estimateDelimiters(filepath)
        self.txtSep.setEditText(delims[0])
        self.txtDecimal.setEditText(delims[1])
        self.txtDateTime.setEditText(f'%Y-%m-%d %H:%M:%S{delims[1]}%f')

    def estimateDelimiters(self, filepath):
        encoding = self.txtEncoding.currentText()
        with open(filepath, 'r', encoding=encoding) as csvfile:
            line1 = next(csvfile)
            line2 = next(csvfile)
            semipos = line1.find(';')
            if semipos == -1:
                seperator = ','
            else:
                seperator = ';'
            periodpos = line2.find('.')
            if periodpos == -1:
                decimal = ','
            else:
                decimal = '.'
        return (seperator, decimal)

    def loadCsvFields(self):
        sep = self.txtSep.currentText()
        if sep == '<tab>':
            sep = '\t'
        filepath = self.txtFile.text()
        # Use the csv module to retrieve csv fields
        for lst in [self.lstAll, self.lstX, self.lstY]:
            lst.clear()
        self.lstAll.setHorizontalHeaderLabels(["Field", "1st Line"])
        encoding = self.txtEncoding.currentText()
        with open(filepath, 'r', encoding=encoding) as csvfile:
            # Artificially drop n first lines as requested
            for _ in range(self.spnLinedrop.value()):
                next(csvfile)
            csvreader = csv.DictReader(csvfile, delimiter=sep)
            row = next(csvreader)
            for key, value in row.items():
                if key is None:
                    continue
                keyitem = QtGui.QStandardItem(key)
                valueitem = QtGui.QStandardItem(value)
                self.lstAll.appendRow([keyitem, valueitem])
        self.lstAll.sort(0)

    def xChanged(self, newtext):
        if self.lstX.rowCount() > 0:
            self.chkGenX.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.chkGenX.setCheckState(QtCore.Qt.Checked)

    def moveToX(self):
        if self.lstX.rowCount() > 0:
            # Only allow one element for X.
            return
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.lstX.appendRow(row)

    def moveToY(self):
        while True:
            selection = self.lstVAll.selectedIndexes()
            if len(selection) < 1:
                break
            rowindex = selection[0].row()
            self.lstY.appendRow(self.lstAll.takeRow(rowindex))

    def delFromX(self):
        try:
            row = self.lstX.takeRow(0)
        except IndexError:
            return
        self.lstAll.appendRow(row)

    def delFromY(self):
        while True:
            rowindexes = self.lstVY.selectedIndexes()
            if len(rowindexes) < 1:
                break
            row = rowindexes[0].row()
            self.lstAll.appendRow(self.lstY.takeRow(row))

    def loadPlot(self):
        yRows = [i.text() for i in self.lstY.findItems("", QtCore.Qt.MatchContains)]
        xRows = [i.text() for i in self.lstX.findItems("", QtCore.Qt.MatchContains)]

        seperator = self.txtSep.currentText()
        if seperator == '<tab>':
            self.csvrequest.seperator = '\t'
        else:
            self.csvrequest.seperator = seperator

        self.csvrequest.generatex = self.chkGenX.checkState() > QtCore.Qt.Unchecked
        if self.csvrequest.generatex or len(xRows) < 1:
            self.csvrequest.dtfield = None
        else:
            self.csvrequest.dtfield = xRows[0]

        self.csvrequest.samplerate = self.spnFs.value()
        self.csvrequest.yfields = yRows
        self.csvrequest.filepath = self.txtFile.text()
        self.csvrequest.decimal = self.txtDecimal.currentText()
        self.csvrequest.datetime_format = self.txtDateTime.currentText()
        self.csvrequest.droplines = self.spnLinedrop.value()
        self.csvrequest.encoding = self.txtEncoding.currentText()
        self.csvrequest.timezone = self.txtTimezone.currentText()

        self.dlgdata.emit(self.csvrequest)
        self.accept()
