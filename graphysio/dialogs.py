import os, csv

from pyqtgraph.Qt import QtGui, QtCore, loadUiType

from graphysio import algorithms, utils

#uiFiles = ['newplot.ui', 'cycledetect.ui', 'filter.ui', 'setuppuloop.ui', 'periodexport.ui']

curPath = os.path.dirname(os.path.abspath(__file__))
uiBasePath = os.path.join(curPath, 'ui', 'designer')
def loadUiFile(uiFile):
    uiPath = os.path.join(uiBasePath, uiFile)
    uiClasses = loadUiType(uiPath)
    return uiClasses

class DlgNewPlot(*loadUiFile('newplot.ui')):
    def __init__(self, parent=None, title="New Plot", directory=""):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle(title)

        self.dircache = directory
        self.plotdata = utils.PlotDescription()

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

    @property
    def result(self):
        return self.plotdata

    # Methods / Callbacks
    def selectFile(self):
        filepath = QtGui.QFileDialog.getOpenFileName(parent = self,
                                                     caption = "Open CSV file",
                                                     directory = self.dircache)
        if not filepath: return
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

    def moveToX(self):
        if self.lstX.rowCount() > 0: return # Only allow one element allowed for X.
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.itemCheckable(row, True)
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
        self.itemCheckable(row, False)
        self.lstAll.appendRow(row)

    def delFromY(self):
        while True:
            rowindexes = self.lstVY.selectedIndexes()
            if len(rowindexes) < 1:
                break
            row = rowindexes[0].row()
            self.lstAll.appendRow(self.lstY.takeRow(row))

    def itemCheckable(self, row, checkable):
            field = row[0]
            if checkable:
                field.setFlags(field.flags() | QtCore.Qt.ItemIsUserCheckable)
                field.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
            else:
                field.setFlags(field.flags() ^ QtCore.Qt.ItemIsUserCheckable)
                field.setData(None, QtCore.Qt.CheckStateRole)

    def loadPlot(self):
        yRows = [i.text() for i in self.lstY.findItems("", QtCore.Qt.MatchContains)]
        xRows = [i.text() for i in self.lstX.findItems("", QtCore.Qt.MatchContains)]
        xState = [i.checkState() for i in self.lstX.findItems("", QtCore.Qt.MatchContains)]
        for s in xState:
            self.plotdata.xisdate = s > QtCore.Qt.Unchecked
            break
        if len(xRows) > 0:
            self.plotdata.xfield = xRows[0]
        else:
            self.plotdata.xfield = None

        seperator = self.txtSep.currentText()
        if seperator == '<tab>':
            self.plotdata.seperator = '\t'
        else:
            self.plotdata.seperator = seperator

        self.plotdata.yfields = yRows
        self.plotdata.filepath = self.txtFile.text()
        self.plotdata.decimal = self.txtDecimal.currentText()
        self.plotdata.datetime_format = self.txtDateTime.currentText()
        self.plotdata.droplines = self.spnLinedrop.value()
        self.plotdata.loadall = not self.chkLoadNotAll.isChecked()
        self.accept()


class DlgCycleDetection(*loadUiFile('cycledetect.ui')):
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
            combo.addItems(['Pressure', 'Velocity', 'None'])
            curveitem = QtGui.QTableWidgetItem(curvename)

            # Preselect velocity based on the field name
            if curvename.lower().find('vel') >= 0:
                combo.setCurrentIndex(1)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

    @property
    def result(self):
        return {curve: combo.currentText() for (curve, combo) in self.choices.items()}


class DlgFilter(*loadUiFile('filter.ui')):
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
            combo.addItems(list(algorithms.Filters.keys()))

            curveitem = QtGui.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

    @property
    def result(self):
        return {curve: combo.currentText() for (curve, combo) in self.choices.items()}


class DlgSetupPULoop(*loadUiFile('setuppuloop.ui')):
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


class DlgPeriodExport(*loadUiFile('periodexport.ui')):
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
        filename = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     options = QtGui.QFileDialog.DontConfirmOverwrite,
                                                     directory = self.dircache)
        if filename:
            self.txtFile.setText(filename)
            self.dircache = os.path.dirname(filename)

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
