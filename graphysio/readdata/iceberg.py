from pandas.api.types import is_datetime64_any_dtype

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

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

    def _load_table(self):
        catalog = SqlCatalog(
            name=self.userdata["catalog_name"], **_credentials_from_config()
        )
        return catalog.load_table(
            f"{self.userdata['namespace']}.{self.userdata['table']}"
        )

    def get_params(self) -> list[ParamSpec]:
        # Stage 1: connection details needed to reach a table.
        if "table" not in self.userdata:
            return [
                ParamSpec("catalog_name", "Catalog name", "str"),
                ParamSpec("namespace", "Namespace", "str"),
                ParamSpec("table", "Table", "str"),
                ParamSpec("row_filter", "Row filter", "str", required=False),
            ]
        # Stage 2: columns of the (now reachable) table.
        if "columns" not in self.userdata:
            colnames = [f.name for f in self._load_table().schema().fields]
            return [
                ParamSpec(
                    "columns",
                    "Choose columns to load",
                    "multichoice",
                    choices=colnames,
                    default=colnames,
                ),
                ParamSpec(
                    "index", "Choose index", "choice", choices=colnames, required=False
                ),
            ]
        return []

    def __call__(self) -> list[PlotData]:
        if not self.userdata.get("columns"):
            return []
        table = self._load_table()

        scan_kwargs: dict = {"selected_fields": tuple(self.userdata["columns"])}
        row_filter = (self.userdata.get("row_filter") or "").strip()
        if row_filter:
            scan_kwargs["row_filter"] = row_filter
        scan_kwargs["limit"] = 100

        df = table.scan(**scan_kwargs).to_pandas()

        if self.userdata.get("index") in df.columns:
            df = df.set_index(self.userdata["index"])

        df = df.dropna(axis="columns", how="all").sort_index()

        if is_datetime64_any_dtype(df.index):
            df.index = df.index.tz_localize(None)
        df.index = df.index.astype("datetime64[ns]").astype("int64")

        name = f"{self.userdata['namespace']}.{self.userdata['table']}"
        return [PlotData(data=df, name=name)]
