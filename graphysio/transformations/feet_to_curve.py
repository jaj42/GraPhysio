from typing import List

from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter, PlotData


def get_feet_to_curve(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    feetitemhash = {}
    for curve in plotwidget.curves.values():
        feetitemhash.update(
            {
                f"{curve.name()}-{feetname}": (curve, feetname)
                for feetname in curve.feetitem.indices.keys()
            }
        )
    param = Parameter("Choose points to create curve", list(feetitemhash.keys()))
    qresult = askUserValue(param)
    curve, feetname = feetitemhash[qresult]

    out_series = curve.getFeetPoints(feetname)
    sname = qresult

    plotdata = PlotData(data=out_series, name=sname)
    return [plotdata]
