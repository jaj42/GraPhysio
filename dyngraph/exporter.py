from __future__ import print_function
import os, csv
import pandas as pd

from PyQt4 import QtGui

from periodexport_ui import Ui_PeriodExport

class Exporter():
    periodfields = ['patient', 'begin', 'end', 'periodid', 'comment']

    def __init__(self, plotdescr, viewbox):
        self.plotdescr = plotdescr
        self.viewbox = viewbox

    def updaterange(self):
        vbrange = self.viewbox.viewRange()
        xmin,xmax = vbrange[0]
        if self.plotdescr.xisdate:
            self.xmin = pd.to_datetime(xmin, unit='ns')
            self.xmax = pd.to_datetime(xmax, unit='ns')
        else:
            self.xmin, self.xmax = int(xmin), int(xmax)

    def tocsv(self):
        filename = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)")
        if not filename: return
        self.updaterange()
        data = self.plotdescr.data.ix[self.xmin : self.xmax]
        datanona = data.dropna(how = 'all', subset = self.plotdescr.yfields)
        datanona.to_csv(filename, datetime_format = "%Y-%m-%d %H:%M:%S.%f")

    def toperiodcsv(self):
        self.updaterange()
        dlg = DlgPeriodExport(begin   = self.xmin,
                              end     = self.xmax,
                              patient = self.plotdescr.name)
        if not dlg.exec_(): return

        if os.path.exists(dlg.filepath):
            fileappend = True
        else:
            fileappend = False

        with open(dlg.filepath, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.periodfields, quoting=csv.QUOTE_MINIMAL)
            if not fileappend: writer.writeheader()
            writer.writerow({'patient'  : dlg.patient,
                             'begin'    : self.xmin,
                             'end'      : self.xmax,
                             'periodid' : dlg.periodname,
                             'comment'  : dlg.comment})

class DlgPeriodExport(QtGui.QDialog, Ui_PeriodExport):
    def __init__(self, begin, end, patient="", parent=None):
        super(DlgPeriodExport, self).__init__(parent=parent)
        self.setupUi(self)

        self.lblPeriodStart.setText(str(begin))
        self.lblPeriodStop.setText(str(end))
        self.txtPatient.setText(patient)

        self.btnOk.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        self.btnBrowse.clicked.connect(self.selectFile)

    def selectFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     options = QtGui.QFileDialog.DontConfirmOverwrite)
        if filename: self.txtFile.setText(filename)

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
