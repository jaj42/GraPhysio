import numpy as np
import pandas as pd

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from graphysio import dialogs
from graphysio.structures import Parameter, PlotData


class SpectrogramWidget(QtWidgets.QWidget):
    def __init__(self, series, Fs, s_chunklen, parent=None):
        super().__init__(parent=parent)
        self.spectro = SpectrogramPlotWidget(series, Fs, s_chunklen, parent)
        self.loslider = QtWidgets.QSlider()
        self.hislider = QtWidgets.QSlider()
        layout = QtWidgets.QHBoxLayout()

        lolayout = QtWidgets.QVBoxLayout()
        lothres = QtWidgets.QLabel('Low')
        lolayout.addWidget(lothres)
        lolayout.addWidget(self.loslider)

        hilayout = QtWidgets.QVBoxLayout()
        hithres = QtWidgets.QLabel('High')
        hilayout.addWidget(hithres)
        hilayout.addWidget(self.hislider)

        layout.addWidget(self.spectro)
        layout.addLayout(lolayout)
        layout.addLayout(hilayout)
        self.setLayout(layout)

    @property
    def menu(self):
        mplot = {'Extract SEF': self.spectro.launchSEFExtract}
        m = {'Plot': mplot}
        return m


class SpectroTimeAxisItem(pg.AxisItem):
    def __init__(self, initvalue, samplerate, chunksize, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initvalue = initvalue / 1e6  # ns to ms
        self.samplerate = samplerate
        self.chunksize = chunksize

    def tickStrings(self, values, scale, spacing):
        ret = []
        value_to_time = self.chunksize / self.samplerate + self.initvalue
        for value in values:
            value = 1e3 * value  # s to ms
            value = value * value_to_time
            date = QtCore.QDateTime.fromMSecsSinceEpoch(value)
            date = date.toTimeSpec(QtCore.Qt.UTC)
            datestr = date.toString("dd/MM/yyyy\nhh:mm:ss.zzz")
            ret.append(datestr)
        return ret


# To set:
# levels
# color gradient
class SpectrogramPlotWidget(pg.PlotWidget):
    def __init__(self, series, Fs, s_chunklen, parent=None):
        # s_chunklen in seconds
        self.name = series.name
        self.parent = parent
        self.origidx = series.index.values

        self.fs = Fs
        self.data = series.values
        self.chunksize = int(s_chunklen * Fs)
        self.win = np.hanning(self.chunksize)

        axisItem = SpectroTimeAxisItem(
            initvalue=self.origidx[0],
            samplerate=self.fs,
            chunksize=self.chunksize,
            orientation='bottom',
        )
        axisItems = {'bottom': axisItem}
        super().__init__(parent=self.parent, axisItems=axisItems)

        self.img = pg.ImageItem()
        self.addItem(self.img)
        self.setLabel('left', 'Frequency', units='Hz')

        # bipolar colormap
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array(
            [
                [0, 0, 0, 255],
                [0, 0, 255, 255],
                [0, 255, 255, 255],
                [255, 255, 0, 255],
                [255, 0, 0, 255],
            ],
            dtype=np.ubyte,
        )
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)

        self.calculate_psd()
        self.render()

    def idx_to_hz(self, idxval):
        conv = self.fs / self.chunksize
        return conv * idxval

    def calcsef(self, perc):
        buf = np.zeros(self.psd.shape[0])
        psdcs = np.cumsum(self.psd, axis=1)
        for i, columncs in enumerate(psdcs):
            thres = perc * columncs[-1] / 100
            sefidx = np.where(columncs > thres)
            try:
                buf[i] = self.idx_to_hz(sefidx[0][0])
            except IndexError:
                pass
        return buf

    def calculate_psd(self):
        nsplit = int(len(self.data) / self.chunksize)
        chunks = self.data[0 : nsplit * self.chunksize]
        chunks = np.split(chunks, nsplit)
        chunks = np.vstack(chunks)
        spec = np.fft.rfft(chunks * self.win) / self.chunksize
        self.psd = np.real(spec) ** 2

    def genIndex(self):
        nwindows = self.psd.shape[0]
        winsize = self.chunksize
        windows = np.lib.stride_tricks.as_strided(
            self.origidx, shape=(nwindows, winsize)
        )
        result = np.apply_along_axis(np.mean, 1, windows)
        index = result.astype(int)
        return index

    def launchSEFExtract(self):
        q = Parameter('SEF percentage', int)
        sefperc = dialogs.askUserValue(q)
        if not sefperc:
            return
        curvename = f'{self.name}-sef{sefperc}'
        sef = self.calcsef(sefperc)
        sefseries = pd.Series(sef, index=self.genIndex(), name=curvename)
        data = {curvename: sefseries}
        plotdata = PlotData(data, name=curvename)
        self.parent.createNewPlotWithData(plotdata)

    def render(self):
        # TODO make lo / hi adjustable
        psdnona = self.psd[~np.isnan(self.psd)]
        hi = np.percentile(psdnona, 95)
        lo = np.percentile(psdnona, 5)
        # print(f'PSD Lo: {lo}, Hi: {hi}')
        self.img.scale(1, self.fs / self.chunksize)
        self.img.setLevels([lo, hi])
        self.img.setImage(self.psd, autoLevels=False)
