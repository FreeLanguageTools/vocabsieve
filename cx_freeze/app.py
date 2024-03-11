#!/usr/bin/env python3
import sys
import os

class dummyStream:
    ''' dummyStream behaves like a stream but does nothing. '''

    def __init__(self): pass
    def write(self, data): pass
    def read(self, data): pass
    def flush(self): pass
    def close(self): pass

if os.environ.get('VOCABSIEVE_DEBUG_BUILD'):
    # redirect all streams to dummy to stop error on stdout
    sys.stdout = dummyStream()
    sys.stderr = dummyStream()
    sys.stdin = dummyStream()
    sys.__stdout__ = dummyStream()
    sys.__stderr__ = dummyStream()
    sys.__stdin__ = dummyStream()
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    from vocabsieve.main import main
    main()
