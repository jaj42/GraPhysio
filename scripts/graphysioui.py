#!/usr/bin/env python3

import sys
from pyqtgraph.Qt import QtGui
from graphysio.mainui import MainUi

import traceback
import logging, logging.handlers

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    winmain = MainUi()
    winmain.show()

    log = logging.getLogger("GraPhysio")
    smtph = logging.handlers.SMTPHandler('puff.joachim.cc', 'graphysio@example.com', 'jaj_graphysio@joachim.cc', 'GraPhysio_error')
    log.addHandler(smtph)

    status = 1
    try:
        status = app.exec_()
    except:
        tb = traceback.format_exc()
        log.error(tb)
    finally:
        sys.exit(status)
