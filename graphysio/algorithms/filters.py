from datetime import datetime
from math import ceil
from typing import Dict

import numexpr as ne
import numpy as np
import pandas as pd
from graphysio.structures import Filter, Parameter
from graphysio.utils import truncatevecs
from scipy import interpolate, signal


class TF(object):
    def __init__(self, num, den, name=''):
        self.num = num
        self.den = den
        self.name = name

    def discretize(self, samplerate):
        systf = (self.num, self.den)
        (dnum, dden, _) = signal.cont2discrete(systf, 1 / samplerate)
        return (np.squeeze(dnum), np.squeeze(dden))


interpkind = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']
Filters = {
    'Lowpass filter': Filter(
        name='lowpass',
        parameters=[
            Parameter('Cutoff frequency (Hz)', int),
            Parameter('Filter order', int),
        ],
    ),
    'Filter ventilation': Filter(name='ventilation', parameters=[]),
    'Savitzky-Golay': Filter(
        name='savgol',
        parameters=[
            Parameter('Window duration', 'time'),
            Parameter('Polynomial order', int),
        ],
    ),
    'Interpolate': Filter(
        name='interp',
        parameters=[
            Parameter('New sampling rate (Hz)', float),
            Parameter('Interpolation type', interpkind),
        ],
    ),
    'Doppler cut': Filter(
        name='dopplercut', parameters=[Parameter('Minimum value', int)]
    ),
    'Differentiate': Filter(name='diff', parameters=[Parameter('Order', int)]),
    'Integrate': Filter(
        name='integrate', parameters=[Parameter('Window duration', 'time')]
    ),
    'Lag': Filter(name='lag', parameters=[Parameter('Time delta', 'time')]),
    'Normalize': Filter(name='norm1', parameters=[]),
    'Set start date/time': Filter(
        name='setdatetime', parameters=[Parameter('DateTime', datetime)]
    ),
    'Tolerant Normalize': Filter(name='norm2', parameters=[]),
    'Enter expression (variable = x)': Filter(
        name='expression', parameters=[Parameter('Expression', str)]
    ),
    'Strided Moving average': Filter(
        name='sma', parameters=[Parameter('Window duration', 'time')]
    ),
}

FeetFilters = {
    'Short cycles': Filter(
        name='shortcycles', parameters=[Parameter('Minimum duration', 'time')]
    )
}

TFs: Dict[str, TF] = {}


def updateTFs():
    tflist = list(TFs.keys())
    if not tflist:
        return
    Filters['Transfer function'] = Filter(
        name='tf', parameters=[Parameter('Transfer function', tflist)]
    )


def norm1(series, samplerate, parameters):
    series -= np.mean(series)
    series /= np.max(series) - np.min(series)
    newname = f'{series.name}-norm'
    return (series.rename(newname), samplerate)


def norm2(series, samplerate, parameters):
    series -= np.mean(series)
    series /= np.std(series)
    newname = f'{series.name}-norm'
    return (series.rename(newname), samplerate)


def expression(series, samplerate, parameters):
    (express,) = parameters
    try:
        filtered = ne.evaluate(express, local_dict={'x': series.to_numpy()})
    except Exception:
        filtered = None
    newname = f'{series.name}-filtered'
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)


def setdatetime(series, samplerate, parameters):
    (timestamp,) = parameters
    newseries = series.copy()
    diff = timestamp - newseries.index[0]
    newseries.index += diff
    newseries = newseries.rename(f'{series.name}-{timestamp}')
    return (newseries, samplerate)


def sma(series, samplerate, parameters):
    (window_s,) = parameters
    serarr = series.to_numpy()
    serlen = len(serarr)
    winsize = int(window_s * samplerate)
    nwindows = ceil(serlen / winsize)
    valstarts = np.arange(0, serlen - winsize, step=winsize)
    resiter = (
        np.mean(serarr[beg:end]) for beg, end in zip(valstarts, valstarts + winsize)
    )
    result = np.fromiter(resiter, dtype=np.float64)
    locidx = winsize * np.arange(0, nwindows - 1) + winsize // 2
    newname = f'{series.name}-sma{window_s}s'
    newseries = pd.Series(result, index=series.index[locidx], name=newname)
    newsamplerate = samplerate / winsize
    return (newseries, newsamplerate)


