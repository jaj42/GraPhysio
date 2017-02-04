import sys
import numpy as np
import pandas as pd
import scipy.signal as signal


class TF(object):
    def __init__(self, num, den, name=''):
        self.num  = num
        self.den  = den
        self.name = name

    def discretize(self, samplerate):
        sys = (self.num, self.den)
        (dnum, dden, dt) = signal.cont2discrete(sys, 1 / samplerate)
        return (np.squeeze(dnum), np.squeeze(dden))

combinum = [1]
combiden = [1]
tfcombi = TF(combinum, combiden, name='tfcombi')

sphygmonum = [0.693489245308734, 132.978069767093, 87009.5691967337, 10914873.0713084, 218273825.541909, 6489400920.14402]
sphygmoden = [1, 180.289425270434, 174563.510125383, 17057258.6774222, 555352944.277185, 6493213494.43661]
tfsphygmo = TF(sphygmonum, sphygmoden, name='tfsphygmo')

Filters = {'savgol125' : 'savgol',
           'tfsphygmo' : 'tf',
           'tfcombi'   : 'tf'}

TFs = {tfsphygmo.name : tfsphygmo,
       tfcombi.name   : tfcombi}

SavGols = {'savgol125' : [3, 29]}

def filter(curve, filtname):
    series = curve.series
    samplerate = curve.samplerate
    if samplerate is None:
        print("Samplerate is not set and could not be inferred.", file=sys.stderr)
        return None

    try:
        filttype = Filters[filtname]
    except KeyError:
        return None

    if filttype == 'tf':
        return applytf(series, TFs[filtname], samplerate)
    elif filttype == 'savgol':
        order, window = SavGols[filtname]
        return applysavgol(series, order, window)
    else:
        return None

def applytf(series, tf, samplerate):
    oldseries = series.dropna()
    (b, a) = tf.discretize(samplerate)
    filtered = signal.lfilter(b, a, oldseries)
    newname = "{}-{}".format(oldseries.name, tf.name)
    return pd.Series(filtered, index=oldseries.index, name=newname)

def applysavgol(series, order, window):
    oldseries = series.dropna()
    filtered = signal.savgol_filter(oldseries, window, order)
    newname = "{}-{}".format(oldseries.name, 'filtered')
    return pd.Series(filtered, index=oldseries.index, name=newname)

def pulsePeaks(series, deriv, samplerate):
    winsum   = int(samplerate / 4)
    winquant = int(samplerate * 3)
    derivsq  = deriv ** 2
    integral = derivsq.rolling(window=winsum,center=True).sum()
    thres    = integral.rolling(window=winquant).quantile(.7)
    thres    = thres.fillna(method='backfill')
    return (integral > thres).astype(int)

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

    peaks = pulsePeaks(series, sndderiv, samplerate)
    peakvar = peaks.diff()
    peakStarts, = (peakvar > 0).nonzero()
    peakStops,  = (peakvar < 0).nonzero()

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
