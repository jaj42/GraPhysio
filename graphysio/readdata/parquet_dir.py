import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import pyarrow.parquet as pa
except ImportError:
    is_available = False
else:
    is_available = True


class ParquetDirReader(BaseReader):
    is_available = is_available

    def _all_columns(self) -> list[str]:
        columns: set[str] = set()
        for fp in self.userdata["path"].glob("*.parquet"):
            columns |= set(pa.ParquetFile(fp).schema.names)
        return sorted(columns)

    def get_params(self) -> list[ParamSpec]:
        # The directory path is supplied externally (folder picker / API), like the
        # file path for single-file readers.
        if "all_columns" in self.userdata:
            return []
        columns = self._all_columns()
        return [
            ParamSpec(
                "all_columns",
                "Choose curves to load",
                "multichoice",
                choices=columns,
                default=columns,
            ),
            ParamSpec("index", "Choose index", "choice", choices=columns, required=False),
        ]

    def __call__(self) -> list[PlotData]:
        wanted = set(self.userdata["all_columns"])
        index = self.userdata.get("index")
        plotdatas = []
        for filepath in self.userdata["path"].glob("*.parquet"):
            column_names = pa.ParquetFile(filepath).schema.names
            user_columns = wanted & set(column_names)
            if index is not None and index in column_names:
                user_columns.add(index)
            if not user_columns:
                continue

            data = pd.read_parquet(filepath, columns=list(user_columns))
            if index in data.columns:
                data = data.set_index(index)
            data = data.dropna(axis="columns", how="all")
            data = data.sort_index()

            if is_datetime64_any_dtype(data.index):
                data.index = data.index.tz_localize(None)
            data.index = data.index.astype("datetime64[ns]").astype("int64")

            plotdatas.append(PlotData(data=data, filepath=filepath))
        return plotdatas
