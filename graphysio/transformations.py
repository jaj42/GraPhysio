from typing import List

import pandas as pd

from graphysio.dialogs import askUserValue
from graphysio.types import Parameter
from graphysio.tsplot import PlotWidget, CurveItem

def perfusionindex(plotwidget: PlotWidget) -> List[CurveItem]:
    curvenames = list(plotwidget.curves.keys())
    q = Parameter('Select Curve', curvenames)
    curvename = askUserValue(q)
    curve = plotwidget.curves[curvename]
    fi = curve.feetitem
    if fi is None or fi.starts.size < 1:
        raise ValueError('No start feet for curve')

    wave = curve.series
    starts = fi.starts['points']
    df = pd.concat([wave, starts], axis=1)
    df = df.interpolate(method='index')

    begins, durations = curve.getCycleIndices()
    pivalues = []
    for begin, duration in zip(begins, durations):
        cycle = df.loc[begin:begin+duration]
        auctot = cycle[wave.name].sum()
        aucbase = cycle[starts.name].sum()
        aucpulse = auctot - aucbase
        pi = aucpulse / auctot
        pivalues.append(pi)

    piseries = pd.Series(pivalues, index=begins)
    piseries.name = "{}-{}".format(wave.name, 'perf')

    newcurve = CurveItem(piseries, pen=plotwidget.getPen())
    return [newcurve]

def feettocurve(plotwidget: PlotWidget) -> List[CurveItem]:
    feetitems = {}
    for curve in plotwidget.curves.values():
        feetitems.update(curve.feetitems)
    feetnames = list(feetitems.keys())
    q = Parameter('Select Curve', feetnames)
    feetname = askUserValue(q)
    fi = feetitems[feetname]
    newcurve = CurveItem(piseries, pen=plotwidget.getPen())
    return [newcurve]
