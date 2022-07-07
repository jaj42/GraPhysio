from datetime import datetime
from typing import List

import numpy as np
from graphysio.dialogs import askUserValue
from graphysio.plotwidgets.curves import CurveItem
from graphysio.structures import Parameter
from scipy import interpolate

try:
    import pyedflib
except ImportError:
    is_available = False
else:
    is_available = True


def interp_series(s, samplerate, start, stop):
    f = interpolate.interp1d(
        s.index, s.values, assume_sorted=True, copy=False, fill_value='extrapolate'
    )
    # Account for periods of missing data.
    duration_s = (stop - start) * 1e-9
    npoints = int(duration_s * samplerate)
    newidx = np.linspace(start, stop, num=npoints)
    return f(newidx)


def curves_to_edf(
    curves: List[CurveItem], filepath: str, index_label: str = 'timens'
) -> None:
    headers = []
    signals = []

    beginns = min(c.series.index[0] for c in curves)
    endns = max(c.series.index[-1] for c in curves)
    begindt = datetime.fromtimestamp(beginns * 1e-9)

    # Use global min / max of values since some viewers need this (edfbrowser)
    physmax = max(c.series.max() for c in curves)
    physmin = min(c.series.min() for c in curves)

    # Ask the user for the physical dimension shared by all curves
    dim = askUserValue(Parameter('Enter physical dimension', str))

    for c in curves:
        s = c.series
        header = {
            'label': c.name(),
            'sample_rate': c.samplerate,
            'physical_max': physmax,
            'physical_min': physmin,
            'digital_max': 32767,
            'digital_min': -32768,
            'transducer': '',
            'prefilter': '',
            'dimension': dim,
        }
        headers.append(header)
        resampled = interp_series(s, c.samplerate, beginns, endns)
        signals.append(resampled)

    edf = pyedflib.EdfWriter(
        str(filepath), len(signals), file_type=pyedflib.FILETYPE_EDFPLUS
    )
    edf.setStartdatetime(begindt)
    edf.setSignalHeaders(headers)
    edf.writeSamples(signals)
    edf.close()


curves_to_edf.is_available = is_available
