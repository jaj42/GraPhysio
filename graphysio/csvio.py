import numpy as np
import pandas as pd
from functools import partial

from pyqtgraph.Qt import QtCore

from graphysio import utils

class Reader(QtCore.QRunnable):
    def __init__(self, csvrequest, sigdata, sigerror):
        super().__init__()
        self.csvrequest = csvrequest
        self.sigdata = sigdata
        self.sigerror = sigerror

    def run(self):
        try:
            data = self.getdata()
        except Exception as e:
            self.sigerror.emit(e)
        else:
            self.sigdata.emit(data)

    def getdata(self):
        if self.csvrequest.loadall:
            # usecols = None loads all columns
            usecols = None
        else:
            usecols = self.csvrequest.fields

        data = pd.read_csv(self.csvrequest.filepath,
                           sep       = self.csvrequest.seperator,
                           usecols   = usecols,
                           decimal   = self.csvrequest.decimal,
                           index_col = False,
                           skiprows  = self.csvrequest.droplines,
                           encoding  = 'latin1',
                           engine    = 'c')

        if self.csvrequest.xisdate:
            dtformat = self.csvrequest.datetime_format
            if dtformat == '<seconds>':
                data['nsdatetime'] = pd.to_datetime(data[self.csvrequest.datefield] * 1e9, unit = 'ns')
            elif dtformat == '<milliseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self.csvrequest.datefield] * 1e6, unit = 'ns')
            elif dtformat == '<microseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self.csvrequest.datefield] * 1e3, unit = 'ns')
            elif dtformat == '<nanoseconds>':
                data['nsdatetime'] = pd.to_datetime(data[self.csvrequest.datefield], unit = 'ns')
            else:
                data['nsdatetime'] = pd.to_datetime(data[self.csvrequest.datefield], format = dtformat)
            data = data.set_index('nsdatetime')

        # Coerce all columns to numeric and remove empty columns
        pdtonum = partial(pd.to_numeric, errors='coerce')
        data = data.apply(pdtonum).dropna(axis='columns', how='all')
        data = data.dropna(axis='rows', how='all')
        data = data.sort_index()

        # Provide a gross estimation of the sampling rate based on the index
        samplerate = estimateSampleRate(data)

        # Don't try requested fields that are empty
        fields = [f for f in self.csvrequest.yfields if f in data.columns]

        plotdata = utils.PlotData(data       = data,
                                  fields     = fields,
                                  samplerate = samplerate,
                                  filepath   = self.csvrequest.filepath)
        return plotdata


def estimateSampleRate(series):
    if type(series.index) != pd.tseries.index.DatetimeIndex:
        return None
    idx = series.index.values
    timedelta = (idx[-1] - idx[0]) / np.timedelta64(1, 's')
    fs = len(idx) / timedelta
    return int(round(fs))
