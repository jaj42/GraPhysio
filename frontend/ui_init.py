#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
#plt.gca().xaxis.set_major_locator(mdates.DayLocator())

#widget_item.setData(0, Qt.UserRole, instance_item)
#widget_item.data(0, Qt.UserRole)  # original python object

#custom context menu
#https://riverbankcomputing.com/pipermail/pyqt/2008-February/018667.html

import rpc,plotwidget

import csv

#import sip
#sip.setapi('QVariant', 2)
#sip.setapi('QString', 2)

from PyQt4.QtCore import Qt, QString
from PyQt4.QtGui  import *

from newplot_ui    import Ui_NewPlot
from mainwindow_ui import Ui_MainWindow

class MainUi(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainUi, self).__init__(parent)
        self.setupUi(self)

        self.menuFile.addAction('&New Plot', self.newPlot, Qt.CTRL + Qt.Key_N)
        self.menuFile.addSeparator()
        self.menuFile.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

    def newPlot(self):
        dlgNewplot = DlgNewPlot()
        if not dlgNewplot.exec_(): return
        query = dlgNewplot.result
        if not query: return

        plot = plotwidget.PlotWidget()
        plot.attachQuery(query)
        tabindex = self.tabWidget.addTab(plot, query.samplename)
        self.tabWidget.setCurrentIndex(tabindex)
        plot.doPlot()

    def fileQuit(self):
        self.close()

class DlgNewPlot(QDialog, Ui_NewPlot):
    def __init__(self, parent=None):
        super(DlgNewPlot, self).__init__(parent)
        self.setupUi(self)

        self.txtSep.addItem(',')
        self.txtSep.addItem(';')

        self.txtEvery.setMinimum(1)
        self.txtEvery.setMaximum(1000)

        # Connect callbacks
        self.btnBrowse.clicked.connect(self.selectFile)
        self.btnLoad.clicked.connect(self.loadCsvFields)
        self.btnOk.clicked.connect(self.loadPlot)
        self.btnCancel.clicked.connect(self.reject)

        # Hack since you cannot pass arguments to Qt's signal connect()
        #def moveToX():   return self.moveFromTo(self.listAll, self.listX)
        def moveToY():   return self.moveFromTo(self.listAll, self.listY)
        def moveFromX(): return self.moveFromTo(self.listX,   self.listAll)
        def moveFromY(): return self.moveFromTo(self.listY,   self.listAll)
        self.btnToX.clicked.connect(self.moveToX)
        self.btnToY.clicked.connect(moveToY)
        self.btnRemoveX.clicked.connect(moveFromX)
        self.btnRemoveY.clicked.connect(moveFromY)

    # Methods
    def selectFile(self):
        self.txtFile.setText(QFileDialog.getOpenFileName())

    def loadCsvFields(self):
        sep = str(self.txtSep.currentText())
        filename = self.txtFile.text()
        fields = []
        # Use the csv module to retrieve csv fields
        with open(filename, 'rb') as csvfile:
            for row in csv.DictReader(csvfile, delimiter=sep):
                fields = row.keys()
                break
        # Clear all lists, then add new fields
        map(lambda lst: lst.clear(), [self.listAll, self.listX, self.listY])
        for field in fields:
            self.listAll.addItem(field)

    def moveFromTo(self, fromList, toList):
        while True:
            rowindexes = fromList.selectedIndexes()
            if len(rowindexes) < 1: break
            row = rowindexes[0].row()
            toList.addItem(fromList.takeItem(row))

    def moveToX(self):
        # Only allow one element in X for now.
        if self.listX.count() > 0: return
        rows = [index.row() for index in self.listAll.selectedIndexes()]
        for row in rows:
            self.listX.addItem(self.listAll.takeItem(row))
            break

    def loadPlot(self):
        xRows = [i.text() for i in self.listX.findItems("", Qt.MatchContains)]
        yRows = [i.text() for i in self.listY.findItems("", Qt.MatchContains)]
        rows = xRows + yRows
        fields = map(str, rows)
        skiplines = self.txtEvery.value()
        filename = self.txtFile.text()
        sep = str(self.txtSep.currentText())
        self.csvquery = rpc.CSVQuery(filename  = filename,
                                     seperator = sep,
                                     fields    = fields,
                                     notnull   = fields,
                                     linerange = None,
                                     skiplines = skiplines,
                                     xrownum   = len(xRows))
        self.accept()

    @property
    def result(self):
        return self.csvquery
