from typing import List

import pandas as pd

from graphysio.dialogs import askUserValue
from graphysio.structures import Parameter
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI


def perfusionindex(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    curvenames = list(plotwidget.curves.keys())
    q = Parameter('Select Curve', curvenames)
    curvename = askUserValue(q)
    curve = plotwidget.curves[curvename]
    if (
        'start' not in curve.feetitem.indices
        or curve.feetitem.indices['start'].size < 1
    ):
        raise ValueError('No start information for curve')

    wave = curve.series
    starts = curve.getFeetPoints('start')
    df = pd.concat([wave, starts], axis=1)
    df = df.interpolate(method='index')

    begins, durations = curve.getCycleIndices()
    pivalues = []
    for begin, duration in zip(begins, durations):
        cycle = df.loc[begin : begin + duration]
        auctot = cycle[wave.name].sum()
        aucbase = cycle[starts.name].sum()
        aucpulse = auctot - aucbase
        pi = aucpulse / auctot
        pivalues.append(pi)

    piseries = pd.Series(pivalues, index=begins)
    piseries.name = f'{wave.name}-perf'

    newcurve = CurveItemWithPOI(
        parent=plotwidget, series=piseries, pen=plotwidget.getPen()
    )
    return [newcurve]


def feettocurve(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
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


Transformations = {'Perfusion Index': perfusionindex, 'Feet to Curve': feettocurve}
