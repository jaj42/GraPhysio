import numpy as np
import pandas as pd

from graphysio.dialogs import DlgListChoice
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

    def askUserInput(self) -> None:
        filepath = str(self.userdata["filepath"])
        raw = mne.io.read_raw(filepath, preload=False, verbose=False)

        ch_names = raw.ch_names
        raw.close()

        def cb(colnames) -> None:
            self.userdata["columns"] = colnames

        dlgchoice = DlgListChoice(ch_names, "Open EEG (MNE)", "Choose curves to load")
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec()

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
