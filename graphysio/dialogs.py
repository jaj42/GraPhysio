import os
import pathlib
from datetime import datetime
from functools import partial
from typing import Optional

from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from graphysio import ui
from graphysio.algorithms import filters
from graphysio.utils import sanitize_filepath
from graphysio.structures import CycleId

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
        configfile, _ = askOpenFilePath('Import dwclib config file')
        with open(configfile,'r') as fd:
            c = fd.read()
        self.dwc_update_config(c)

    def accept(self) -> None:
        data = {}
        data["patientid"] = self.patient.name
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


def askUserValue(param):  # noqa: C901
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
) -> Optional[pathlib.Path]:
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


def askDirPath(caption: str, folder: str = "") -> Optional[pathlib.Path]:
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
