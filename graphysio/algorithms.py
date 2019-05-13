import itertools
from functools import partial
from collections import namedtuple
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import signal, interpolate

from graphysio.utils import truncatevecs

Filter = namedtuple('Filter', ['name', 'parameters'])
Parameter = namedtuple('Parameter', ['description', 'request'])

DEBUGWIDGET = None

class TF(object):
    def __init__(self, num, den, name=''):
        self.num  = num
        self.den  = den
        self.name = name

    def discretize(self, samplerate):
        systf = (self.num, self.den)
        (dnum, dden, _) = signal.cont2discrete(systf, 1 / samplerate)
        return (np.squeeze(dnum), np.squeeze(dden))

TFs = {}
interpkind = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']

Filters = {'Lowpass filter' : Filter(name='lowpass', parameters=[Parameter('Cutoff frequency (Hz)', int), Parameter('Filter order', int)]),
           'Filter ventilation' : Filter(name='ventilation', parameters=[]),
           'Savitzky-Golay' : Filter(name='savgol', parameters=[Parameter('Window size (s)', float), Parameter('Polynomial order', int)]),
           'Interpolate' : Filter(name='interp', parameters=[Parameter('New sampling rate (Hz)', float), Parameter('Interpolation type', interpkind)]),
           'Doppler cut' : Filter(name='dopplercut', parameters=[Parameter('Minimum value', int)]),
           'Fill NaNs' : Filter(name='fillnan', parameters=[]),
           'Differentiate' : Filter(name='diff', parameters=[Parameter('Order', int)]),
           'Lag' : Filter(name='lag', parameters=[Parameter('Amount (s)', float)]),
           'Normalize' : Filter(name='norm1', parameters=[]),
           'Set start date/time' : Filter(name='setdatetime', parameters=[Parameter('DateTime', datetime)]),
           'Tolerant Normalize' : Filter(name='norm2', parameters=[]),
           'Enter expression (variable = x)' : Filter(name='expression', parameters=[Parameter('Expression', str)]),
           'Pressure scale' : Filter(name='pscale', parameters=[Parameter('Systole', int), Parameter('Diastole', int), Parameter('Mean', int)]),
           'Affine scale' : Filter(name='affine', parameters=[Parameter('Scale factor', float), Parameter('Translation factor', float)])}

FeetFilters = {'Short cycles' : Filter(name='shortcycles', parameters=[Parameter('Minimum duration (ms)', int)])}

def updateTFs():
    tflist = list(TFs.keys())
    Filters['Transfer function'] = Filter(name='tf', parameters=[Parameter('Transfer function', tflist)])
updateTFs()

def norm1(series, samplerate, parameters):
    series -= np.mean(series)
    series /= np.max(series) - np.min(series)
    newname = "{}-{}".format(series.name, 'norm')
    return (series.rename(newname), samplerate)

def norm2(series, samplerate, parameters):
    series -= np.mean(series)
    series /= np.std(series)
    newname = "{}-{}".format(series.name, 'norm')
    return (series.rename(newname), samplerate)

from sympy import lambdify
from sympy.abc import x
from sympy.parsing.sympy_parser import parse_expr
def expression(series, samplerate, parameters):
    express, = parameters
    expr = parse_expr(express)
    f = lambdify(x, expr, 'numpy')
    filtered = f(series.values)
    newname = "{}-{}".format(series.name, 'filtered')
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries.rename(newname), samplerate)

def setdatetime(series, samplerate, parameters):
    timestamp, = parameters
    newseries = series.copy()
    diff = timestamp - newseries.index[0]
    newseries.index += diff
    newname = "{}-{}".format(series.name, timestamp)
    return (newseries.rename(newname), samplerate)

def savgol(series, samplerate, parameters):
    window, order = parameters
    window = np.floor(window * samplerate)
    if not window % 2:
        # window is even, we need odd
        window += 1
    filtered = signal.savgol_filter(series.values, int(window), order)
    newname = "{}-{}".format(series.name, 'filtered')
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def lag(series, samplerate, parameters):
    timedelta, = parameters
    nindex = series.index.values + timedelta * 1e9
    newname = "{}-{}s".format(series.name, timedelta)
    newseries = pd.Series(series.values, index=nindex, name=newname)
    return (newseries, samplerate)

def affine(series, samplerate, parameters):
    a, b = parameters
    filtered = a * series + b
    newname = "{}-{}-{}-{}".format(series.name, 'affine', a, b)
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def tf(series, samplerate, parameters):
    filtname, = parameters
    tf = TFs[filtname]
    b, a = tf.discretize(samplerate)
    seriesnona = series.dropna()
    filtered = signal.lfilter(b, a, seriesnona)
    newname = "{}-{}".format(seriesnona.name, tf.name)
    newseries = pd.Series(filtered, index=seriesnona.index, name=newname)
    return (newseries, samplerate)

