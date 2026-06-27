import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import pyarrow.parquet as pa  # pyright: ignore[reportMissingTypeStubs]
    import pyarrow.types as patypes  # pyright: ignore[reportMissingTypeStubs]
except ImportError:
    is_available = False
else:
    is_available = True

# User-facing time-unit tokens mapped to their multiplier into nanoseconds. Used when
# the parquet index is an integer counter rather than a real datetime. The token style
# mirrors csv.py's DT_FORMAT_TOKENS.
TIME_UNIT_NS = {
    "<nanoseconds>": 1,
    "<microseconds>": 1_000,
    "<milliseconds>": 1_000_000,
    "<seconds>": 1_000_000_000,
    "<minutes>": 60_000_000_000,
    "<hours>": 3_600_000_000_000,
}


class ParquetReader(BaseReader):
    is_available = is_available

    def _index_is_datetime(self) -> bool:
        """Whether the chosen index column is a timestamp, read from the schema only.

        No index picked means a RangeIndex of row numbers, which is not a datetime.
        """
        index = self.userdata.get("index")
        if not index:
            return False
        field = pa.read_schema(self.userdata["filepath"]).field(index)
        return patypes.is_timestamp(field.type)

    def get_params(self) -> list[ParamSpec]:
        # Stage 1: which curves to load and which column is the index.
        if "columns" not in self.userdata:
            schema = pa.read_schema(self.userdata["filepath"])
            colnames = schema.names
            # A timestamp column is the natural index; default to the first one (an
            # unnamed pandas datetime index is written as ``__index_level_0__``). A
            # selected index column is moved out of the curves by ``set_index`` in
            # __call__, so it is harmless to leave it among the curve choices.
            index_default = next(
                (f.name for f in schema if patypes.is_timestamp(f.type)), None
            )
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
                    default=index_default,
                    required=False,
                ),
            ]
        # Stage 2: an integer index has no intrinsic time unit -- ask for it.
        if "timeunit" not in self.userdata and not self._index_is_datetime():
            return [
                ParamSpec(
                    "timeunit",
                    "Index time unit",
                    "choice",
                    choices=list(TIME_UNIT_NS),
                    default="<nanoseconds>",
                ),
            ]
        return []

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
            data.index = data.index.astype("datetime64[ns]").astype("int64")
        else:
            factor = TIME_UNIT_NS[self.userdata.get("timeunit") or "<nanoseconds>"]
            data.index = (data.index.to_numpy() * factor).astype("int64")

        return PlotData(data=data, filepath=filepath)
