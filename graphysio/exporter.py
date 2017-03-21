import os, csv

import numpy as np
import pandas as pd

from pyqtgraph.Qt import QtGui

from graphysio import utils
from graphysio.dialogs import DlgPeriodExport

class TsExporter():
    periodfields = ['patient', 'begin', 'end', 'periodid', 'comment']

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.outdir = os.path.expanduser('~')

    def seriestocsv(self):
        filename = "{}-subset.csv".format(self.name)
        defaultpath = os.path.join(self.outdir, filename)
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     directory = defaultpath)
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if not filepath:
            return

        self.outdir = os.path.dirname(filepath)
        xmin, xmax = self.parent.vbrange
        series = [curve.series for curve in self.parent.curves.values()]
        data = pd.concat(series, axis=1).sort_index()
        data['datetime'] = pd.to_datetime(data.index, unit = 'ns')
        data = data.ix[xmin:xmax]
        data.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f")

    def periodstocsv(self):
        xmin, xmax = self.parent.vbrange
        dlg = DlgPeriodExport(begin   = xmin,
                              end     = xmax,
                              patient = self.name,
                              directory = self.outdir)
        if not dlg.exec_():
            return
        self.name = dlg.patient
        self.outdir = os.path.dirname(dlg.filepath)

        if os.path.exists(dlg.filepath):
            fileappend = True
        else:
            fileappend = False

        with open(dlg.filepath, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.periodfields, quoting=csv.QUOTE_MINIMAL)
            if not fileappend: writer.writeheader()
            writer.writerow({'patient'  : dlg.patient,
                             'begin'    : xmin,
                             'end'      : xmax,
                             'periodid' : dlg.periodname,
                             'comment'  : dlg.comment})

    def cyclepointstocsv(self):
        filename = "{}-feet.csv".format(self.name)
        defaultpath = os.path.join(self.outdir, filename)
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     directory = defaultpath)
        # PyQt5 API change
        if type(filepath) is not str:
            filepath = filepath[0]

        if not filepath: return
        self.outdir = os.path.dirname(filepath)
        feetitems = self.parent.feetitems.values()
        feetidx = [pd.Series(item.feet.index) for item in feetitems]
        feetnames = [item.feet.name for item in feetitems]
        df = pd.concat(feetidx, axis=1, keys=feetnames)
        df.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f")

class PuExporter():
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.outdir = os.path.expanduser('~')

    def exportloops(self):
        outdirtmp = QtGui.QFileDialog.getExistingDirectory(caption = "Export to",
                                                             directory = self.outdir)
        if outdirtmp:
            self.outdir = outdirtmp
        self.writetable()
        self.writeloops()

    def writetable(self):
        if self.outdir is None:
            return
        data = []
        for loop in self.parent.loops:
            alpha, beta, gamma = loop.angles
            tmpdict = {'alpha' : alpha, 'beta' : beta, 'gamma' : gamma}
            data.append(tmpdict)
        df = pd.DataFrame(data)
        df.index += 1
        filename = "{}-loopdata.csv".format(self.name)
        outfile = os.path.join(self.outdir, filename)
        df.to_csv(outfile)

    def writeloops(self):
        if self.outdir is None:
            return
        for n, loop in enumerate(self.parent.loops):
            df = pd.DataFrame({'u' : loop.u, 'p' : loop.p})
            filename = "{}-{}.csv".format(self.name, n)
            outfile = os.path.join(self.outdir, filename)
            df.to_csv(outfile)
