import os
from enum import Enum
from collections import namedtuple


Filter = namedtuple('Filter', ['name', 'parameters'])
Parameter = namedtuple('Parameter', ['description', 'request'])


class FootType(Enum):
    start = 'start'
    stop = 'stop'
    diastole = 'diastole'
    systole = 'systole'
    dicrotic = 'dicrotic'


class CycleId(Enum):
    none = 'None'
    foot = 'Pressure foot'
    pressure = 'Pressure Full'
    velocity = 'Velocity'


class PlotData:
    def __init__(self, data=[], filepath="", name=None):
        self.data = data
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
