from typing import List

import numpy as np
import pandas as pd
import scipy.io

from graphysio.plotwidgets.curves import CurveItem


def curves_to_matlab(
    curves: List[CurveItem], filepath: str, index_label: str = "timens"
) -> None:
    sers = [c.series for c in curves]
    data = pd.concat(sers, axis=1).sort_index()
    data["timens"] = data.index.to_numpy()
    scipy.io.savemat(filepath, {"data": data.to_dict("list")})

curves_to_matlab.is_available = True
