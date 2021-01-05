import numpy as np
import pandas as pd
import pyarrow.parquet as pa

from graphysio.dialogs import DlgListChoice
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData


class ParquetReader(BaseReader):
    def askUserInput(self):
        filepath = self.userdata['filepath']
        s = pa.read_schema(filepath)
        colnames = s.names

        def cb(columns):
            self.userdata['columns'] = columns

        dlgchoice = DlgListChoice(colnames, 'Open Parquet', 'Choose curves to load')
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec_()

    def __call__(self) -> PlotData:
        filepath = self.userdata['filepath']
        data = pd.read_parquet(filepath, columns=self.userdata['columns'])

        data = data.dropna(axis='columns', how='all')
        data = data.sort_index()
        data.index = data.index.astype(np.int64)

        return PlotData(data=data, filepath=filepath)
