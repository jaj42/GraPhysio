from typing import List

import pandas as pd
from graphysio.plotwidgets.curves import CurveItem

try:
    import pyarrow.parquet
except ImportError:
    is_available = False
else:
    is_available = True


def export_curves(
    curves: List[CurveItem], filepath: str, index_label: str = 'timens'
) -> None:
    sers = [c.series for c in curves]
    data = pd.concat(sers, axis=1).sort_index()
    data.to_parquet(
        filepath,
        engine='pyarrow',
        compression='gzip',
        coerce_timestamps='us',
        allow_truncated_timestamps=True,
    )


export_curves.is_available = is_available