def savgol(series, samplerate, parameters):
    window, order = parameters
    window = np.floor(window * samplerate)
    if not window % 2:
        # window is even, we need odd
        window += 1
    filtered = signal.savgol_filter(series.values, int(window), order)
    newname = f'{series.name}-filtered'
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)


def lag(series, samplerate, parameters):
    (timedelta,) = parameters
    nindex = series.index.values + timedelta * 1e9
    newname = f'{series.name}-{timedelta}s'
    newseries = pd.Series(series.values, index=nindex, name=newname)
    return (newseries, samplerate)


def tf(series, samplerate, parameters):
    (filtname,) = parameters
    tf = TFs[filtname]
    b, a = tf.discretize(samplerate)
    filtered = signal.lfilter(b, a, series)
    newname = f'{series.name}-{tf.name}'
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)


def lowpass(series, samplerate, parameters):
    Fc, order = parameters
    Wn = Fc * 2 / samplerate
    b, a = signal.butter(order, Wn)
    filtered = signal.lfilter(b, a, series)
    newname = f'{series.name}-lp{Fc}'
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)


def ventilation(series, samplerate, parameters):
    order = 12
    # Filter between 10 and 20 per minute
    bornes_hz = np.array([10, 20]) / 60
    Wn = [Fc * 2 / samplerate for Fc in bornes_hz]
    b, a = signal.butter(order, Wn, btype='bandstop')
    filtered = signal.filtfilt(b, a, series.values)
    newname = f'{series.name}-novent'
    newseries = pd.Series(filtered, index=series.index, name=newname)
    return (newseries, samplerate)


def interp(series, samplerate, parameters):
    newsamplerate, method = parameters
    oldidx = series.index
    f = interpolate.interp1d(
        oldidx, series.values, kind=method, fill_value='extrapolate'
    )
    step = 1e9 / newsamplerate  # 1e9 to convert Hz to ns
    newidx = np.arange(oldidx[0], oldidx[-1], step, dtype=np.int64)
    resampled = f(newidx)
    newname = f'{series.name}-{newsamplerate}Hz'
    newseries = pd.Series(resampled, index=newidx, name=newname)
    return (newseries, newsamplerate)


def dopplercut(series, samplerate, parameters):
    (minvel,) = parameters
    (notlow,) = (series < minvel).to_numpy().nonzero()
    newname = f'{series.name}-{minvel}+'
    newseries = series.rename(newname)
    newseries.iloc[notlow] = 0
    return (newseries, samplerate)


def integrate(series, samplerate, parameters):
    (duration,) = parameters
    window = int(np.floor(duration * samplerate))
    integrated = series.rolling(window, center=True).sum()
    newname = f'{series.name}-integrate{duration}s'
    newseries = integrated.rename(newname)
    return (newseries, samplerate)


def diff(series, samplerate, parameters):
    (order,) = parameters
    diffed = np.diff(series.values, order)
    newname = f'{series.name}-diff{order}'
    newseries = pd.Series(diffed, index=series.index[order:], name=newname)
    return (newseries, samplerate)


filtfuncs = {
    'savgol': savgol,
    'lag': lag,
    'tf': tf,
    'sma': sma,
    'lowpass': lowpass,
    'ventilation': ventilation,
    'interp': interp,
    'dopplercut': dopplercut,
    'integrate': integrate,
    'diff': diff,
    'norm1': norm1,
    'norm2': norm2,
    'expression': expression,
    'setdatetime': setdatetime,
}


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
        (minDuration,) = parameters
        minCycleLength = minDuration * 1e9  # Transform ms to ns
        cycleDurations = (stop - start for start, stop in zip(starts, stops))
        boolidx = [d >= minCycleLength for d in cycleDurations]
        starts, stops, boolidx = truncatevecs([starts, stops, boolidx])
        newstarts = starts[boolidx]
        newstops = stops[boolidx]
    else:
        errmsg = f'Unknown filter: {filtname}'
        raise ValueError(errmsg)
    return (newstarts, newstops)
