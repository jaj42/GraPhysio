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


def _local_tz():
    """The machine's local timezone -- what the user reads From/To in."""
    return datetime.now().astimezone().tzinfo


def _fmt_dt(value) -> str:
    """Format a timestamp for an ``<input type=datetime-local>`` default.

    The widget is timezone-naive, so we show *local* wall-clock time: a tz-aware
    value (dwclib returns UTC) is converted to the local zone first, then the tz is
    dropped. The user sees local time and gets local-time data back.
    """
    ts = pd.Timestamp(value)
    if ts.tz is not None:
        ts = ts.tz_convert(_local_tz()).tz_localize(None)
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _to_aware(value) -> datetime:
    """Parse a From/To answer into a tz-aware datetime dwclib expects.

    The web sends a naive local ISO string and the desktop a naive datetime; both
    are interpreted as local time and localized, so the query range matches what
    the user entered (and the data comes back in the same zone, not UTC).
    """
    ts = pd.Timestamp(value)
    if ts.tz is None:
        ts = ts.tz_localize(_local_tz())
    return ts.to_pydatetime()


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
                ParamSpec("type", "Data type", "choice",
                          choices=["numerics", "waves"], default="numerics"),
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
            ParamSpec("from", "From", "datetime",
                      default=_fmt_dt(patient["data_begin"])),
            ParamSpec("to", "To", "datetime",
                      default=_fmt_dt(patient["data_end"])),
            ParamSpec("items", f"{kind} (comma-separated)", "str",
                      default=", ".join(labels)),
        ]

    def __call__(self) -> list[PlotData]:
        if not self.userdata:
            return []
        items = self.userdata["items"]
        if isinstance(items, str):
            items = [s.strip() for s in items.split(",") if s.strip()]

        dtbegin = _to_aware(self.userdata["from"])
        dtend = _to_aware(self.userdata["to"])

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
        df.index = df.index.astype("datetime64[ns]").astype("int")

        return [PlotData(data=df, name=str(self.userdata["patientid"]))]
