import numpy as np
import pandas as pd

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import pyedflib
except ImportError:
    is_available = False
else:
    is_available = True


class EdfReader(BaseReader):
    is_available = is_available

    def _signal_labels(self) -> list[str]:
        edf = pyedflib.EdfReader(str(self.userdata["filepath"]))
        try:
            return [edf.getSignalHeader(i)["label"] for i in range(edf.signals_in_file)]
        finally:
            edf.close()

    def get_params(self) -> list[ParamSpec]:
        if "columns" in self.userdata:
            return []
        labels = self._signal_labels()
        return [
            ParamSpec(
                "columns",
                "Choose curves to load",
                "multichoice",
                choices=labels,
                default=labels,
            ),
        ]

    def __call__(self) -> PlotData | None:
        filepath = str(self.userdata["filepath"])
        edf = pyedflib.EdfReader(filepath)
        # Map requested signal labels back to their channel indices.
        label_to_idx = {
            edf.getSignalHeader(i)["label"]: i for i in range(edf.signals_in_file)
        }
        beginns = edf.getStartdatetime().timestamp() * 1e9
        nsamplesPerChannel = edf.getNSamples()

        signals = []
        for label in self.userdata["columns"]:
            i = label_to_idx[label]
            h = edf.getSignalHeader(i)
            fs = h["sample_rate"]
            n = nsamplesPerChannel[i]
            endns = beginns + n * 1e9 / fs
            idx = np.linspace(beginns, endns, num=n, dtype=np.int64)
            s = pd.Series(edf.readSignal(i), index=idx, name=h["label"])
            signals.append(s)
        edf.close()

        if not signals:
            return None

        df = pd.concat(signals, axis=1)
        return PlotData(data=df, filepath=filepath)
