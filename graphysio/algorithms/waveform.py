import itertools

import numpy as np
import pandas as pd

from graphysio.utils import truncatevecs
from graphysio.algorithms.filters import savgol


def findPressureFeet(curve):
    series = curve.series
    samplerate = curve.samplerate

    fstderiv = series.diff().shift(-1)
    sndderiv = fstderiv.diff().shift(-1)

    # Remove deceleration peaks
    sndderiv = sndderiv * (fstderiv > 0)

    def performWindowing(sumcoef=4, quantcoef=3):
        # Find pulse rising edge
        winsum = int(samplerate / sumcoef)
        winquant = int(samplerate * quantcoef)
        sndderivsq = sndderiv ** 2
        integral = sndderivsq.rolling(window=winsum, center=True).sum()
        thres = integral.rolling(window=winquant).quantile(0.7)
        thres = thres.fillna(method='backfill')
        risings = (integral > thres).astype(int)
        risingvar = risings.diff()
        (risingStarts,) = (risingvar > 0).to_numpy().nonzero()
        (risingStops,) = (risingvar < 0).to_numpy().nonzero()
        return (risingStarts, risingStops)

    found = False
    for quantcoef in [3, 2, 1]:
        # Try again with smaller window if we find nothing
        risingStarts, risingStops = performWindowing(quantcoef=quantcoef)
        try:
            risingStops = risingStops[risingStops > risingStarts[0]]
            found = True
            break
        except IndexError:
            continue

    # Last resort: find one foot on the whole series
    if not found:
        risingStarts = [0]
        risingStops = [len(sndderiv) - 1]

    def locateMaxima():
        for start, stop in zip(risingStarts, risingStops):
            idxstart = sndderiv.index[start]
            idxstop = sndderiv.index[stop]
            try:
                maximum = sndderiv.loc[idxstart:idxstop].idxmax()
            except ValueError:
                continue
            else:
                yield maximum

    cycleStarts = pd.Index(list(locateMaxima()))
    return cycleStarts


def findFlowCycles(curve):
    series = curve.series
    bincycles = (series > series.min()).astype(int)
    (idxstarts,) = (bincycles.diff().shift(-1) > 0).to_numpy().nonzero()
    (idxstops,) = (bincycles.diff() < 0).to_numpy().nonzero()
    cycleStarts = series.iloc[idxstarts]
    cycleStops = series.iloc[idxstops]

    # Handle the case where we start within a cycle
    try:
        cycleStops = cycleStops[cycleStops.index > cycleStarts.index[0]]
    except IndexError as e:
        raise TypeError(f'No cycle detected: {e}')

    return (cycleStarts.index, cycleStops.index)


def findPressureFullBak(curve):
    series = curve.series
    samplerate = curve.samplerate

    fstderivraw = series.diff().iloc[1:]
    sndderivraw = fstderivraw.diff().iloc[1:]
    # Smoothen the derivatives
    fstderiv, _ = savgol(fstderivraw, samplerate, (0.16, 2))
    sndderiv, _ = savgol(sndderivraw, samplerate, (0.16, 2))

    cycles = []
    starts, durations = curve.getCycleIndices()
    for start, duration in zip(starts, durations):
        stop = start + duration
        diastop = start - duration
        dia = findPOI(series, [start, diastop], 'min', windowsize=0.05, forcesign=False)
        sbp = findPOI(series, [start, stop], 'max', windowsize=0.05)
        peridic = findPOI(sndderiv, [sbp, stop], 'max', windowsize=0.15)
        dic = findHorizontal(fstderiv, peridic)
        cycle = (dia, sbp, dic)
        cycles.append(cycle)

    indices = [pd.Index(idx, dtype=np.int64) for idx in zip(*cycles)]
    return indices


def findPressureCycles(curve):
    series = curve.series

    cycles = []
    starts, durations = curve.getCycleIndices()
    for start, duration in zip(starts, durations):
        stop = start + duration
        diastop = start - duration
        dia = findPOI(series, [start, diastop], 'min', windowsize=0.05, forcesign=False)
        sbp = findPOI(series, [start, stop], 'max', windowsize=0.05)
        cycle = (dia, sbp)
        cycles.append(cycle)
    indices = [pd.Index(idx, dtype=np.int64) for idx in zip(*cycles)]
    return indices


