#!/usr/bin/env python3
# mypy: ignore-errors
from PyQt5.QtWidgets import QApplication  # pylint: disable=wrong-import-position
import sys


class dummyStream:
    ''' dummyStream behaves like a stream but does nothing. '''

    def __init__(self):
        pass

    def write(self, data):
        pass

    def read(self, data):
        pass

    def flush(self):
        pass

    def close(self):
        pass


# check if we are on windows
# redirect all streams to dummy to stop crashing because there is no stdout
sys.stdout = dummyStream()
sys.stderr = dummyStream()
sys.stdin = dummyStream()
sys.__stdout__ = dummyStream()
sys.__stderr__ = dummyStream()
sys.__stdin__ = dummyStream()


if __name__ == "__main__":
    from vocabsieve.main import main
    main()
