from collections import namedtuple
from enum import Enum
from pathlib import Path

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
    rwave = 'ECG R Wave'


class PlotData:
    def __init__(self, data, filepath: Path, name: str = None):
        self.data = data
        self.filepath = Path(filepath)
        self._name = name

    @property
    def name(self):
        if self._name is not None:
            name = self._name
        else:
            name = self.filepath.stem
        return name

    @property
    def folder(self):
        return self.filepath.parent
