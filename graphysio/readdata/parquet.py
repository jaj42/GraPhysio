import numpy as np
import pandas as pd

from graphysio.structures import PlotData
from graphysio.readdata.baseclass import BaseReader


class ParquetReader(BaseReader):
    def __call__(self) -> PlotData:
        filepath = self.userdata['filepath']
        data = pd.read_parquet(filepath)

        data = data.dropna(axis='columns', how='all')
        data = data.sort_index()
        data.index = data.index.astype(np.int64)

        plotdata = PlotData(data=data, filepath=filepath)
        return plotdata
