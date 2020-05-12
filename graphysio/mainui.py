import os
import itertools
from functools import partial

# Error printing
import sys
import traceback

from PyQt5 import QtCore, QtWidgets

from graphysio import dialogs, utils, ui, readdata
from graphysio.plotwidgets import TSWidget


class MainUi(ui.Ui_MainWindow, QtWidgets.QMainWindow):
    hasdata = QtCore.pyqtSignal(object)
    haserror = QtCore.pyqtSignal(object)
    setcoords = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        getCLIShell = partial(utils.getshell, ui=self)
        launchNewPlot = partial(self.launchReadData, newwidget=True)
        launchAppendPlot = partial(self.launchReadData, newwidget=False)

        mnewplot = self.menuFile.addMenu('New Plot')
        for lbl in readdata.readers:
            f = partial(launchNewPlot, datasource=lbl)
            mnewplot.addAction(f'From {lbl.capitalize()}', self.errguard(f))

        mappplot = self.menuFile.addMenu('Append to Plot')
        for lbl in readdata.readers:
            f = partial(launchAppendPlot, datasource=lbl)
            mappplot.addAction(f'From {lbl.capitalize()}', self.errguard(f))

        self.menuFile.addSeparator()
        self.menuFile.addAction('&Load plugin', self.errguard(utils.loadmodule))
        self.menuFile.addAction('Get CLI shell', self.errguard(getCLIShell))
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.close, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        self.haserror.connect(utils.displayError)
        self.setcoords.connect(self.setCoords)

    def setCoords(self, x, y):
        dt = x / 1e6  # convert from ns to ms
        date = QtCore.QDateTime.fromMSecsSinceEpoch(dt)
        date = date.toTimeSpec(QtCore.Qt.UTC)
        timestr = date.toString("dd/MM/yyyy hh:mm:ss.zzz")
        self.lblCoords.setText(f'Time: {timestr}, Value: {y}')

    def errguard(self, f):
        # Lift exceptions to UI reported errors
        def wrapped():
            try:
                f()
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                self.haserror.emit(e)

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

    def launchReadData(self, datasource, newwidget=True, cb=None):
        try:
            self.hasdata.disconnect()
        except:
            pass
        if cb is not None:
            title = "Load Data"
            self.hasdata.connect(cb)
        elif newwidget:
            title = "New Plot"
            self.hasdata.connect(self.createNewPlotWithData)
        else:
            title = "Append to Plot"
            self.hasdata.connect(self.appendToPlotWithData)

        def cb(datarequest):
            self.dircache = datarequest.folder
            self.lblStatus.setText(f'Loading... {datarequest.name}...')
            Reader = readdata.readers[datasource]
            reader = Reader(datarequest, self.hasdata, self.haserror)
            QtCore.QThreadPool.globalInstance().start(reader)

        DlgNewPlot = readdata.dlgNewPlots[datasource]
        dlgNewplot = DlgNewPlot(parent=self, title=title, directory=self.dircache)
        dlgNewplot.dlgdata.connect(cb)
        dlgNewplot.exec_()

    def appendToPlotWithData(self, plotdata, destidx=None):
        if destidx is None:
            plotwidget = self.tabWidget.currentWidget()
        else:
            plotwidget = self.tabWidget.widget(destidx)
        if plotwidget is None:
            self.haserror.emit('No plot selected.')
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

    def createNewPlotWithData(self, plotdata):
        plotwidget = TSWidget(plotdata=plotdata, parent=self)
        plotwidget.properties['dircache'] = self.dircache
        self.addTab(plotwidget, plotdata.name)
        self.lblStatus.setText("Loading... done")
