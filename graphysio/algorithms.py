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

pulseheartnum = [0.693489245308734, 132.978069767093, 87009.5691967337, 10914873.0713084, 218273825.541909, 6489400920.14402]
pulseheartden = [1, 180.289425270434, 174563.510125383, 17057258.6774222, 555352944.277185, 6493213494.43661]
tfpulseheart = TF(pulseheartnum, pulseheartden, name='HeartPulse')

tfs = {tfpulseheart.name : tfpulseheart}
interpkind = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']

Filters = {'Lowpass filter' : Filter(name='lowpass', parameters=[Parameter('Cutoff frequency (Hz)', int), Parameter('Filter order', int)]),
           'Savitzky-Golay' : Filter(name='savgol', parameters=[Parameter('Window size (s)', float), Parameter('Polynomial order', int)]),
           'Interpolate' : Filter(name='interp', parameters=[Parameter('New sampling rate (Hz)', int), Parameter('Interpolation type', interpkind)]),
           'Doppler cut' : Filter(name='dopplercut', parameters=[Parameter('Minimum velocity (cm/s)', int)]),
           'Fill NaNs' : Filter(name='fillnan', parameters=[]),
           'Pressure scale' : Filter(name='pscale', parameters=[Parameter('Systole', int), Parameter('Diastole', int), Parameter('Mean', int)]),
           'Affine scale' : Filter(name='affine', parameters=[Parameter('a (y=ax+b)', float), Parameter('b (y=ax+b)', float)]),
           'Transfer function' : Filter(name='tf', parameters=[Parameter('Transfer function', list(tfs.keys()))])}

def _savgol(series, samplerate, parameters):
    window, order = parameters
    window = np.floor(window * samplerate)
    if not window % 2:
        # window is even, we need odd
        window += 1
    filtered = signal.savgol_filter(series, int(window), order)
    newname = "{}-{}".format(series.name, 'filtered')
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def _affine(series, samplerate, parameters):
    a, b = parameters
    filtered = a * series + b
    newname = "{}-{}-{}-{}".format(series.name, 'affine', a, b)
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def _tf(series, samplerate, parameters):
    filtname, = parameters
    tf = tfs[filtname]
    b, a = tf.discretize(samplerate)
    filtered = signal.lfilter(b, a, series)
    newname = "{}-{}".format(series.name, tf.name)
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def _lowpass(series, samplerate, parameters):
    Fc, order = parameters
    Wn = Fc * 2 / samplerate
    b, a = signal.butter(order, Wn)
    filtered = signal.lfilter(b, a, series)
    newname = "{}-lp{}".format(series.name, Fc)
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)

def _interp(series, samplerate, parameters):
    newsamplerate, method = parameters
    npoints = len(series) * newsamplerate / samplerate
    oldidx = series.index
    f = interpolate.interp1d(oldidx, series.values, kind=method)
    newidx = np.linspace(oldidx[1], oldidx[-1], num=npoints)
    resampled = f(newidx)
    newname = "{}-{}Hz".format(series.name, newsamplerate)
    newseries = pd.Series(resampled, index=newidx, name=newname)
    return (newseries, newsamplerate)

def _dopplercut(series, samplerate, parameters):
    minvel, = parameters
    notlow, = (series < minvel).nonzero()
    newname = "{}-{}+".format(series.name, minvel)
    newseries = series.rename(newname)
    newseries.iloc[notlow] = 0
    return (newseries, samplerate)

def _fillnan(series, samplerate, parameters):
    newseries = series.interpolate(method='index', limit_direction='both')
    newname = "{}-nona".format(series.name)
    return (newseries.rename(newname), samplerate)

def _pscale(series, samplerate, parameters):
    sys, dia, mean = parameters
    detrend = series - series.mean()
    scaled = detrend * (sys - dia) / (series.max() - series.min())
    newseries = scaled + mean
    newname = "{}-pscale".format(series.name)
    return (newseries.rename(newname), samplerate)

filtfuncs = {'savgol'     : _savgol,
             'affine'     : _affine,
             'tf'         : _tf,
             'lowpass'    : _lowpass,
             'interp'     : _interp,
             'dopplercut' : _dopplercut,
             'pscale'     : _pscale,
             'fillnan'    : _fillnan}

def filter(curve, filtname, paramgetter):
    samplerate = curve.samplerate
    series = curve.series
    if samplerate is None:
        raise TypeError("Samplerate is not set and could not be inferred.")

    filt = Filters[filtname]
    parameters = map(paramgetter, filt.parameters)

    return filtfuncs[filt.name](series, samplerate, parameters)

def findPressureFeet(curve):
    series = curve.series.dropna()
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

    found = False
    for quantcoef in [3, 2, 1]:
        # Try again with smaller window if we find nothing
        risingStarts, risingStops = performWindowing(quantcoef=quantcoef)
        try:
            risingStops = risingStops[risingStops > risingStarts[0]]
            found = True
            break
        except IndexError as e:
            continue

    # Last resort: find one foot on the whole series
    if not found:
        risingStarts = [0]
        risingStops  = [len(sndderiv.index) - 1]

    def locateMaxima():
        for start, stop in zip(risingStarts, risingStops):
            idxstart = sndderiv.index[start]
            idxstop  = sndderiv.index[stop]
            try:
                maximum = sndderiv.ix[idxstart:idxstop].idxmax()
            except ValueError as e:
                print("local maximum error: {} [{} - {}] in [{} - {}]".format(e, idxstart, idxstop, sndderiv.index[0], sndderiv.index[-1]), file=sys.stderr)
                continue
            else:
                yield maximum

    cycleStarts = series[list(locateMaxima())]
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

    # Filter noise cycles which are shorter than 150ms
    #minSystoleLength = 15e5 * samplerate
    #def notShortCycles():
    #    for (startidx, stopidx) in zip(cycleStarts.index, cycleStops.index):
    #        if stopidx - startidx >= minSystoleLength:
    #            yield (startidx, stopidx)
    #startidx, stopidx = zip(*notShortCycles())
    startidx, stopidx = zip(*zip(cycleStarts.index, cycleStops.index))
    cycleStarts = cycleStarts[list(startidx)]
    cycleStops = cycleStops[list(stopidx)]

    return (cycleStarts, cycleStops)
