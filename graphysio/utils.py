import os
import sys
import imp

from functools import partial
from itertools import cycle

import numpy as np
from pyqtgraph.Qt import QtGui, loadUiType

import pathvalidate

sanitize_filename = partial(pathvalidate.sanitize_filename, platform='auto')
sanitize_filepath = partial(pathvalidate.sanitize_filepath, platform='auto')


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


curPath = os.path.dirname(os.path.abspath(__file__))
uiBasePath = os.path.join(curPath, 'ui')


def loadUiFile(uiFile):
    uiPath = os.path.join(uiBasePath, uiFile)
    uiClasses = loadUiType(uiPath)
    # form class and Qt base class.
    return uiClasses


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
    defaultdir = os.path.expanduser('~')
    filepath = QtGui.QFileDialog.getOpenFileName(
        caption="Import module", filter="Python files (*.py)", directory=defaultdir
    )
    if type(filepath) is not str:
        # PyQt5 API change
        filepath = filepath[0]
    if not filepath:
        # Cancel pressed
        return

    folder, filename = os.path.split(filepath)
    modulename, _ = os.path.splitext(filename)
    f, filename, description = imp.find_module(modulename, [folder])

    bcbak = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        imp.load_module('graphysio.plugin', f, filename, description)
    finally:
        sys.dont_write_bytecode = bcbak
        f.close()


def clip(vec, vrange):
    if vrange is None:
        return vec
    xmin, xmax = vrange
    cond = (vec > xmin) & (vec < xmax)
    return vec[cond]


def truncatevecs(vecs):
    # Ensure all vectors have the same length by truncating the end
    maxidx = min(map(len, vecs))
    newvecs = [vec[0:maxidx] for vec in vecs]
    return newvecs


def getshell(ui=None):
    import IPython

    IPython.embed(ui=ui)


def displayError(errmsg):
    msgbox = QtGui.QMessageBox()
    msgbox.setWindowTitle("Error")
    msgbox.setText(str(errmsg))
    msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
    msgbox.setIcon(QtGui.QMessageBox.Critical)
    msgbox.exec_()
