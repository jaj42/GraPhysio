from typing import List

from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter


def get_feet_to_curve(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    feetitemhash = {}
    for curve in plotwidget.curves.values():
        feetitemhash.update(
            {
                f'{curve.name()}-{feetname}': (curve, feetname)
                for feetname in curve.feetitem.indices.keys()
            }
        )
    param = Parameter("Choose points to create curve", list(feetitemhash.keys()))
    qresult = askUserValue(param)
    curve, feetname = feetitemhash[qresult]

    newseries = curve.getFeetPoints(feetname)
    newseries.name = qresult

    newcurve = CurveItemWithPOI(
        parent=plotwidget, series=newseries, pen=plotwidget.getPen()
    )
    return [newcurve]
