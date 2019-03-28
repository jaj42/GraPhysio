from functools import partial

import numpy as np
import pandas as pd

from pyqtgraph.Qt import QtCore

from graphysio.types import PlotData

class Reader(QtCore.QRunnable):
    def __init__(self, csvrequest, sigdata, sigerror):
        super().__init__()
        self.csvrequest = csvrequest
        self.sigdata = sigdata
        self.sigerror = sigerror

    def run(self) -> None:
        try:
            data = self.getdata()
        except Exception as e:
            #raise e
            self.sigerror.emit(e)
        else:
            self.sigdata.emit(data)

    def getdata(self) -> PlotData:
        data = pd.read_csv(self.csvrequest.filepath,
                           sep       = self.csvrequest.seperator,
                           usecols   = self.csvrequest.fields,
                           decimal   = self.csvrequest.decimal,
                           skiprows  = self.csvrequest.droplines,
                           encoding  = self.csvrequest.encoding,
                           index_col = False,
                           engine    = 'c')

        pdtonum = partial(pd.to_numeric, errors='coerce')
        dtformat = self.csvrequest.datetime_format
        if self.csvrequest.generatex:
            data.index = (1e9 * data.index / self.csvrequest.samplerate).astype(np.int64)
            # Make all data numeric and remove empty rows
            data = data.apply(pdtonum)
            data = data.dropna(axis='rows', how='all')
        else:
            datacolumns = data.columns.drop(self.csvrequest.dtfield)
            # Make all data numeric or drop if impossible
            data[datacolumns] = data[datacolumns].apply(pdtonum)
            # Make timestamp unique and use mean of values on duplicates
            data = data.groupby(self.csvrequest.dtfield, as_index=False).mean()
            # Remove empty rows
            data = data.dropna(axis='rows', how='all', subset=datacolumns)
            # Remove timestamp column from data
            timestamp = data[self.csvrequest.dtfield]
            data = data.drop(columns=self.csvrequest.dtfield)

            if dtformat == '<seconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e9, unit = 'ns')
            elif dtformat == '<milliseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e6, unit = 'ns')
            elif dtformat == '<microseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e3, unit = 'ns')
            elif dtformat == '<nanoseconds>':
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp, unit = 'ns')
            elif dtformat == '<infer>':
                timestamp = pd.to_datetime(timestamp, infer_datetime_format=True)
            else:
                timestamp = pd.to_datetime(timestamp, format = dtformat)

            # Convert timestamp to UTC
            timestamp = pd.Index(timestamp).tz_localize(self.csvrequest.timezone).tz_convert('UTC')
            timestamp = timestamp.astype(np.int64)
            data = data.set_index([timestamp])

        data = data.dropna(axis='columns', how='all')
        data = data.sort_index()

        plotdata = PlotData(data = data, filepath = self.csvrequest.filepath)
        return plotdata
