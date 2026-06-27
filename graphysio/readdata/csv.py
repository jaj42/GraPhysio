import csv
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import pandas as pd

from graphysio.core.params import ParamSpec
from graphysio.readdata.baseclass import BaseReader
from graphysio.structures import PlotData

# Separator tokens presented to the user, mapped to what pandas expects.
SEP_TOKENS = {",": ",", ";": ";", "<tab>": "\t", "<whitespace>": r"\s+"}
DT_FORMAT_TOKENS = [
    "<infer>",
    "<seconds>",
    "<milliseconds>",
    "<microseconds>",
    "<nanoseconds>",
    "<minutes>",
    "<hours>",
]


class CsvReader(BaseReader):
    is_available = True

    def _guess_delimiters(self, encoding: str = "utf-8") -> tuple[str, str]:
        with open(self.userdata["filepath"], encoding=encoding) as f:
            seperator = ";" if ";" in next(f) else ","
            decimal = "." if "." in next(f) else ","
        return seperator, decimal

    def _safe_guess(self) -> tuple[str, str]:
        """Best-effort delimiter guess that never raises.

        Used only to pre-fill the stage-1 defaults; the file may be in a non-UTF-8
        encoding the user hasn't told us about yet, so a decode failure here just
        falls back to the common comma/dot.
        """
        try:
            return self._guess_delimiters("utf-8")
        except (UnicodeDecodeError, OSError, StopIteration):
            return ",", "."

    def _header(self, sep: str, droplines: int, encoding: str) -> list[str]:
        real_sep = SEP_TOKENS.get(sep, sep)
        with open(self.userdata["filepath"], encoding=encoding) as f:
            for _ in range(droplines):
                next(f)
            reader = csv.reader(f, delimiter="\t" if real_sep == r"\s+" else real_sep)
            row = next(reader)
        return [c for c in row if c]

    def get_params(self) -> list[ParamSpec]:
        """Staged schema for headless/web loading.

        Two stages, because reading the header to list the columns needs the
        encoding/separator -- which we must ask for *first* (a non-UTF-8 file would
        otherwise blow up before the user can choose ``latin1``):

        1. encoding + separator + decimal + header lines to skip;
        2. once those are known, read the header and offer the columns / time setup.

        The desktop uses the richer ``DlgNewPlotCsv`` (which sets ``csvrequest``
        directly); when that is present we need nothing more.
        """
        u = self.userdata
        if "csvrequest" in u or "yfields" in u:
            return []

        # Stage 1: how to decode and split the raw rows. No file read with a
        # user-supplied encoding yet, so this stage can never raise a decode error.
        if "encoding" not in u:
            sep, decimal = self._safe_guess()
            return [
                ParamSpec("encoding", "File encoding", "str", default="utf-8"),
                ParamSpec(
                    "seperator",
                    "Field separator",
                    "choice",
                    choices=list(SEP_TOKENS),
                    default=sep,
                ),
                ParamSpec(
                    "decimal",
                    "Decimal separator",
                    "choice",
                    choices=[".", ","],
                    default=decimal,
                ),
                ParamSpec(
                    "droplines",
                    "Header lines to skip",
                    "int",
                    default=0,
                    required=False,
                ),
            ]

        # Stage 2: now we can read the header with the chosen encoding/separator.
        encoding = u.get("encoding") or "utf-8"
        sep = u.get("seperator", ",")
        droplines = int(u.get("droplines") or 0)
        columns = self._header(sep, droplines, encoding)
        return [
            ParamSpec(
                "yfields",
                "Curves to load",
                "multichoice",
                choices=columns,
                default=columns,
            ),
            ParamSpec(
                "dtfield",
                "Time column (leave empty to generate from rate)",
                "choice",
                choices=columns,
                required=False,
            ),
            ParamSpec(
                "datetime_format",
                "Time column format",
                "choice",
                choices=DT_FORMAT_TOKENS,
                default="<infer>",
                required=False,
            ),
            ParamSpec(
                "samplerate",
                "Sampling rate (Hz), if generating time",
                "int",
                default=0,
                required=False,
            ),
            ParamSpec("timezone", "Timezone", "str", default="UTC", required=False),
            ParamSpec("filterexpr", "Row filter expression", "str", required=False),
        ]

    def _build_request(self) -> "CsvRequest":
        u = self.userdata
        dtfield = u.get("dtfield") or None
        clusterid = u.get("clusterid") or None
        exclude = {dtfield, clusterid}
        yfields = [c for c in u["yfields"] if c not in exclude]
        sep = SEP_TOKENS.get(u.get("seperator", ","), u.get("seperator", ","))
        return CsvRequest(
            filepath=Path(u["filepath"]),
            seperator=sep,
            decimal=u.get("decimal", "."),
            dtfield=dtfield,
            yfields=yfields,
            datetime_format=u.get("datetime_format") or "<infer>",
            droplines=int(u.get("droplines") or 0),
            generatex=dtfield is None,
            clusterid=clusterid,
            timezone=u.get("timezone") or "UTC",
            encoding=u.get("encoding") or "utf-8",
            samplerate=int(u.get("samplerate") or 0),
            filterexpr=(u.get("filterexpr") or None),
        )

    def __call__(self) -> list[PlotData]:
        request = self.userdata.get("csvrequest")
        if request is None:
            if "yfields" not in self.userdata:
                return []
            request = self._build_request()
        data = pd.read_csv(
            request.filepath,
            sep=request.seperator,
            usecols=request.fields,
            decimal=request.decimal,
            skiprows=request.droplines,
            encoding=request.encoding,
            index_col=False,
        )
        pdtonum = partial(pd.to_numeric, errors="coerce")
        dtformat = request.datetime_format
        if request.generatex:
            data.index = (1e9 * data.index / request.samplerate).astype("int64")
            # Make all data numeric and remove empty rows
            datacols = data.columns.difference([request.clusterid])
            data[datacols] = data[datacols].apply(pdtonum)
            data = data.dropna(axis="rows", how="all", subset=datacols)
        else:
            timestamp = data[request.dtfield]
            data = data.drop(columns=request.dtfield)
            # Force all columns to numeric
            datacols = data.columns.difference([request.clusterid])
            data[datacols] = data[datacols].apply(pdtonum)
            # data = data.dropna(axis="rows", how="all", subset=datacols)
            nanrows = data[datacols].isna().all(axis=1)
            data = data[~nanrows]
            timestamp = timestamp[~nanrows]

            if dtformat == "<hours>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 3.6e12, unit="ns")
            elif dtformat == "<minutes>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 6e10, unit="ns")
            elif dtformat == "<seconds>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e9, unit="ns")
            elif dtformat == "<milliseconds>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e6, unit="ns")
            elif dtformat == "<microseconds>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp * 1e3, unit="ns")
            elif dtformat == "<nanoseconds>":
                timestamp = pdtonum(timestamp)
                timestamp = pd.to_datetime(timestamp, unit="ns")
            else:
                if dtformat == "<infer>":
                    opts = {}
                else:
                    opts = {"format": dtformat}
                timestamp = pd.to_datetime(timestamp, **opts)
                timestamp = pd.Index(timestamp)
                if timestamp.tz is None:
                    timestamp = timestamp.tz_localize(request.timezone)
                timestamp = timestamp.tz_convert("UTC").tz_localize(None)

            timestamp = timestamp.astype("datetime64[ns]").astype("int64")
            data = data.set_index([timestamp])

        data = data.dropna(axis="columns", how="all")
        data = data.sort_index()

        # Apply user filter on data
        if request.filterexpr is not None:
            data = data.query(request.filterexpr)

        fp = request.filepath
        if request.clusterid:
            g = data.groupby(request.clusterid)
            plotdata = [
                PlotData(
                    data=df.drop(columns=request.clusterid),
                    filepath=fp,
                    name=f"{fp.stem}-{i}",
                )
                for i, df in g
            ]
        else:
            plotdata = [PlotData(data=data, filepath=fp)]

        return plotdata


@dataclass
class CsvRequest:
    """Group needed parameters to parse the CSV file."""

    filepath: Path
    seperator: str
    decimal: str
    dtfield: str
    yfields: list[str]
    datetime_format: str
    droplines: int
    generatex: bool
    clusterid: str
    timezone: str
    encoding: str
    samplerate: int
    filterexpr: str | None

    @property
    def fields(self) -> list[str]:
        dtfields = [] if self.dtfield is None else [self.dtfield]
        clusterfields = [] if self.clusterid is None else [self.clusterid]
        return dtfields + clusterfields + self.yfields
