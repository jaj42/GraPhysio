from pyqtgraph.Qt import QtGui, QtCore

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from numpy import arange, sin, pi

mplwidget = None

class FigureCanvas(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setParent(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.updateGeometry()

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        clearAction = menu.addAction("Clear content")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == clearAction:
            self.axes.cla()
