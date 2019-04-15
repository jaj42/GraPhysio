import os, csv
import string
from datetime import datetime

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

from graphysio import algorithms, utils, types
from graphysio.types import CsvRequest


class DlgNewPlot(*utils.loadUiFile('newplot.ui')):
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

    @property
    def result(self):
        return self.csvrequest

    # Methods / Callbacks
    def selectFile(self):
        filepath = QtGui.QFileDialog.getOpenFileName(parent = self,
                                                     caption = "Open CSV file",
                                                     directory = self.dircache)
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
        self.txtDateTime.setEditText("%Y-%m-%d %H:%M:%S{}%f".format(delims[1]))

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
                decimal   = ','
            else:
                decimal   = '.'
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
            for i in range(self.spnLinedrop.value()):
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

        self.csvrequest.generatex = (self.chkGenX.checkState() > QtCore.Qt.Unchecked)
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
        self.accept()

class DlgCycleDetection(*utils.loadUiFile('cycledetect.ui')):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if plotframe is None:
            return

        for n, curvename in enumerate(plotframe.curves.keys()):
            combo = QtGui.QComboBox()
            combo.addItems([ft.value for ft in types.CycleId])
            curveitem = QtGui.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    @property
    def result(self):
        return {curve: combo.currentText() for (curve, combo) in self.choices.items()}


class DlgFilter(*utils.loadUiFile('filter.ui')):
    def __init__(self, parent=None, filterfeet=False):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if plotframe is None:
            return

        def fillTable(items, itemtype, filters):
            rowoffset = self.table.rowCount()
            for n, itemname in enumerate(items):
                combo = QtGui.QComboBox()

                combo.addItems(['None'])
                filternames = list(filters.keys())
                combo.addItems(filternames)

                curveitem = QtGui.QTableWidgetItem(itemname)

                idx = rowoffset + n
                self.table.insertRow(idx)
                self.table.setItem(idx, 0, curveitem)
                self.table.setCellWidget(idx, 1, combo)
                self.choices[itemname] = (combo, itemtype)

        curves = list(plotframe.curves.keys())
        if filterfeet:
            self.chkNewcurve.hide()
            fillTable(curves, 'curve', algorithms.FeetFilters)
        else:
            fillTable(curves, 'curve', algorithms.Filters)

        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    @property
    def result(self):
        curvefilters = {}
        for itemname, value in self.choices.items():
            combo, itemtype = value
            curvefilters[itemname] = combo.currentText()

        createnew = (self.chkNewcurve.checkState() > QtCore.Qt.Unchecked)
        return (createnew, curvefilters)


