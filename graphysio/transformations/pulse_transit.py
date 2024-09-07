from typing import List

import numpy as np
import pandas as pd
from physiocurve.pressure.foot import find_tangent_intersections
from physiocurve.pressure.incycle import find_dia_sys

from graphysio.dialogs import askUserValue
from graphysio.plotwidgets import PlotWidget
from graphysio.plotwidgets.curves import CurveItemWithPOI
from graphysio.structures import Parameter, PlotData
from graphysio.utils import truncatevecs


def get_tt(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    feetitemhash = build_feet_dict(plotwidget.curves)

    param = Parameter("Choose starting points", list(feetitemhash))
    qresult = askUserValue(param)
    beg_curve, beg_feetname = feetitemhash[qresult]

    param = Parameter("Choose ending points", list(feetitemhash))
    qresult = askUserValue(param)
    end_curve, end_feetname = feetitemhash[qresult]

    idxbeg = beg_curve.feetitem.indices[beg_feetname]
    idxend = end_curve.feetitem.indices[end_feetname]
    idxbeg, idxend = truncatevecs([idxbeg, idxend])

    tt = np.abs(idxend - idxbeg)  # nanoseconds
    tt /= 1e6  # milliseconds

    out_series = pd.Series(tt, index=idxbeg)
    sname = f"TT [{beg_curve.name()}_{beg_feetname} - {end_curve.name()}_{end_feetname}] (ms)"
    plotdata = PlotData(data=out_series, name=sname)

    return [plotdata]


def get_pat(plotwidget: PlotWidget) -> List[CurveItemWithPOI]:
    curvenames = list(plotwidget.curves.keys())
    if len(curvenames) < 2:
        msg = "Insufficient data"
        raise ValueError(msg)
    q = Parameter("Select ECG curve", curvenames)
    curvename = askUserValue(q)
    ecgcurve = plotwidget.curves[curvename]

    q = Parameter("Select Pulse curve", curvenames)
    curvename = askUserValue(q)
    pulsecurve = plotwidget.curves[curvename]
    pulse = pulsecurve.series

    try:
        idxfeet = pulsecurve.feetitem.indices["start"]
        idxrwave = ecgcurve.feetitem.indices["rwave"]
    except KeyError as e:
        msg = "Detect feet and R waves first"
        raise ValueError(msg) from e

    argfeet = pulse.index.get_indexer(idxfeet)
    argdia, argsys = find_dia_sys(pulse.to_numpy(), pulsecurve.samplerate, argfeet)
    precise_feet = find_tangent_intersections(pulse.to_numpy(), argdia, argsys)

    time_scale = (pulse.index[-1] - pulse.index[0]) / len(pulse)
    idx_precise_feet = precise_feet * time_scale + pulse.index[0]

    idx_precise_feet, idxrwave = truncatevecs([idx_precise_feet, idxrwave])

    pat = np.abs(idx_precise_feet - idxrwave)  # nanoseconds
    pat /= 1e6  # milliseconds

    out_series = pd.Series(pat, index=idxrwave)
    sname = f"PAT {pulse.name} (ms)"
    plotdata = PlotData(data=out_series, name=sname)

    return [plotdata]


def build_feet_dict(curves):
    feetitemhash = {}
    for curve in curves.values():
        feetitemhash.update(
            {
                f"{curve.name()}-{feetname}": (curve, feetname)
                for feetname in curve.feetitem.indices
            },
        )
    return feetitemhash
