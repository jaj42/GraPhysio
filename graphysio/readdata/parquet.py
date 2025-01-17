import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from graphysio.dialogs import DlgListChoice
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import pyarrow.parquet as pa
except ImportError:
    is_available = False
else:
    is_available = True


class ParquetReader(BaseReader):
    is_available = is_available

    def askUserInput(self) -> None:
        filepath = self.userdata["filepath"]
        s = pa.read_schema(filepath)
        colnames = s.names

        def cb(columns) -> None:
            self.userdata["columns"] = columns

        dlgchoice = DlgListChoice(colnames, "Open Parquet", "Choose curves to load")
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec()

    def __call__(self) -> PlotData:
        filepath = self.userdata["filepath"]
        data = pd.read_parquet(filepath, columns=self.userdata["columns"])

        data = data.dropna(axis="columns", how="all")
        data = data.sort_index()

        if is_datetime64_any_dtype(data.index):
            data.index = data.index.tz_localize(None)
        data.index = data.index.astype("datetime64[ns]").astype("int")

        return PlotData(data=data, filepath=filepath)
