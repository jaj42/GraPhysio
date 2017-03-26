import os, csv

from pyqtgraph.Qt import QtGui, QtCore

from graphysio import algorithms, utils

class DlgNewPlot(*utils.loadUiFile('newplot.ui')):
    def __init__(self, parent=None, title="New Plot", directory=""):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle(title)

        self.dircache = directory
        self.csvrequest = utils.CsvRequest()

        # Attach models to ListViews
        self.lstX = QtGui.QStandardItemModel()
        self.lstY = QtGui.QStandardItemModel()
        self.lstAll = QtGui.QStandardItemModel()

        self.lstVX.setModel(self.lstX)
        self.lstVY.setModel(self.lstY)
        self.lstVAll.setModel(self.lstAll)

        # Setup Field Table
        self.lstVAll.verticalHeader().hide()
        self.lstVAll.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

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
        with open(filepath, 'r', encoding='latin1') as csvfile:
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
        fields = []
        # Use the csv module to retrieve csv fields
        for lst in [self.lstAll, self.lstX, self.lstY]: lst.clear()
        self.lstAll.setHorizontalHeaderLabels(["Field", "1st Line"])
        with open(filepath, 'r') as csvfile:
            # Artificially drop n first lines as requested
            for i in range(self.spnLinedrop.value()):
                next(csvfile)
            csvreader = csv.DictReader(csvfile, delimiter=sep)
            row = next(csvreader)
            for key, value in row.items():
                if key is None: continue
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
        if self.lstX.rowCount() > 0: return # Only allow one element allowed for X.
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.lstX.appendRow(row)

    def moveToY(self):
        while True:
            selection = self.lstVAll.selectedIndexes()
            if len(selection) < 1: break
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
            combo.addItems(['None', 'Pressure', 'Velocity'])
            curveitem = QtGui.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

    @property
    def result(self):
        return {curve: combo.currentText() for (curve, combo) in self.choices.items()}


class DlgFilter(*utils.loadUiFile('filter.ui')):
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

            combo.addItems(['None'])
            filters = list(algorithms.Filters.keys())
            combo.addItems(filters)

            curveitem = QtGui.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

    @property
    def result(self):
        filthash = {curve: combo.currentText() for (curve, combo) in self.choices.items()}
        newcurve = (self.chkNewcurve.checkState() > QtCore.Qt.Unchecked)
        return (newcurve, filthash)


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

        hiddenhash = {curve.name(): curve for curve in hidden}
        self.curvehash = {curve.name(): curve for curve in visible}
        self.curvehash.update(hiddenhash)

        for curve in visible:
            self.addCurve(curve.name(), checked=True)
        for curve in hidden:
            self.addCurve(curve.name(), checked=False)

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
    elif type(param.request) is list:
        value, isok = QtGui.QInputDialog.getItem(None, 'Enter value', param.description, param.request, editable=False)
    else:
        raise TypeError("Unknown request type")

    if isok:
        return value
    else:
        return None
