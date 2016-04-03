from __future__ import print_function
import os, csv
import pandas as pd

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
        dlg = DlgNewPlot(begin   = self.xmin,
                         end     = self.xmax,
                         patient = self.plotdescr.name)
        if not dlgNewplot.exec_(): return

        if os.path.exists(dlg.filename):
            fileappend = True
        else:
            fileappend = False

        with open(dlg.filename, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=periodfields, quoting=csv.QUOTE_MINIMAL)
            if not fileappend: writer.writeheader()
            writer.writerow({'patient'  : dlg.patient,
                             'begin'    : self.xmin,
                             'end'      : self.xmax,
                             'periodid' : dlg.periodname,
                             'comment'  : dlg.comment})

class DlgPeriodExport(QtGui.QDialog, Ui_ExportPeriod):
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
                                                     filter  = "CSV files (*.csv *.dat)")
        if filename: self.txtFile.setText(filename)

    @property
    def filename(self):
        return self.txtFile.currentText()

    @property
    def patient(self):
        return self.txtPatient.currentText()

    @property
    def comment(self):
        return self.txtComment.currentText()

    @property
    def periodname(self):
        return self.txtPeriod.currentText()

