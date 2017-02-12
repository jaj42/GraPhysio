import sys
from collections import namedtuple

import numpy as np
import pandas as pd
from scipy import signal, interpolate


Filter = namedtuple('Filter', ['name', 'parameters'])
Parameter = namedtuple('Parameter', ['description', 'request'])

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

interpkind = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']
Filters = {'Lowpass filter' : Filter(name='lowpass', parameters=[Parameter('Cutoff frequency (Hz)', int), Parameter('Filter order', int)]),
           'Savitzky-Golay' : Filter(name='savgol', parameters=[Parameter('Window size (s)', float), Parameter('Polynomial order', int)]),
           'Interpolate' : Filter(name='interp', parameters=[Parameter('New sampling rate (Hz)', int), Parameter('Interpolation type', interpkind)]),
           'Doppler cut' : Filter(name='dopplercut', parameters=[Parameter('Minimum velocity (cm/s)', int)]),
           'Sphygmo TF' : Filter(name='tf', parameters=[])}

def filter(curve, filtname, paramgetter):
    samplerate = curve.samplerate
    oldseries = curve.series
    if samplerate is None:
        raise TypeError("Samplerate is not set and could not be inferred.")

    filt = Filters[filtname]
    parameters = map(paramgetter, filt.parameters)

    if filt.name == 'tf':
        tf = TFs[filtname]
        b, a = tf.discretize(samplerate)
        filtered = signal.lfilter(b, a, oldseries)
        newname = "{}-{}".format(oldseries.name, tf.name)
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    elif filt.name == 'savgol':
        window, order = parameters
        window = np.floor(window * samplerate)
        if not window % 2:
            # window is even, we need odd
            window += 1
        filtered = signal.savgol_filter(oldseries, int(window), order)
        newname = "{}-{}".format(oldseries.name, 'filtered')
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    elif filt.name == 'lowpass':
        Fc, order = parameters
        Wn = Fc * 2 / samplerate
        b, a = signal.butter(order, Wn)
        filtered = signal.lfilter(b, a, oldseries)
        newname = "{}-lowpass".format(oldseries.name)
        newseries = pd.Series(filtered, index=oldseries.index, name=newname)
    elif filt.name == 'interp':
        newsamplerate, method = parameters
        npoints = len(oldseries) * newsamplerate / samplerate
        oldidx = oldseries.index
        f = interpolate.interp1d(oldidx, oldseries.values, kind=method)
        newidx = np.linspace(oldidx[1], oldidx[-1], num=npoints)
        resampled = f(newidx)
        newname = "{}-{}Hz".format(oldseries.name, newsamplerate)
        newseries = pd.Series(resampled, index=newidx, name=newname)
        samplerate = newsamplerate
    elif filt.name == 'dopplercut':
        minvel, = parameters
        notlow, = (oldseries < minvel).nonzero()
        newname = "{}-{}+".format(oldseries.name, minvel)
        newseries = oldseries.rename(newname)
        newseries.iloc[notlow] = 0
    else:
        raise TypeError("Unknown filter.")

    return (newseries, samplerate)

def findPressureFeet(curve):
    series = curve.series
    samplerate = curve.samplerate
    if samplerate is None:
        raise TypeError("Samplerate is not set and could not be inferred.")

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

    for quantcoef in [3, 2, 1]:
        risingStarts, risingStops = performWindowing(quantcoef=quantcoef)
        try:
            risingStops = risingStops[risingStops > risingStarts[0]]
            break
        except IndexError as e:
            if quantcoef == 1:
                raise TypeError("No foot detected: {}".format(e))

    def locateMaxima():
        for start, stop in zip(risingStarts, risingStops):
            idxstart = sndderiv.index.values[start]
            idxstop  = sndderiv.index.values[stop]
            try:
                maximum = sndderiv.ix[idxstart:idxstop].idxmax()
            except ValueError as e:
                print("local maximum error: {} [{} - {}] in [{} - {}]".format(e, idxstart, idxstop, sndderiv.index[0], sndderiv.index[-1]), file=sys.stderr)
                continue
            else:
                yield maximum

    return series[list(locateMaxima())]

def findFlowCycles(curve):
    series = curve.series
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

    # Filter noise cycles which are shorter than 150ms
    #startidx, stopidx = zip(*zip(cycleStarts.index, cycleStops.index))
    minSystoleLength = 15e5 * samplerate
    def notShortCycles():
        for (startidx, stopidx) in zip(cycleStarts.index, cycleStops.index):
            if stopidx - startidx >= minSystoleLength:
                yield (startidx, stopidx)
    startidx, stopidx = zip(*notShortCycles())
    cycleStarts = cycleStarts[list(startidx)]
    cycleStops = cycleStops[list(stopidx)]

    return (cycleStarts, cycleStops)
