import pyedflib
import numpy as np
import pandas as pd

from graphysio.structures import PlotData
from graphysio.readdata.baseclass import BaseReader


class EdfReader(BaseReader):
    def __call__(self) -> PlotData:
        filepath = str(self.userdata['filepath'])
        edf = pyedflib.EdfReader(filepath)
        beginns = edf.getStartdatetime().timestamp() * 1e9
        nsamplesPerChannel = edf.getNSamples()

        signals = []
        for i in range(edf.signals_in_file):
            h = edf.getSignalHeader(i)
            fs = h['sample_rate']
            n = nsamplesPerChannel[i]
            endns = beginns + n * 1e9 / fs
            idx = np.linspace(beginns, endns, num=n, dtype=np.int64)
            s = pd.Series(edf.readSignal(i), index=idx, name=h['label'])
            signals.append(s)
        edf.close()

        df = pd.concat(signals, axis=1)
        plotdata = PlotData(data=df, filepath=filepath)

        return plotdata
