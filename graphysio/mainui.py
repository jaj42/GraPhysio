import os
import itertools
from functools import partial

from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

# Error printing
import sys
import traceback

from PyQt5 import QtCore, QtWidgets

from graphysio import dialogs, utils, ui, readdata
from graphysio.plotwidgets import TSWidget


class MainUi(ui.Ui_MainWindow, QtWidgets.QMainWindow):
    setcoords = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.dataq = Queue()
        self.executor = ThreadPoolExecutor()
        self.datahandler = self.createNewPlotWithData

        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        getCLIShell = partial(utils.getshell, ui=self)

        # mnewplot = self.menuFile.addMenu('New Plot')
        # mnewplot.addAction('From File', launchNewPlot)
        self.menuFile.addAction('New Plot', self.launchNewPlot)

        # mappplot = self.menuFile.addMenu('Append to Plot')
        # mappplot.addAction('From File', launchAppendPlot)
        self.menuFile.addAction('Append to Plot', self.launchAppendPlot)

        self.menuFile.addSeparator()
        self.menuFile.addAction('&Load plugin', self.errguard(utils.loadmodule))
        self.menuFile.addAction('Get CLI shell', self.errguard(getCLIShell))
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.close, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        self.setcoords.connect(self.setCoords)

        # Launch timer to handle new plot data
        self.data_timer = QtCore.QTimer()
        self.data_timer.timeout.connect(self.read_plot_data)
        self.data_timer.setInterval(1000)  # Milliseconds
        self.data_timer.start()

    def setCoords(self, x, y):
        dt = x / 1e6  # convert from ns to ms
        date = QtCore.QDateTime.fromMSecsSinceEpoch(dt)
        date = date.toTimeSpec(QtCore.Qt.UTC)
        timestr = date.toString("dd/MM/yyyy hh:mm:ss.zzz")
        self.lblCoords.setText(f'Time: {timestr}, Value: {y}')

    def read_plot_data(self):
        try:
            plotdata = self.dataq.get(block=False)
        except Empty:
            return
        self.datahandler(plotdata)

    def print_exception(self, e):
        traceback.print_exc(file=sys.stdout)
        utils.displayError(e)

    def errguard(self, f):
        # Lift exceptions to UI reported errors
        def wrapped():
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
                tmptabname = f'{tabname}{i+1}'
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

    def tabChanged(self, tabid):
        destwidget = self.tabWidget.widget(tabid)
        if destwidget is None:
            return
        self.menuBar.clear()
        self.menuBar.addMenu(self.menuFile)
        for title, submenu in destwidget.menu.items():
            menu = self.menuBar.addMenu(title)
            for title, item in submenu.items():
                menu.addAction(title, item)

    def launchNewPlot(self):
        reader = readdata.FileReader()
        reader.askFile(self.dircache)
        future = self.executor.submit(reader.get_plotdata)
        def cb(future):
            plotdata = future.result()
            self.dataq.put(plotdata)
        self.datahandler = self.createNewPlotWithData
        future.add_done_callback(cb)

    def launchAppendPlot(self):
        reader = readdata.FileReader()
        reader.askFile(self.dircache)
        future = self.executor.submit(reader.get_plotdata)
        def cb(future):
            plotdata = future.result()
            self.dataq.put(plotdata)
        self.datahandler = self.appendToPlotWithData
        future.add_done_callback(cb)

    def createNewPlotWithData(self, plotdata):
        plotwidget = TSWidget(plotdata=plotdata, parent=self)
        plotwidget.properties['dircache'] = self.dircache
        self.addTab(plotwidget, plotdata.name)
        self.lblStatus.setText("Loading... done")

    def appendToPlotWithData(self, plotdata, destidx=None):
        if destidx is None:
            plotwidget = self.tabWidget.currentWidget()
        else:
            plotwidget = self.tabWidget.widget(destidx)
        if plotwidget is None:
            utils.displayError('No plot selected.')
            return
        dorealign = dialogs.userConfirm(
            'Timeshift new curves to make the beginnings coincide?',
            title='Append to plot',
        )

        for fieldname in plotdata.data:
            newname = plotwidget.validateNewCurveName(fieldname)
            if newname is None:
                continue
            if newname != fieldname:
                plotdata.data.rename(columns={fieldname: newname}, inplace=True)

        plotwidget.appendData(plotdata, dorealign)
        plotwidget.properties['dircache'] = self.dircache
        self.lblStatus.setText("Loading... done")
