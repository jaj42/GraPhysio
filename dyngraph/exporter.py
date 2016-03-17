from __future__ import print_function

class Exporter():
    def init(self, plotinfo, viewbox):
        self.plotinfo = plotinfo
        self.viewbox = viewbox
        datalen = plotinfo.plotdata.shape[0] 
        vbrange = viewbox.viewRange()
        xmin,xmax = vbrange[0]
        if xmin <= 0: xmin = 0
        if xmax >= datalen: xmax = datalen
        self.xmax, self.xmin = xmax, xmin

    def tocsv(self, filename):
        data = self.plotinfo.plotdata.iloc[self.xmin : self.xmax]
        data.to_csv(filename, index = False)
