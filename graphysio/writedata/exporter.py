import os
import csv
from itertools import zip_longest

import pandas as pd

from graphysio.dialogs import DlgPeriodExport, askDirPath, askSaveFilePath
from graphysio.utils import sanitize_filename
from graphysio import writedata

file_filters = ';;'.join(
    [f'{ext.upper()} files (*.{ext})' for ext in writedata.curve_writers]
)


class TsExporter:
    periodfields = ['patient', 'begin', 'end', 'periodid', 'comment']

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        try:
            self.outdir = parent.properties['dircache']
        except KeyError:
            self.outdir = os.path.expanduser('~')

    def curves(self) -> None:
        filepath, ext = askSaveFilePath(
            'Export to', f'{self.name}.csv', self.outdir, filter=file_filters
        )
        if filepath is None:
            return
        self.outdir = os.path.dirname(filepath)
        curves = list(self.parent.curves.values())
        export_func = writedata.curve_writers[ext]
        export_func(curves, filepath)

    def periods(self):
        xmin, xmax = self.parent.vbrange
        dlg = DlgPeriodExport(
            begin=xmin, end=xmax, patient=self.name, directory=self.outdir
        )

        def cb(result):
            patient, comment, periodname, filepath = result
            self.name = patient
            self.outdir = os.path.dirname(filepath)

            with open(filepath, 'a', newline='') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=self.periodfields, quoting=csv.QUOTE_MINIMAL
                )
                if not os.path.exists(filepath):
                    writer.writeheader()
                writer.writerow(
                    {
                        'patient': patient,
                        'begin': xmin,
                        'end': xmax,
                        'periodid': periodname,
                        'comment': comment,
                    }
                )

        dlg.dlgdata.connect(cb)
        dlg.exec_()

    def cycles(self) -> None:
        outdir = askDirPath("Export to", self.outdir)
        if outdir is None:
            # Cancel pressed
            return

        # Some non trivial manipulations to get the cycles from all
        # curves, then reorganize to group by the n-th cycle from each
        # curve and put those cycles into a dataframe for export.
        def getCurveCycles(curve):
            cycleIdx = curve.getCycleIndices()
            cycles = (curve.series.loc[b : b + d] for b, d in zip(*cycleIdx))
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
            df['datetime'] = pd.to_datetime(df.index, unit='ns')

            filename = sanitize_filename(f'{self.name}-{n+1}.csv')
            filepath = os.path.join(self.outdir, filename)
            df.to_csv(
                filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens'
            )

    def cyclepoints(self) -> None:
        filepath, _ = askSaveFilePath('Export to', f'{self.name}-feet.csv', self.outdir)
        if filepath is None:
            # Cancel pressed
            return
        self.outdir = os.path.dirname(filepath)

        feetseries = []
        for c in self.parent.curves.values():
            for k, v in c.feetitem.indices.items():
                feetseries.append(pd.Series(v, name=f'{c.name()}-{k}'))
        df = pd.concat(feetseries, axis=1)
        df.to_csv(filepath, index_label='idx')


class PuExporter:
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        try:
            self.outdir = parent.properties['dircache']
        except KeyError:
            self.outdir = os.path.expanduser('~')

    def exportloops(self):
        outdir = askDirPath('Export to', self.outdir)
        if outdir is None:
            # Cancel pressed
            return
        self.outdir = outdir
        self.writetable()
        self.writeloops()

    def writetable(self):
        data = []
        for loop in self.parent.loops:
            alpha, beta, gala = loop.angles
            delay = loop.offset / 1e6
            tmpdict = {'alpha': alpha, 'beta': beta, 'gala': gala, 'delay': delay}
            data.append(tmpdict)
        df = pd.DataFrame(data)
        df.index += 1
        filename = sanitize_filename(f'{self.name}-loopdata.csv')
        filepath = os.path.join(self.outdir, filename)
        df.to_csv(filepath, index_label='idx')

    def writeloops(self):
        for n, loop in enumerate(self.parent.loops):
            df = loop.df
            filename = sanitize_filename(f'{self.name}-{n+1}.csv')
            filepath = os.path.join(self.outdir, filename)
            df['datetime'] = pd.to_datetime(df.index, unit='ns')
            df.to_csv(
                filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens'
            )


class POIExporter:
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        try:
            self.outdir = parent.properties['dircache']
        except KeyError:
            self.outdir = os.path.expanduser('~')

    def poi(self):
        filepath, _ = askSaveFilePath('Export to', f'{self.name}-poi.csv', self.outdir)
        if filepath is None:
            # Cancel pressed
            return
        self.outdir = os.path.dirname(filepath)

        srcseries = self.parent.curve.series
        poiidx = self.parent.curve.feetitem.indices[self.parent.pointkey]
        pois = srcseries[poiidx.dropna()].rename('poi')
        sers = [srcseries, pois]
        df = pd.concat(sers, axis=1, keys=[s.name for s in sers])
        df['datetime'] = pd.to_datetime(df.index, unit='ns')
        df.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label='timens')
