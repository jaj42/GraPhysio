#!/usr/local/bin/python2.7

import socket, json, os
import numpy    as np
import numpy.ma as ma
from string import Template

class CSVQuery:
    querytemplate = Template('ReadVector {fileName = "$filename", '
                             'seperator = \'$sep\', '
                             'fields = [$fields], '
                             'range = $range, '
                             'notnull = [$notnull], '
                             'skiplines = $skiplines}')

    def __init__(self, filename, seperator, xfields, yfields, notnull, linerange = None, skiplines = 1):
        self.__dataset   = None

        self.__ipcstream = DataStream()
        self.__filename  = str(filename)
        self.__notnull   = notnull
        self.__seperator = seperator
        self.__xfields   = xfields
        self.__yfields   = yfields
        self.__fields    = self.__xfields + self.__yfields
        self.setRange(linerange)
        self.setSkiplines(skiplines)

    def __genQuery(self):
        strfields  = ', '.join('"' + str(x) + '"' for x in self.__fields)
        strnotnull = ', '.join('"' + str(x) + '"' for x in self.__notnull)
        return self.querytemplate.substitute(filename  = self.__filename,
                                             sep       = self.__seperator,
                                             fields    = strfields,
                                             notnull   = strnotnull,
                                             range     = self.__genRangeForQuery(),
                                             skiplines = self.getSkiplines())

    def execute(self):
        """
        The backend drops every other line to get a partial result when
        asked to do so with the 'skiplines' parameter.
        We create a masked array buffer with the partial results like so:
        backend implementation: skiplines n full      = partial
                                skiplines 3 range(10) = [1, 4, 7, 10]
        len(partial) = ceiling(len(full) / n)
        n*(len(partial) - 1) < len(full) <= n*len(partial)
        -> set len(buffer) to n*len(partial)
        """
        # Do we already have the data, or do we need a new request?
#        if self.__dataset is not None and self.__rangetuple is not None:
#            subMask = self.__dataset.mask[self.__rangetuple[0]:self.__rangetuple[1], :, 0]
#            if not 1 in subMask:
#                # There are some values that we do not have.
#                return


        self.__ipcstream.sendRequest(self.__genQuery())
        if self.__ipcstream.failed:
            print "IPC error: {}.".format(self.__ipcstream.errmsg)
            return None
        # This is where the actual communication with the backend happens
        rawarray = json.load(self.__ipcstream)
        if len(rawarray) == 0:
            print "Got empty result"
            return None

        # tabledat has shape (m, n) where n is the number of channels
        # and m the vector length of the channel.
        tabledat = np.array(rawarray)
        # XXX xdat not used yet
        xnum = len(self.__xfields)
        ydat = tabledat[:,xnum:]

        nSl     = self.getSkiplines()
        lenPart = ydat.shape[0]
        nCh     = ydat.shape[1]

        if xnum > 0:
            xdat = tabledat[:,:xnum]
        else:
            # No X axis defined, generate X axis as index of Y axis.
            xdat = np.tile(np.arange(lenPart) * nSl, nCh).reshape(nCh, lenPart).T

        # Pyqtgraph needs an ndarray with shape (N, 2) per channel
        # Construct a masked ndarray with shape (N, 2, M) 
        # N is the vector length, M is the number of channels, 2 is for X and Y axis
        if self.__dataset is None:
            tmpVect = np.zeros(lenPart * nSl * 2 * nCh).reshape(lenPart * nSl, 2, nCh)
            tmpMask = np.ones (lenPart * nSl * 2 * nCh).reshape(lenPart * nSl, 2, nCh)
            self.__dataset = ma.masked_array(tmpVect.copy(), mask = tmpMask.copy())

        arrIndex = np.arange(lenPart) * nSl
        self.__dataset[arrIndex, 0, :] = xdat
        self.__dataset[arrIndex, 1, :] = ydat
        self.__dataset.mask[arrIndex, :, :] = False

        # We have the masked array, however we only return the valid data
        # We have to put it in shape
        retData = self.__dataset[~self.__dataset.mask]
        retLen = len(retData) / nCh / 2
        retShape = (retLen, 2, nCh)
        return retData.reshape(retShape)

    def __genRangeForQuery(self):
        if self.__rangetuple is None:
            rangetxt = "All"
        elif len(self.__rangetuple) < 2:
            rangetxt = "All"
        else:
            rangetxt = "Subset {} {}".format(self.__rangetuple[0], self.__rangetuple[1])
        return rangetxt

    def getRange(self):
        return self.__rangetuple

    def setRange(self, x):
        self.__rangetuple = x

    def getSkiplines(self):
        return self.__skiplines

    def setSkiplines(self, x):
        self.__skiplines = x

    @property
    def samplename(self):
        base = os.path.basename(self.__filename)
        sext = os.path.splitext(base)
        return sext[0]

    @property
    def rawquery(self):
        query = self.__genQuery()
        return query

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
