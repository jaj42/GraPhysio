from typing import List
from datetime import datetime

import pyedflib
import numpy as np
from scipy import interpolate

from graphysio.plotwidgets.curves import CurveItem


def interp_series(s, start, stop):
    f = interpolate.interp1d(
        s.index, s.values, assume_sorted=True, fill_value=0, copy=False
    )
    newidx = np.linspace(start, stop, num=len(s))
    resampled = f(newidx)
    return resampled


def curves_to_edf(
    curves: List[CurveItem], filepath: str, index_label: str = 'timens'
) -> None:
    headers = []
    signals = []

    beginns = min([c.series.index[0] for c in curves])
    endns = max([c.series.index[-1] for c in curves])
    begindt = datetime.fromtimestamp(beginns * 1e-9)

    for c in curves:
        s = c.series
        header = {
            'label': c.name(),
            'sample_rate': c.samplerate,
            'physical_max': s.max(),
            'physical_min': s.min(),
            'digital_max': 32767,
            'digital_min': -32768,
            'transducer': '',
            'prefilter': '',
            'dimension': '',
        }
        headers.append(header)
        resampled = interp_series(s, beginns, endns)
        signals.append(resampled)

    edf = pyedflib.EdfWriter(
        str(filepath), len(signals), file_type=pyedflib.FILETYPE_EDFPLUS
    )
    edf.setStartdatetime(begindt)
    edf.setSignalHeaders(headers)
    edf.writeSamples(signals)
    edf.close()
