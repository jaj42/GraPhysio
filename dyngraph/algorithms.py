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
        try:
            iterator = np.nditer((peakStarts, peakStops))
        except ValueError as e:
            print("nditer error: {}".format(e), sys.stderr)
            return
        for start, stop in iterator:
            idxstart = sndderiv.index.values[start]
            idxstop  = sndderiv.index.values[stop]
            maximum = sndderiv[idxstart:idxstop].idxmax()
            yield maximum

    return series[list(locateMaxima())]
