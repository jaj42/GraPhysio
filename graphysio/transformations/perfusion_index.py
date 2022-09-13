from typing import List

import pandas as pd
from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter


def get_perfusion_index(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    curvenames = list(plotwidget.curves.keys())
    curvenames = list(plotwidget.curves.keys())
    if len(curvenames) < 1:
        raise ValueError('No curve')
    elif len(curvenames) > 1:
        q = Parameter('Select Curve', curvenames)
        curvename = askUserValue(q)
    else:
        curvename = curvenames[0]

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
