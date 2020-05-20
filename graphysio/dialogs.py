from typing import Optional
from datetime import datetime
import os
import pathlib
from functools import partial

from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from graphysio import ui
from graphysio.algorithms import filters
from graphysio.utils import sanitize_filepath
from graphysio.structures import CycleId

ureg = UnitRegistry()


class DlgCycleDetection(ui.Ui_CycleDetection, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

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
            combo.addItems([ft.value for ft in CycleId])
            curveitem = QtGui.QTableWidgetItem(curvename)

            self.table.insertRow(n)
            self.table.setItem(n, 0, curveitem)
            self.table.setCellWidget(n, 1, combo)
            self.choices[curvename] = combo

        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    def accept(self):
        result = {curve: combo.currentText() for (curve, combo) in self.choices.items()}
        self.dlgdata.emit(result)
        super().accept()


class DlgFilter(ui.Ui_Filter, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, filterfeet=False):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.choices = {}

        plotframe = self.parent().tabWidget.currentWidget()
        if not plotframe:
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
            fillTable(curves, 'curve', filters.FeetFilters)
        else:
            fillTable(curves, 'curve', filters.Filters)

        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    def accept(self):
        curvefilters = {}
        for itemname, value in self.choices.items():
            combo, itemtype = value
            curvefilters[itemname] = combo.currentText()
        createnew = self.chkNewcurve.checkState() > QtCore.Qt.Unchecked
        result = (createnew, curvefilters)
        self.dlgdata.emit(result)
        super().accept()


class DlgSetupPULoop(ui.Ui_SetupPULoop, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

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

    def accept(self):
        uname = self.comboU.currentText()
        pname = self.comboP.currentText()
        result = (uname, pname)
        self.dlgdata.emit(result)
        super().accept()


class DlgPeriodExport(ui.Ui_PeriodExport, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

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
        filepath = QtGui.QFileDialog.getSaveFileName(
            caption="Export to",
            filter="CSV files (*.csv *.dat)",
            options=QtGui.QFileDialog.DontConfirmOverwrite,
            directory=self.dircache,
        )
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if filepath:
            self.txtFile.setText(filepath)
            self.dircache = os.path.dirname(filepath)

    def accept(self):
        patient = self.txtPatient.text()
        comment = self.txtComment.text()
        periodname = self.txtPeriod.currentText()
        filepath = self.txtFile.text()
        result = (patient, comment, periodname, filepath)
        self.dlgdata.emit(result)
        super().accept()


class DlgCurveSelection(ui.Ui_CurveSelection, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, visible=[], hidden=[], parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

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

    def openProperties(self):
        selected = self.lstCurves.selectedItems()
        try:
            curvename = selected[0].text()
        except IndexError:
            return
        curve = self.curvehash[curvename]

        def cb(resultdict):
            self.curveproperties[curve] = resultdict

        dlg = DlgCurveProperties(curve)
        dlg.dlgdata.connect(cb)
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

    def accept(self):
        items = self.lstCurves.findItems("", QtCore.Qt.MatchContains)
        ischecked = lambda item: not (item.checkState() == QtCore.Qt.Unchecked)
        checked = list(filter(ischecked, items))
        visible = set([self.curvehash[item.text()] for item in checked])
        result = (visible, self.curveproperties)
        self.dlgdata.emit(result)
        super().accept()


class DlgCurveProperties(ui.Ui_CurveProperties, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

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
        self.btnColor.setStyleSheet(f'background-color: {color.name()}')
        self.lblSamplerate.setText(str(curve.samplerate))

    def ok(self):
        symbol = self.cmbSymbol.currentText().lower()
        symbol = None if symbol == 'none' else symbol

        connect = str(self.cmbConnect.currentText().lower())
        connect = [0] if connect == 'none' else connect

        result = {
            'name': self.txtName.text(),
            'connect': connect,
            'symbol': symbol,
            'width': self.spnWidth.value(),
            'color': self.color,
        }
        self.dlgdata.emit(result)
        self.accept()

    def chooseColor(self):
        color = QtGui.QColorDialog.getColor()
        if not color.isValid():
            return
        self.color = color
        self.btnColor.setStyleSheet(f'background-color: {color.name()}')


class DlgSetDateTime(ui.Ui_SetDateTime, QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, prevdatetime=None):
        super().__init__(parent=parent)
        self.setupUi(self)

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
        timestamp = dt.toMSecsSinceEpoch() * 1e6
        self.dlgdata.emit(timestamp)
        self.accept()


class DlgCurveAlgebra(QtWidgets.QDialog):
    dlgdata = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, curvecorr={}):
        super().__init__(parent=parent)
        self.setupUi(curvecorr)

    def setupUi(self, curvecorr):
        vstack = QtWidgets.QVBoxLayout(self)

        self.lbl = QtWidgets.QLabel('Enter formula for new curve:')
        vstack.addWidget(self.lbl)

        self.formula = QtWidgets.QLineEdit('a^2 + log(2*b)')
        vstack.addWidget(self.formula)

        curveslbl = '\n'.join([f'{x}: {y}' for x, y in curvecorr.items()])
        self.curveletters = QtWidgets.QLabel(curveslbl)
        vstack.addWidget(self.curveletters)

        self.buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        vstack.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.setLayout(vstack)

    def accept(self):
        result = self.formula.text()
        self.dlgdata.emit(result)
        super().accept()


def askUserValue(param):
    if param.request == 'time':
        value, isok = QtGui.QInputDialog.getText(None, 'Enter time', param.description)
        try:
            value = ureg.Quantity(value)
            if value.dimensionless:
                # Default to second if no unit is specified
                value = ureg.Quantity(value.magnitude, 's')
            value = value.to_base_units().magnitude
        except (DimensionalityError, UndefinedUnitError, ValueError):
            return None
    elif param.request is str:
        value, isok = QtGui.QInputDialog.getText(None, 'Enter value', param.description)
    elif param.request is int:
        value, isok = QtGui.QInputDialog.getInt(None, 'Enter value', param.description)
    elif param.request is float:
        value, isok = QtGui.QInputDialog.getDouble(
            None, 'Enter value', param.description, decimals=3
        )
    elif param.request is bool:
        request = ['Yes', 'No']
        tmpvalue, isok = QtGui.QInputDialog.getItem(
            None, 'Enter value', param.description, request, editable=False
        )
        value = tmpvalue == 'Yes'
    elif param.request is datetime:
        dlg = DlgSetDateTime()
        isok = dlg.exec_()
        value = dlg.result
    elif type(param.request) is list:
        value, isok = QtGui.QInputDialog.getItem(
            None, 'Choose value', param.description, param.request, editable=False
        )
    else:
        raise TypeError("Unknown request type")

    if isok:
        return value
    else:
        return None


def userConfirm(question: str, title: str = '') -> bool:
    if not title:
        title = question
    reply = QtGui.QMessageBox.question(
        None, title, question, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No
    )
    confirmed = reply == QtGui.QMessageBox.Yes
    return confirmed


def askFilePath(
    func,
    caption: str,
    filename: str = '',
    folder: str = '',
    filter: str = "CSV files (*.csv *.dat)",
) -> Optional[pathlib.Path]:
    if not folder:
        default = pathlib.Path.home()
    else:
        default = pathlib.Path(folder)

    if filename:
        default = pathlib.Path(default, filename)

    fileinfo = func(caption=caption, filter=filter, directory=str(default))
    filepath = fileinfo[0]
    if not filepath:
        # Cancel pressed
        return (None, None)
    filepath = sanitize_filepath(filepath)
    filepath = pathlib.Path(filepath).resolve()
    ext = filepath.suffix[1:]
    return (filepath, ext)


askOpenFilePath = partial(askFilePath, QtGui.QFileDialog.getOpenFileName)
askSaveFilePath = partial(askFilePath, QtGui.QFileDialog.getSaveFileName)


def askDirPath(caption: str, folder: str = '') -> Optional[pathlib.Path]:
    if not folder:
        folder = str(pathlib.Path.home())

    outdirtmp = QtGui.QFileDialog.getExistingDirectory(
        caption=caption, directory=folder
    )
    if not outdirtmp:
        # Cancel pressed
        return None
    return pathlib.Path(outdirtmp).resolve()
