import os
import sys
import time
import imp

from enum import Enum
from itertools import cycle

import pandas as pd
from pyqtgraph.Qt import QtGui, loadUiType

class FootType(Enum):
    none     = 'None'
    pressure = 'Pressure'
    velocity = 'Velocity'

class CsvRequest():
    def __init__(self, filepath  = "",
                       seperator = ",",
                       decimal   = ".",
                       dtfield  = None,
                       yfields = [],
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f",
                       droplines = 0,
                       generatex = False,
                       samplerate = None):
        self.filepath = filepath
        self.seperator = seperator
        self.decimal = decimal
        self.dtfield = dtfield
        self.yfields = yfields
        self.datetime_format = datetime_format
        self.droplines = droplines
        self.generatex = generatex
        self.samplerate = samplerate

    @property
    def fields(self):
        dtfields = [] if self.dtfield is None else [self.dtfield]
        return dtfields + self.yfields

    @property
    def name(self):
        name, _ = os.path.splitext(os.path.basename(self.filepath))
        return name

    @property
    def folder(self):
        folder = os.path.dirname(self.filepath)
        return folder

class PlotData():
    def __init__(self, data = None,
                       fields = [],
                       filepath = "",
                       name = None):
        self.data = data
        self.fields = fields
        self.filepath = filepath
        self._name = name

    @property
    def name(self):
        if self._name is not None:
            name = self._name
        else:
            name, _ = os.path.splitext(os.path.basename(self.filepath))
        return name

    @property
    def folder(self):
        folder = os.path.dirname(self.filepath)
        return folder


# https://stackoverflow.com/questions/5478351/python-time-measure-function
def Timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
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

curPath = os.path.dirname(os.path.abspath(__file__))
uiBasePath = os.path.join(curPath, 'ui')
def loadUiFile(uiFile):
    uiPath = os.path.join(uiBasePath, uiFile)
    uiClasses = loadUiType(uiPath)
    return uiClasses

def estimateSampleRate(series):
    idx = series.index.values
    timedelta = (idx[-1] - idx[0]) * 1e-9
    fs = len(idx) / timedelta
    return int(round(fs))

def loadmodule():
    defaultdir = os.path.expanduser('~')
    filepath = QtGui.QFileDialog.getOpenFileName(caption = "Import module",
                                                 filter  = "Python files (*.py)",
                                                 directory = defaultdir)
    if type(filepath) is not str:
        # PyQt5 API change
        filepath = filepath[0]
    if not filepath:
        # Cancel pressed
        return

    folder, filename = os.path.split(filepath)
    modulename, _ = os.path.splitext(filename)
    f, filename, description = imp.find_module(modulename, [folder])

    bcbak = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        imp.load_module('graphysio.plugin', f, filename, description)
    finally:
        sys.dont_write_bytecode = bcbak
        f.close()

def getshell(ui=None):
    import IPython
    IPython.embed(ui=ui)
