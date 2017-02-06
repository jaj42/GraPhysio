import os
import time

from enum import Enum
from itertools import cycle

import pandas as pd
from pyqtgraph.Qt import QtGui

class FootType(Enum):
    none     = 'None'
    pressure = 'Pressure'
    velocity = 'Velocity'

class FilterType(Enum):
    none      = 'None'
    tfcombi   = 'TF Combi'
    tfsphygmo = 'TF Sphygmo'

class PlotDescription():
    def __init__(self, filepath  = "",
                       seperator = ",",
                       decimal   = ".",
                       xfield  = None,
                       yfields = [],
                       xisdate = False,
                       droplines = 0,
                       loadall = False,
                       samplerate = None,
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filepath = filepath
        self.seperator = seperator
        self.decimal = decimal
        self.xfield  = xfield
        self.yfields = yfields
        self.loadall = loadall
        self.datetime_format = datetime_format
        self.xisdate = xisdate
        self.droplines = droplines
        self.samplerate = samplerate
        self.data = None

    @property
    def fields(self):
        xfields = [] if self.xfield is None else [self.xfield]
        return xfields + self.yfields

    @property
    def datefield(self):
        if not self.xisdate: return False
        return self.xfield if self.xfield is not None else False

    @property
    def xvalues(self):
        if not self.xisdate and self.xfield is not None:
            values = self.data[self.xfield].values
            return values.astype(np.float64)
        else:
            return None

    @property
    def name(self):
        name, _ = os.path.splitext(os.path.basename(self.filepath))
        return name

    @property
    def folder(self):
        folder = os.path.dirname(self.filepath)
        return folder


# https://stackoverflow.com/questions/5478351/python-time-measure-function
def Timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print ('{} function took {:.3f} ms'.format(f.__name__, (time2 - time1) * 1000))
        return ret
    return wrap

def Colors():
    qtcolors = [
        QtGui.QColor(0, 114, 189),
        QtGui.QColor(217, 83, 25),
        QtGui.QColor(237, 177, 32),
        QtGui.QColor(126, 47, 142),
        QtGui.QColor(119, 172, 48),
        QtGui.QColor(77, 190, 238),
        QtGui.QColor(162, 20, 47)
    ]
    return cycle(qtcolors)

def getvbrange(plotwidget):
    vbrange = plotwidget.vb.viewRange()
    xmin, xmax = vbrange[0]
    if plotwidget.plotdata.xisdate:
        xmin = pd.to_datetime(xmin, unit='ns')
        xmax = pd.to_datetime(xmax, unit='ns')
    else:
        xmin, xmax = int(xmin), int(xmax)
    return (xmin, xmax)
