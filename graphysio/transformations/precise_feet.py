from typing import List

import numpy as np
import pandas as pd
from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter, PlotData
from physiocurve.pressure.foot import find_tangent_intersections


def get_precise_feet(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    curvenames = list(plotwidget.curves.keys())
    if len(curvenames) < 1:
        raise ValueError("No curve")
    elif len(curvenames) > 1:
        q = Parameter("Select Curve", curvenames)
        curvename = askUserValue(q)
    else:
        curvename = curvenames[0]

    curve = plotwidget.curves[curvename]
    wave = curve.series

    try:
        idxdia = curve.feetitem.indices["diastole"]
        idxsys = curve.feetitem.indices["systole"]
    except KeyError as e:
        raise ValueError("No systole or diastole") from e

    argdia = wave.index.get_indexer(idxdia)
    argsys = wave.index.get_indexer(idxsys)

    intersections = find_tangent_intersections(wave.to_numpy(), argdia, argsys)

    scale = (wave.index[-1] - wave.index[0]) / len(wave)
    intersections = intersections * scale + wave.index[0]
    intersections = np.rint(intersections).astype(np.int64)

    y_value_index = wave.index.get_indexer(intersections, method="nearest")
    y_values = wave.iloc[y_value_index]

    out_series = pd.Series(y_values.to_numpy(), index=intersections)
    sname = f"{wave.name}-precise_feet"

    plotdata = PlotData(data=out_series, name=sname)
    return [plotdata]
