"""Binary (Apache Arrow IPC) serialization of curve windows.

Sending decimated windows as Arrow IPC -- rather than JSON -- keeps the payload
compact and lets the frontend (apache-arrow JS) hand uPlot typed arrays directly,
with no parse step. Each message is a two-column table: ``t`` (int64 epoch-ns) and
``v`` (float64).
"""

from __future__ import annotations

import pandas as pd
import pyarrow as pa

__all__ = ["ARROW_MEDIA_TYPE", "series_to_arrow_ipc"]

ARROW_MEDIA_TYPE = "application/vnd.apache.arrow.stream"


def series_to_arrow_ipc(series: pd.Series) -> bytes:
    """Serialize a time-indexed Series to an Arrow IPC stream (``t``/``v`` columns)."""
    table = pa.table(
        {
            "t": pa.array(series.index.to_numpy(), type=pa.int64()),
            "v": pa.array(series.to_numpy(), type=pa.float64()),
        }
    )
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()
