import os, csv
from itertools import zip_longest

import pandas as pd

from pyqtgraph.Qt import QtGui

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
        if type(filepath) is not str:
            # PyQt5 API change
            filepath = filepath[0]
        if not filepath:
            # Cancel pressed
            return
        filepath = os.path.normpath(filepath)
        self.outdir = os.path.dirname(filepath)
        xmin, xmax = self.parent.vbrange
        series = [curve.series[~curve.series.index.duplicated()] for curve in self.parent.curves.values()]
        data = pd.concat(series, axis=1).sort_index()
        data['datetime'] = pd.to_datetime(data.index, unit = 'ns')
        data = data.loc[xmin:xmax]
        data.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens')

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

        with open(dlg.filepath, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.periodfields, quoting=csv.QUOTE_MINIMAL)
            if not os.path.exists(dlg.filepath):
                writer.writeheader()
            writer.writerow({'patient'  : dlg.patient,
                             'begin'    : xmin,
                             'end'      : xmax,
                             'periodid' : dlg.periodname,
                             'comment'  : dlg.comment})

    def cyclestocsv(self):
        outdirtmp = QtGui.QFileDialog.getExistingDirectory(caption = "Export to",
                                                           directory = self.outdir)
        if not outdirtmp:
            # Cancel pressed
            return
        self.outdir = os.path.normpath(outdirtmp)

        # Some non trivial manipulations to get the cycles from all
        # curves, then reorganize to group by the n-th cycle from each
        # curve and put those cycles into a dataframe for export.
        def getCurveCycles(curve):
            cycleIdx = curve.getCycleIndices()
            cycles = (curve.series.loc[b:b+d] for b, d in zip(*cycleIdx))
            return cycles

        curves = self.parent.curves.values()
        allByCurve = (getCurveCycles(curve) for curve in curves)
        allByCycle = zip_longest(*allByCurve)

        for n, cycle in enumerate(allByCycle):
            idxstart = None
            for s in cycle:
                # Make all series start at the same point
                if s is None or len(s) < 1:
                    continue
                if idxstart is None:
                    idxstart = s.index[0]
                idxdelta = s.index[0] - idxstart
                s.index -= idxdelta
            df = pd.concat(cycle, axis=1)
            df['datetime'] = pd.to_datetime(df.index, unit = 'ns')

            filename = "{}-{}.csv".format(self.name, n+1)
            filepath = os.path.join(self.outdir, filename)
            df.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens')

    def cyclepointstocsv(self):
        filename = "{}-feet.csv".format(self.name)
        defaultpath = os.path.join(self.outdir, filename)
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     directory = defaultpath)
        if type(filepath) is not str:
            # PyQt5 API change
            filepath = filepath[0]
        if not filepath:
            # Cancel pressed
            return
        filepath = os.path.normpath(filepath)
        self.outdir = os.path.dirname(filepath)

        starts = [curve.feet['start'] for curve in self.parent.curves.values() if 'start' in curve.feet]
        feetidx = [pd.Series(item.index) for item in starts]
        feetnames = [item.name for item in starts]
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
        if not outdirtmp:
            # Cancel pressed
            return
        self.outdir = os.path.normpath(outdirtmp)
        self.writetable()
        self.writeloops()

    def writetable(self):
        data = []
        for loop in self.parent.loops:
            alpha, beta, gala = loop.angles
            delay = loop.offset / 1e6
            tmpdict = {'alpha' : alpha, 'beta' : beta, 'gala' : gala, 'delay' : delay}
            data.append(tmpdict)
        df = pd.DataFrame(data)
        df.index += 1
        filename = "{}-loopdata.csv".format(self.name)
        filepath = os.path.join(self.outdir, filename)
        df.to_csv(filepath, index_label='idx')

    def writeloops(self):
        for n, loop in enumerate(self.parent.loops):
            df = loop.df
            filename = "{}-{}.csv".format(self.name, n+1)
            filepath = os.path.join(self.outdir, filename)
            df['datetime'] = pd.to_datetime(df.index, unit = 'ns')
            df.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens')

class POIExporter():
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.outdir = os.path.expanduser('~')

    def poitocsv(self):
        filename = "{}-poi.csv".format(self.name)
        defaultpath = os.path.join(self.outdir, filename)
        filepath = QtGui.QFileDialog.getSaveFileName(caption = "Export to",
                                                     filter  = "CSV files (*.csv *.dat)",
                                                     directory = defaultpath)
        if type(filepath) is not str:
            # PyQt5 API change
            filepath = filepath[0]
        if not filepath:
            # Cancel pressed
            return
        filepath = os.path.normpath(filepath)
        self.outdir = os.path.dirname(filepath)

        srcseries = self.parent.curve.series
        poiidx = self.parent.curve.feetitem.indices[self.parent.pointkey]
        pois = srcseries[poiidx.dropna()].rename('poi')
        sers = [srcseries, pois]
        df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
        df['datetime'] = pd.to_datetime(df.index, unit = 'ns')
        df.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens')
