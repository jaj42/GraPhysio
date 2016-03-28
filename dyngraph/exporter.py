from __future__ import print_function
import pandas as pd

class Exporter():
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

    def tocsv(self, filename):
        self.updaterange()
        data = self.plotdescr.data.ix[self.xmin : self.xmax]
        datanona = data.dropna(how = 'all', subset = self.plotdescr.yfields)
        datanona.to_csv(filename, datetime_format = "%Y-%m-%d %H:%M:%S.%f")
