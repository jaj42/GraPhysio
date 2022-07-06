# GraPhysio
GraPhysio is a graphical time series visualizer created for biometric data
signals from ICU patient monitors. It is however not limited to this. It can
handle low frequency and high frequency data as well as aggregating and
synchronizing signals from different sources. GraPhysio supports basic
mathematical operations and filters and can help selecting and exporting time
periods. GraPhysio can read data from CSV, Parquet and EDF files and can write
CSV, Parquet, EDF and Matlab files.

## Install instructions
For the best experience, conda is recommended:

conda install -c conda-forge graphysio

Alternatively you can then install the latest version of GraPhysio from PyPi by
tying the following command:

> python -m pip install graphysio

You can launch GraPhysio by typing:

> python -m graphysio
