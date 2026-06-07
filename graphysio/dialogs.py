import csv
import importlib
import os
import pathlib
import re
import sys
from datetime import datetime
from functools import partial

from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from graphysio import ui
from graphysio.algorithms import filters
from graphysio.core.params import ParamSpec, gather
from graphysio.structures import CycleId, Parameter
from graphysio.utils import sanitize_filepath

ureg = UnitRegistry()


class DlgCycleDetection(ui.Ui_CycleDetection, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if plotframe is None:
            return

        for n, curvename in enumerate(plotframe.curves.keys()):
            combo = QtWidgets.QComboBox()
            combo.addItems([ft.value for ft in CycleId])
            curveitem = QtWidgets.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents,
        )

    def accept(self) -> None:
        result = {curve: combo.currentText() for (curve, combo) in self.choices.items()}
        self.dlgdata.emit(result)
        super().accept()


class DlgDWCOpen(ui.Ui_DWCOpen, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, dwclib, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dwc_search_function = dwclib.read_patient
        self.dwc_update_config = dwclib.common.db.update_config
        self.patient = None

        self.searchButton.clicked.connect(self.search_patient)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.loadConfigButton.clicked.connect(self.update_config)

    def search_patient(self):
        self.lstLabels.clear()
        type_of_data = self.cmbTypeofData.currentText()
        if type_of_data.lower() == "numerics":
            data_req = "numericsublabels"
        elif type_of_data.lower() == "waves":
            data_req = "wavelabels"
        else:
            raise ValueError(f"Wrong data type: {data_req}")
        patientid = self.txtPatientId.text()
        res = self.dwc_search_function(patientid)
        self.patient = res
        if res is None:
            self.lblFound.setText("Not found")
            return
        self.lblFound.setText(f"Found: {res['lastname']}, {res['firstname']}")
        self.dtFrom.setDateTime(res["data_begin"])
        self.dtTo.setDateTime(res["data_end"])
        for lbl in res[data_req]:
            self.lstLabels.addItem(lbl)

    def update_config(self) -> None:
        configfile, _ = askOpenFilePath("Import dwclib config file")
        with open(configfile, "r") as fd:
            c = fd.read()
        self.dwc_update_config(c)

    def accept(self) -> None:
        data = {}
        data["patientid"] = self.txtPatientId.text()
        data["from"] = self.dtFrom.dateTime().toPython()
        data["to"] = self.dtTo.dateTime().toPython()
        data["items"] = [item.text() for item in self.lstLabels.selectedItems()]
        data["type"] = self.cmbTypeofData.currentText().lower()
        self.dlgdata.emit(data)
        super().accept()


class DlgFilter(ui.Ui_Filter, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, parent=None, filterfeet=False) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if not plotframe:
            return

        def fillTable(items, itemtype, filters) -> None:
            rowoffset = self.table.rowCount()
            for n, itemname in enumerate(items):
                combo = QtWidgets.QComboBox()

                combo.addItems(["None"])
                filternames = list(filters.keys())
                combo.addItems(filternames)

                curveitem = QtWidgets.QTableWidgetItem(itemname)

                idx = rowoffset + n
                self.table.insertRow(idx)
                self.table.setItem(idx, 0, curveitem)
                self.table.setCellWidget(idx, 1, combo)
                self.choices[itemname] = (combo, itemtype)

        curves = list(plotframe.curves.keys())
        if filterfeet:
            self.chkNewcurve.hide()
            fillTable(curves, "curve", filters.FeetFilters)
        else:
            fillTable(curves, "curve", filters.Filters)

        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents,
        )

    def accept(self) -> None:
        curvefilters = {}
        for itemname, value in self.choices.items():
            combo, itemtype = value
            curvefilters[itemname] = combo.currentText()
        result = (self.chkNewcurve.isChecked(), curvefilters)
        self.dlgdata.emit(result)
        super().accept()


