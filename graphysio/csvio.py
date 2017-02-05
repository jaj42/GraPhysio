import numpy as np
import pandas as pd
from functools import partial

from PyQt4 import QtCore
from graphysio import utils

class Reader(QtCore.QRunnable):
    def __init__(self, plotdata, sigdata, sigerror):
        super().__init__()
        self._plotdata = plotdata
        self.sigdata = sigdata
        self.sigerror = sigerror

    def run(self):
        try:
            data = self.getdata()
        except ValueError as e:
            self.sigerror.emit(e)
        else:
            self._plotdata.data = data
            self.sigdata.emit(self._plotdata)

    def getdata(self):
        if self._plotdata.loadall:
            # usecols = None loads all columns
            usecols = None
        else:
            usecols = self._plotdata.fields

        data = pd.read_csv(self._plotdata.filepath,
                           sep       = self._plotdata.seperator,
                           usecols   = usecols,
                           decimal   = self._plotdata.decimal,
                           index_col = False,
                           skiprows  = self._plotdata.droplines,
                           encoding  = 'latin1',
                           engine    = 'c')

        if self._plotdata.xisdate:
            dtformat = self._plotdata.datetime_format
            if dtformat == '<seconds>':
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield] * 1e9, unit = 'ns')
            elif dtformat == '<milliseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield] * 1e6, unit = 'ns')
            elif dtformat == '<microseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield] * 1e3, unit = 'ns')
            elif dtformat == '<nanoseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield], unit = 'ns')
            else:
                data['nsdatetime'] = pd.to_datetime(data[self._plotdata.datefield], format = dtformat)
            data = data.set_index('nsdatetime')

        # Coerce all columns to numeric and remove empty columns
        pdtonum = partial(pd.to_numeric, errors='coerce')
        data = data.apply(pdtonum).dropna(axis='columns', how='all')
        data = data.dropna(axis='rows', how='all')

        # Provide a gross estimation of the sampling rate based on the index
        self._plotdata.samplerate = estimateSampleRate(data)

        # Don't try requested fields that are empty
        self._plotdata.yfields = [f for f in self._plotdata.yfields if f in data.columns]

        return data


def estimateSampleRate(series):
    if type(series.index) != pd.tseries.index.DatetimeIndex:
        return None
    idx = series.index.values
    timedelta = (idx[-1] - idx[0]) / np.timedelta64(1, 's')
    fs = len(idx) / timedelta
    return int(round(fs))
