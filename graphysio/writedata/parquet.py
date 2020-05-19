from typing import List

import pandas as pd

from graphysio.plotwidgets.curves import CurveItem


def curves_to_parquet(
    curves: List[CurveItem], filepath: str, index_label: str = 'timens'
) -> None:
    sers = [c.series for c in curves]
    data = pd.concat(sers, axis=1).sort_index()
    data.index = data.index.astype('M8[ns]')
    data.to_parquet(filepath, compression='gzip', allow_truncated_timestamps=True)