class DlgSetupPULoop(*utils.loadUiFile('setuppuloop.ui')):
    def __init__(self, sourcewidget, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        try:
            curvenames = list(sourcewidget.curves.keys())
        except AttributeError:
            return

        self.comboU.addItems(curvenames)
        self.comboP.addItems(curvenames)

    @property
    def result(self):
        uname = self.comboU.currentText()
        pname = self.comboP.currentText()
        return (uname, pname)


class DlgPeriodExport(*utils.loadUiFile('periodexport.ui')):
    def __init__(self, begin, end, patient="", directory="", parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.dircache = directory

        self.lblPeriodStart.setText(str(begin))
        self.lblPeriodStop.setText(str(end))
        self.txtPatient.setText(patient)

        self.btnOk.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        self.btnBrowse.clicked.connect(self.selectFile)

    def selectFile(self):
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     options = QtGui.QFileDialog.DontConfirmOverwrite,
                                                     directory = self.dircache)
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if filepath:
            self.txtFile.setText(filepath)
            self.dircache = os.path.dirname(filepath)

    @property
    def patient(self):
        return self.txtPatient.text()

    @property
    def comment(self):
        return self.txtComment.text()

    @property
    def periodname(self):
        return self.txtPeriod.currentText()

    @property
    def filepath(self):
        return self.txtFile.text()

class DlgCurveSelection(*utils.loadUiFile('curveselect.ui')):
    def __init__(self, visible=[], hidden=[], parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.btnProperties.clicked.connect(self.openProperties)

        hiddenhash = {curve.name(): curve for curve in hidden}
        self.curvehash = {curve.name(): curve for curve in visible}
        self.curvehash.update(hiddenhash)

        for curve in visible:
            self.addCurve(curve.name(), checked=True)
        for curve in hidden:
            self.addCurve(curve.name(), checked=False)

    def openProperties(self):
        selected = self.lstCurves.selectedItems()
        try:
            curvename = selected[0].text()
        except IndexError:
            return
        curve = self.curvehash[curvename]
        dlg = DlgCurveProperties(curve)
        dlg.exec_()

    def addCurve(self, name, checked):
        item = QtGui.QListWidgetItem()
        item.setText(name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        if checked:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)
        self.lstCurves.addItem(item)

    @property
    def result(self):
        items = self.lstCurves.findItems("", QtCore.Qt.MatchContains)
        ischecked = lambda item: not (item.checkState() == QtCore.Qt.Unchecked)
        checked = list(filter(ischecked, items))
        unchecked = [item for item in items if item not in checked]
        visible = [self.curvehash[item.text()] for item in checked]
        invisible = [self.curvehash[item.text()] for item in unchecked]
        return (visible, invisible)

class DlgCurveProperties(*utils.loadUiFile('curveproperties.ui')):
    def __init__(self, curve, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.curve = curve

        self.okButton.clicked.connect(self.ok)
        self.cancelButton.clicked.connect(self.reject)
        self.btnColor.clicked.connect(self.chooseColor)

        connect = curve.opts['connect']
        symbol = curve.opts['symbol']
        if symbol is None:
            symbol = 'None'

        pen = curve.opts['pen']
        if isinstance(pen, QtGui.QPen):
            color = pen.color()
            width = pen.width()
        else:
            color = pen
            width = 1
        self.color = color

        idx = self.cmbConnect.findText(connect, QtCore.Qt.MatchFixedString)
        self.cmbConnect.setCurrentIndex(idx)

        idx = self.cmbSymbol.findText(symbol, QtCore.Qt.MatchFixedString)
        self.cmbSymbol.setCurrentIndex(idx)

        self.cmbSymbol.setEditText(symbol)
        self.grpName.setTitle(curve.name())
        self.txtName.setText(curve.name())
        self.spnWidth.setValue(width)
        self.btnColor.setStyleSheet('background-color: {}'.format(color.name()))
        self.lblSamplerate.setText(str(curve.samplerate))

    def ok(self):
        connect = str(self.cmbConnect.currentText().lower())
        if connect == 'none':
            connect = [0]
        symbol = self.cmbSymbol.currentText().lower()
        if symbol == 'none':
            symbol = None

        #self.curve.setData(connect=connect, symbol=symbol)
        self.curve.setData(symbol=symbol)

        width = self.spnWidth.value()
        pen = pg.mkPen(color=self.color, width=width)
        self.curve.setPen(pen)

        self.accept()

    def chooseColor(self):
        color = QtGui.QColorDialog.getColor()
        if not color.isValid():
            return
        self.color = color
        self.btnColor.setStyleSheet('background-color: {}'.format(color.name()))

class DlgSetDateTime(*utils.loadUiFile('datetime.ui')):
    def __init__(self, parent=None, prevdatetime=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.timestamp = 0

        self.btnOk.clicked.connect(self.ok)
        self.btnCancel.clicked.connect(self.reject)

        if prevdatetime is None:
            datetime = QtCore.QDateTime.currentDateTime()
        else:
            datetime = QtCore.QDateTime.fromMSecsSinceEpoch(prevdatetime / 1e6)
        curdate = datetime.date()
        curtime = datetime.time()
        self.widgetCalendar.setSelectedDate(curdate)
        self.edDate.setDate(curdate)
        self.edTime.setTime(curtime)

    def ok(self):
        date = self.edDate.date()
        time = self.edTime.time()
        dt = QtCore.QDateTime(date, time, QtCore.Qt.UTC)
        self.timestamp = dt.toMSecsSinceEpoch() * 1e6
        self.accept()

    @property
    def result(self):
        return self.timestamp

class DlgCurveAlgebra(QtWidgets.QDialog):
    def __init__(self, parent=None, curvecorr={}):
        super().__init__(parent=parent)
        self.setupUi(curvecorr)
    
    def setupUi(self, curvecorr):
        vstack = QtWidgets.QVBoxLayout(self)

        self.lbl = QtWidgets.QLabel('Enter formula for new curve:')
        vstack.addWidget(self.lbl)

        self.formula = QtWidgets.QLineEdit('a^2 + log(2*b)')
        vstack.addWidget(self.formula)

        curveslbl = '\n'.join(['{}: {}'.format(x,y) for x,y in curvecorr.items()])
        self.curveletters = QtWidgets.QLabel(curveslbl)
        vstack.addWidget(self.curveletters)

        self.buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        vstack.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.setLayout(vstack)

    @property
    def result(self):
        return self.formula.text()

def askUserValue(param):
    if param.request is str:
        value, isok = QtGui.QInputDialog.getText(None, 'Enter value', param.description)
    elif param.request is int:
        value, isok = QtGui.QInputDialog.getInt(None, 'Enter value', param.description)
    elif param.request is float:
        value, isok = QtGui.QInputDialog.getDouble(None, 'Enter value', param.description, decimals=3)
    elif param.request is bool:
        request = ['Yes', 'No']
        tmpvalue, isok = QtGui.QInputDialog.getItem(None, 'Enter value', param.description, request, editable=False)
        value = (tmpvalue == 'Yes')
    elif param.request is datetime:
        dlg = DlgSetDateTime()
        isok = dlg.exec_()
        value = dlg.result
    elif type(param.request) is list:
        value, isok = QtGui.QInputDialog.getItem(None, 'Enter value', param.description, param.request, editable=False)
    else:
        raise TypeError("Unknown request type")

    if isok:
        return value
    else:
        return None

def userConfirm(question, title=None):
    if title is None:
        title = question
    reply = QtGui.QMessageBox.question(None, title, question, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
    confirmed = (reply == QtGui.QMessageBox.Yes)
    return confirmed
