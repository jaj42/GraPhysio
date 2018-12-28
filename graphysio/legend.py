import pyqtgraph as pg

__all__ = ['LegendItem']

class LegendItem(pg.LegendItem):
    def __init__(self, size=None, offset=(40,5)):
        super().__init__(size, offset)

    def paint(self, p, *args):
        p.setPen(pg.mkPen(0,0,0,255))
        p.setBrush(pg.mkBrush(255,255,255,255))
        p.drawRect(self.boundingRect())

    def addItem(self, item, name):
        # Make the line width bigger
        pen = pg.mkPen(item.opts['pen'], width=2)
        newitem = pg.PlotDataItem(pen=pen)
        super().addItem(newitem, name)
