#!/usr/local/bin/python2.7

import socket, json, os
import numpy as np
from string import Template


class CSVQuery:
    querytemplate = Template('ReadVector {fileName = "$filename", '
                             'seperator = \'$sep\', '
                             'fields = [$fields], '
                             'range = $range, '
                             'notnull = [$notnull], '
                             'skiplines = $skiplines}')

    def __init__(self, filename, seperator, xfields, yfields, notnull, linerange, skiplines):
        self.__query     = ""
        self.__filelines = None

        self.__ipcstream = DataStream()
        self.__filename  = str(filename)
        self.__notnull   = notnull
        self.__seperator = seperator
        self.__skiplines = skiplines
        self.__xfields   = xfields
        self.__yfields   = yfields
        self.__fields    = self.__xfields + self.__yfields

        self.__updateRange(linerange)

    def __updateQuery(self):
        strfields  = ', '.join('"' + str(x) + '"' for x in self.__fields)
        strnotnull = ', '.join('"' + str(x) + '"' for x in self.__notnull)
        self.__query = self.querytemplate.substitute(filename  = self.__filename,
                                                     sep       = self.__seperator,
                                                     fields    = strfields,
                                                     notnull   = strnotnull,
                                                     range     = self.__linerange,
                                                     skiplines = self.__skiplines)

    def __updateRange(self, rangetuple):
        if rangetuple is None:
            rangetxt = "All"
        elif len(rangetuple) < 2:
            rangetxt = "All"
        else:
            rangetxt = "Subset {} {}".format(rangetuple[0], rangetuple[1])
        self.__linerange = rangetxt

    def execute(self):
        self.__ipcstream.sendRequest(self.rawquery)
        if self.__ipcstream.failed:
            print "IPC error: {}.".format(self.__ipcstream.errmsg)
            return None
        jsdata = json.load(self.__ipcstream)
        tabledat = np.array(jsdata, dtype=np.float)
        veclen = len(tabledat)
        if self.__filelines is None:
            # After the first query we know how many lines the file really has
            # except for lines seen as null by the backend, which are ignored
            self.__filelines = veclen * self.skiplines

        #tabledat has X and Y vectors stacked horizontally
        xnum = len(self.__xfields)
        # XXX xvecs are not implemented yet
        #xvecs = tabledat[:,:xnum]
        yvecs = tabledat[:,xnum:]

        # Pyqtgraph needs: numpy array with shape (N, 2) where x=data[:,0] and y=data[:,1]
        # This constructs an ndarray with shape (N, 2, M) where M is the number of datasets
        # XXX This should probably be optimized at some point
        veclen = len(yvecs)
        xarr = np.arange(veclen)
        plotarrays = []
        for vector in yvecs.T:
            dataset = np.vstack([xarr, vector]).T
            plotarrays.append(dataset)
        plotdata = np.dstack(plotarrays)
        return plotdata

    @property
    def samplename(self):
        base = os.path.basename(self.__filename)
        sext = os.path.splitext(base)
        return sext[0]

    @property
    def rawquery(self):
        self.__updateQuery()
        return self.__query

    @property
    def filename(self):
        return self.__filename

    @property
    def seperator(self):
        return self.__seperator

    @property
    def xfields(self):
        return self.__xfields

    @property
    def yfields(self):
        return self.__yfields

    @property
    def notnull(self):
        return self.__notnull

    @property
    def linerange(self):
        return self.__linerange
    @linerange.setter
    def linerange(self, x):
        self.__updateRange(x)

    @property
    def skiplines(self):
        return self.__skiplines
    @skiplines.setter
    def skiplines(self, x):
        self.__skiplines = x

class DataStream:
    def __init__(self):
        self.__clearStatus()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect(("localhost", 4242))
        self.__fd = self.__sock.makefile('rw')

    def sendRequest(self, querymsg):
        self.__clearStatus()
        self.__writeLine(querymsg)
        status = self.__readLine()
        self.__errmsg = status
        if status.startswith("Ok"):
            self.__canread = True
        else:
            self.__canread = False
            self.__iserror = True

    def read(self, n=-1):
        if not self.__canread: return None
        self.__canread = False

        data = self.__readLine()
        # XXX wrong implementation for partial read.
        if n >= 0: return data[:n]
        return data

    def __clearStatus(self):
        self.__canread = False
        self.__iserror = False
        self.__errmsg  = ""

    def __writeLine(self, msg):
        self.__fd.writelines([msg])
        self.__fd.flush()

    def __readLine(self):
        data = self.__fd.readline()
        return data.rstrip("\n")

    def __del__(self):
        self.__writeLine("CloseConnection")

    @property
    def errmsg(self):
        return self.__errmsg

    @property
    def failed(self):
        return self.__iserror
