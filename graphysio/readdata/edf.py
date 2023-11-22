import numpy as np
import pandas as pd
from graphysio.dialogs import DlgListChoice
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

    def askUserInput(self):
        filepath = str(self.userdata["filepath"])
        edf = pyedflib.EdfReader(filepath)

        signals = {}
        for i in range(edf.signals_in_file):
            h = edf.getSignalHeader(i)
            signals[h["label"]] = i
        edf.close()

        def cb(colnames):
            self.userdata["columns"] = [signals[lbl] for lbl in colnames]

        colnames = list(signals.keys())
        dlgchoice = DlgListChoice(colnames, "Open EDF", "Choose curves to load")
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec_()

    def __call__(self) -> PlotData:
        filepath = str(self.userdata["filepath"])
        edf = pyedflib.EdfReader(filepath)
        beginns = edf.getStartdatetime().timestamp() * 1e9
        nsamplesPerChannel = edf.getNSamples()

        signals = []
        for i in self.userdata["columns"]:
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
