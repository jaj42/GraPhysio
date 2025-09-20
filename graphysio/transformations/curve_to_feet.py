from typing import List

from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI, POIItem
from graphysio.structures import Parameter


def get_curve_to_feet(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    curvenames = list(plotwidget.curves.keys())
    param = Parameter("Choose points", curvenames)
    qresult = askUserValue(param)
    feet_src = plotwidget.curves[qresult]

    param = Parameter("Choose destination curve", curvenames)
    qresult = askUserValue(param)
    feet_dst = plotwidget.curves[qresult]

    param = Parameter("Choose feet type", list(POIItem.sym.keys()))
    feet_type = askUserValue(param)

    locs = feet_dst.series.index.get_indexer(feet_src.series.index, method="nearest")
    feet_dst.feetitem.indices[feet_type] = feet_dst.series.index[locs]
    feet_dst.feetitem.render()

    return []
