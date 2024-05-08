import os
import sys
from functools import partial
from itertools import cycle

import numpy as np
import pathvalidate
from pyqtgraph.Qt import QtGui, QtWidgets

sanitize_filename = partial(pathvalidate.sanitize_filename, platform="auto")
sanitize_filepath = partial(pathvalidate.sanitize_filepath, platform="auto")

import importlib.util


def Colors():
    qtcolors = [
        QtGui.QColor(0, 114, 189),
        QtGui.QColor(217, 83, 25),
        QtGui.QColor(237, 177, 32),
        QtGui.QColor(126, 47, 142),
        QtGui.QColor(119, 172, 48),
        QtGui.QColor(77, 190, 238),
        QtGui.QColor(162, 20, 47),
    ]
    return cycle(qtcolors)


def estimateSampleRate(series):
    intervals = np.diff(series.index)
    # 1e9 to account for ns -> Hz
    fs = 1e9 / np.median(intervals)
    if fs == np.inf:
        fs = 0
    if fs > 1:
        fs = int(round(fs))
    return fs


def loadmodule():
    defaultdir = os.path.expanduser("~")
    filepath = QtWidgets.QFileDialog.getOpenFileName(
        caption="Import module", filter="Python files (*.py)", directory=defaultdir
    )
    if not isinstance(filepath, str):
        # PyQt5 API change
        filepath = filepath[0]
    if not filepath:
        # Cancel pressed
        return

    bcbak = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("graphysio.plugin", filepath)
        foo = importlib.util.module_from_spec(spec)
        sys.modules["graphysio.plugin"] = foo
        spec.loader.exec_module(foo)
    finally:
        sys.dont_write_bytecode = bcbak


def clip(vec, vrange):
    if vrange is None:
        return vec
    xmin, xmax = vrange
    cond = (vec > xmin) & (vec < xmax)
    return vec[cond]


def truncatevecs(vecs):
    # Ensure all vectors have the same length by truncating the end
    maxidx = min(map(len, vecs))
    return [vec[0:maxidx] for vec in vecs]


def getshell(ui=None):
    import IPython

    IPython.embed(ui=ui)


def displayError(errmsg):
    msgbox = QtWidgets.QMessageBox()
    msgbox.setWindowTitle("Error")
    msgbox.setText(str(errmsg))
    msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgbox.setIcon(QtWidgets.QMessageBox.Critical)
    msgbox.exec_()
