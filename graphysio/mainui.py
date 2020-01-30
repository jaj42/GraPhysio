import os
import itertools
from functools import partial

from PyQt5 import QtCore, QtWidgets

from graphysio import dialogs, utils, csvio, ui
from graphysio.plotwidgets import TSWidget


class MainUi(ui.Ui_MainWindow, QtWidgets.QMainWindow):
    hasdata  = QtCore.pyqtSignal(object)
    haserror = QtCore.pyqtSignal(object)
    setcoords = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.dircache = os.path.expanduser('~')

        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        launchNewPlot    = partial(self.launchReadData, newwidget=True)
        launchAppendPlot = partial(self.launchReadData, newwidget=False)
        getCLIShell = partial(utils.getshell, ui=self)
        self.menuFile.addAction('&New Plot',       self.errguard(launchNewPlot),    QtCore.Qt.CTRL + QtCore.Qt.Key_N)
        self.menuFile.addAction('&Append to Plot', self.errguard(launchAppendPlot), QtCore.Qt.CTRL + QtCore.Qt.Key_A)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Load plugin', self.errguard(utils.loadmodule))
        self.menuFile.addAction('Get CLI shell', self.errguard(getCLIShell))
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.close, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        self.haserror.connect(utils.displayError)
        self.setcoords.connect(self.setCoords)

    def setCoords(self, x, y):
        dt = x / 1e6 # convert from ns to ms
        date = QtCore.QDateTime.fromMSecsSinceEpoch(dt)
        date = date.toTimeSpec(QtCore.Qt.UTC)
        timestr = date.toString("dd/MM/yyyy hh:mm:ss.zzz")
        self.lblCoords.setText(f'Time: {timestr}, Value: {y:.2E}')

    def errguard(self, f):
        # Lift exceptions to UI reported errors
        def wrapped():
            try:
                f()
            except Exception as e:
                # Re-raise errors here for DEBUG
                #raise e
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

    def launchReadData(self, newwidget=True, cb=None):
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

        dlgNewplot = dialogs.DlgNewPlot(parent=self, title=title, directory=self.dircache)
        if not dlgNewplot.exec_():
            return
        csvrequest = dlgNewplot.result
        self.dircache = csvrequest.folder
        self.lblStatus.setText(f'Loading... {csvrequest.name}...')

        reader = csvio.Reader(csvrequest, self.hasdata, self.haserror)
        QtCore.QThreadPool.globalInstance().start(reader)

    def appendToPlotWithData(self, plotdata, destidx=None):
        if destidx is None:
            plotwidget = self.tabWidget.currentWidget()
        else:
            plotwidget = self.tabWidget.widget(destidx)
        if plotwidget is None:
            self.haserror.emit('No plot selected.')
            return
        dorealign = dialogs.userConfirm('Timeshift new curves to make the beginnings coincide?', title='Append to plot')

        for fieldname in plotdata.data:
            newname = plotwidget.validateNewCurveName(fieldname)
            if newname is None:
                continue
            if newname != fieldname:
                plotdata.data.rename(columns={fieldname : newname}, inplace=True)

        plotwidget.appendData(plotdata, dorealign)
        plotwidget.properties['dircache'] = self.dircache
        self.lblStatus.setText("Loading... done")

    def createNewPlotWithData(self, plotdata):
        plotwidget = TSWidget(plotdata=plotdata, parent=self)
        plotwidget.properties['dircache'] = self.dircache
        self.addTab(plotwidget, plotdata.name)
        self.lblStatus.setText("Loading... done")
