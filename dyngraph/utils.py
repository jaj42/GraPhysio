import os
from enum import Enum

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
                       isunixtime = False,
                       loadall = False,
                       datetime_format = "%Y-%m-%d %H:%M:%S,%f"):
        self.filepath = filepath
        self.seperator = seperator
        self.decimal = decimal
        self.xfield  = xfield
        self.yfields = yfields
        self.loadall = loadall
        self.datetime_format = datetime_format
        self.xisdate = xisdate
        self.isunixtime = isunixtime
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
