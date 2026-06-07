from pandas.api.types import is_datetime64_any_dtype

from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import Parameter, PlotData

try:
    from pyiceberg.catalog.sql import SqlCatalog
except ImportError:
    is_available = False
else:
    is_available = True


def _credentials_from_config() -> dict:
    from graphysio.config import load_config

    config = load_config()
    section = config["iceberg"] if "iceberg" in config else {}
    return {
        "uri": section.get("catalog-uri", ""),
        "s3.endpoint": section.get("s3-endpoint", ""),
        "s3.access-key-id": section.get("accesskey", ""),
        "s3.secret-access-key": section.get("secretkey", ""),
    }


class IcebergReader(BaseReader):
    is_available = is_available

    def askUserInput(self) -> None:
        from graphysio.dialogs import DlgIcebergOpen, DlgListChoice, askUserValue

        def cb(conndata) -> None:
            self.userdata.update(conndata)
            credentials = _credentials_from_config()
            catalog = SqlCatalog(name=conndata["catalog_name"], **credentials)
            table = catalog.load_table(f"{conndata['namespace']}.{conndata['table']}")
            colnames = [field.name for field in table.schema().fields]

            def cb2(columns) -> None:
                self.userdata["columns"] = columns
                param = Parameter("Choose Index", columns)
                idx = askUserValue(param)
                if idx is not None:
                    self.userdata["index"] = idx

            dlg = DlgListChoice(colnames, "Iceberg Table", "Choose columns to load")
            dlg.dlgdata.connect(cb2)
            dlg.exec()

        dlg = DlgIcebergOpen()
        dlg.dlgdata.connect(cb)
        dlg.exec()

    def get_plotdata(self) -> list[PlotData]:
        if not self.userdata.get("columns"):
            return []
        credentials = _credentials_from_config()
        catalog = SqlCatalog(name=self.userdata["catalog_name"], **credentials)
        table = catalog.load_table(f"{self.userdata['namespace']}.{self.userdata['table']}")

        scan_kwargs: dict = {"selected_fields": tuple(self.userdata["columns"])}
        row_filter = self.userdata.get("row_filter", "").strip()
        if row_filter:
            scan_kwargs["row_filter"] = row_filter

        scan_kwargs["limit"] = 100

        df = table.scan(**scan_kwargs).to_pandas()

        print(df)

        if self.userdata.get("index") in df.columns:
            df = df.set_index(self.userdata["index"])

        df = df.dropna(axis="columns", how="all").sort_index()

        if is_datetime64_any_dtype(df.index):
            df.index = df.index.tz_localize(None)
        df.index = df.index.astype("datetime64[ns]").astype("int")

        name = f"{self.userdata['namespace']}.{self.userdata['table']}"
        return [PlotData(data=df, name=name)]
