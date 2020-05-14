from typing import List

import pandas as pd

from graphysio.plotwidgets.curves import CurveItem


def curves_to_csv(
    curves: List[CurveItem], filepath: str, index_label: str = 'timens'
) -> None:
    sers = [c.series for c in curves]
    data = pd.concat(sers, axis=1).sort_index()
    data['datetime'] = pd.to_datetime(data.index, unit='ns')
    data.to_csv(filepath, date_format="%Y-%m-%d %H:%M:%S.%f", index_label=index_label)
