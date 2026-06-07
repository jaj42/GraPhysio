from pandas.api.types import is_datetime64_any_dtype

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

try:
    import dwclib
except ImportError:
    is_available = False
else:
    is_available = True


class DwcReader(BaseReader):
    is_available = is_available

    def get_params(self) -> list[ParamSpec]:
        # Flat schema for headless/web use. The desktop uses the richer DlgDWCOpen
        # (patient search etc.), which populates userdata directly.
        if self.userdata.get("items"):
            return []
        return [
            ParamSpec("type", "Data type", "choice",
                      choices=["numerics", "waves"], default="numerics"),
            ParamSpec("patientid", "Patient id", "str"),
            ParamSpec("from", "From", "datetime"),
            ParamSpec("to", "To", "datetime"),
            ParamSpec("items", "Sublabels/labels (comma-separated)", "str"),
        ]

    def __call__(self) -> list[PlotData]:
        if not self.userdata:
            return []
        items = self.userdata["items"]
        if isinstance(items, str):
            items = [s.strip() for s in items.split(",") if s.strip()]
        if self.userdata["type"] == "numerics":
            df = dwclib.read_numerics(
                patientids=self.userdata["patientid"],
                dtbegin=self.userdata["from"],
                dtend=self.userdata["to"],
                sublabels=items,
            )
        elif self.userdata["type"] == "waves":
            df = dwclib.read_waves(
                patientid=self.userdata["patientid"],
                dtbegin=self.userdata["from"],
                dtend=self.userdata["to"],
                labels=items,
            )
        else:
            raise ValueError("wrong data request type")

        if is_datetime64_any_dtype(df.index):
            df.index = df.index.tz_localize(None)
        df.index = df.index.astype("datetime64[ns]").astype("int")

        return [PlotData(data=df, name=str(self.userdata["patientid"]))]
