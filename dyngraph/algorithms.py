import sys

import numpy as np
import pandas as pd

def findPressureFeet(series):
    sndderiv = series.diff().diff().shift(-2)
    try:
        threshold = np.percentile(sndderiv.dropna(), 98)
    except IndexError as e:
        print("percentile error: {}".format(e), sys.stderr)
        return pd.Series()

    peaks = np.diff((sndderiv > threshold).astype(int))
    peakStarts = np.flatnonzero(peaks > 0)
    peakStops  = np.flatnonzero(peaks < 0)

    def locateMaxima():
        for start, stop in zip(peakStarts, peakStops):
            idxstart = sndderiv.index.values[start]
            idxstop  = sndderiv.index.values[stop]
            maximum = sndderiv[idxstart:idxstop].idxmax()
            yield maximum

    return series[list(locateMaxima())]

def findFlowCycles(series):
    bincycles = (series > series.min()).astype(int)
    idxstarts, = (bincycles.diff().shift(-1) > 0).nonzero()
    idxstops,  = (bincycles.diff() < 0).nonzero()
    cycleStarts = series.iloc[idxstarts]
    cycleStops  = series.iloc[idxstops]

    # Handle the case where we start within a cycle
    cycleStops = cycleStops[cycleStops.index > cycleStarts.index[0]]

    # Filter noise cycles which are shorter than 240ms
    if type(series.index) == pd.tseries.index.DatetimeIndex:
        def notShortCycles():
            minSystoleLength = pd.Timedelta('240ms')
            for (startidx, stopidx) in zip(cycleStarts.index, cycleStops.index):
                if stopidx - startidx >= minSystoleLength:
                    yield (startidx, stopidx)
        (startidx, stopidx) = zip(*notShortCycles())
        cycleStarts = cycleStarts[list(startidx)]
        cycleStops = cycleStops[list(stopidx)]

    return (cycleStarts, cycleStops)
