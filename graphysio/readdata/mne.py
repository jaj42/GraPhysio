import numpy as np
import pandas as pd

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import mne
except ImportError:
    is_available = False
else:
    is_available = True


class MneReader(BaseReader):
    is_available = is_available

    def get_params(self) -> list[ParamSpec]:
        if "columns" in self.userdata:
            return []
        filepath = str(self.userdata["filepath"])
        raw = mne.io.read_raw(filepath, preload=False, verbose=False)
        ch_names = raw.ch_names
        raw.close()
        return [
            ParamSpec(
                "columns",
                "Choose curves to load",
                "multichoice",
                choices=ch_names,
                default=ch_names,
            ),
        ]

    def __call__(self) -> PlotData:
        filepath = str(self.userdata["filepath"])
        raw = mne.io.read_raw(filepath, preload=True, verbose=False)

        meas_date = raw.info["meas_date"]
        if meas_date is not None:
            beginns = int(meas_date.timestamp() * 1e9)
        else:
            beginns = 0

        # fs = raw.info["sfreq"]
        picks = self.userdata["columns"]
        data, times = raw.get_data(picks=picks, return_times=True)
        raw.close()

        ch_names = [raw.ch_names[raw.ch_names.index(p)] for p in picks]

        signals = []
        for i, name in enumerate(ch_names):
            idx = (beginns + times * 1e9).astype(np.int64)
            s = pd.Series(data[i], index=idx, name=name)
            signals.append(s)

        if not signals:
            return None

        df = pd.concat(signals, axis=1)
        return PlotData(data=df, filepath=filepath)
