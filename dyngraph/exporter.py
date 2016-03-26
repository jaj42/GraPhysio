from __future__ import print_function
import pandas as pd

class Exporter():
    def __init__(self, plotinfo, viewbox):
        self.plotinfo = plotinfo
        self.viewbox = viewbox

    def updaterange(self):
        vbrange = self.viewbox.viewRange()
        xmin,xmax = vbrange[0]
        if self.plotinfo.xisdate:
            self.xmin = pd.to_datetime(xmin)
            self.xmax = pd.to_datetime(xmax)
        else:
            self.xmin, self.xmax = int(xmin), int(xmax)

    def tocsv(self, filename):
        self.updaterange()
        data = self.plotinfo.plotdata.ix[self.xmin : self.xmax]
        datanona = data.dropna(how = 'all', subset = self.plotinfo.yfields)
        datanona.to_csv(filename, index = False)
