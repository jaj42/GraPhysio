#!/usr/local/bin/python2.7

import socket

class DataStream:
    def __init__(self, query):
        self.endreached = False
        self.buf = ""
        self.startsock(query)
    def startsock(self, query):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", 4242))
        self.sock.sendall(query)
        # read one line
        # if error: self.endreached = True
    def fillbuf(self):
        if self.endreached == True:
            self.sock.close()
            return
        self.buf += self.sock.recv(2048)
        # Data ends with newline
        if self.buf.endswith("\n"):
            self.endreached = True
            self.buf = self.buf.rstrip("\n")
    def read(self, n=-1):
        if n < 0:
            while not self.endreached:
                self.fillbuf()
            data = self.buf
        else:
            while len(self.buf) < n and not self.endreached:
                self.fillbuf()
            data = self.buf[:n]
        self.buf = ""
        return data
