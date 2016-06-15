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
        self.dircache = ""
        self.patientcache = ""

    def updaterange(self):
        vbrange = self.viewbox.viewRange()
        xmin,xmax = vbrange[0]
        self.xmin, self.xmax = xmin, xmax

    def tocsv(self):
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     directory = self.dircache)
        if not filepath: return
        self.dircache = os.path.dirname(filepath)
        self.updaterange()
        data = self.plotdescr.data.ix[self.xmin : self.xmax]
        datanona = data.dropna(how = 'all', subset = self.plotdescr.yfields)
        datanona.to_csv(filepath, datetime_format = "%Y-%m-%d %H:%M:%S.%f")

    def toperiodcsv(self):
        self.updaterange()
        if not self.patientcache:
            self.patientcache = self.plotdescr.name
        dlg = DlgPeriodExport(begin   = self.xmin,
                              end     = self.xmax,
                              patient = self.patientcache,
                              directory = self.dircache)
        if not dlg.exec_(): return
        self.patientcache = dlg.patient
        self.dircache = os.path.dirname(dlg.filepath)

        if os.path.exists(dlg.filepath):
            fileappend = True
        else:
            fileappend = False

        with open(dlg.filepath, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.periodfields, quoting=csv.QUOTE_MINIMAL)
            if not fileappend: writer.writeheader()
            writer.writerow({'patient'  : dlg.patient,
                             'begin'    : self.xmin,
                             'end'      : self.xmax,
                             'periodid' : dlg.periodname,
                             'comment'  : dlg.comment})

class DlgPeriodExport(QtGui.QDialog, Ui_PeriodExport):
    def __init__(self, begin, end, patient="", directory="", parent=None):
        super(DlgPeriodExport, self).__init__(parent=parent)
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
