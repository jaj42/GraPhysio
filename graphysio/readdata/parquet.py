import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import pyarrow.parquet as pa  # pyright: ignore[reportMissingTypeStubs]
except ImportError:
    is_available = False
else:
    is_available = True


class ParquetReader(BaseReader):
    is_available = is_available

    def get_params(self) -> list[ParamSpec]:
        if "columns" in self.userdata:
            return []
        colnames = pa.read_schema(self.userdata["filepath"]).names
        return [
            ParamSpec(
                "columns",
                "Choose curves to load",
                "multichoice",
                choices=colnames,
                default=colnames,
            ),
            ParamSpec(
                "index",
                "Choose index",
                "choice",
                choices=colnames,
                required=False,
            ),
        ]

    def __call__(self) -> PlotData:
        filepath = self.userdata["filepath"]
        columns = list(self.userdata["columns"])
        index = self.userdata.get("index")
        # Make sure the index column is read even if it was not picked as a curve.
        if index is not None and index not in columns:
            columns = [*columns, index]
        data = pd.read_parquet(filepath, columns=columns)
        if index in data.columns:
            data = data.set_index(index)

        data = data.dropna(axis="columns", how="all")
        data = data.sort_index()

        if is_datetime64_any_dtype(data.index):
            data.index = data.index.tz_localize(None)
        data.index = data.index.astype("datetime64[ns]").astype("int")

        return PlotData(data=data, filepath=filepath)
