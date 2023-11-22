from typing import List

from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter, PlotData


def get_feet_time_interval(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
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

    points = curve.getFeetPoints(feetname)
    time_intervals = points.index.to_series().diff()  # ns
    time_intervals /= 1e6  # ms

    sname = f"{qresult}(ms)"

    plotdata = PlotData(data=time_intervals, name=sname)
    return [plotdata]
