import sys
from collections import namedtuple

import numpy as np
import pandas as pd
import scipy.signal as signal


Filter = namedtuple('Filter', ['type', 'parameters'])
Parameter = namedtuple('Parameter', ['description', 'type'])

class TF(object):
    def __init__(self, num, den, name=''):
        self.num  = num
        self.den  = den
        self.name = name

    def discretize(self, samplerate):
        sys = (self.num, self.den)
        (dnum, dden, dt) = signal.cont2discrete(sys, 1 / samplerate)
        return (np.squeeze(dnum), np.squeeze(dden))

sphygmonum = [0.693489245308734, 132.978069767093, 87009.5691967337, 10914873.0713084, 218273825.541909, 6489400920.14402]
sphygmoden = [1, 180.289425270434, 174563.510125383, 17057258.6774222, 555352944.277185, 6493213494.43661]
tfsphygmo = TF(sphygmonum, sphygmoden, name='Sphygmo TF')

TFs = {tfsphygmo.name : tfsphygmo}

Filters = {'Lowpass filter' : Filter(type='lp', parameters=[Parameter('Cutoff frequency (Hz)', int), Parameter('Filter order', int)]),
           'Savitzky-Golay' : Filter(type='savgol', parameters=[Parameter('Window length (s)', float), Parameter('Polynomial order', int)]),
           'Sphygmo TF' : Filter(type='tf', parameters=[])}

def filter(curve, filtname, typefullfiller):
    samplerate = curve.samplerate
    oldseries = curve.series.dropna()
    if samplerate is None:
        print("Samplerate is not set and could not be inferred.", file=sys.stderr)
        return None

    try:
        filt = Filters[filtname]
    except KeyError:
        return None

    parameters = map(typefullfiller, filt.parameters)

    if filt.type == 'tf':
        tf = TFs[filtname]
        b, a = tf.discretize(samplerate)
        filtered = signal.lfilter(b, a, oldseries)
        newname = "{}-{}".format(oldseries.name, tf.name)
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    elif filt.type == 'savgol':
        window, order = parameters
        # Get the closest odd integer for the window
        window = np.floor(window * samplerate)
        if not window % 2:
            # window is even, we need odd
            window += 1
        filtered = signal.savgol_filter(oldseries, int(window), order)
        newname = "{}-{}".format(oldseries.name, 'filtered')
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    elif filt.type == 'lp':
        Fc, order = parameters
        Wn = Fc * 2 / samplerate
        b, a = signal.butter(order, Wn)
        filtered = signal.lfilter(b, a, oldseries)
        newname = "{}-lowpass".format(oldseries.name)
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    else:
        newseries = None
    return newseries

def findPressureFeet(curve):
    series = curve.series.dropna()
    samplerate = curve.samplerate
    if samplerate is None:
        print("Samplerate is not set and could not be inferred.", file=sys.stderr)
        return pd.Series()

    fstderiv = series.diff().shift(-1)
    sndderiv = fstderiv.diff().shift(-1)

    # Remove deceleration peaks
    sndderiv = sndderiv * (fstderiv > 0)

    # Find pulse rising edge
    winsum   = int(samplerate / 4)
    winquant = int(samplerate * 3)
    sndderivsq  = sndderiv ** 2
    integral = sndderivsq.rolling(window=winsum,center=True).sum()
    thres    = integral.rolling(window=winquant).quantile(.7)
    thres    = thres.fillna(method='backfill')
    risings = (integral > thres).astype(int)

    risingvar = risings.diff()
    risingStarts, = (risingvar > 0).nonzero()
    risingStops,  = (risingvar < 0).nonzero()

    # Handle the case where we start near a foot
    try:
        risingStops = risingStops[risingStops > risingStarts[0]]
    except IndexError as e:
        print("No foot detected: {}".format(e), file=sys.stderr)
        return pd.Series()

    def locateMaxima():
        for start, stop in zip(risingStarts, risingStops):
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
    series = series.dropna()
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
        minSystoleLength = pd.Timedelta('200ms')
        def notShortCycles():
            for (startidx, stopidx) in zip(cycleStarts.index, cycleStops.index):
                if stopidx - startidx >= minSystoleLength:
                    yield (startidx, stopidx)
        (startidx, stopidx) = zip(*notShortCycles())
        cycleStarts = cycleStarts[list(startidx)]
        cycleStops = cycleStops[list(stopidx)]

    return (cycleStarts, cycleStops)
