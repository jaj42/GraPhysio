import rpc

import json
import os
import numpy as np
from string import Template

def runQuery(csvquery):
    reader = rpc.DataStream(csvquery.query)
    jsdata = json.load(reader)
    return np.matrix(jsdata)

class CSVQuery:
    querytemplate = Template('ReadVector {fileName = "$filename", seperator = \'$sep\','
                             'fields = [$fields],'
                             'range = $range,'
                             'notnull = [$notnull],'
                             'skiplines = $skiplines}')

    def __init__(self, filename, seperator, fields, notnull, linerange, skiplines):
        self.filename  = str(filename)
        self.fields    = fields
        self.notnull   = notnull
        self.sep       = seperator
        self.linerange = linerange
        self.skiplines = skiplines

        strfields  = ', '.join('"' + str(x) + '"' for x in fields)
        strnotnull = ', '.join('"' + str(x) + '"' for x in notnull)
        self.query = self.querytemplate.substitute(filename=filename, sep=seperator, fields=strfields,
                                                   notnull=strnotnull, range=linerange, skiplines=skiplines)

    @property
    def samplename(self):
        base = os.path.basename(self.filename)
        sext = os.path.splitext(base)
        return sext[0]

    @property
    def query(self):
        # todo update query with new values
        return self.query

    @property
    def file(self):
        return self.filename

    @property
    def seperator(self):
        return self.sep

    @property
    def fields(self):
        return self.fields

    @property
    def notnull(self):
        return self.notnull

    @property
    def range(self):
        return self.linerange

    @property
    def every(self):
        return self.skiplines
    @every.setter
    def every(self, x):
        self.skiplines = x