class DlgSetupPULoop(ui.Ui_SetupPULoop, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, sourcewidget, parent=None) -> None:
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

    def accept(self) -> None:
        uname = self.comboU.currentText()
        pname = self.comboP.currentText()
        result = (uname, pname)
        self.dlgdata.emit(result)
        super().accept()


class DlgPeriodExport(ui.Ui_PeriodExport, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, begin, end, patient="", directory="", parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.dircache = directory

        self.lblPeriodStart.setText(str(begin))
        self.lblPeriodStop.setText(str(end))
        self.txtPatient.setText(patient)

        self.btnOk.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        self.btnBrowse.clicked.connect(self.selectFile)

    def selectFile(self) -> None:
        filepath = QtWidgets.QFileDialog.getSaveFileName(
            caption="Export to",
            filter="CSV files (*.csv *.dat)",
            options=QtWidgets.QFileDialog.DontConfirmOverwrite,
            dir=self.dircache,
        )
        # PyQt5 API change
        if not isinstance(filepath, str):
            filepath = filepath[0]

        if filepath:
            self.txtFile.setText(filepath)
            self.dircache = os.path.dirname(filepath)

    def accept(self) -> None:
        patient = self.txtPatient.text()
        comment = self.txtComment.text()
        periodname = self.txtPeriod.currentText()
        filepath = self.txtFile.text()
        result = (patient, comment, periodname, filepath)
        self.dlgdata.emit(result)
        super().accept()


class DlgCurveSelection(ui.Ui_CurveSelection, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, visible=None, hidden=None, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        if visible is None:
            visible = []
        if hidden is None:
            hidden = []

        self.curveproperties = {}

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

    def openProperties(self) -> None:
        selected = self.lstCurves.selectedItems()
        try:
            curvename = selected[0].text()
        except IndexError:
            return
        curve = self.curvehash[curvename]

        def cb(resultdict) -> None:
            self.curveproperties[curve] = resultdict

        dlg = DlgCurveProperties(curve)
        dlg.dlgdata.connect(cb)
        dlg.exec()

    def addCurve(self, name, checked) -> None:
        item = QtWidgets.QListWidgetItem()
        item.setText(name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        if checked:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)
        self.lstCurves.addItem(item)

    def accept(self) -> None:
        items = self.lstCurves.findItems("", QtCore.Qt.MatchContains)
        checked_items = [i for i in items if i.checkState() != QtCore.Qt.Unchecked]
        visible_items = {self.curvehash[item.text()] for item in checked_items}
        result = (visible_items, self.curveproperties)
        self.dlgdata.emit(result)
        super().accept()


class DlgCurveProperties(ui.Ui_CurveProperties, QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, curve, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.curve = curve

        self.okButton.clicked.connect(self.ok)
        self.cancelButton.clicked.connect(self.reject)
        self.btnColor.clicked.connect(self.chooseColor)

        connect = curve.opts["connect"]
        symbol = curve.opts["symbol"]
        if symbol is None:
            symbol = "None"

        pen = curve.opts["pen"]
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
        self.btnColor.setStyleSheet(f"background-color: {color.name()}")
        self.lblSamplerate.setText(str(curve.samplerate))

    def ok(self) -> None:
        symbol = self.cmbSymbol.currentText().lower()
        symbol = None if symbol == "none" else symbol

        connect = str(self.cmbConnect.currentText().lower())
        connect = [0] if connect == "none" else connect

        result = {
            "name": self.txtName.text(),
            "connect": connect,
            "symbol": symbol,
            "width": self.spnWidth.value(),
            "color": self.color,
        }
        self.dlgdata.emit(result)
        self.accept()

    def chooseColor(self) -> None:
        color = QtWidgets.QColorDialog.getColor()
        if not color.isValid():
            return
        self.color = color
        self.btnColor.setStyleSheet(f"background-color: {color.name()}")


class DlgSetDateTime(ui.Ui_SetDateTime, QtWidgets.QDialog):
    def __init__(self, parent=None, prevdatetime=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.dlgdata = None
        self.btnOk.clicked.connect(self.ok)
        self.btnCancel.clicked.connect(self.reject)

        if prevdatetime is None:
            datetime = QtCore.QDateTime.currentDateTime()
        else:
            datetime = QtCore.QDateTime.fromMSecsSinceEpoch(int(prevdatetime / 1e6))
        curdate = datetime.date()
        curtime = datetime.time()
        self.widgetCalendar.setSelectedDate(curdate)
        self.edDate.setDate(curdate)
        self.edTime.setTime(curtime)

    def ok(self) -> None:
        date = self.edDate.date()
        time = self.edTime.time()
        dt = QtCore.QDateTime(date, time, QtCore.Qt.UTC)
        timestamp = dt.toMSecsSinceEpoch() * 1e6
        self.dlgdata = timestamp
        self.accept()


class DlgCurveAlgebra(QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, parent=None, curvecorr=None) -> None:
        super().__init__(parent=parent)
        if curvecorr is None:
            curvecorr = {}
        self.setupUi(curvecorr)

    def setupUi(self, curvecorr) -> None:
        vstack = QtWidgets.QVBoxLayout(self)

        self.lbl = QtWidgets.QLabel("Enter formula for new curve:")
        vstack.addWidget(self.lbl)

        self.formula = QtWidgets.QLineEdit("a**2 + log(2*b)")
        vstack.addWidget(self.formula)

        curveslbl = "\n".join([f"{x}: {y}" for x, y in curvecorr.items()])
        self.curveletters = QtWidgets.QLabel(curveslbl)
        vstack.addWidget(self.curveletters)

        self.buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        vstack.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.setLayout(vstack)

    def accept(self) -> None:
        result = self.formula.text()
        self.dlgdata.emit(result)
        super().accept()


class DlgListChoice(QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, items, title="", message="", parent=None) -> None:
        super().__init__(parent=parent)
        form = QtWidgets.QFormLayout(self)
        form.addRow(QtWidgets.QLabel(message))
        self.listView = QtWidgets.QListView(self)
        form.addRow(self.listView)
        model = QtGui.QStandardItemModel(self.listView)
        self.setWindowTitle(title)
        for item in items:
            standardItem = QtGui.QStandardItem(item)
            standardItem.setCheckable(True)
            standardItem.setCheckState(QtCore.Qt.Checked)
            standardItem.setEditable(False)
            model.appendRow(standardItem)
        self.listView.setModel(model)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        form.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def itemsSelected(self):
        selected = []
        model = self.listView.model()
        i = 0
        while model.item(i):
            if model.item(i).checkState() != QtCore.Qt.Unchecked:
                selected.append(model.item(i).text())
            i += 1
        return selected

    def accept(self) -> None:
        result = self.itemsSelected()
        self.dlgdata.emit(result)
        super().accept()


def askUserValue(param: Parameter):  # noqa: C901
    if param.request == "time":
        value, isok = QtWidgets.QInputDialog.getText(
            None,
            "Enter time",
            param.description,
        )
        try:
            value = ureg.Quantity(value)
            if value.dimensionless:
                # Default to second if no unit is specified
                value = ureg.Quantity(value.magnitude, "s")
            value = value.to_base_units().magnitude
        except (DimensionalityError, UndefinedUnitError, ValueError):
            return None
    elif param.request is str:
        value, isok = QtWidgets.QInputDialog.getText(
            None,
            "Enter value",
            param.description,
        )
    elif param.request is int:
        value, isok = QtWidgets.QInputDialog.getInt(
            None,
            "Enter value",
            param.description,
        )
    elif param.request is float:
        value, isok = QtWidgets.QInputDialog.getDouble(
            None,
            "Enter value",
            param.description,
            decimals=3,
        )
    elif param.request is bool:
        request = ["Yes", "No"]
        tmpvalue, isok = QtWidgets.QInputDialog.getItem(
            None,
            "Enter value",
            param.description,
            request,
            editable=False,
        )
        value = tmpvalue == "Yes"
    elif param.request is datetime:
        dlg = DlgSetDateTime()
        isok = dlg.exec()
        value = dlg.dlgdata
    elif isinstance(param.request, list):
        value, isok = QtWidgets.QInputDialog.getItem(
            None,
            "Choose value",
            param.description,
            param.request,
            editable=False,
        )
    else:
        msg = "Unknown request type"
        raise TypeError(msg)

    if isok:
        return value
    else:
        return None


def userConfirm(question: str, title: str = "") -> bool:
    if not title:
        title = question
    reply = QtWidgets.QMessageBox.question(
        None,
        title,
        question,
        QtWidgets.QMessageBox.Yes,
        QtWidgets.QMessageBox.No,
    )
    return reply == QtWidgets.QMessageBox.Yes


def askFilePath(
    func,
    caption: str,
    filename: str = "",
    folder: str = "",
    filter: str = "",
) -> tuple[pathlib.Path | None, str | None]:
    default = pathlib.Path(folder) if folder else pathlib.Path.home()
    if filename:
        default = pathlib.Path(default, filename)

    fileinfo = func(caption=caption, filter=filter, dir=str(default))
    filepath = fileinfo[0]
    if not filepath:
        # Cancel pressed
        return (None, None)
    filepath = sanitize_filepath(filepath)
    filepath = pathlib.Path(filepath).resolve()
    ext = filepath.suffix[1:]
    return (filepath, ext)


askOpenFilePath = partial(askFilePath, QtWidgets.QFileDialog.getOpenFileName)
askSaveFilePath = partial(askFilePath, QtWidgets.QFileDialog.getSaveFileName)


def askDirPath(caption: str, folder: str = "") -> pathlib.Path | None:
    if not folder:
        folder = str(pathlib.Path.home())

    outdirtmp = QtWidgets.QFileDialog.getExistingDirectory(
        caption=caption,
        dir=str(folder),
    )
    if not outdirtmp:
        # Cancel pressed
        return None
    return pathlib.Path(outdirtmp).resolve()


class DlgIcebergOpen(QtWidgets.QDialog):
    dlgdata = QtCore.Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Open Iceberg Table")
        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.txtNamespace = QtWidgets.QLineEdit("default")
        self.txtCatalogName = QtWidgets.QLineEdit("iceberg_catalog")
        self.txtTable = QtWidgets.QLineEdit()
        self.txtTable.setPlaceholderText("table_name")
        self.txtRowFilter = QtWidgets.QLineEdit()
        self.txtRowFilter.setPlaceholderText("column = 'value'  (optional)")

        form.addRow("Namespace:", self.txtNamespace)
        form.addRow("Catalog name:", self.txtCatalogName)
        form.addRow("Table name:", self.txtTable)
        form.addRow("Row filter:", self.txtRowFilter)
        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config(self) -> None:
        from graphysio.config import load_config

        config = load_config()
        section = config["iceberg"] if "iceberg" in config else {}
        self.txtNamespace.setText(section.get("namespace", "default"))
        self.txtCatalogName.setText(section.get("catalog_name", "iceberg_catalog"))

    def accept(self) -> None:
        result = {
            "catalog_name": self.txtCatalogName.text(),
            "namespace": self.txtNamespace.text(),
            "table": self.txtTable.text(),
            "row_filter": self.txtRowFilter.text(),
        }
        self.dlgdata.emit(result)
        super().accept()


class DlgNewPlotCsv(ui.Ui_NewPlot, QtWidgets.QDialog):
    def __init__(self, filepath, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle(f"Open {filepath.name}")

        self.filepath = filepath
        self.csvrequest = None

        # Attach models to ListViews
        self.lstX = QtGui.QStandardItemModel()
        self.lstY = QtGui.QStandardItemModel()
        self.lstCluster = QtGui.QStandardItemModel()
        self.lstAll = QtGui.QStandardItemModel()

        self.lstVX.setModel(self.lstX)
        self.lstVY.setModel(self.lstY)
        self.lstVCluster.setModel(self.lstCluster)
        self.lstVAll.setModel(self.lstAll)

        # Setup Field Table
        self.lstVAll.verticalHeader().hide()
        self.lstVAll.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch,
        )
        self.lstVAll.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # Connect callbacks
        self.btnLoad.clicked.connect(self.loadCsvFields)
        self.btnOk.clicked.connect(self.loadPlot)
        self.btnCancel.clicked.connect(self.reject)
        self.btnToX.clicked.connect(self.moveToX)
        self.btnToY.clicked.connect(self.moveToY)
        self.btnToCluster.clicked.connect(self.move_to_cluster)
        self.btnRemoveX.clicked.connect(self.delFromX)
        self.btnRemoveY.clicked.connect(self.delFromY)
        self.btnRemoveCluster.clicked.connect(self.delFromCluster)
        self.lstVX.currentIndexChanged.connect(self.xChanged)

        # Guesstimate CSV field and decimal seperators
        delims = self.estimateDelimiters(filepath)
        self.txtSep.setEditText(delims[0])
        self.txtDecimal.setEditText(delims[1])
        self.txtDateTime.setEditText(f"%Y-%m-%d %H:%M:%S{delims[1]}%f")

    # Methods / Callbacks
    def estimateDelimiters(self, filepath):
        encoding = self.txtEncoding.currentText()
        with open(filepath, encoding=encoding) as csvfile:
            seperator = ";" if ";" in next(csvfile) else ","
            decimal = "." if "." in next(csvfile) else ","
        return (seperator, decimal)

    def loadCsvFields(self) -> None:
        filterfunc = lambda f: f
        sep = self.txtSep.currentText()
        if sep == "<tab>":
            sep = "\t"
        elif sep == "<whitespace>":
            sep = " "
            whitespace_pattern = re.compile(r"\s+")
            filterfunc = lambda file: (
                whitespace_pattern.sub(" ", line) for line in file
            )

        # Use the csv module to retrieve csv fields
        for lst in [self.lstAll, self.lstX, self.lstY]:
            lst.clear()
        self.lstAll.setHorizontalHeaderLabels(["Field", "1st Line"])
        encoding = self.txtEncoding.currentText()
        with open(self.filepath, encoding=encoding) as csvfile:
            # Artificially drop n first lines as requested
            for _ in range(self.spnLinedrop.value()):
                next(csvfile)
            csvreader = csv.DictReader(filterfunc(csvfile), delimiter=sep)
            row = next(csvreader)
            for key, value in row.items():
                if key is None:
                    continue
                keyitem = QtGui.QStandardItem(key)
                valueitem = QtGui.QStandardItem(value)
                self.lstAll.appendRow([keyitem, valueitem])
        self.lstAll.sort(0)

    def xChanged(self, _newtext) -> None:
        if self.lstX.rowCount() > 0:
            self.chkGenX.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.chkGenX.setCheckState(QtCore.Qt.Checked)

    def move_to_cluster(self) -> None:
        if self.lstCluster.rowCount() > 0:
            # Only allow one element for Cluster Id.
            return
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.lstCluster.appendRow(row)

    def moveToX(self) -> None:
        if self.lstX.rowCount() > 0:
            # Only allow one element for X.
            return
        selection = self.lstVAll.selectedIndexes()
        rowindex = selection[0].row()
        row = self.lstAll.takeRow(rowindex)
        self.lstX.appendRow(row)

    def moveToY(self) -> None:
        while True:
            selection = self.lstVAll.selectedIndexes()
            if len(selection) < 1:
                break
            rowindex = selection[0].row()
            self.lstY.appendRow(self.lstAll.takeRow(rowindex))

    def delFromCluster(self) -> None:
        if not self.lstCluster.rowCount():
            return
        row = self.lstCluster.takeRow(0)
        self.lstAll.appendRow(row)

    def delFromX(self) -> None:
        if not self.lstX.rowCount():
            return
        row = self.lstX.takeRow(0)
        self.lstAll.appendRow(row)

    def delFromY(self) -> None:
        while True:
            rowindexes = self.lstVY.selectedIndexes()
            if len(rowindexes) < 1:
                break
            row = rowindexes[0].row()
            self.lstAll.appendRow(self.lstY.takeRow(row))

    def loadPlot(self) -> None:
        from graphysio.readdata.csv import CsvRequest

        yRows = [i.text() for i in self.lstY.findItems("", QtCore.Qt.MatchContains)]
        xRows = [i.text() for i in self.lstX.findItems("", QtCore.Qt.MatchContains)]
        cRows = [
            i.text() for i in self.lstCluster.findItems("", QtCore.Qt.MatchContains)
        ]

        seperator = self.txtSep.currentText()
        if seperator == "<tab>":
            seperator = "\t"
        elif seperator == "<whitespace>":
            seperator = r"\s+"

        try:
            dtfield = xRows[0]
        except IndexError:
            dtfield = None

        try:
            cid = cRows[0]
        except IndexError:
            cid = None

        filterexpr = self.txtFilter.text().strip()
        if not filterexpr:
            filterexpr = None

        req = CsvRequest(
            filepath=self.filepath,
            seperator=seperator,
            decimal=self.txtDecimal.currentText(),
            dtfield=dtfield,
            yfields=yRows,
            datetime_format=self.txtDateTime.currentText(),
            droplines=self.spnLinedrop.value(),
            generatex=self.chkGenX.isChecked(),
            clusterid=cid,
            timezone=self.txtTimezone.currentText(),
            encoding=self.txtEncoding.currentText(),
            samplerate=self.spnFs.value(),
            filterexpr=filterexpr,
        )

        self.csvrequest = req
        self.accept()


# --- Desktop adapter: render a reader's Qt-free ParamSpec schema with Qt dialogs ---

_KIND_TO_REQUEST = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "time": "time",
    "datetime": datetime,
}


def _multichoice_qt(spec: ParamSpec):
    dlg = DlgListChoice(list(spec.choices or []), "Choose", spec.label)
    if dlg.exec():
        return dlg.itemsSelected()
    return None


def ask_params_qt(params: list[ParamSpec]):
    """Render a list of ParamSpec with Qt dialogs; return answers or None if cancelled.

    Cancelling a *required* param aborts the whole gather (returns None); optional
    params left blank are stored as None.
    """
    answers: dict = {}
    for p in params:
        if p.kind == "multichoice":
            value = _multichoice_qt(p)
            if value is None:
                return None
        elif p.kind == "choice":
            value = askUserValue(Parameter(p.label, list(p.choices or [])))
            if value is None and p.required:
                return None
        else:
            value = askUserValue(Parameter(p.label, _KIND_TO_REQUEST[p.kind]))
            if value is None and p.required:
                return None
        answers[p.name] = value
    return answers


def drive_reader_qt(reader) -> bool:
    """Configure a reader's userdata via Qt, returning True if ready, False if cancelled.

    CSV and DWC keep their bespoke rich dialogs; every other reader is driven
    generically through its ``get_params`` schema.
    """
    from graphysio.readdata.csv import CsvReader
    from graphysio.readdata.dwc import DwcReader

    if isinstance(reader, CsvReader):
        dlg = DlgNewPlotCsv(pathlib.Path(reader.userdata["filepath"]))
        if dlg.exec() and dlg.csvrequest is not None:
            reader.set_data({"csvrequest": dlg.csvrequest})
            return True
        return False

    if isinstance(reader, DwcReader):
        import dwclib

        captured: dict = {}
        dlg = DlgDWCOpen(dwclib)
        dlg.dlgdata.connect(captured.update)
        if dlg.exec() and captured:
            reader.set_data(captured)
            return True
        return False

    return gather(reader, ask_params_qt)


def loadmodule() -> None:
    defaultdir = os.path.expanduser("~")
    filepath, _ = askOpenFilePath(
        "Import module",
        folder=defaultdir,
        filter="Python files (*.py)",
    )
    if not filepath:
        return

    bcbak = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("graphysio.plugin", filepath)
        foo = importlib.util.module_from_spec(spec)
        sys.modules["graphysio.plugin"] = foo
        spec.loader.exec_module(foo)
    finally:
        sys.dont_write_bytecode = bcbak
