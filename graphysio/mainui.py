import itertools
import os
import sys
import traceback
from functools import partial
from queue import Queue
from typing import Optional

from pebble import ProcessPool
from pyqtgraph import QtCore, QtWidgets

from graphysio import dialogs, readdata, ui, utils
from graphysio.dialogs import loadmodule
from graphysio.plotwidgets import TimeAxisItem, TSWidget
from graphysio.writedata.exporter import TsExporter


class MainUi(ui.Ui_MainWindow, QtWidgets.QMainWindow):
    setcoords = QtCore.Signal(float, float)

    def __init__(self, input_file=None, parent=None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser("~")

        self.dataq = Queue()
        self.pool = ProcessPool()
        self.datahandler = self.createNewPlotWithData
        self.exporter = TsExporter(self, "mainui", self.tabWidget)

        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        launchNewPlot = partial(self.launchOpenFile, self.createNewPlotWithData)
        launchAppendPlot = partial(self.launchOpenFile, self.appendToPlotWithData)
        self.menuFile.addAction("New Plot", launchNewPlot)
        self.menuFile.addAction("Append to Plot", launchAppendPlot)

        if readdata.DwcReader.is_available:
            launchNewDwcPlot = partial(self.launchOpenDwc, self.createNewPlotWithData)
            self.menuFile.addAction("New Plot from DWC", launchNewDwcPlot)

        if readdata.ParquetDirReader.is_available:
            launchNewParquetDirPlot = partial(
                self.launchOpenParquetDir, self.createNewPlotWithData
            )
            self.menuFile.addAction(
                "New Plots from Parquet Directory", launchNewParquetDirPlot
            )

        if readdata.IcebergReader.is_available:
            launchNewIcebergPlot = partial(self.launchOpenIceberg, self.createNewPlotWithData)
            self.menuFile.addAction("New Plot from Iceberg", launchNewIcebergPlot)

        self.menuFile.addSeparator()
        self.menuFile.addAction(
            "Export all plots", self.errguard(self.exporter.curves_all_plots)
        )
        self.menuFile.addSeparator()
        self.menuFile.addAction("&Load plugin", self.errguard(loadmodule))
        self.menuFile.addSeparator()
        self.menuFile.addAction("&Quit", self.close, QtCore.Qt.CTRL | QtCore.Qt.Key_Q)

        self.setcoords.connect(self.setCoords)

        # Launch timer to handle new plot data
        self.data_timer = QtCore.QTimer()
        self.data_timer.timeout.connect(self.read_plot_data)
        self.data_timer.setInterval(1000)  # Milliseconds
        self.data_timer.start()

        # If file was provided on command line, load it
        if input_file:
            self.launchOpenFile(self.createNewPlotWithData, input_file)

    def closeEvent(self, event) -> None:
        self.pool.stop()
        self.pool.join()
        super().closeEvent(event)

    def setCoords(self, x, y) -> None:
        if TimeAxisItem.is_relative_time(x):
            timestr = TimeAxisItem.conv_relative(x)
        else:
            timestr = TimeAxisItem.conv_absolute(x, mainwindow=True)
        self.lblCoords.setText(f"Time: {timestr}, Value: {y}")

    def read_plot_data(self) -> None:
        while not self.dataq.empty():
            data = self.dataq.get()
            # Plotdata can be an object or a list of objects
            try:
                iter(data)
            except TypeError:
                data = [data]
            for plotdata in data:
                self.datahandler(plotdata)

    def print_exception(self, e) -> None:
        traceback.print_exc(file=sys.stdout)
        utils.displayError(e)

    def errguard(self, f):
        # Lift exceptions to UI reported errors
        def wrapped() -> None:
            try:
                f()
            except Exception as e:
                self.print_exception(e)

        return wrapped

    def addTab(self, widget: QtWidgets.QWidget, tabname: str) -> None:
        tabnames = []
        for i in range(self.tabWidget.count()):
            tabnames.append(self.tabWidget.tabText(i))
        if tabname in tabnames:
            tmptabname = tabname
            # Duplicate tab name. Add a number to the end
            for i in itertools.count():
                tmptabname = f"{tabname}_{i + 1}"
                if tmptabname not in tabnames:
                    break
            tabname = tmptabname
        tabindex = self.tabWidget.addTab(widget, tabname)
        self.tabWidget.setCurrentIndex(tabindex)

    def closeTab(self, i) -> None:
        w = self.tabWidget.widget(i)
        self.tabWidget.removeTab(i)
        w.close()
        w.deleteLater()
        del w

    def tabChanged(self, tabid) -> None:
        destwidget = self.tabWidget.widget(tabid)
        if destwidget is None:
            return
        self.menuBar.clear()
        self.menuBar.addMenu(self.menuFile)
        for title, submenu in destwidget.menu.items():
            menu = self.menuBar.addMenu(title)
            for title, item in submenu.items():
                menu.addAction(title, item)

    def launchOpenDwc(self, datahandler) -> None:
        reader = readdata.DwcReader()
        if not dialogs.drive_reader_qt(reader):
            return
        self.lblStatus.setText("Loading DWC...")
        future = self.pool.schedule(reader.get_plotdata)

        def cb(future) -> None:
            plotdata = future.result()
            for iplotdata in plotdata:
                self.dataq.put(iplotdata)
            self.lblStatus.setText("Loading... done")

        self.datahandler = datahandler
        future.add_done_callback(cb)

    def launchOpenParquetDir(self, datahandler) -> None:
        reader = readdata.ParquetDirReader()
        folder = dialogs.askDirPath("Open Parquet Directory")
        if folder is None:
            return
        reader.set_data({"path": folder})
        if not dialogs.drive_reader_qt(reader):
            return
        self.lblStatus.setText("Loading Parquet Files...")
        future = self.pool.schedule(reader.get_plotdata)

        def cb(future) -> None:
            self.lblStatus.setText("Loading... done")
            plotdata = future.result()
            for iplotdata in plotdata:
                self.dataq.put(iplotdata)

        self.datahandler = datahandler
        future.add_done_callback(cb)

    def launchOpenIceberg(self, datahandler) -> None:
        reader = readdata.IcebergReader()
        if not dialogs.drive_reader_qt(reader):
            return
        self.lblStatus.setText("Loading Iceberg...")
        future = self.pool.schedule(reader.get_plotdata)

        def cb(future) -> None:
            self.lblStatus.setText("Loading... done")
            plotdata = future.result()
            for iplotdata in plotdata:
                self.dataq.put(iplotdata)

        self.datahandler = datahandler
        future.add_done_callback(cb)

    def launchOpenFile(self, datahandler, filepath=None) -> None:
        reader = readdata.FileReader()
        if filepath:
            self.dircache = reader.load_file(filepath)
        else:
            self.dircache = reader.user_choose_file(self.dircache)
        if reader.reader is None:
            # File selection was cancelled.
            return
        if not dialogs.drive_reader_qt(reader.reader):
            return
        self.lblStatus.setText("Loading File...")
        future = self.pool.schedule(reader.get_plotdata)

        def cb(future) -> None:
            self.lblStatus.setText("Loading... done")
            plotdata = future.result()
            if plotdata:
                self.dataq.put(plotdata)

        self.datahandler = datahandler
        future.add_done_callback(cb)

    def createNewPlotWithData(self, plotdata) -> None:
        properties = {"dircache": self.dircache}
        plotwidget = TSWidget(plotdata, parent=self, properties=properties)
        self.addTab(plotwidget, plotdata.name)

    def appendToPlotWithData(
        self,
        plotdata,
        destidx=None,
        do_timeshift: Optional[bool] = None,
    ) -> None:
        if destidx is None:
            plotwidget = self.tabWidget.currentWidget()
        else:
            plotwidget = self.tabWidget.widget(destidx)
        if plotwidget is None:
            utils.displayError("No plot selected.")
            return
        if do_timeshift is None:
            do_timeshift = dialogs.userConfirm(
                "Timeshift new curves to make the beginnings coincide?",
                title="Append to plot",
            )

        for fieldname in plotdata.data:
            newname = plotwidget.validateNewCurveName(fieldname)
            if newname is None:
                continue
            if newname != fieldname:
                plotdata.data = plotdata.data.rename(columns={fieldname: newname})

        plotwidget.appendData(plotdata, do_timeshift)
        plotwidget.properties["dircache"] = self.dircache