def findPressureFull(curve):
    dia, sbp = findPressureCycles(curve)
    upstroke_duration = np.abs(sbp - dia)
    dia1, sbp1 = truncatevecs([dia[1:], sbp])
    dic = findDicProj(curve.series, dia1, sbp1, upstroke_duration)
    return [dia, sbp, dic]


# Utility function for point placing


def isbetter(new, ref, kind, forcesign):
    if kind == 'max':
        condition = new > ref
        if forcesign:
            condition = condition or (new < 0)
    elif kind == 'min':
        condition = new < ref
        if forcesign:
            condition = condition or (new > 0)
    else:
        raise ValueError(kind)
    return condition


def genWindows(soi, interval, windowspan):
    begin, end = interval
    ltr = end > begin
    windowspan *= 1e9  # s to ns
    if begin is None or end is None:
        return
    if ltr:
        direction = 1
    else:
        direction = -1
    for n in itertools.count():
        start = begin + direction * n * windowspan
        stop = start + direction * windowspan

        # Stop condition if we exceed end
        if ltr:
            if stop >= end:
                stop = end
        else:
            if stop <= end:
                stop = end
            start, stop = (stop, start)

        window = soi.loc[start:stop]
        if len(window) < 1:
            return
        yield window.index.values


def findPOI(soi, interval, kind, windowsize, forcesign=True):
    if kind not in ['min', 'max']:
        raise ValueError(kind)
    argkind = 'idx' + kind

    goodwindow = []
    previous = -np.inf if kind == 'max' else np.inf
    for window in genWindows(soi, interval, windowsize):
        zoi = soi.loc[window]
        new = getattr(zoi, kind)()
        if isbetter(new, previous, kind, forcesign):
            goodwindow = window
        else:
            break
        previous = new
    finalzoi = soi.loc[goodwindow]
    try:
        retidx = getattr(finalzoi, argkind)()
    except ValueError:
        # No POI found
        retidx = None
    return retidx


def findPOIGreedy(soi, start, kind):
    if kind not in ['min', 'max']:
        raise ValueError(kind)
    loc = soi.index.get_loc(start, method='nearest')
    # Find direction
    try:
        finddir = soi.iloc[[loc - 1, loc, loc + 1]]
    except IndexError:
        # We're at the edge of the curve
        return start
    npminmax = np.argmin if kind == 'min' else np.argmax
    direction = npminmax(finddir.values) - 1
    if direction == 0:
        # We're already at the local minimum
        return start
    curloc = loc
    while True:
        nextloc = curloc + direction
        try:
            samplesoi = soi.iloc[[curloc, nextloc]]
        except IndexError:
            # We're at the edge of the curve
            break
        nextisbetter = npminmax(samplesoi.values)
        if not nextisbetter:
            # Minimum found
            break
        curloc = nextloc
    return soi.index[curloc]


def findHorizontal(soi, loc):
    if loc is None:
        return None
    step = 8000000  # 8 ms (from ns)
    end = loc + 10 * step
    zoi = soi.loc[loc:end]
    horidx = zoi.abs().idxmin()
    return horidx


def distance(l1, l2, p):
    return np.cross(l2 - l1, p - l1) / np.linalg.norm(l2 - l1)


def findDicProj(series, dia, sbp, upstroke_duration):
    dics = []
    for si, di, up in zip(sbp, dia, upstroke_duration):
        zoi = series.loc[si:di]
        if len(zoi) < 1:
            continue
        p1 = np.array([si, zoi.iloc[0]])
        p2 = np.array([di, zoi.iloc[-1]])
        p3 = np.vstack([zoi.index, zoi.values]).transpose()
        d = distance(p1, p2, p3)
        # Limit search zone to the beginning of the segment
        search_len = len(series.loc[si : si + 2 * up])
        search_zone = d[0:search_len]
        argmin = np.argmin(search_zone)
        dics.append(zoi.index[argmin])
    return pd.Index(dics)
