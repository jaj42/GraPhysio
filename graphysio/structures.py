from collections import namedtuple
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd

Filter = namedtuple("Filter", ["name", "parameters"])
Parameter = namedtuple("Parameter", ["description", "request"])


class CycleId(Enum):
    none = "None"
    foot = "Pressure foot"
    pressure = "Pressure Full"
    velocity = "Velocity"
    rwave = "ECG R Wave"
    foottan = "Pressure foot (tangents)"
    pressurebis = "Pressure full (physiocurve)"
    ecg = "ECG full"


class PlotData:
    def __init__(
        self,
        data,
        filepath: Optional[Path] = None,
        name: Optional[str] = None,
    ) -> None:
        if filepath is None and name is None:
            msg = "At least one of filepath or name needs to be specified."
            raise ValueError(msg)
        if filepath is not None:
            self.filepath = Path(filepath)
        self._name = name
        if isinstance(data, pd.Series):
            self.data = data.to_frame(name=self.name)
        else:
            self.data = data

    @property
    def name(self):
        return self._name if self._name is not None else self.filepath.stem

    @property
    def folder(self):
        return self.filepath.parent
