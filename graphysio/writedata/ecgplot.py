from typing import List

from graphysio.plotwidgets.curves import CurveItem
import numpy as np
from scipy import interpolate

import ecg_plot


def interp_series(s, start, stop, npoints):
    f = interpolate.interp1d(
        s.index,
        s.values,
        assume_sorted=True,
        copy=False,
        fill_value="extrapolate",
    )
    newidx = np.linspace(start, stop, num=npoints)
    return f(newidx)


def export_curves(
    curves: List[CurveItem],
    filepath: str,
    index_label: str = "timens",
) -> None:
    beginns = min(c.series.index[0] for c in curves)
    endns = max(c.series.index[-1] for c in curves)
    duration_s = (endns - beginns) * 1e-9
    samplerate = int(max([c.samplerate for c in curves]))
    npoints = int(duration_s * samplerate)
    resampled = [interp_series(c.series, beginns, endns, npoints) for c in curves]
    ecg = np.vstack(resampled)
    names = [c.name() for c in curves]
    ecg_plot.plot(
        ecg, sample_rate=samplerate, title=filepath.stem, lead_index=names, columns=1
    )
    ecg_plot.save_as_png(filepath.stem, f"{filepath.parent}/")


export_curves.is_available = True
