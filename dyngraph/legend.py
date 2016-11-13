import pyqtgraph as pg
__all__ = ['MyLegendItem']

class MyLegendItem(pg.LegendItem):
    def __init__(self, size=None, offset=(40,5)):
        super().__init__(size, offset)
        
    def paint(self, p, *args):
        p.setPen(pg.mkPen(0,0,0,255))
        p.setBrush(pg.mkBrush(255,255,255,255))
        p.drawRect(self.boundingRect())
