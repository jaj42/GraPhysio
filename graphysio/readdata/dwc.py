from datetime import datetime

import pandas as pd
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


def _fmt_dt(value) -> str:
    """Format a timestamp for an ``<input type=datetime-local>`` default.

    The whole DWC pipeline works in naive UTC: dwclib reads the ``DATETIMEOFFSET``
    ``TimeStamp`` back as UTC and ``__call__`` drops the tz, so the plot x-axis is
    naive UTC. We display and round-trip From/To in that same frame -- a tz-aware
    value is reduced to naive UTC without shifting the wall clock.
    """
    ts = pd.Timestamp(value)
    if ts.tz is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _to_naive(value) -> datetime:
    """Parse a From/To answer into the naive datetime dwclib/pymssql expects.

    Both callers are already naive -- the web sends a naive ISO string and the
    desktop a naive ``QDateTime.toPython()`` -- so this only parses the web string
    into a real datetime. That matters: a parsed datetime makes pymssql 2.3.2 emit
    the canonical ``'2026-06-06 09:37:47.000'`` literal. (A tz-aware datetime would
    instead emit the broken ``'2026-06-06 09:37:47.000000T'`` -- stray ``T``,
    six-digit microseconds, offset dropped -- which SQL Server cannot convert; the
    reason we never localise here.) Against a ``DATETIMEOFFSET`` column SQL Server
    reads an offset-less literal as UTC and compares on the UTC instant, matching
    the naive-UTC axis the data comes back on.
    """
    return pd.Timestamp(value).to_pydatetime()


class DwcReader(BaseReader):
    is_available = is_available

    def get_params(self) -> list[ParamSpec]:
        """Staged schema mirroring the desktop's two-step ``DlgDWCOpen``.

        1. Patient id + data type. Once known we look the patient up...
        2. ...and pre-fill the available time range and labels, exactly like the
           desktop dialog fills its From/To fields and its label list widget after
           you click "Search".

        The desktop uses the richer ``DlgDWCOpen`` (which sets every field at once,
        with ``items`` as a list); when that has run we need nothing more.
        """
        u = self.userdata
        # Desktop bespoke dialog populated everything in one shot.
        if u.get("items") and "from" in u:
            return []

        # Stage 1: who and what kind of data. Needed before we can query the patient.
        if "patientid" not in u:
            return [
                ParamSpec(
                    "type",
                    "Data type",
                    "choice",
                    choices=["numerics", "waves"],
                    default="numerics",
                ),
                ParamSpec("patientid", "Patient id", "str"),
            ]

        # Stage 2: look the patient up to pre-fill the time range and label list.
        if "from" not in u:
            return self._patient_params()

        return []

    def _patient_params(self) -> list[ParamSpec]:
        patient = dwclib.read_patient(self.userdata["patientid"])
        if patient is None:
            raise ValueError(f"Patient not found: {self.userdata['patientid']!r}")

        is_waves = self.userdata.get("type") == "waves"
        labels = patient["wavelabels"] if is_waves else patient["numericsublabels"]
        labels = list(labels or [])
        kind = "Labels" if is_waves else "Sublabels"

        return [
            ParamSpec(
                "from", "From", "datetime", default=_fmt_dt(patient["data_begin"])
            ),
            ParamSpec("to", "To", "datetime", default=_fmt_dt(patient["data_end"])),
            ParamSpec(
                "items", f"{kind} (comma-separated)", "str", default=", ".join(labels)
            ),
        ]

    def __call__(self) -> list[PlotData]:
        if not self.userdata:
            return []
        items = self.userdata["items"]
        if isinstance(items, str):
            items = [s.strip() for s in items.split(",") if s.strip()]

        dtbegin = _to_naive(self.userdata["from"])
        dtend = _to_naive(self.userdata["to"])

        if self.userdata["type"] == "numerics":
            df = dwclib.read_numerics(
                patientids=self.userdata["patientid"],
                dtbegin=dtbegin,
                dtend=dtend,
                sublabels=items,
            )
        elif self.userdata["type"] == "waves":
            df = dwclib.read_waves(
                patientid=self.userdata["patientid"],
                dtbegin=dtbegin,
                dtend=dtend,
                labels=items,
            )
        else:
            raise ValueError("wrong data request type")

        if is_datetime64_any_dtype(df.index):
            df.index = df.index.tz_localize(None)
        df.index = df.index.astype("datetime64[ns]").astype("int64")

        return [PlotData(data=df, name=str(self.userdata["patientid"]))]