def lowpass(series, samplerate, parameters):
    Fc, order = parameters
    Wn = Fc * 2 / samplerate
    b, a = signal.butter(order, Wn)
    seriesnona = series.dropna()
    filtered = signal.lfilter(b, a, seriesnona)
    newname = "{}-lp{}".format(seriesnona.name, Fc)
    newseries = pd.Series(filtered, index=seriesnona.index, name=newname)
    return (newseries, samplerate)

def ventilation(series, samplerate, parameters):
    order = 8
    Wn = [Fc * 2 / samplerate for Fc in (.13, .36)]
    b, a = signal.butter(order, Wn, btype='bandstop')
    filtered = signal.lfilter(b, a, series)
    print(filtered)
    newname = "{}-novent".format(series.name)
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def interp(series, samplerate, parameters):
    newsamplerate, method = parameters
    oldidx = series.index
    f = interpolate.interp1d(oldidx, series.values, kind=method)
    step = 1e9 / newsamplerate # 1e9 to convert Hz to ns
    newidx = np.arange(oldidx[0], oldidx[-1], step, dtype=np.int64)
    resampled = f(newidx)
    newname = "{}-{}Hz".format(series.name, newsamplerate)
    newseries = pd.Series(resampled, index=newidx, name=newname)
    return (newseries, newsamplerate)

def dopplercut(series, samplerate, parameters):
    minvel, = parameters
    notlow, = (series < minvel).nonzero()
    newname = "{}-{}+".format(series.name, minvel)
    newseries = series.rename(newname)
    newseries.iloc[notlow] = 0
    return (newseries, samplerate)

def diff(series, samplerate, parameters):
    order, = parameters
    diffed = np.diff(series.values, order)
    newname = "{}-diff{}".format(series.name, order)
    newseries = pd.Series(diffed, index=series.index[order:], name=newname)
    return (newseries.rename(newname), samplerate)

def fillnan(series, samplerate, parameters):
    newseries = series.interpolate(method='index', limit_direction='both')
    newname = "{}-nona".format(series.name)
    return (newseries.rename(newname), samplerate)

def pscale(series, samplerate, parameters):
    sbp, dbp, mbp = parameters
    detrend = series - series.mean()
    scaled = detrend * (sbp - dbp) / (series.max() - series.min())
    newseries = scaled + mbp
    newname = "{}-pscale".format(series.name)
    return (newseries.rename(newname), samplerate)

filtfuncs = {'savgol'     : savgol,
             'affine'     : affine,
             'lag'        : lag,
             'tf'         : tf,
             'lowpass'    : lowpass,
             'ventilation': ventilation,
             'interp'     : interp,
             'dopplercut' : dopplercut,
             'diff'       : diff,
             'pscale'     : pscale,
             'norm1'      : norm1,
             'norm2'      : norm2,
             'expression' : expression,
             'setdatetime' : setdatetime,
             'fillnan'    : fillnan}

def filter(curve, filtname, paramgetter):
    samplerate = curve.samplerate
    series = curve.series
    filt = Filters[filtname]
    parameters = map(paramgetter, filt.parameters)
    return filtfuncs[filt.name](series, samplerate, parameters)

def filterFeet(starts, stops, filtname, paramgetter):
    filt = FeetFilters[filtname]
    parameters = map(paramgetter, filt.parameters)

    if filt.name == 'shortcycles':
        if len(stops) < 1:
            # No stop information
            raise ValueError('No stop feet')
        msMinDuration, = parameters
        minCycleLength = msMinDuration * 1e6 # Transform ms to ns
        cycleDurations = (stop - start for start, stop in zip(starts, stops))
        boolidx = [d >= minCycleLength for d in cycleDurations]
        starts, stops, boolidx = truncatevecs([starts, stops, boolidx])
        newstarts = starts[boolidx]
        newstops = stops[boolidx]
    else:
        errmsg = 'Unknown filter: {}'.format(filtname)
        raise ValueError(errmsg)
    return (newstarts, newstops)

