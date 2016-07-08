import sys

import numpy as np
import pandas as pd

def calcSampleRate(series):
    if type(series.index) != pd.tseries.index.DatetimeIndex:
        print("No time information for cycle identification", file=sys.stderr)
        return 125
    starttime = series.index.values[0]
    stopidx = series.index.get_loc(starttime + pd.Timedelta('1s'), method='nearest')
    return stopidx

def pulsePeaks(series, deriv):
    samplerate = calcSampleRate(series)
    winsum   = int(samplerate / 4)
    winquant = int(samplerate * 3)
    derivsq  = deriv ** 2
    integral = derivsq.rolling(window=winsum,center=True).sum()
    thres    = integral.rolling(window=winquant).quantile(.7)
    thres    = thres.fillna(method='backfill')
    return (integral > thres).astype(int)

def findPressureFeet(series):
    fstderiv = series.diff().shift(-1)
    sndderiv = fstderiv.diff().shift(-1)

    # Remove deceleration peaks
    sndderiv = sndderiv * (fstderiv > 0)

    peaks = pulsePeaks(series, sndderiv)
    peakvar = np.diff(peaks.astype(int))
    peakStarts = np.flatnonzero(peakvar > 0)
    peakStops  = np.flatnonzero(peakvar < 0)

    # Handle the case where we start near a foot
    try:
        peakStops = peakStops[peakStops > peakStarts[0]]
    except IndexError as e:
        print("No foot detected: {}".format(e), file=sys.stderr)
        return pd.Series()

    def locateMaxima():
        for start, stop in zip(peakStarts, peakStops):
            idxstart = sndderiv.index.values[start]
            idxstop  = sndderiv.index.values[stop]
            try:
                maximum = sndderiv[idxstart:idxstop].idxmax()
            except ValueError as e:
                print("local maximum error: {} [{} - {}]".format(e, idxstart, idxstop), file=sys.stderr)
                continue
            else:
                yield maximum

    return series[list(locateMaxima())]

def findFlowCycles(series):
    bincycles = (series > series.min()).astype(int)
    idxstarts, = (bincycles.diff().shift(-1) > 0).nonzero()
    idxstops,  = (bincycles.diff() < 0).nonzero()
    cycleStarts = series.iloc[idxstarts]
    cycleStops  = series.iloc[idxstops]

    # Handle the case where we start within a cycle
    try:
        cycleStops = cycleStops[cycleStops.index > cycleStarts.index[0]]
    except IndexError as e:
        print("No cycle detected: {}".format(e), file=sys.stderr)
        return (pd.Series(), pd.Series())

    # Filter noise cycles which are shorter than 240ms
    if type(series.index) == pd.tseries.index.DatetimeIndex:
        minSystoleLength = pd.Timedelta('240ms')
        def notShortCycles():
            for (startidx, stopidx) in zip(cycleStarts.index, cycleStops.index):
                if stopidx - startidx >= minSystoleLength:
                    yield (startidx, stopidx)
        (startidx, stopidx) = zip(*notShortCycles())
        cycleStarts = cycleStarts[list(startidx)]
        cycleStops = cycleStops[list(stopidx)]

    return (cycleStarts, cycleStops)
