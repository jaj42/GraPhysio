# GraPhysio
GraPhysio is a graphical data visualizer for physiologic data signals from ICU patient monitors.

## Install instructions
To make GraPhysio work you need Python version >=3.4 as well as PyQt4. GraPhysio makes heavy use of scientific Python libraries Pandas, NumPy, SciPy.
Plotting relies on the excellent PyQtGraph library.
You may want to install one of the scientific Python packages like [Anaconda](https://www.continuum.io/downloads). Make sure to grab the Python 3 version.
Once you have Anaconda, you can install PyQt4 with the following command:

> conda install pyqt=4

You can then install the latest version of GraPhysio by tying the following command:

> pip install graphysio

You can launch GraPhysio by typing:

> graphysioui.py
