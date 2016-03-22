from __future__ import print_function

class Exporter():
    def __init__(self, plotinfo, viewbox):
        self.plotinfo = plotinfo
        self.viewbox = viewbox

    def updaterange(self):
        datalen = self.plotinfo.plotdata.shape[0] - 1
        vbrange = self.viewbox.viewRange()
        xmin,xmax = vbrange[0]
        if xmin <= 0: xmin = 0
        if xmax >= datalen: xmax = datalen
        self.xmax, self.xmin = int(xmax), int(xmin)

    def tocsv(self, filename):
        self.updaterange()
        data = self.plotinfo.plotdata.iloc[self.xmin : self.xmax]
        datanona = data.dropna(how = 'all', subset = self.plotinfo.fields)
        datanona.to_csv(filename, index = False)
