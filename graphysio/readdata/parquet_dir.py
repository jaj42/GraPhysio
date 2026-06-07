import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from graphysio.dialogs import DlgListChoice, askUserValue, askDirPath
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import Parameter, PlotData

try:
    import pyarrow.parquet as pa
except ImportError:
    is_available = False
else:
    is_available = True


class ParquetDirReader(BaseReader):
    is_available = is_available

    def askUserInput(self) -> None:
        parquet_folder = askDirPath("Open Parquet Directory")
        if parquet_folder is None:
            return
        self.userdata["path"] = parquet_folder
        columns: set[str] = set()
        for fp in parquet_folder.glob("*.parquet"):
            parquet_file = pa.ParquetFile(fp)  # pyright: ignore[reportPossiblyUnboundVariable]
            file_columns = parquet_file.schema.names
            columns |= set(file_columns)

        def cb(columns: list[str]) -> None:
            self.userdata["all_columns"] = set(columns)
            param = Parameter("Choose Index", columns)
            qresult = askUserValue(param)
            if qresult is not None:
                self.userdata["index"] = qresult

        dlgchoice = DlgListChoice(
            columns, "Open Parquet Directory", "Choose curves to load"
        )
        dlgchoice.dlgdata.connect(cb)
        dlgchoice.exec()

    def get_plotdata(self) -> list[PlotData]:
        plotdatas = []
        for filepath in self.userdata["path"].glob("*.parquet"):
            parquet_file = pa.ParquetFile(filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
            column_names = parquet_file.schema.names
            user_columns = self.userdata["all_columns"] & set(column_names)

            data = pd.read_parquet(filepath, columns=list(user_columns))
            if self.userdata["index"] in data.columns:
                data = data.set_index(self.userdata["index"])
            data = data.dropna(axis="columns", how="all")
            data = data.sort_index()

            if is_datetime64_any_dtype(data.index):
                data.index = data.index.tz_localize(None)
            data.index = data.index.astype("datetime64[ns]").astype("int")

            plotdatas.append(PlotData(data=data, filepath=filepath))
        return plotdatas