def findPressureFeet(curve):
    series = curve.series.dropna()
    samplerate = curve.samplerate

    fstderiv = series.diff().shift(-1)
    sndderiv = fstderiv.diff().shift(-1)

    # Remove deceleration peaks
    sndderiv = sndderiv * (fstderiv > 0)

    def performWindowing(sumcoef = 4, quantcoef = 3):
        # Find pulse rising edge
        winsum   = int(samplerate / sumcoef)
        winquant = int(samplerate * quantcoef)
        sndderivsq  = sndderiv ** 2
        integral = sndderivsq.rolling(window=winsum, center=True).sum()
        thres = integral.rolling(window=winquant).quantile(.7)
        thres = thres.fillna(method='backfill')
        risings = (integral > thres).astype(int)
        risingvar = risings.diff()
        risingStarts, = (risingvar > 0).nonzero()
        risingStops,  = (risingvar < 0).nonzero()
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
        risingStops  = [len(sndderiv) - 1]

    def locateMaxima():
        for start, stop in zip(risingStarts, risingStops):
            idxstart = sndderiv.index[start]
            idxstop  = sndderiv.index[stop]
            try:
                maximum = sndderiv.loc[idxstart:idxstop].idxmax()
            except ValueError:
                continue
            else:
                yield maximum

    cycleStarts = pd.Index(list(locateMaxima()))
    return cycleStarts

def findFlowCycles(curve):
    series = curve.series.dropna()
    samplerate = curve.samplerate
    bincycles = (series > series.min()).astype(int)
    idxstarts, = (bincycles.diff().shift(-1) > 0).nonzero()
    idxstops,  = (bincycles.diff() < 0).nonzero()
    cycleStarts = series.iloc[idxstarts]
    cycleStops  = series.iloc[idxstops]

    # Handle the case where we start within a cycle
    try:
        cycleStops = cycleStops[cycleStops.index > cycleStarts.index[0]]
    except IndexError as e:
        raise TypeError("No cycle detected: {}".format(e))

    return (cycleStarts.index, cycleStops.index)

def findPressureFull(curve):
    from graphysio.debug import mplwidget
    global DEBUGWIDGET
    DEBUGWIDGET = mplwidget

    series = curve.series.dropna()
    samplerate = curve.samplerate

    fstderivraw = series.diff().iloc[1:]
    sndderivraw = fstderivraw.diff().iloc[1:]
    # Smoothen the derivatives
    fstderiv, _ = savgol(fstderivraw, samplerate, (.16, 2))
    sndderiv, _ = savgol(sndderivraw, samplerate, (.16, 2))

    if DEBUGWIDGET:
        DEBUGWIDGET.axes.plot(series.index.values, series.values)

    cycles = []
    starts, durations = curve.getCycleIndices()
    for start, duration in zip(starts, durations):
        stop = start + duration
        diastop = start - duration
        dia = findPOI(series, [start, diastop], 'min', windowsize=.05, forcesign=False)
        sbp = findPOI(series, [start, stop], 'max', windowsize=.05)
        peridic = findPOI(sndderiv, [sbp, stop], 'max', windowsize=.15)
        dic = findHorizontal(fstderiv, peridic)
        if DEBUGWIDGET:
            DEBUGWIDGET.axes.axvline(x=peridic)
            DEBUGWIDGET.axes.axvline(x=dic, color='r')
        cycle = (dia, sbp, dic)
        cycles.append(cycle)

    indices = [pd.Index(idx, dtype=np.int64) for idx in zip(*cycles)]
    return indices


# Utility function for point placing

def isbetter(new, ref, kind, forcesign):
    if kind == 'max':
        condition = (new > ref)
        if forcesign:
            condition = condition or (new < 0)
    elif kind == 'min':
        condition = (new < ref)
        if forcesign:
            condition = condition or (new > 0)
    else:
        raise ValueError(kind)
    return condition

def genWindows(soi, interval, windowspan):
    begin, end = interval
    ltr = (end > begin)
    windowspan *= 1e9 # s to ns
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
    global DEBUGWIDGET
    if kind not in ['min', 'max']:
        raise ValueError(kind)
    argkind = 'idx' + kind

    goodwindow = []
    previous = -np.inf if kind == 'max' else np.inf
    for window in genWindows(soi, interval, windowsize):
        zoi = soi.loc[window]
        if DEBUGWIDGET:
            DEBUGWIDGET.axes.plot(window, zoi.values * 50)
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
        finddir = soi.iloc[[loc-1, loc, loc+1]]
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
    global DEBUGWIDGET
    if loc is None:
        return None
    step = 8000000 # 8 ms (from ns)
    end = loc + 10 * step
    zoi = soi.loc[loc:end]
    if DEBUGWIDGET:
        DEBUGWIDGET.axes.plot(zoi.index.values, zoi.values * 50)
    horidx = zoi.abs().idxmin()
    return horidx
